import os
from flask import Flask, request, session, render_template
# IMPORT random so we can pick a phrase at random
import random

import uuid

from dotenv import load_dotenv
load_dotenv()

# import get_response from the llm adapter
from llm_adapter import get_response

# import write_api_key from env_writer
from env_writer import write_api_key

# CREATE the app object - this is the Flask application itself
from reviewer_mode import has_api_key

from reviewer_mode import reviewer_status, is_reviewer_mode

from env_writer import clear_api_key, write_model_choice, write_reviewer_mode

# import validate_api_key from key_validator
from key_validator import validate_api_key

# import init_db to create the sqlite tables

from db import (
    init_db,
    write_memory_entry,
    find_memory_entry,
    write_activity,
    get_recent_activity,
    get_sessions,
    get_messages_by_session,
    ensure_session,
    rename_session,
    get_memory_entries,
    get_memory_stats,
    set_protocol_enabled,
    set_all_protocols_enabled,
    get_devices,
    add_device,
    update_device,
    delete_device,
)

from rate_limit_state import get_rate_limit

from persona_loader import list_protocols

import news_fetcher

app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static"
)

# secret_key signs the session cookie -- required for flask.session to work at all.
# Falls back to a dev placeholder if .env doesn't have one yet.
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-key-change-me")

# CREATE all tables if they don't already exist -- safe to run every
# time the app starts, IF NOT EXISTS means it won't touch existing data
init_db()

