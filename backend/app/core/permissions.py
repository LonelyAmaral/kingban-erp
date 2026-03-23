"""Role-based permission checking."""

from app.core.constants import ROLES


def has_permission(role: str, action: str) -> bool:
    """Check if a role has permission for a given action.

    Actions format: "read:clients", "write:orders", "delete:*"
    """
    perms = ROLES.get(role, [])
    if "*" in perms:
        return True

    action_type, resource = action.split(":", 1) if ":" in action else (action, "*")

    for perm in perms:
        perm_type, perm_resource = perm.split(":", 1) if ":" in perm else (perm, "*")
        if (perm_type == action_type or perm_type == "*") and \
           (perm_resource == resource or perm_resource == "*"):
            return True
    return False
