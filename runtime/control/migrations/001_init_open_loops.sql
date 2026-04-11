CREATE TABLE IF NOT EXISTS open_loops (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    owner TEXT NOT NULL,
    status TEXT NOT NULL,
    priority TEXT NOT NULL
);
