from flask import Flask, request
# IMPORT random so we can pick a phrase at random
import random

from dotenv import load_dotenv
load_dotenv()

# import get_response from the llm adapter
from llm_adapter import get_response

# import write_api_key from env_writer
from env_writer import write_api_key

# CREATE the app object - this is the Flask application itself
from reviewer_mode import has_api_key

from reviewer_mode import reviewer_status

from env_writer import clear_api_key

# import validate_api_key from key_validator
from key_validator import validate_api_key

# import init_db to create the sqlite tables
from db import init_db

app= Flask(__name__)

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
    # other 7 states from the .md file go here eventually - not now
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

    # otherwise, pass the message to the adapter and get a response back
    reply = get_response(message)

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

# get reviewer status once before deciding how to run
status = reviewer_status()

# reviewer mode locks to localhost regardless of future defaults;
# normal mode stays open for phone/car clients later
host = "127.0.0.1" if status["reviewer_mode"] else "0.0.0.0"

if __name__=="__main__":
    app.run(host=host, debug=True, port=5000)