# In-memory cache of the most recent Claude token rate-limit headers.
# Deliberately not persisted to disk/DB -- resets on every process start,
# so "no Claude call yet this session" is a real, meaningful state the
# dashboard can distinguish from "reserves are actually low."
_state = {
    "limit": None,
    "remaining": None,
    "reset": None,
}


def set_rate_limit(limit, remaining, reset):
    _state["limit"] = limit
    _state["remaining"] = remaining
    _state["reset"] = reset


def get_rate_limit():
    return dict(_state)
