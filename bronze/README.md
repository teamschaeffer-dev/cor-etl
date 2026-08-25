# 🥉 Bronze Layer

The Bronze layer serves as the raw ingestion stage for all source data.

## Key Design Principles
1. **Raw Format Preservation**: Data is stored in raw JSON / semi-structured `VARIANT` formats directly as fetched from the source (e.g. SharePoint API).
2. **Metadata Enrichment**: Every raw record is tagged with audit columns:
   - `_ingested_at` (TIMESTAMP_NTZ)
   - `_source_system` (VARCHAR)
   - `_batch_id` (VARCHAR)
   - `raw_payload` (VARIANT)
3. **Immutable & Append-Only**: Records are appended without destructively updating existing rows, maintaining audit history for complete lineage and reproducibility.

## Folder Structure
- `ddl/`: DDL scripts for Snowflake Bronze schemas, internal stages, and raw landing tables.
- `pipelines/`: Python ingestion scripts for extracting source data and staging into Snowflake.
