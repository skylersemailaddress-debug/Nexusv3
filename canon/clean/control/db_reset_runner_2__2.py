import json
import os
import sys

try:
    import psycopg
except Exception as e:
    print(f"PSYCO_PG_IMPORT_ERROR: {e}", file=sys.stderr)
    sys.exit(2)

db_name = os.environ["NEXUS_DB_NAME"]
db_user = os.environ["NEXUS_DB_USER"]
db_password = os.environ["NEXUS_DB_PASSWORD"]
db_host = os.environ["NEXUS_DB_HOST"]
db_port = int(os.environ["NEXUS_DB_PORT"])
report_path = os.environ["NEXUS_DB_REPORT"]

conninfo = f"host={db_host} port={db_port} user={db_user} password={db_password} dbname=postgres"

with psycopg.connect(conninfo, autocommit=True) as conn:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s AND pid <> pg_backend_pid()",
            (db_name,),
        )
        cur.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
        cur.execute(f'CREATE DATABASE "{db_name}"')
        cur.execute("SELECT datname FROM pg_database WHERE datname = %s", (db_name,))
        row = cur.fetchone()
        if not row or row[0] != db_name:
            raise RuntimeError(f"Database verification failed for {db_name}")

result = {
    "db_name": db_name,
    "db_user": db_user,
    "db_host": db_host,
    "db_port": db_port,
    "status": "db-reset-complete",
}
with open(report_path, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2)
