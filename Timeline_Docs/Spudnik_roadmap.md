# Spudnik_roadmap.md
# Spudnik — Vision, Platform Scope & Security Roadmap

---

## THE VISION

Replace Siri / Google Assistant entirely, across every surface:
- **Phone** (Android) — primary interface, mic in/out, wake-word + push-to-talk
- **Computer** (desktop) — text or voice, same brain
- **Car** — voice-first, hands-free, safety-critical context

Same personality, same memory, everywhere. Not three separate assistants
that happen to share a name — one Tater, reachable from anywhere, via
Lazarus as the single brain.

---

## CAPABILITY LIST

| Capability | What it means | How it gets built |
|---|---|---|
| Voice conversation | Talk to Tater, get spoken replies | faster-whisper (STT) + Ollama + Piper (TTS) |
| Web search | "Look this up" | SearxNG self-hosted on Lazarus, called server-side, results fed to the LLM as context, summarized in Tater's voice |
| Phone calls | "Call Mom" | Android Intent triggers native dialer — Tater doesn't build its own calling stack, it hands off to the phone's existing capability |
| Maps / navigation | "Directions to work" | Android Intent hands off to the Google Maps app directly (no need to embed Maps API for basic nav) |
| Location-aware queries | "What's near me" | Google Places API, called server-side with an API key that never touches the phone |
| Project/status awareness | "What's up with Chronos Fading" | Reads tater-projects.md |
| Daily briefings | Weather, gaming news, patches, etc. | Six existing protocols, to be rebuilt as their own file |

---

## PLATFORM NOTES & KNOWN CHALLENGES

**Phone (Android):** The most straightforward target. Native Kotlin app,
mic access, wake-word + push-to-talk both supported. This is the build-first
platform.

**Desktop:** Second easiest — a lightweight client (browser tab or thin app)
talking to Lazarus over Tailscale. No new backend work needed, just a thin
client.

**Car:** The hardest and riskiest platform. Two honest constraints worth
knowing now, before this becomes a blocker later:
- Android Auto restricts what third-party apps can do with voice
  interaction, for driver-distraction/safety reasons — it's not a fully
  open surface the way a phone app is.
- Fully replacing the phone's *default* assistant (the one that answers
  "Hey Google" system-wide, including in car mode) requires the app to
  be set as the default digital assistant in Android settings, which
  has its own requirements and isn't guaranteed to work smoothly with
  a custom app.
- **Recommendation:** treat car support as its own phase, after phone +
  desktop are solid. It may end up being "the phone app, connected to
  the car's Bluetooth/Android Auto display" rather than a from-scratch
  car integration — lower risk, same practical result.

---

## SECURITY REQUIREMENTS (NON-NEGOTIABLE)

Since this thing will be able to place calls, access location, and hold
a running log of your life — security isn't an afterthought layer, it's
part of the initial build.

1. **Network transport:** Tailscale handles encrypted transport between
   phone/desktop and Lazarus. This solves "don't expose your home network
   to the open internet" — it does NOT solve app-level authentication.

2. **App-level authentication:** Even inside your own Tailnet, the Flask
   backend needs to verify that a request actually came from your phone/
   desktop client — a token or session-based auth layer, not just "if it
   can reach the server, trust it." This matters if a device is ever lost,
   stolen, or someone else gets on your Tailnet.

3. **API keys never live on the phone.** Google Maps / Places / Search API
   keys stay server-side on Lazarus, inside the Flask app. An Android APK
   can be decompiled — anything embedded in it should be treated as
   eventually public. The phone app talks to your Flask server; your
   Flask server talks to Google.

4. **Phone calls require explicit confirmation.** No autonomous calling.
   Tater should always confirm ("Want me to call X?") before the dialer
   Intent actually fires — this is the single highest-risk feature if it
   ever misfires or mishears.

5. **Mic handling:** No raw audio streams continuously to the server.
   Wake-word detection happens locally on-device (Porcupine runs on-phone,
   not round-tripped to Lazarus) — only the actual command audio after
   activation gets sent. Clear visual indicator whenever the mic is
   actively capturing.

6. **Data at rest:** The SQLite database on Lazarus holds memory logs,
   argument history, and personal context — this should be access-
   controlled at the OS level at minimum, encrypted at rest as a stretch
   goal.

7. **Sensitive Android permissions** (CALL_PHONE, contacts, location,
   background mic) get requested individually, at time of first use, with
   a clear explanation — not all requested up front on install.

8. **Dependency hygiene:** Flask app and its dependencies (including
   whatever search tools, faster-whisper, Piper) get kept current.
   A home-hosted server reachable from anywhere is a real target if
   left stale.

9. **API keys in the repo (reviewer/teacher demo mode):** Never committed,
   ever — not yours, not a teacher's. Reviewer copies of the project use
   their own Claude Platform key, entered once through the local first-run
   setup webview, written straight to a local `.env` that's gitignored.
   `setup.sh` handles venv/install/config; the key itself is the one
   manual, non-automatable step, by design.

---

## SUGGESTED BUILD ORDER (PHASED)

**Phase 1 — Core loop, phone only, no car, no calls yet**
- Flask backend + Tailscale reachability confirmed
- faster-whisper + Piper wired into llm_adapter.py
- Kotlin app: push-to-talk only (wake-word deferred)
- Basic conversation working end-to-end, persona files loaded
- Reviewer-mode setup flow (setup.sh + first-run API-key webview) working
  for teacher demo copies

**Phase 2 — Add capability, still phone-first**
- Web search tool wired into the backend (SearxNG)
- Maps/navigation via Intent handoff
- Wake-word added (Porcupine)
- App-level auth token implemented

**Phase 3 — Desktop client**
- Thin client hitting the same Flask backend
- Same auth model extended

**Phase 4 — Phone calls**
- Contact resolution + confirmation flow
- CALL_PHONE permission handling

**Phase 5 — Car**
- Evaluate Android Auto constraints for real
- Likely: extend the phone app rather than build a separate car app

---

## OPEN DECISIONS

- Desktop client: browser tab vs dedicated lightweight app
- Auth token scheme: simple shared secret vs something more robust
  (this matters more once calls/location are in play)
- Exact wake-word engine config (Porcupine free tier limits, if any,
  worth a look before Phase 2 starts)