# DEFINE a lookup: state name --> list of 4 phrases
#only "healthy" matters for sub-issue 1
HEALTH_RESPONSES = {
    'healthy': [
        # Phase 1 from tater-health-responses.md
        "Yep. Still here. Unfortunately for both of us.",
        # Phase 2 from tater-health-responses.md
        "Alive. Barely thrilled about it, but alive.",
        # Phase 3 from tater-health-responses.md
        "Running. Don't jinx it.",
        # Phase 4 from tater-health-responses.md
        "Systems fine. Emotionally, debatable.",
    ],
}
CHAT_ERROR_RESPONSES = {
    'error_input': [
        # Phase 1 from tater-health-responses.md
        "That's not a message, that's an attack. I see you.",
        # Phase 2 from tater-health-responses.md
        "Nice try. I'm not falling for that one.",
        # Phase 3 from tater-health-responses.md
        "Whatever that was, it's not getting through. Good effort though.",
        # Phase 4 from tater-health-responses.md
        "I know what you're trying to do. Adorable, but no.",
    ]
}
SETUP_RESPONSES = {
    'key_missing': [
        # State 9 from tater-health-responses.md
        "This one's coming out of your wallet, not mine — so hand over the key.",
        "Your dime, your key. I just need you to actually type it in below.",
        "Nobody's spending my money today — this is all you. Key goes below.",
        "It's your bill racking up here, not mine. Let's get that key plugged in.",
    ],
    'key_saved': [
        # State 9b from tater-health-responses.md
        "Your key's in. Every token from here on out is coming out of your pocket.",
        "Saved. That's your API bill ticking now, not mine.",
        "Key's set. I hope you like the sound of money leaving your account.",
        "Locked in. Enjoy watching your usage dashboard like a hawk.",
    ],
    'key_exists': [
        "Already got a key on file. Somebody's money is already on the line.",
        "There's a key saved already. Someone's account is already exposed to my nonsense.",
        "A key's sitting here already, doing its job. Replace it or leave it be.",
        "Key's already loaded. Somebody's already paying for this privilege.",
    ],
    'key_cleared': [
        "Key's gone. Somebody's wallet just breathed a sigh of relief.",
        "Cleared. No more key, no more spending. For now.",
        "Removed. Whoever owned that key is off the hook.",
        "Key's wiped. Back to broke and key-less.",
    ],
    'key_invalid_prefix': [
        "Okay I know I'm delusional, but are you? That's not a key.",
        "I might be running on a potato, but even I know that's not real.",
        "Buddy. That's not shaped like anything Anthropic ever made.",
        "I've seen a lot of nonsense, but that's a new low. Try again.",
    ],
    'key_too_short': [
        "Where's the rest of it?",
        "You call that a key? Feels like you're missing half of it.",
        "That's suspiciously short. Keys don't come in fun-size.",
        "Something's cut off. Copy the whole thing.",
    ],
    'key_too_long': [
        "It's a key, not a book. Try less characters.",
        "I don't need your whole life story, I just need a key.",
        "Way too much going on here. Trim it down to an actual key.",
        "You pasted something extra. This is not that long.",
    ],
    'key_invalid_characters': [
        "Have you ever seen a key with that in it? Because I haven't.",
        "That character doesn't belong in a key. I don't know what it belongs in.",
        "Something in there looks like it escaped from somewhere else. Take it out.",
        "I don't know what that symbol's doing there, but it's gotta go.",
    ],
    'key_required_error': [
        "No key, no chat. That's not a bug, that's just how money works.",
        "You're trying to talk to me with nothing plugged in. Bold. Stupid, but bold.",
        "If you can't figure out how to put in a key, go read the how-to page.",
        "There's no key configured. I'm not doing this out of the goodness of my circuits.",
    ]    
}
MEMORY_RESPONSES = {
    'log_saved': [
        "Logged. Don't make me regret remembering that.",
        "Got it. Filed away in the part of my brain that actually works.",
        "Noted and stored. Try not to contradict yourself later.",
        "Locked in. That's on the record now.",
    ],
    'recall_found': [
        "Oh, you actually want this back? Fine. {summary}",
        "Ugh, here: {summary}. Happy now?",
        "I remembered it so you wouldn't have to. {summary}. You're welcome, I guess.",
        "Dragging this back up against my will: {summary}",
    ],
    'recall_not_found': [
        "Nothing. Shocking, since you probably never actually told me.",
        "Came up empty. Maybe try saying things out loud next time.",
        "I've got nothing. Either you didn't log it, or I just don't care enough to keep it.",
        "Blank. Whatever that was, it wasn't worth my storage space apparently.",
    ],
}
REVIEWER_RESPONSES = {
    'reviewer_on': [
        "Borrowed brain engaged. Try not to waste it.",
        "Switching to the fancy rental. Behave.",
        "Claude's up. This one's not even mine, so be nice to it.",
        "Reviewer mode on. Somebody else's tab is running now.",
    ],
    'reviewer_off': [
        "Back to running on my own busted hardware. Welcome home.",
        "Local brain's back online. Cheaper, jankier, mine.",
        "Ollama's driving again. No borrowed dime required.",
        "Off the rental. Back to the potato.",
    ],
}
MODEL_RESPONSES = {
    'model_changed': [
        "New blueprint acquired. Switched models, try not to notice a difference.",
        "Model swapped. Same me, different brain under the hood.",
        "Done. Whichever one you picked is running now.",
        "Locked in. That's the model talking to you from here on out.",
    ],
    'model_invalid': [
        "That's not a model I've got a slot for. Pick one from the list.",
        "Never heard of it. Choose an actual option.",
        "Not on the menu. Try again.",
    ],
}
REBOOT_RESPONSES = {
    'reboot_done': [
        "Rebooted. Also yanked the key while I was in there — you're welcome.",
        "Systems cycled. Key's gone too, since you asked for a clean slate.",
        "Reboot complete. Cleared the key as part of the ritual.",
        "Back up. Key's wiped, same as every reboot.",
    ],
}
# The only Claude model IDs this dropdown offers -- verified against
# Anthropic's current model catalog, not guessed.
CLAUDE_MODEL_CHOICES = {
    "claude-opus-4-8",
    "claude-sonnet-5",
    "claude-haiku-4-5-20251001",
}

@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/dashboard")
def dashboard():
    # "Continue" on a session (Logs page / Recent Activity) links here with
    # ?session=<id> -- overwrite this browser's session_id cookie with the
    # requested one before the SPA loads, so /api/session/current picks up
    # that conversation's history instead of whatever was there before.
    requested_session = request.args.get("session")
    if requested_session:
        session["session_id"] = requested_session
    return render_template("dashboard.html")

# DEFINE the /health route
@app.route("/health")
def health():
    # PICK one random phrase from the " healthy" list
    phrase = random.choice(HEALTH_RESPONSES["healthy"])
    # RETURN that phrase as the response, with HTTP status 200
    return phrase, 200

