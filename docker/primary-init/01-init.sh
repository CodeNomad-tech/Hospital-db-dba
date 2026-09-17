#!/bin/bash
set -e

# Create a dedicated replication role (never reuse the superuser for this).
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE ROLE replicator WITH REPLICATION LOGIN PASSWORD '${POSTGRES_PASSWORD}';
EOSQL

# Allow the replica container to connect for streaming replication.
echo "host replication replicator 0.0.0.0/0 md5" >> "$PGDATA/pg_hba.conf"
echo "host all all 0.0.0.0/0 md5" >> "$PGDATA/pg_hba.conf"

# Load schema, indexes, roles, and seed data.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /sql/01_schema.sql
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /sql/02_indexes.sql
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /sql/03_roles_and_permissions.sql
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /sql/04_seed_data.sql
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -c "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;"
