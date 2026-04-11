CREATE TABLE IF NOT EXISTS runtime_accounts (
    username TEXT PRIMARY KEY,
    role TEXT NOT NULL,
    token TEXT NOT NULL UNIQUE,
    is_active INTEGER NOT NULL DEFAULT 1
);