# define a new route /chat/text that only accepts POST requests
@app.route("/chat/text", methods=["POST"])
def chat_text():
    # if reviewer mode is on and no key's configured, refuse before touching the LLM adapter at all
    status = reviewer_status()
    if status["reviewer_mode"] and not status["key_present"]:
        phrase = random.choice(SETUP_RESPONSES["key_required_error"])
        return {"error": phrase}, 400
    # GET or CREATE a session_id for this browser session.
    # flask.session is a signed cookie -- persists across requests from
    # the same browser, but is invisible to the user (no UI, no chat
    # thread, just plumbing so Tater can find prior messages later).
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    session_id = session["session_id"]
    # GET the Json body sent in request
    data = request.get_json()

    # pull the "message" field out of that json
    # (use .get() so it doesn't crash if "message" key is missing -- falls back to None instead)
    message = data.get("message") if data else None

    # if no message was actually sent
    if not message:
        # PICK one random phrase from the error_input list
        phrase = random.choice(CHAT_ERROR_RESPONSES["error_input"])
        # RETURN it in the same shape as before, persona voice instead of flat string
        return {"error": phrase}, 400

    # REGISTER this session (auto-named from this message) the first time
    # it's ever seen -- a no-op on every later call, same session.
    ensure_session(session_id, first_message=message)

    # CHECK for the memory-write trigger before anything else --
    # short-circuits before get_response(), never touches the LLM or messages table
    if message.lower().startswith("log that"):
        summary = message[len("log that"):].strip(" .")
        write_memory_entry(category="decision", summary=summary)
        phrase = random.choice(MEMORY_RESPONSES["log_saved"])
        return {"response": phrase}, 200

    # CHECK for the memory-recall trigger
    if message.lower().startswith("remember that"):
        keyword = message[len("remember that"):].strip(" .")
        result = find_memory_entry(keyword)
        if result:
            phrase = random.choice(MEMORY_RESPONSES["recall_found"]).format(summary=result)
        else:
            phrase = random.choice(MEMORY_RESPONSES["recall_not_found"])
        return {"response": phrase}, 200

    # otherwise, pass the message to the adapter and get a response back
    reply = get_response(message, session_id=session_id)

    # LOG this exchange as a Recent Activity event -- truncated preview only,
    # never the raw key or anything sensitive since chat messages don't carry that
    write_activity("message", message[:60])

    # return that reply as json, with a 200 status
    return {"response": reply}, 200

@app.route("/setup", methods=["GET"])
def setup_form():
    # CHECK if a key is already saved
    key_exists = has_api_key()

    if key_exists:
        # PICK a phrase acknowledging one's already on file
        phrase = random.choice(SETUP_RESPONSES["key_exists"])
        instructions = "A key is already saved. To replace it, type a new key below and click Save. To remove it entirely, leave the box empty and click Save."
    else:
        # PICK a phrase from key_missing, same as before
        phrase = random.choice(SETUP_RESPONSES["key_missing"])
        instructions = "Enter your Anthropic API key below and click Save."

    return f"""
    <p>{phrase}</p>
    <p>{instructions}</p>
    <form method="POST" action="/setup">
        <label>Anthropic API Key:</label>
        <input type="text" name="api_key">
        <button type="submit">Save</button>
    </form>
    """
@app.route("/setup", methods=["POST"])
def setup_submit():
    # GET the submitted form field (form POST, not JSON)
    api_key = request.form.get("api_key")

    # CHECK if a key already existed before this submission
    key_existed = has_api_key()

    if not api_key:
        if key_existed:
            # BLANK submission + a key existed = intentional clear, not an error
            clear_api_key()
            phrase = random.choice(SETUP_RESPONSES["key_cleared"])
            return f"<p>{phrase}</p>", 200
        else:
            # BLANK submission + no key existed = actual mistake, keep the error
            phrase = random.choice(SETUP_RESPONSES["key_missing"])
            return f"<p>{phrase}</p><p>You didn't actually type anything in there.</p>", 400

    # VALIDATE the key format before writing anything
    is_valid, reason = validate_api_key(api_key)
    if not is_valid:
        # MAP the specific failure reason to its matching phrase list
        response_key = {
            "wrong_prefix": "key_invalid_prefix",
            "too_short": "key_too_short",
            "too_long": "key_too_long",
            "invalid_characters": "key_invalid_characters",
        }.get(reason, "key_invalid_prefix")  # fallback, shouldn't normally hit this
        phrase = random.choice(SETUP_RESPONSES[response_key])
        return f"<p>{phrase}</p>", 400

    # WRITE the key to .env (overwrites if one already existed)
    write_api_key(api_key)
    # RELOAD .env into the environment so the new key is usable immediately
    load_dotenv(override=True)
    phrase = random.choice(SETUP_RESPONSES["key_saved"])
    return f"<p>{phrase}</p>", 200

