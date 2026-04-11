from app.db import get_conn


def get_project_now(project_id: str) -> dict:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            select id, name, status, current_objective_id, active_pack_ids, meta, created_at, updated_at
            from projects
            where id = %s
            """,
            (project_id,),
        )
        project = cur.fetchone()

        if not project:
            return {"ok": False, "error": f"Project not found: {project_id}"}

        objective = None
        if project.get("current_objective_id"):
            cur.execute(
                """
                select id, title, description, status, priority, next_step_id, meta, created_at, updated_at
                from objectives
                where id = %s
                """,
                (project["current_objective_id"],),
            )
            objective = cur.fetchone()

        next_step = None
        if objective and objective.get("next_step_id"):
            cur.execute(
                """
                select id, title, status, kind, meta, created_at, updated_at
                from next_steps
                where id = %s
                """,
                (objective["next_step_id"],),
            )
            next_step = cur.fetchone()

        cur.execute(
            """
            select id, title, severity, status, meta, created_at, updated_at
            from blockers
            where project_id = %s and status = 'open'
            order by created_at desc
            """,
            (project_id,),
        )
        blockers = cur.fetchall()

        cur.execute(
            """
            select id, capability_id, status, approval_mode, risk_level, result, error, created_at, updated_at
            from jobs
            where project_id = %s
            order by created_at desc
            limit 10
            """,
            (project_id,),
        )
        recent_jobs = cur.fetchall()

        cur.execute(
            """
            select id, kind, title, path, payload, meta, created_at, updated_at
            from artifacts
            where project_id = %s
            order by created_at desc
            limit 10
            """,
            (project_id,),
        )
        recent_artifacts = cur.fetchall()

        cur.execute(
            """
            select id, role, content, meta, created_at
            from messages
            where project_id = %s
            order by created_at desc
            limit 10
            """,
            (project_id,),
        )
        recent_messages = list(reversed(cur.fetchall()))

        return {
            "ok": True,
            "project": project,
            "objective": objective,
            "next_step": next_step,
            "blockers": blockers,
            "recent_jobs": recent_jobs,
            "recent_artifacts": recent_artifacts,
            "recent_messages": recent_messages,
        }
