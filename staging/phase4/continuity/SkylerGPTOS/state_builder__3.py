from app.db import get_conn

def get_project_now(project_id: str, memory_query: str | None = None) -> dict:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            select id, name, status, active_pack_ids, meta, created_at, updated_at
            from projects
            where id = %s
            """,
            (project_id,),
        )
        project = cur.fetchone()

        if not project:
            return {"ok": False, "error": f"Project not found: {project_id}"}

        cur.execute(
            """
            select id, project_id, current_objective, next_step, status, structured_state, version_no, updated_at
            from project_state
            where project_id = %s
            """,
            (project_id,),
        )
        project_state = cur.fetchone()

        objective = None
        objective_id = None
        if project_state and project_state.get("structured_state"):
            objective_id = project_state["structured_state"].get("current_objective_id")

        if objective_id:
            cur.execute(
                """
                select id, title, description, status, priority, next_step_id, meta, created_at, updated_at
                from objectives
                where id = %s
                """,
                (objective_id,),
            )
            objective = cur.fetchone()

        next_step = None
        next_step_id = None
        if project_state and project_state.get("structured_state"):
            next_step_id = project_state["structured_state"].get("next_step_id")
        elif objective and objective.get("next_step_id"):
            next_step_id = objective["next_step_id"]

        if next_step_id:
            cur.execute(
                """
                select id, title, status, kind, meta, created_at, updated_at
                from next_steps
                where id = %s
                """,
                (next_step_id,),
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
            select id, role, content_text as content, meta, sequence_no, created_at
            from messages
            where project_id = %s
            order by sequence_no desc, created_at desc
            limit 10
            """,
            (project_id,),
        )
        recent_messages = list(reversed(cur.fetchall()))

        def fetch_memory(query_text: str | None):
            memory_clauses = [
                "status = 'active'",
                "(project_id = %s or project_id is null)",
                "(scope = 'project' or scope = 'global')",
            ]
            memory_params = [project_id]

            if query_text:
                memory_clauses.append("(title ilike %s or content ilike %s)")
                memory_params.append(f"%{query_text}%")
                memory_params.append(f"%{query_text}%")

            memory_params.append(5)

            cur.execute(
                f"""
                select id, project_id, scope, title, content, status, confidence, meta, updated_at
                from memory_records
                where {" and ".join(memory_clauses)}
                order by confidence desc, updated_at desc
                limit %s
                """,
                memory_params,
            )
            return cur.fetchall()

        relevant_memory = fetch_memory(memory_query)

        if memory_query and not relevant_memory:
            relevant_memory = fetch_memory(None)

        return {
            "ok": True,
            "project": project,
            "project_state": project_state,
            "objective": objective,
            "next_step": next_step,
            "blockers": blockers,
            "recent_jobs": recent_jobs,
            "recent_artifacts": recent_artifacts,
            "recent_messages": recent_messages,
            "relevant_memory": relevant_memory,
        }