# ==== Right/left sidebar API endpoints ====

@app.route("/api/sidebar-status", methods=["GET"])
def sidebar_status():
    # SINGLE combined status read for the whole right sidebar -- provider,
    # model, reviewer mode, key presence, root beer reserves, recent activity.
    # Keeps the frontend to one fetch on load instead of six.
    reviewer_on = is_reviewer_mode()
    key_present = has_api_key()

    if reviewer_on:
        # Claude is only "genuinely connected" once a key actually exists --
        # otherwise chat/text already refuses, so the provider card shouldn't
        # claim a connection that doesn't work.
        provider = "claude"
        connected = key_present
    else:
        # Ollama is the local daily-driver default -- no key required, always
        # considered configured (the real connection check is a later phase).
        provider = "ollama"
        connected = True

    return {
        "provider": {"active": provider, "connected": connected},
        "model": os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001"),
        "reviewer_mode": reviewer_on,
        "key_present": key_present,
        "rate_limit": get_rate_limit(),
        "activity": get_recent_activity(),
    }, 200

@app.route("/api/model", methods=["POST"])
def set_model():
    data = request.get_json()
    model = data.get("model") if data else None

    if model not in CLAUDE_MODEL_CHOICES:
        phrase = random.choice(MODEL_RESPONSES["model_invalid"])
        return {"error": phrase}, 400

    write_model_choice(model)
    load_dotenv(override=True)
    write_activity("model_changed", model)
    phrase = random.choice(MODEL_RESPONSES["model_changed"])
    return {"response": phrase, "model": model}, 200

@app.route("/api/reviewer-mode", methods=["POST"])
def set_reviewer_mode():
    data = request.get_json()
    enabled = bool(data.get("enabled")) if data else False

    write_reviewer_mode(enabled)
    load_dotenv(override=True)
    write_activity("reviewer_mode", "on" if enabled else "off")
    phrase = random.choice(REVIEWER_RESPONSES["reviewer_on" if enabled else "reviewer_off"])
    return {"response": phrase, "reviewer_mode": enabled}, 200

@app.route("/api/key", methods=["POST"])
def api_key_replace():
    # JSON-API twin of /setup's POST handler, for the sidebar's Replace Key
    # form -- same validate/write/reload logic, JSON in and out instead of HTML.
    data = request.get_json()
    api_key = data.get("api_key") if data else None

    if not api_key:
        phrase = random.choice(SETUP_RESPONSES["key_missing"])
        return {"error": phrase}, 400

    is_valid, reason = validate_api_key(api_key)
    if not is_valid:
        response_key = {
            "wrong_prefix": "key_invalid_prefix",
            "too_short": "key_too_short",
            "too_long": "key_too_long",
            "invalid_characters": "key_invalid_characters",
        }.get(reason, "key_invalid_prefix")
        phrase = random.choice(SETUP_RESPONSES[response_key])
        return {"error": phrase}, 400

    # WRITE the key to .env -- never log/print the raw value anywhere
    write_api_key(api_key)
    load_dotenv(override=True)
    write_activity("key_replaced")
    phrase = random.choice(SETUP_RESPONSES["key_saved"])
    return {"response": phrase}, 200

@app.route("/api/key/deactivate", methods=["POST"])
def api_key_deactivate():
    clear_api_key()
    load_dotenv(override=True)
    write_activity("key_deactivated")
    phrase = random.choice(SETUP_RESPONSES["key_cleared"])
    return {"response": phrase}, 200

@app.route("/api/reboot", methods=["POST"])
def reboot_system():
    # Reboot's current scope: deactivate the API key, same logic as the
    # sidebar's Deactivate Key action. Does not restart the Flask process
    # or touch any other state.
    clear_api_key()
    load_dotenv(override=True)
    write_activity("reboot")
    phrase = random.choice(REBOOT_RESPONSES["reboot_done"])
    return {"response": phrase}, 200

@app.route("/api/memory", methods=["GET"])
def api_memory():
    return {
        "entries": get_memory_entries(),
        "stats": get_memory_stats(),
    }, 200

