import os
import re

from db import get_protocols_enabled_map

# Resolves to backend/persona/, no matter what directory
# the Flask process was actually launched from.
PERSONA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "persona")
PROTOCOLS_DIR = os.path.join(PERSONA_DIR, "protocols")

# Matches a leading `---\n...\n---\n` frontmatter block, capturing the
# frontmatter body separately from whatever follows it.
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n(.*)$", re.DOTALL)

def load_persona(filename):
    with open(os.path.join(PERSONA_DIR, filename), "r", encoding="utf-8") as f:
        return f.read()

def _parse_protocol_file(filename):
    # Parses the simple `---\nkey: value\n---\n<body>` frontmatter every
    # protocol file uses. A file with no frontmatter still loads, just
    # with the filename standing in for title/summary.
    path = os.path.join(PROTOCOLS_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()

    match = FRONTMATTER_RE.match(raw)
    if not match:
        return {"filename": filename, "title": filename, "summary": "", "body": raw.strip()}

    frontmatter, body = match.groups()
    meta = {}
    for line in frontmatter.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()

    return {
        "filename": filename,
        "title": meta.get("title", filename),
        "summary": meta.get("summary", ""),
        "body": body.strip(),
    }

def list_protocols():
    # Scans persona/protocols/ at call time -- the list Protocols page
    # and the system prompt both see is always exactly what's on disk
    # right now, never a hardcoded catalog that can drift from reality.
    if not os.path.isdir(PROTOCOLS_DIR):
        return []

    filenames = sorted(f for f in os.listdir(PROTOCOLS_DIR) if f.endswith(".md"))
    enabled_map = get_protocols_enabled_map()

    protocols = []
    for filename in filenames:
        parsed = _parse_protocol_file(filename)
        # A protocol that's never been toggled defaults to enabled --
        # matches "protocols are on unless someone turns them off."
        parsed["enabled"] = enabled_map.get(filename, True)
        protocols.append(parsed)
    return protocols

def build_system_prompt(mode="default"):
    # always-on identity files -- loaded on every call, every provider
    always_on = [
        "tater-persona.md",   # core identity + argument protocol
        "tater-lore.md",
        "tater-lexicon.md",
        "tater-media.md",
        "tater-hobbies.md",   # Sarah's actual hobbies/interests -- context about her, not Tater
    ]

    # mode-specific files -- only loaded when the calling route explicitly
    # requests that mode. tater-projects.md's exclusion from every other
    # mode IS the hard technical exclusion we scoped earlier.
    mode_files = {
        "project_status": ["tater-projects.md", "tater-project-status-protocol.md"],
        "video": ["tater-video-protocol.md"],
        "tech": ["tater-tech-protocol.md"],
        "default": [],
    }

    files = always_on + mode_files.get(mode, [])
    chunks = [load_persona(fname) for fname in files]

    # Enabled protocols (Protocols page toggles) get folded in on every
    # call, same as the always-on files -- a protocol that's off is
    # excluded here entirely, not just hidden from the UI list.
    for protocol in list_protocols():
        if protocol["enabled"]:
            chunks.append(protocol["body"])

    return "\n\n---\n\n".join(chunks)
