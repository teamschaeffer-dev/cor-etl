-- ==============================================================================
-- Snowflake Bronze Layer Schema & Table Initialization
-- Database: COR_DB
-- Schema:   BRONZE
-- ==============================================================================

USE DATABASE COR_DB;

-- Create Bronze Schema if not exists
CREATE SCHEMA IF NOT EXISTS BRONZE;
USE SCHEMA BRONZE;

-- Create Internal Stage for staging raw JSON payloads before COPY INTO
CREATE STAGE IF NOT EXISTS BRONZE.RAW_SHAREPOINT_STAGE
    FILE_FORMAT = (TYPE = 'JSON' STRIP_OUTER_ARRAY = TRUE);

-- Create Raw Landing Table for SharePoint Data
-- Stores exact API response payload in VARIANT with audit tracking metadata
CREATE TABLE IF NOT EXISTS BRONZE.RAW_SHAREPOINT_DATA (
    record_id        VARCHAR(255)       DEFAULT NULL,
    raw_payload      VARIANT            NOT NULL,
    _source_system   VARCHAR(100)       DEFAULT 'SHAREPOINT_API',
    _batch_id        VARCHAR(100)       NOT NULL,
    _ingested_at     TIMESTAMP_NTZ      DEFAULT CURRENT_TIMESTAMP()
);

-- Comment on Bronze Table
COMMENT ON TABLE BRONZE.RAW_SHAREPOINT_DATA IS 'Raw append-only landing table for SharePoint list items and documents ingested via API';
