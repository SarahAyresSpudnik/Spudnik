import re

def validate_api_key(key):
    # Checks a submitted key against the real Anthropic key format
    # before anything gets written to .env.
    # Real keys: sk-ant-api03-<~95 base64url chars>, or sk-ant-oat01- for OAuth tokens.
    # Returns (True, None) if valid, or (False, "reason") if not.

    if key is None:
        return False, "empty"

    # STRIP leading/trailing whitespace — catches accidental spaces from copy/paste
    key = key.strip()

    if key == "":
        return False, "empty"

    # CHECK it starts with the right prefix
    if not key.startswith("sk-ant-"):
        return False, "wrong_prefix"

    # CHECK length — split into too_short vs too_long so the response
    # can be specific about which problem it is
    if len(key) < 40:
        return False, "too_short"
    if len(key) > 120:
        return False, "too_long"

    # CHECK only letters, digits, dashes, and underscores appear anywhere in the key
    if not re.fullmatch(r"[A-Za-z0-9_-]+", key):
        return False, "invalid_characters"

    return True, None