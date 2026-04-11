from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from app.db import get_conn
from app.settings import settings
from app.services.automation_scheduler import register_default_rules

MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"
REQUIRED_TABLES = (
    "projects",
    "objectives",
    "next_steps",
    "blockers",
    "messages",
    "memory_records",
    "jobs",
    "project_state",
)
MIGRATIONS = (
    ("001_init", MIGRATIONS_DIR / "001_init.sql"),
    ("002_v2_bridge", MIGRATIONS_DIR / "002_v2_bridge.sql"),
    ("003_bridge_seed_sync", MIGRATIONS_DIR / "003_bridge_seed_sync.sql"),
    ("004_execution_hardening", MIGRATIONS_DIR / "004_execution_hardening.sql"),
    ("005_job_approval", MIGRATIONS_DIR / "005_job_approval.sql"),
    ("006_enterprise_foundation", MIGRATIONS_DIR / "006_enterprise_foundation.sql"),
    ("007_distributed_runners", MIGRATIONS_DIR / "007_distributed_runners.sql"),
    ("008_nexus_v2_wave2", MIGRATIONS_DIR / "008_nexus_v2_wave2.sql"),
)

_BOOTSTRAP_STATUS: dict[str, object] = {
    "ok": False,
    "canonical_db": settings.canonical_db_name,
    "database_name": None,
    "applied_migrations": [],
    "missing_tables": [],
    "default_project_present": False,
}


def _database_name() -> str:
    path = urlparse(settings.database_url).path.strip("/")
    if not path:
        raise RuntimeError("DATABASE_URL must include a database name")
    return path.split("/")[-1]


def validate_canonical_database() -> str:
    db_name = _database_name()
    if db_name != settings.canonical_db_name:
        raise RuntimeError(
            f"Invalid DATABASE_URL database '{db_name}'. Expected '{settings.canonical_db_name}'."
        )
    _BOOTSTRAP_STATUS["database_name"] = db_name
    return db_name


def _ensure_schema_migrations(cur) -> None:
    cur.execute(
        """
        create table if not exists schema_migrations (
            id text primary key,
            applied_at timestamptz not null default now()
        )
        """
    )


def _table_exists(cur, table_name: str) -> bool:
    cur.execute(
        """
        select 1
        from information_schema.tables
        where table_schema = 'public' and table_name = %s
        limit 1
        """,
        (table_name,),
    )
    return cur.fetchone() is not None


def _column_exists(cur, table_name: str, column_name: str) -> bool:
    cur.execute(
        """
        select 1
        from information_schema.columns
        where table_schema = 'public'
          and table_name = %s
          and column_name = %s
        limit 1
        """,
        (table_name, column_name),
    )
    return cur.fetchone() is not None


