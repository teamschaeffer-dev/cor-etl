# 🥈 Silver Layer

The Silver layer contains cleaned, validated, normalized, and conformed data structures derived from raw Bronze landing tables.

## Key Design Principles
1. **Schema Enforcement**: Semi-structured `VARIANT` fields in Bronze are parsed, type-cast, and mapped into relational columns.
2. **Data Cleaning & Enrichment**:
   - Handle missing/null values.
   - Standardize column naming conventions (e.g. `snake_case`).
   - Deduplicate records based on business keys / entity IDs (`record_id`).
3. **Data Quality Verification**: Enforce data integrity constraints and validate key relationships.

## Folder Structure
- `ddl/`: DDL scripts for Snowflake Silver tables, views, and transformation procedures/models.
