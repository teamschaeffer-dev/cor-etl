import os
import json
import uuid
import tempfile
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

import snowflake.connector
from .sharepoint_client import SharePointGraphClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def load_environment():
    """Load configuration from .env file if available."""
    env_paths = [
        Path(__file__).resolve().parents[3] / ".env",
        Path(__file__).resolve().parents[3] / "config" / ".env",
    ]
    for env_path in env_paths:
        if env_path.exists():
            logger.info(f"Loading environment variables from {env_path}")
            load_dotenv(dotenv_path=env_path)
            break


def get_snowflake_connection():
    """Create and return a Snowflake connection using environment parameters."""
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        role=os.getenv("SNOWFLAKE_ROLE", "ETL_ROLE"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
        database=os.getenv("SNOWFLAKE_DATABASE", "COR_DB"),
        schema=os.getenv("SNOWFLAKE_SCHEMA", "BRONZE"),
    )


def stage_and_load_to_snowflake(conn, items: list, batch_id: str):
    """Write raw JSON payloads to a temporary file, stage to Snowflake, and COPY into RAW_SHAREPOINT_DATA table."""
    if not items:
        logger.warning("No items to load into Snowflake.")
        return

    cursor = conn.cursor()
    try:
        # Format records with audit metadata wrapper
        records_to_load = []
        for item in items:
            record_id = str(item.get("id", ""))
            records_to_load.append({
                "record_id": record_id,
                "raw_payload": item,
                "_batch_id": batch_id,
                "_source_system": "SHAREPOINT_API"
            })

        # Write records to local temporary JSON file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp_file:
            json.dump(records_to_load, tmp_file)
            tmp_file_path = tmp_file.name

        filename = os.path.basename(tmp_file_path)
        logger.info(f"Staging temporary file {filename} to Snowflake @BRONZE.RAW_SHAREPOINT_STAGE...")

        # 1. PUT local JSON file to Snowflake stage
        put_sql = f"PUT file://{tmp_file_path.replace('\\', '/')} @BRONZE.RAW_SHAREPOINT_STAGE/{batch_id}/ OVERWRITE = TRUE"
        cursor.execute(put_sql)

        # 2. COPY INTO RAW_SHAREPOINT_DATA table from stage
        logger.info("Executing COPY INTO BRONZE.RAW_SHAREPOINT_DATA...")
        copy_sql = f"""
            COPY INTO BRONZE.RAW_SHAREPOINT_DATA (record_id, raw_payload, _source_system, _batch_id, _ingested_at)
            FROM (
                SELECT 
                    $1:record_id::VARCHAR,
                    $1:raw_payload::VARIANT,
                    $1:_source_system::VARCHAR,
                    $1:_batch_id::VARCHAR,
                    CURRENT_TIMESTAMP()
                FROM @BRONZE.RAW_SHAREPOINT_STAGE/{batch_id}/
            )
            FILE_FORMAT = (TYPE = 'JSON' STRIP_OUTER_ARRAY = TRUE)
            ON_ERROR = 'CONTINUE';
        """
        cursor.execute(copy_sql)
        logger.info("Successfully loaded records into BRONZE.RAW_SHAREPOINT_DATA.")

        # Clean up local temporary file
        os.remove(tmp_file_path)

    finally:
        cursor.close()


def run_pipeline():
    """Main execution function for SharePoint to Bronze Snowflake pipeline."""
    load_environment()

    # Retrieve parameters
    tenant_id = os.getenv("AZURE_TENANT_ID")
    client_id = os.getenv("AZURE_CLIENT_ID")
    client_secret = os.getenv("AZURE_CLIENT_SECRET")
    site_id = os.getenv("SHAREPOINT_SITE_ID")
    list_id = os.getenv("SHAREPOINT_LIST_ID")

    if not all([tenant_id, client_id, client_secret, site_id, list_id]):
        missing = [k for k, v in {
            "AZURE_TENANT_ID": tenant_id,
            "AZURE_CLIENT_ID": client_id,
            "AZURE_CLIENT_SECRET": client_secret,
            "SHAREPOINT_SITE_ID": site_id,
            "SHAREPOINT_LIST_ID": list_id
        }.items() if not v]
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    batch_id = f"sharepoint_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    logger.info(f"Starting SharePoint Ingestion Pipeline. Batch ID: {batch_id}")

    # Step 1: Extract from SharePoint
    sp_client = SharePointGraphClient(tenant_id=tenant_id, client_id=client_id, client_secret=client_secret)
    items = sp_client.get_list_items(site_id=site_id, list_id=list_id)

    # Step 2: Load to Snowflake Bronze Layer
    conn = get_snowflake_connection()
    try:
        stage_and_load_to_snowflake(conn, items, batch_id)
    finally:
        conn.close()

    logger.info("SharePoint to Bronze pipeline completed successfully.")


if __name__ == "__main__":
    run_pipeline()
