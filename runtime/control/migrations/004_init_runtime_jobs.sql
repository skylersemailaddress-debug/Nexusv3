CREATE TABLE IF NOT EXISTS runtime_jobs (
    id TEXT PRIMARY KEY,
    job_type TEXT NOT NULL,
    job_name TEXT NOT NULL,
    status TEXT NOT NULL,
    requested_by TEXT NOT NULL,
    requested_role TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    result_json TEXT NULL,
    error_text TEXT NULL,
    created_at INTEGER NOT NULL,
    started_at INTEGER NULL,
    completed_at INTEGER NULL
);
