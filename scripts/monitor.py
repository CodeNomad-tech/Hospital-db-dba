#!/usr/bin/env python3
"""
monitor.py - lightweight DBA health check for the hospital database.

Checks:
  1. Slowest queries (via pg_stat_statements)
  2. Current connection count vs max_connections
  3. Table bloat / dead tuple estimate (needs VACUUM?)
  4. Long-running / idle-in-transaction sessions
  5. Replication lag (if a replica is attached)

Usage:
  pip install psycopg2-binary
  python monitor.py --host localhost --port 5432 --db hospital_db --user hospital_admin_login
"""

import argparse
import sys
import psycopg2
import psycopg2.extras


def connect(args):
    return psycopg2.connect(
        host=args.host, port=args.port, dbname=args.db,
        user=args.user, password=args.password,
    )


def run(conn, label, query, warn_fn=None):
    print(f"\n--- {label} ---")
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        try:
            cur.execute(query)
        except psycopg2.Error as e:
            print(f"  (skipped: {e.pgerror.strip() if e.pgerror else e})")
            conn.rollback()
            return
        rows = cur.fetchall()
        if not rows:
            print("  OK - nothing to report")
            return
        for row in rows:
            line = ", ".join(f"{k}={v}" for k, v in row.items())
            flag = " ⚠" if warn_fn and warn_fn(row) else ""
            print(f"  {line}{flag}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="localhost")
    p.add_argument("--port", default="5432")
    p.add_argument("--db", default="hospital_db")
    p.add_argument("--user", default="hospital_admin_login")
    p.add_argument("--password", default="")
    args = p.parse_args()

    conn = connect(args)
    conn.autocommit = True

    run(conn, "Top 5 slowest queries (avg ms)", """
        SELECT substring(query, 1, 60) AS query, calls,
               round(mean_exec_time::numeric, 2) AS avg_ms,
               round(total_exec_time::numeric, 2) AS total_ms
        FROM pg_stat_statements
        ORDER BY mean_exec_time DESC
        LIMIT 5;
    """, warn_fn=lambda r: r["avg_ms"] and r["avg_ms"] > 100)

    run(conn, "Connections vs limit", """
        SELECT count(*) AS current_connections,
               (SELECT setting FROM pg_settings WHERE name = 'max_connections') AS max_connections
        FROM pg_stat_activity;
    """)

    run(conn, "Tables needing VACUUM (dead tuples > 10%)", """
        SELECT relname AS table_name, n_live_tup, n_dead_tup,
               round(100.0 * n_dead_tup / GREATEST(n_live_tup + n_dead_tup, 1), 1) AS dead_pct
        FROM pg_stat_user_tables
        WHERE n_dead_tup > 0
        ORDER BY dead_pct DESC
        LIMIT 10;
    """, warn_fn=lambda r: r["dead_pct"] and r["dead_pct"] > 10)

    run(conn, "Long-running or idle-in-transaction sessions", """
        SELECT pid, state, now() - query_start AS duration,
               substring(query, 1, 50) AS query
        FROM pg_stat_activity
        WHERE state != 'idle'
          AND now() - query_start > interval '5 seconds'
        ORDER BY duration DESC;
    """)

    run(conn, "Replication lag (replicas attached to this node)", """
        SELECT client_addr, state,
               pg_wal_lsn_diff(sent_lsn, replay_lsn) AS lag_bytes
        FROM pg_stat_replication;
    """, warn_fn=lambda r: r["lag_bytes"] and r["lag_bytes"] > 10_000_000)

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    sys.exit(main())
