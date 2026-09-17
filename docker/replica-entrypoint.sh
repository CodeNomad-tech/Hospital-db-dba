#!/bin/bash
set -e

if [ -z "$(ls -A "$PGDATA" 2>/dev/null)" ]; then
    echo "Replica data directory empty - taking base backup from primary..."
    export PGPASSWORD="${POSTGRES_PASSWORD}"

    until pg_isready -h db-primary -p 5432 -U replicator; do
        echo "Waiting for primary to be ready..."
        sleep 2
    done

    pg_basebackup -h db-primary -D "$PGDATA" -U replicator -Fp -Xs -P -R

    # -R writes standby.signal + primary_conninfo automatically.
    echo "Base backup complete. Starting as standby."
fi

exec docker-entrypoint.sh postgres
