ROLE_OPERATOR = "operator"
ROLE_ADMIN = "admin"

ROLE_ORDER = {
    ROLE_OPERATOR: 10,
    ROLE_ADMIN: 20,
}


def is_valid_role(role: str) -> bool:
    return role in ROLE_ORDER


def has_required_role(actual_role: str, required_role: str) -> bool:
    if not is_valid_role(actual_role) or not is_valid_role(required_role):
        return False
    return ROLE_ORDER[actual_role] >= ROLE_ORDER[required_role]
