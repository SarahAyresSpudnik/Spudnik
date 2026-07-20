import os

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

    # a missing trailing newline on the last existing line would otherwise
    # merge straight into whatever gets appended next
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"

    for i, line in enumerate(lines):
        if line.startswith("ANTHROPIC_API_KEY="):
            lines[i] = f"ANTHROPIC_API_KEY={key}\n"
            key_written = True
            break

    if not key_written:
        lines.append(f"ANTHROPIC_API_KEY={key}\n")

    with open(env_path, "w") as f:
        f.writelines(lines)

def write_model_choice(model, env_path=".env"):
    # Same replace-or-append pattern as write_api_key --
    # avoids duplicate CLAUDE_MODEL lines in .env
    lines = []
    model_written = False

    try:
        with open(env_path, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        lines = []

    # a missing trailing newline on the last existing line would otherwise
    # merge straight into whatever gets appended next
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"

    for i, line in enumerate(lines):
        if line.startswith("CLAUDE_MODEL="):
            lines[i] = f"CLAUDE_MODEL={model}\n"
            model_written = True
            break

    if not model_written:
        lines.append(f"CLAUDE_MODEL={model}\n")

    with open(env_path, "w") as f:
        f.writelines(lines)
        
def clear_api_key(env_path=".env"):
    # Reads .env line by line, removes the ANTHROPIC_API_KEY line entirely
    # if it exists. Leaves every other line untouched.
    #
    # Also pops it straight out of the running process's environment --
    # load_dotenv(override=True) only ever overrides keys still present in
    # the file, it never unsets a key that's been removed. Without this,
    # has_api_key() would keep reporting a key exists until the process
    # restarts, even though .env no longer has one.
    os.environ.pop("ANTHROPIC_API_KEY", None)

    try:
        with open(env_path, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        return  # nothing to clear if the file doesn't even exist

    # KEEP every line except the one starting with ANTHROPIC_API_KEY=
    remaining_lines = [line for line in lines if not line.startswith("ANTHROPIC_API_KEY=")]

    with open(env_path, "w") as f:
        f.writelines(remaining_lines)

def write_reviewer_mode(enabled, env_path=".env"):
    # Same replace-or-append pattern as write_api_key/write_model_choice --
    # avoids duplicate REVIEWER_MODE lines in .env
    lines = []
    value = "true" if enabled else "false"
    mode_written = False

    try:
        with open(env_path, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        lines = []

    # a missing trailing newline on the last existing line would otherwise
    # merge straight into whatever gets appended next
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"

    for i, line in enumerate(lines):
        if line.startswith("REVIEWER_MODE="):
            lines[i] = f"REVIEWER_MODE={value}\n"
            mode_written = True
            break

    if not mode_written:
        lines.append(f"REVIEWER_MODE={value}\n")

    with open(env_path, "w") as f:
        f.writelines(lines)

