import os

# Resolves to backend/persona/, no matter what directory
# the Flask process was actually launched from.
PERSONA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "persona")

def load_persona(filename):
    with open(os.path.join(PERSONA_DIR, filename), "r", encoding="utf-8") as f:
        return f.read()

def build_system_prompt(mode="default"):
    # always-on identity files -- loaded on every call, every provider
    always_on = [
        "tater-persona.md",   # core identity + argument protocol
        "tater-lore.md",
        "tater-lexicon.md",
        "tater-media.md",
        "tater-memory.md",
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
    return "\n\n---\n\n".join(chunks)