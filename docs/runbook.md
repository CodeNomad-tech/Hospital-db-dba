# DBA Runbook

Operational procedures for this database, written the way an on-call DBA
would want them: short, exact commands, no ambiguity.

## Daily backup

Automated via cron (see `scripts/backup.sh`):

```bash
0 2 * * * /path/to/hospital-db-dba/scripts/backup.sh >> /var/log/hospital_backup.log 2>&1
```

Manual run:
```bash
./scripts/backup.sh
```

Backups are custom-format `pg_dump` files in `backups/`, retained for
14 days by default (`RETENTION_DAYS` env var), and integrity-checked
with `pg_restore --list` immediately after creation so a corrupt backup
is caught the same night, not during an actual outage.

## Restore / disaster recovery

```bash
./scripts/restore.sh backups/hospital_db_20260101_020000.dump
```

This restores into a **new** database (`hospital_db_restore`), never
directly over production. Steps after restore:
1. Verify row counts printed at the end of the script look sane.
2. Spot-check a few known records.
3. Only then: rename databases or repoint the app connection string.

**RTO/RPO for this setup:** RPO is bounded by backup frequency (24h with
the default cron). For a lower RPO, add WAL archiving
(`archive_mode = on`) for point-in-time recovery instead of relying on
nightly dumps alone.

## Adding a new user

```sql
-- Pick the role matching their job function (see sql/03_roles_and_permissions.sql)
CREATE USER new_doctor_username WITH PASSWORD 'use_a_generated_password' IN ROLE hospital_doctor;
```

Never grant `hospital_admin` to an application user. It should only be
used interactively by the DBA, and ideally only via a bastion/jump host.

## Removing a user

```sql
REASSIGN OWNED BY departing_user TO hospital_admin_login;
DROP OWNED BY departing_user;
DROP USER departing_user;
```

## Setting up replication (already automated in docker-compose)

The replica in `docker/docker-compose.yml` bootstraps itself via
`pg_basebackup -R` on first start, which streams a full copy of the
primary and configures standby mode automatically. To check replication
health:

```bash
python scripts/monitor.py --host localhost --user hospital_admin_login
```

Look at the "Replication lag" section of the output — anything flagged
with ⚠ (>10MB behind) needs investigation: check network between
primary/replica, and confirm the replica isn't CPU/disk starved.

## Promoting the replica (primary failure)

```bash
docker exec hospital-db-replica pg_ctl promote -D /var/lib/postgresql/data
```

After promotion, repoint the application's connection string at the
former replica, then rebuild a new replica once a new primary is
established.

## Routine health check

```bash
python scripts/monitor.py --host localhost --user hospital_admin_login
```

Run this manually when the app "feels slow," or on a schedule
(cron/CI) and pipe output to your alerting channel of choice. It flags:
slow queries, connection count, table bloat, long-running transactions,
and replication lag.

## Incident: table is bloated / slow after mass update

```sql
VACUUM (VERBOSE, ANALYZE) hospital.appointments;
```

If bloat is severe and downtime is acceptable:
```sql
VACUUM FULL hospital.appointments;  -- takes an exclusive lock, plan a maintenance window
```

## Incident: a query is suddenly slow

1. `EXPLAIN ANALYZE` the query — check for a seq scan where an index
   scan was expected.
2. Check `pg_stat_statements` (via `scripts/monitor.py`) for what
   changed in call volume.
3. Check `pg_stat_user_tables` — has this table's data grown/shifted
   enough that the planner's row estimates are stale? Run `ANALYZE
   table_name;`.
