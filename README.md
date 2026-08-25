# Snowflake Medallion Architecture ETL (`cor-etl`)

This repository contains data pipelines and Snowflake database definitions following the **Medallion Architecture** pattern (`Bronze` -> `Silver` -> `Gold`).

## Architecture Overview

```
               +-----------------------+
               |  SharePoint / External|
               +-----------+-----------+
                           |
                           v  (Ingestion)
              +------------+------------+
              |     BRONZE LAYER        |  Raw, append-only landing layer
              | (JSON / Raw Payload)    |
              +------------+------------+
                           |
                           v  (Cleaning & Deduplication)
              +------------+------------+
              |     SILVER LAYER        |  Conformed, cleaned data models
              | (Normalized Tables)     |
              +------------+------------+
                           |
                           v  (Aggregation & Business Logic)
              +------------+------------+
              |      GOLD LAYER         |  Analytics-ready Data Marts
              | (Star Schema / Views)   |
              +-------------------------+
```

### 🥉 Bronze Layer (`bronze/`)
- **Purpose**: Raw data ingestion from source systems (APIs, SharePoint, S3/Azure Blob stages).
- **Format**: Immutable, append-only staging tables preserving source structure (typically stored as Snowflake `VARIANT` or semi-structured JSON).
- **Example Pipeline**: `sharepoint_ingestion` pulls data from SharePoint via Microsoft Graph API and stages raw records into Snowflake.

### 🥈 Silver Layer (`silver/`)
- **Purpose**: Cleaned, transformed, standardized, and deduplicated data.
- **Format**: Relational tables with enforced data types, primary keys, and data hygiene constraints.

### 🥇 Gold Layer (`gold/`)
- **Purpose**: Business-level aggregations, dimensional modeling (star schemas), data marts, and reporting views.
- **Format**: Optimized tables and views consumption-ready for BI tools (Power BI, Tableau, ThoughtSpot).

---

## Directory Layout

```
cor-etl/
├── config/                  # Configuration templates and environment settings
├── bronze/                  # Raw layer DDL scripts and ingestion pipelines
│   ├── ddl/                 # Snowflake Bronze DDL scripts
│   └── pipelines/           # Ingestion code (SharePoint, APIs, etc.)
├── silver/                  # Silver layer DDL scripts & transformation logic
│   └── ddl/
└── gold/                    # Gold layer DDL scripts & aggregation logic
    └── ddl/
```

## Setup & Running Pipelines

1. **Environment Configuration**:
   Copy `config/config.example.env` to `.env` and fill in your credentials for Microsoft Azure / SharePoint and Snowflake:
   ```bash
   cp config/config.example.env .env
   ```

2. **Dependencies**:
   Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. **Database Preparation**:
   Run DDL scripts in `bronze/ddl/01_create_bronze_schema_and_tables.sql` in your Snowflake instance.

4. **Run Ingestion**:
   ```bash
   python -m bronze.pipelines.sharepoint_ingestion.load_sharepoint_to_bronze
   ```