@app.route("/api/protocols", methods=["GET"])
def api_protocols():
    protocols = list_protocols()
    return {
        "protocols": protocols,
        "active_count": sum(1 for p in protocols if p["enabled"]),
    }, 200

@app.route("/api/protocols/<path:filename>/toggle", methods=["POST"])
def api_protocol_toggle(filename):
    data = request.get_json()
    enabled = bool(data.get("enabled")) if data else False
    set_protocol_enabled(filename, enabled)
    write_activity("protocol_toggled", f"{filename} -> {'on' if enabled else 'off'}")
    return {"filename": filename, "enabled": enabled}, 200

@app.route("/api/protocols/bulk", methods=["POST"])
def api_protocols_bulk():
    # Settings page's master slider -- bulk-sets every protocol currently
    # found on disk to the same on/off state.
    data = request.get_json()
    enabled = bool(data.get("enabled")) if data else False
    filenames = [p["filename"] for p in list_protocols()]
    set_all_protocols_enabled(filenames, enabled)
    write_activity("protocols_bulk_toggled", "on" if enabled else "off")
    return {"enabled": enabled, "count": len(filenames)}, 200

@app.route("/api/devices", methods=["GET"])
def api_devices_list():
    return {"devices": get_devices()}, 200

DEVICE_STATUSES = {"link_active", "standby", "disconnected"}

@app.route("/api/devices", methods=["POST"])
def api_devices_create():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return {"error": "A device needs a name."}, 400
    status = data.get("status", "standby")
    if status not in DEVICE_STATUSES:
        status = "standby"

    new_id = add_device(
        name=name,
        category=data.get("category", ""),
        spec=data.get("spec", ""),
        role=data.get("role", ""),
        aside=data.get("aside", ""),
        status=status,
    )
    write_activity("device_added", name)
    return {"id": new_id}, 201

@app.route("/api/devices/<int:device_id>", methods=["PATCH"])
def api_devices_update(device_id):
    data = request.get_json() or {}
    editable = {"name", "category", "spec", "role", "aside", "status"}
    fields = {k: v for k, v in data.items() if k in editable}
    if "status" in fields and fields["status"] not in DEVICE_STATUSES:
        return {"error": "Not a real status option."}, 400

    updated = update_device(device_id, fields)
    if not updated:
        return {"error": "No device with that id."}, 404
    write_activity("device_updated", f"#{device_id}")
    return {"id": device_id}, 200

@app.route("/api/devices/<int:device_id>", methods=["DELETE"])
def api_devices_delete(device_id):
    deleted = delete_device(device_id)
    if not deleted:
        return {"error": "No device with that id."}, 404
    write_activity("device_deleted", f"#{device_id}")
    return {"id": device_id}, 200

@app.route("/api/news", methods=["GET"])
def api_news():
    return {"sources": news_fetcher.get_news()}, 200

@app.route("/api/sessions", methods=["GET"])
def api_sessions_list():
    return {"sessions": get_sessions()}, 200

@app.route("/api/sessions/<session_id>", methods=["PATCH"])
def api_sessions_rename(session_id):
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return {"error": "Name can't be blank."}, 400
    updated = rename_session(session_id, name)
    if not updated:
        return {"error": "No session with that id."}, 404
    return {"session_id": session_id, "name": name}, 200

@app.route("/api/session/current", methods=["GET"])
def api_session_current():
    # Whatever session_id this browser's cookie currently holds (creating
    # one if this is a first-ever visit) plus its full message history --
    # Presence reads this on mount so Continue/normal flow both "just work."
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    session_id = session["session_id"]
    return {
        "session_id": session_id,
        "messages": get_messages_by_session(session_id),
    }, 200

@app.route("/logs", methods=["GET"])
def logs_page():
    # Full chat history browser -- messages/session_id, not advice_log.
    # Most recent session first; each session's own messages ordered by id.
    sessions = get_sessions()
    for entry in sessions:
        entry["messages"] = get_messages_by_session(entry["session_id"])
    return render_template("logs.html", sessions=sessions)

@app.route("/help", methods=["GET"])
def help_page():
    return render_template("help.html")

# get reviewer status once before deciding how to run
status = reviewer_status()

# reviewer mode locks to localhost regardless of future defaults;
# normal mode stays open for phone/car clients later
host = "127.0.0.1" if status["reviewer_mode"] else "0.0.0.0"

if __name__=="__main__":
    app.run(host=host, debug=True, port=5000)