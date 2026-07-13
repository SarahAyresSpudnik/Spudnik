import os
# Define main funct every route will call
def get_response(message):
    #read the LLM_provider environment variable
    # if it's not set at all, default to "olllama"
    provider = os.getenv("LLM_PROVIDER", "ollama")

    # if the provider is set to ollama
    if provider == "ollama":
        # this is where real Ollama connection logiv goes later
        return "STUB: ollama path was called"

    # if Provider is set to claude
    elif provider == "claude":
        # this is where real claude API logic goes later
        return "STUB: claude path was called"

    # if provider is set to something unrecognized
    else:
        # This shouldn't normally happen, but fail load, not silent
        return f"STUB: unrecognized provider '{provider}'"
