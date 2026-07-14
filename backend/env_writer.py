def write_api_key(key, env_path=".env"):
    # Reads .env line by line, replaces ANTHROPIC_API_KEY if it exists,
    # otherwise appends it as a new line. Avoids duplicate key lines.
    lines = []
    key_written = False

    try:
        with open(env_path, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        lines = []

    for i, line in enumerate(lines):
        if line.startswith("ANTHROPIC_API_KEY="):
            lines[i] = f"ANTHROPIC_API_KEY={key}\n"
            key_written = True
            break

    if not key_written:
        lines.append(f"ANTHROPIC_API_KEY={key}\n")

    with open(env_path, "w") as f:
        f.writelines(lines)