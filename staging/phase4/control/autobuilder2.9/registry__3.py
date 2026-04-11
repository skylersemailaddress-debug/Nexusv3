from runtime.handlers.default_handler import run as default_run

HANDLERS = {
    "default": default_run,
}


def get_handler(name: str):
    if name not in HANDLERS:
        raise ValueError(f"Unknown handler: {name}")
    return HANDLERS[name]
