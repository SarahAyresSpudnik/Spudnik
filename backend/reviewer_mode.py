import os

def is_reviewer_mode():
    # Reviewer mode env var controls this - defaults to false if uset
    return os.environ.get("REVIEWER_MODE","false").lower() =="true"

def has_api_key():
    # Checks if ANTHROPIC_API_KEY is set in .env and isn't just blank/whitespace.
    # Used later to decide if the reviewer setup form needs to fire.
    key = os.environ.get("ANTHROPIC_API_KEY")
    return key is not None and key.strip() != ""

def reviewer_status():
    # Single entry point app.py will use — bundles both checks into one result.
    # key_present stays None when reviewer mode is off, since the key check doesn't even matter in that case.
    if not is_reviewer_mode():
        return {"reviewer_mode":False, "key_present": None}
    return {"reviewer_mode": True, "key_present": has_api_key()}