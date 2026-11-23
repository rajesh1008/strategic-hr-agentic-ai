# Strategic HR in the Age of Agentic AI, Chapter 5: 46 Days
# Listing: Group Applications by Shared Identifiers (Under the Hood)
# Union-find over phone and email. A face scan would need a written release under Illinois BIPA; this check uses none.

def find_rings(applications):
    """Group applications that share a phone number or an email address."""
    parent = {a.id: a.id for a in applications}
    def root(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    first_seen = {}
    for a in applications:
        for key in (("phone", a.phone), ("email", (a.email or "").lower())):
            if not key[1]:
                continue
            if key in first_seen:
                parent[root(a.id)] = root(first_seen[key])
            else:
                first_seen[key] = a.id
    groups = {}
    for a in applications:
        groups.setdefault(root(a.id), []).append(a.id)
    return [g for g in groups.values() if len(g) > 1]   # to security