def reconcile_bridge_schema() -> None:
    with get_conn() as conn, conn.cursor() as cur:
        if not _table_exists(cur, "projects"):
            return
        _ensure_schema_migrations(cur)

        if _table_exists(cur, "messages"):
            cur.execute(
                """
                alter table messages
                  add column if not exists content_text text,
                  add column if not exists content_structured jsonb,
                  add column if not exists sequence_no bigint
                """
            )

            if _column_exists(cur, "messages", "content") and _column_exists(cur, "messages", "content_text"):
                cur.execute(
                    """
                    update messages
                    set content_text = content
                    where content_text is null
                    """
                )

            cur.execute(
                """
                with ranked as (
                  select id,
                         row_number() over (
                           partition by project_id
                           order by created_at, id
                         ) as seq
                  from messages
                )
                update messages m
                set sequence_no = ranked.seq
                from ranked
                where m.id = ranked.id
                  and (m.sequence_no is null or m.sequence_no <> ranked.seq)
                """
            )

            cur.execute("select count(*) as n from messages where sequence_no is null")
            row = cur.fetchone()
            remaining_nulls = row["n"] if isinstance(row, dict) else row[0]
            if remaining_nulls == 0:
                cur.execute("alter table messages alter column sequence_no set not null")

            cur.execute(
                """
                create unique index if not exists idx_messages_project_sequence_no
                on messages(project_id, sequence_no)
                """
            )

        if _table_exists(cur, "jobs"):
            cur.execute(
                """
                alter table jobs
                  add column if not exists claimed_by text,
                  add column if not exists claim_token text,
                  add column if not exists approval_required boolean not null default false,
                  add column if not exists approval_status text not null default 'not_required',
                  add column if not exists retry_count integer not null default 0,
                  add column if not exists max_retries integer not null default 0,
                  add column if not exists next_retry_at timestamptz,
                  add column if not exists lease_expires_at timestamptz,
                  add column if not exists dead_lettered_at timestamptz,
                  add column if not exists last_retry_at timestamptz,
                  add column if not exists approved_by text,
                  add column if not exists approved_at timestamptz,
                  add column if not exists rejected_by text,
                  add column if not exists rejected_at timestamptz,
                  add column if not exists rejection_reason text,
                  add column if not exists failure_class text,
                  add column if not exists failure_signature text,
                  add column if not exists retry_policy text,
                  add column if not exists last_failure_at timestamptz
                """
            )

        if _table_exists(cur, "projects"):
            cur.execute(
                """
                create table if not exists project_state (
                  id text primary key,
                  project_id text unique not null references projects(id) on delete cascade,
                  current_objective text,
                  next_step text,
                  status text not null default 'active',
                  structured_state jsonb not null default '{}'::jsonb,
                  version_no bigint not null default 1,
                  updated_at timestamptz not null default now()
                )
                """
            )

            objectives_exists = _table_exists(cur, "objectives")
            next_steps_exists = _table_exists(cur, "next_steps")

            if objectives_exists and next_steps_exists:
                cur.execute(
                    """
                    insert into project_state (
                      id,
                      project_id,
                      current_objective,
                      next_step,
                      status,
                      structured_state,
                      version_no,
                      updated_at
                    )
                    select
                      'state-' || p.id,
                      p.id,
                      o.title,
                      ns.title,
                      'active',
                      jsonb_build_object(
                        'current_objective_id', p.current_objective_id,
                        'next_step_id', o.next_step_id,
                        'blocker_ids_open', '[]'::jsonb,
                        'meta', '{}'::jsonb
                      ),
                      1,
                      now()
                    from projects p
                    left join objectives o
                      on o.id = p.current_objective_id
                    left join next_steps ns
                      on ns.id = o.next_step_id
                    on conflict (project_id) do update
                    set current_objective = excluded.current_objective,
                        next_step = excluded.next_step,
                        structured_state = excluded.structured_state,
                        updated_at = now()
                    """
                )

        cur.execute(
            """
            create table if not exists system_control_plane (
              system_key text primary key,
              mode text not null default 'active',
              reason text,
              updated_by text,
              updated_at timestamptz not null default now()
            )
            """
        )
        cur.execute(
            """
            insert into system_control_plane (system_key, mode, reason, updated_by)
            values ('global', 'active', 'bootstrap', 'system')
            on conflict (system_key) do nothing
            """
        )
        cur.execute(
            """
            create table if not exists runner_heartbeats (
              runner_id text primary key,
              status text not null default 'idle',
              project_id text,
              job_id text,
              last_heartbeat timestamptz not null default now(),
              meta jsonb not null default '{}'::jsonb,
              capabilities jsonb not null default '[]'::jsonb,
              max_concurrency integer not null default 1,
              desired_state text not null default 'active',
              last_claim_at timestamptz
            )
            """
        )
        cur.execute(
            """
            alter table runner_heartbeats
              add column if not exists capabilities jsonb not null default '[]'::jsonb,
              add column if not exists max_concurrency integer not null default 1,
              add column if not exists desired_state text not null default 'active',
              add column if not exists last_claim_at timestamptz
            """
        )
        cur.execute(
            """
            create table if not exists audit_log (
              id bigserial primary key,
              action text not null,
              actor text not null,
              role text not null,
              project_id text,
              job_id text,
              request_id text,
              outcome text not null default 'success',
              details jsonb not null default '{}'::jsonb,
              created_at timestamptz not null default now()
            )
            """
        )
        cur.execute(
            """
            create table if not exists state_versions (
              id bigserial primary key,
              project_id text not null,
              version_no bigint not null,
              source text not null,
              request_id text,
              job_id text,
              artifact_id text,
              snapshot jsonb not null default '{}'::jsonb,
              created_at timestamptz not null default now()
            )
            """
        )
        cur.execute(
            """
            create table if not exists plans (
              id text primary key,
              project_id text not null references projects(id) on delete cascade,
              title text not null,
              objective text not null,
              status text not null default 'draft',
              requested_by text,
              replan_count integer not null default 0,
              meta jsonb not null default '{}'::jsonb,
              created_at timestamptz not null default now(),
              updated_at timestamptz not null default now()
            )
            """
        )
        cur.execute(
            """
            create table if not exists plan_steps (
              id text primary key,
              plan_id text not null references plans(id) on delete cascade,
              project_id text not null references projects(id) on delete cascade,
              title text not null,
              description text,
              status text not null default 'pending',
              order_index integer not null default 0,
              dependency_ids jsonb not null default '[]'::jsonb,
              last_job_id text,
              outcome_summary text,
              meta jsonb not null default '{}'::jsonb,
              created_at timestamptz not null default now(),
              updated_at timestamptz not null default now()
            )
            """
        )
        cur.execute(
            """
            create table if not exists automation_rules (
              id text primary key,
              name text not null,
              trigger_type text not null,
              trigger_key text not null,
              enabled boolean not null default true,
              dry_run boolean not null default true,
              schedule_seconds integer,
              action_kind text not null default 'observe',
              meta jsonb not null default '{}'::jsonb,
              created_at timestamptz not null default now(),
              updated_at timestamptz not null default now()
            )
            """
        )
        cur.execute(
            """
            create table if not exists automation_runs (
              id bigserial primary key,
              rule_id text references automation_rules(id) on delete set null,
              trigger_type text not null,
              trigger_key text not null,
              project_id text,
              status text not null default 'recorded',
              dry_run boolean not null default true,
              details jsonb not null default '{}'::jsonb,
              created_at timestamptz not null default now()
            )
            """
        )
        register_default_rules(cur)

        conn.commit()


