from flask import Flask
# IMPORT random so we can pick a phrase at random
import random
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
    # other 7 states from the .md file go here eventually - not now
}
# DEFINE the /health route
@app.route("/health")
def health():
    # PICK one random phrase from the " healthy" list
    phrase = random.choice(HEALTH_RESPONSES["healthy"])
    # RETURN that phrase as the response, with HTTP status 200
    return phrase, 200
# IF this file is run directly (not imported by something else)...
if __name__=="__main__":
    #...START the flask dev server
    app.run(debug=True, port=5000)