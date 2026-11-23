# Strategic HR in the Age of Agentic AI, Chapter 3: 549 Hours
# Listing: Who May Receive a Flag (Under the Hood)
# The list is configuration the Data Protection Officer signs.

SEES = {"manager",
        "partner_hrbp"}  # 2 quarters
NEVER = {"performance_review",
         "managers_manager"}

def deliver(flag, role: str):
    if role in NEVER:
        raise PermissionError(role)
    if role not in SEES:
        raise PermissionError(role)
    return send(flag, to=role,
                action="admin_help")
