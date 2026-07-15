import os
from reviewer_mode import is_reviewer_mode

# Define main funct every route will call
def get_response(message):
    # reviewer mode always forces Claude, regardless of LLM_PROVIDER --
    # no dropdown, no way to misconfigure this into hitting Ollama on a machine that doesn't have it
    if is_reviewer_mode():
        provider = "claude"
    else:
        # normal local daily-driver flow -- read LLM_provider environment variable
        # if it's not set at all, default to "ollama"
        provider = os.getenv("LLM_PROVIDER", "ollama")

    # if the provider is set to ollama
    if provider == "ollama":
        # this is where real Ollama connection logic goes later
        return "STUB: ollama path was called"

    # if Provider is set to claude
    elif provider == "claude":
        # this is where real claude API logic goes later
        return "STUB: claude path was called"

    # if provider is set to something unrecognized
    else:
        # This shouldn't normally happen, but fail loud, not silent
        return f"STUB: unrecognized provider '{provider}'"