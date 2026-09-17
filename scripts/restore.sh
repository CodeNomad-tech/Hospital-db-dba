#!/bin/bash
# ============================================================
# Restore the hospital database from a pg_dump custom-format backup.
# Usage: ./restore.sh /path/to/hospital_db_TIMESTAMP.dump
#
# This restores into a freshly created database named hospital_db_restore
# so you never overwrite production data by accident. Rename/promote it
# manually once you've verified it.
# ============================================================
set -euo pipefail

BACKUP_FILE="${1:?Usage: ./restore.sh <backup_file.dump>}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-hospital_admin_login}"
RESTORE_DB_NAME="${RESTORE_DB_NAME:-hospital_db_restore}"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Backup file not found: $BACKUP_FILE" >&2
    exit 1
fi

echo "[$(date)] Creating clean target database: ${RESTORE_DB_NAME}"
dropdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" --if-exists "$RESTORE_DB_NAME"
createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$RESTORE_DB_NAME"

echo "[$(date)] Restoring ${BACKUP_FILE} into ${RESTORE_DB_NAME}..."
pg_restore -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$RESTORE_DB_NAME" \
    --no-owner --no-privileges --jobs=4 "$BACKUP_FILE"

echo "[$(date)] Restore complete. Verifying row counts..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$RESTORE_DB_NAME" -c "
    SELECT 'patients' AS table_name, COUNT(*) FROM hospital.patients
    UNION ALL SELECT 'appointments', COUNT(*) FROM hospital.appointments
    UNION ALL SELECT 'admissions', COUNT(*) FROM hospital.admissions;
"

echo "[$(date)] Done. Review ${RESTORE_DB_NAME}, then promote it if it checks out."
