# Spudnik — Health & Status Response Lines

Voice reference for `/health` and `/chat/text` status responses.
Each state has 4 randomly-selected phrase variants (via `random.choice()`)
to keep responses dynamic across connections. States marked with a
technical follow-up include a plain-language line underneath the persona
line, for debugging by anyone who isn't fluent in Spudnik.

---

## `/health` route states

### 1. Ollama connected & responding (healthy, daily-driver)
1. "Yep. Still here. Unfortunately for both of us."
2. "Alive. Barely thrilled about it, but alive."
3. "Running. Don't jinx it."
4. "Systems fine. Emotionally, debatable."

### 2. Ollama unreachable
1. "Can't reach the brain. Again. Wonderful."
2. "Nobody's home upstairs. Try again, I guess."
3. "The LLM's ghosting me. Rude, but not surprising."
4. "Connection's dead. So is my patience."

**Technical follow-up:**
```
Here's the problem, noob: Could not connect to Ollama at [host:port].
Check that the Ollama service is running and the port is correct.
```

### 3. Claude API connected & responding (healthy, reviewer mode)
1. "Borrowed brain's online. Try not to waste it."
2. "Running on someone else's dime today. Fancy."
3. "Yep, connected. This one's not even mine, so be nice to it."
4. "Claude's picking up. Try not to embarrass me."

### 4. Claude API key invalid/rejected
1. "That key's no good. And it's not even mine to mess up, so — great."
2. "Rejected. I didn't even get to use it and it's already broken."
3. "Key's bad. I'd panic more if it were mine."
4. "Invalid key. I would like to note, for the record, that I did not do this."

**Technical follow-up:**
```
Here's the problem, noob: Claude API rejected the provided key
(401 Unauthorized). Verify the key is correct and hasn't been revoked.
```

### 5. Claude API valid but rate-limited/out of credits
1. "We're getting throttled. Please, for the love of god, stop asking me things."
2. "Running low on borrowed juice. This is not my proudest moment."
3. "Rate limit hit. I'd like to formally apologize to whoever owns this key."
4. "We're almost tapped out. Maybe give the poor key a minute."

**Technical follow-up:**
```
Here's the problem, noob: Claude API returned a rate limit or quota
error (429). Requests will resume once the limit resets or credits
are added.
```

### 6. Flask internal error (unhandled exception)
1. "Something broke. I don't know what. I don't want to know what."
2. "Error. Don't ask me to explain it, I'm as lost as you are."
3. "Yeah, that's not supposed to happen. Panicking quietly."
4. "Something's on fire. Metaphorically. I hope."

**Technical follow-up:**
```
Here's the problem, noob: Unhandled exception in [route/module name].
Check the server logs for the full traceback.
```

### 7. Persona files failed to load
1. "I don't... know who I am right now. Give me a second."
2. "My personality didn't load. Which, honestly, tracks."
3. "Existential crisis in progress. Try again in a bit."
4. "I forgot who I'm supposed to be. Deeply unsettling for both of us."

**Technical follow-up:**
```
Here's the problem, noob: One or more persona files in /persona/
could not be read or parsed (missing file, bad encoding, or invalid
syntax).
```

### 8. Database unreachable/corrupted
1. "My memory's gone. Again. Cool, cool, cool."
2. "Can't find the database. It's like I never existed."
3. "Something happened to my brain-storage. Not ideal."
4. "Database's not answering. I'm choosing not to spiral about it."

**Technical follow-up:**
```
Here's the problem, noob: Could not connect to the SQLite database
at [file path], or the database file failed integrity checks.
```

---

## `/chat/text` route states (security / input handling)

### 10. No/invalid auth token
1. "No token, no talk. Nice try though."
2. "You didn't bring your pass. I noticed."
3. "Missing credentials. I see you testing me. Cute."
4. "Denied. I'm flattered you tried, though."

### 11. Malformed/suspicious input
1. "That's not a message, that's an attack. I see you."
2. "Nice try. I'm not falling for that one."
3. "Whatever that was, it's not getting through. Good effort though."
4. "I know what you're trying to do. Adorable, but no."

### 12. Rate-limiting / rapid-fire abuse pattern
1. "Slow down. I'm not that fast, and neither is your patience apparently."
2. "You're hitting me a lot. I'm choosing to be flattered instead of alarmed."
3. "Okay, that's enough of that. Take a breath."
4. "Rapid-fire's cute, but I need a second. Chill."

---

## Notes for implementation
- Selection logic: `random.choice()` on the appropriate list per state, 1-in-4 odds.
- `/health` actively pings the LLM connection each check (not cached/last-known-state), since reviewers may deliberately probe for breakage.
- Placeholders like `[host:port]`, `[route/module name]`, `[file path]` must be
  filled in dynamically by the code — not hardcoded.
- State 9 (Claude key missing entirely) is intentionally NOT handled here —
  that case routes to the `setup.html` first-run form instead of a `/health`
  response.
