from flask import Flask, request
# IMPORT random so we can pick a phrase at random
import random
# import get_response from the llm adapter
from llm_adapter import get_response
# CREATE the app object - this is the Flask application itself
app= Flask(__name__)
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

# IF this file is run directly (not imported by something else)...
if __name__=="__main__":
    #...START the flask dev server
    app.run(debug=True, port=5000)