def run_migrations() -> list[str]:
    applied: list[str] = []
    with get_conn() as conn, conn.cursor() as cur:
        _ensure_schema_migrations(cur)
        conn.commit()

        for migration_id, migration_path in MIGRATIONS:
            cur.execute("select 1 from schema_migrations where id = %s", (migration_id,))
            if cur.fetchone():
                continue

            sql = migration_path.read_text(encoding="utf-8")
            cur.execute(sql)
            cur.execute(
                "insert into schema_migrations (id) values (%s) on conflict (id) do nothing",
                (migration_id,),
            )
            conn.commit()
            applied.append(migration_id)

    _BOOTSTRAP_STATUS["applied_migrations"] = applied
    return applied


def validate_required_tables() -> list[str]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            select tablename
            from pg_tables
            where schemaname = 'public'
            """
        )
        rows = cur.fetchall()
        existing = set()
        for row in rows:
            if isinstance(row, dict):
                existing.add(row["tablename"])
            else:
                existing.add(row[0])

    missing = [table for table in REQUIRED_TABLES if table not in existing]
    _BOOTSTRAP_STATUS["missing_tables"] = missing
    if missing:
        raise RuntimeError(f"Missing required tables: {missing}")
    return missing


def ensure_default_project() -> bool:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            insert into projects (id, name, status)
            values ('default', 'Default Project', 'active')
            on conflict (id) do nothing
            """
        )
        conn.commit()

        cur.execute("select 1 from projects where id = 'default'")
        exists = cur.fetchone() is not None

    _BOOTSTRAP_STATUS["default_project_present"] = exists
    if not exists:
        raise RuntimeError("Canonical project 'default' is missing")
    return exists


def bootstrap_system() -> dict[str, object]:
    validate_canonical_database()
    reconcile_bridge_schema()
    run_migrations()
    validate_required_tables()
    ensure_default_project()
    _BOOTSTRAP_STATUS["ok"] = True
    return dict(_BOOTSTRAP_STATUS)


def get_bootstrap_status() -> dict[str, object]:
    return dict(_BOOTSTRAP_STATUS)
