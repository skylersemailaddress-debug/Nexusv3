from runtime.db.pg import conn
import time

def heartbeat(worker_id):
    c = conn()
    cur = c.cursor()

    cur.execute("""
    INSERT INTO workers (id, last_seen)
    VALUES (%s, %s)
    ON CONFLICT (id) DO UPDATE SET last_seen = EXCLUDED.last_seen
    """, (worker_id, time.time()))

    c.commit()
    c.close()
