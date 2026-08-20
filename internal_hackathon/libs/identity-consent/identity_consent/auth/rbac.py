"""Role-to-scope policy shared by API adapters."""

ROLE_SCOPES: dict[str, frozenset[str]] = {
    "farmer": frozenset({"profile:write:self", "consent:write:self", "data:read:self"}),
    "extension_officer": frozenset({"risk:read:district", "case:write", "copilot:read", "notification:write"}),
    "district_admin": frozenset({"risk:read:district", "case:write", "analytics:read", "audit:read"}),
    "admin": frozenset({"*"}),
    "auditor": frozenset({"audit:read", "analytics:read"}),
}


def scopes_for_role(role: str) -> frozenset[str]:
    return ROLE_SCOPES.get(role, frozenset())


def require_scope(context, scope: str) -> None:
    if not context.has(scope) and scope not in scopes_for_role(context.role):
        raise PermissionError(f"scope required: {scope}")
