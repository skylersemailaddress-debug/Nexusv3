import os
import time
import uuid
import psycopg2

from runtime.runner.structured_logging import setup_logging
from runtime.runner.failure_codes import EXECUTION_ERROR, DB_ERROR, UNKNOWN_ERROR
from runtime.runner.retry_policy import max_retries
from runtime.queue.pg_claim import claim_job
from runtime.queue.pg_queue import complete
from runtime.runner.run_execution_graph import execute_node

DB_URL = os.environ.get("NEXUS_DB_URL", "postgresql://postgres:postgres@localhost:5432/nexus")
POLL_SECONDS = int(os.environ.get("NEXUS_WORKER_POLL_SECONDS", "2"))

logger = setup_logging()

def mark_failed(job_id: str, error: str, failure_code: str):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE jobs
        SET status = 'failed',
            completed_at = EXTRACT(EPOCH FROM NOW())
        WHERE id = %s
        """,
        (job_id,)
    )
    conn.commit()
    cur.close()
    conn.close()
    logger.error(f"job failed: {error}", extra={"job_id": job_id, "failure_code": failure_code})

def worker_loop():
    worker_id = str(uuid.uuid4())
    logger.info("worker starting", extra={"worker_id": worker_id})

    while True:
        try:
            job_id = claim_job(worker_id)
        except Exception as e:
            logger.error(f"claim failed: {e}", extra={"worker_id": worker_id, "failure_code": DB_ERROR})
            time.sleep(POLL_SECONDS)
            continue

        if not job_id:
            time.sleep(POLL_SECONDS)
            continue

        logger.info("job claimed", extra={"worker_id": worker_id, "job_id": job_id})

        try:
            packet = execute_node(job_id)
            if packet.get("status") == "done":
                complete(job_id)
                logger.info("job completed", extra={"worker_id": worker_id, "job_id": job_id})
            else:
                mark_failed(job_id, packet.get("error", "execution failed"), EXECUTION_ERROR)
        except psycopg2.Error as e:
            mark_failed(job_id, str(e), DB_ERROR)
        except Exception as e:
            mark_failed(job_id, str(e), UNKNOWN_ERROR)

if __name__ == "__main__":
    worker_loop()
