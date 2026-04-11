import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENV_DIR = ROOT / "env"

def load_env_file(app_env: str):
    mapping = {
        "dev": ENV_DIR / ".env.dev",
        "staging": ENV_DIR / ".env.staging",
        "production": ENV_DIR / ".env.production",
    }
    path = mapping.get(app_env)
    if not path or not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())

def get_runtime_config():
    app_env = os.environ.get("APP_ENV", "dev")
    load_env_file(app_env)
    return {
        "app_env": app_env,
        "api_host": os.environ.get("API_HOST", "127.0.0.1"),
        "api_port": os.environ.get("API_PORT", "8000"),
        "ui_host": os.environ.get("UI_HOST", "127.0.0.1"),
        "ui_port": os.environ.get("UI_PORT", "5173"),
        "database_url": os.environ.get("DATABASE_URL", "sqlite:///runtime/data/nexus_runtime.db"),
        "allowed_origins": os.environ.get("ALLOWED_ORIGINS", "http://127.0.0.1:5173"),
        "log_level": os.environ.get("LOG_LEVEL", "INFO"),
        "reverse_proxy_enabled": os.environ.get("REVERSE_PROXY_ENABLED", "false"),
        "tls_enabled": os.environ.get("TLS_ENABLED", "false"),
        "rate_limit_window_seconds": os.environ.get("RATE_LIMIT_WINDOW_SECONDS", "60"),
        "rate_limit_max_requests": os.environ.get("RATE_LIMIT_MAX_REQUESTS", "120"),
        "session_ttl_seconds": os.environ.get("SESSION_TTL_SECONDS", "43200"),
        "session_ended_retention_seconds": os.environ.get("SESSION_ENDED_RETENTION_SECONDS", "604800"),
        "observability_log_max_bytes": os.environ.get("OBSERVABILITY_LOG_MAX_BYTES", "1048576"),
        "observability_log_max_files": os.environ.get("OBSERVABILITY_LOG_MAX_FILES", "5"),
    }
