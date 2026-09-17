#!/bin/bash
# ============================================================
# Nightly logical backup of the hospital database.
# Usage: ./backup.sh
# Cron example (2 AM daily):
#   0 2 * * * /path/to/hospital-db-dba/scripts/backup.sh >> /var/log/hospital_backup.log 2>&1
# ============================================================
set -euo pipefail

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-hospital_db}"
DB_USER="${DB_USER:-hospital_admin_login}"
BACKUP_DIR="${BACKUP_DIR:-$(dirname "$0")/../backups}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/hospital_db_${TIMESTAMP}.dump"

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting backup -> ${BACKUP_FILE}"

# Custom format (-Fc): compressed, supports selective/parallel restore.
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -Fc -f "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "[$(date)] Backup succeeded: $(du -h "$BACKUP_FILE" | cut -f1)"
else
    echo "[$(date)] Backup FAILED" >&2
    exit 1
fi

# Verify the dump isn't corrupt before trusting it.
pg_restore --list "$BACKUP_FILE" > /dev/null
echo "[$(date)] Backup integrity check passed."

# Rotate old backups.
find "$BACKUP_DIR" -name "hospital_db_*.dump" -mtime +"$RETENTION_DAYS" -delete
echo "[$(date)] Rotated backups older than ${RETENTION_DAYS} days."
