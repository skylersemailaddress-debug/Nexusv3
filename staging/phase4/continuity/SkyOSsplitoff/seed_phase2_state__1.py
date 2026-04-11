import psycopg

conn = psycopg.connect("postgres://postgres:postgres@localhost:5432/skyler")
cur = conn.cursor()

cur.execute(
"insert into objectives (id, project_id, title, status, meta) "
"values ('obj_phase2_continuity','default','Stabilize continuity and state layer','active','{\"source\":\"phase2_seed\"}') "
"on conflict (id) do nothing;"
)

cur.execute(
"insert into next_steps (id, project_id, objective_id, title, status, kind, meta) "
"values ('step_phase2_hydration','default','obj_phase2_continuity','Resolve objective + next_step hydration','ready','task','{\"source\":\"phase2_seed\"}') "
"on conflict (id) do nothing;"
)

conn.commit()
print("Seed complete.")
