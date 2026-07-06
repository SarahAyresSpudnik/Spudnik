# Spudnik_roadmap.md
# Spudnik — Vision, Platform Scope & Security Roadmap
# Updated: reprioritized for desktop-first build order

---

## THE VISION

Replace Siri / Google Assistant entirely, across every surface:
- **Computer** (desktop) — text or voice, local daily driver
- **Phone** (Android) — mic in/out, wake-word + push-to-talk
- **Car** — voice-first, hands-free, safety-critical context

Same personality, same memory, everywhere. Not separate assistants that
happen to share a name — one Tater, reachable from anywhere, via Lazarus
as the single brain.

---

## PRIORITY NOTE

**Desktop is the deadline-critical piece.** Both the local daily-driver
version and the teacher reviewer version need to be working before the
end of summer semester. Phone (Kotlin/Android) is real work, but it is
NOT blocking that deadline — it's the next phase after desktop is solid.

---

## CAPABILITY LIST

| Capability | What it means | How it gets built |
|---|---|---|
| Voice conversation | Talk to Tater, get spoken replies | faster-whisper (STT) + Ollama + Piper (TTS) |
| Web search | "Look this up" | SearxNG self-hosted on Lazarus, called server-side, results fed to the LLM as context, summarized in Tater's voice |
| Phone calls | "Call Mom" | Android Intent triggers native dialer — Tater doesn't build its own calling stack, it hands off to the phone's existing capability |
| Maps / navigation | "Directions to work" | Android Intent hands off to the Google Maps app directly (no need to embed Maps API for basic nav) |
| Location-aware queries | "What's near me" | Google Places API, called server-side with an API key that never touches the client |
| Project/status awareness | "What's up with Chronos Fading" | Reads tater-projects.md |
| Daily briefings | Weather, gaming news, patches, etc. | Six existing protocols, to be rebuilt as their own file |

---

## PLATFORM NOTES & KNOWN CHALLENGES

**Desktop (build first):** Genuinely the fastest path to something done —
no mic permissions, no background service restrictions, no app store
concerns. Two variants of the same Flask app:
- **Local daily driver** — `LLM_PROVIDER=ollama`, runs on Lazarus, free,
  no key needed
- **Teacher reviewer version** — `LLM_PROVIDER=claude`, `REVIEWER_MODE=true`,
  bound to `127.0.0.1` only, first-run webview collects their own API key
  once, never touches git

A browser tab pointed at `localhost:5000` is a legitimate "client" here —
no separate frontend framework required unless something fancier is
wanted later.

**Phone (Android):** Native Kotlin app, mic access, wake-word +
push-to-talk both supported. Real work — background audio services,
battery-optimization exemptions, foreground service notifications for
wake-word listening. Comes after desktop is solid, not before.

**Car:** The hardest and riskiest platform, further out still. Two
honest constraints worth knowing now, before this becomes a blocker
later:
- Android Auto restricts what third-party apps can do with voice
  interaction, for driver-distraction/safety reasons — it's not a fully
  open surface the way a phone app is.
- Fully replacing the phone's *default* assistant (the one that answers
  "Hey Google" system-wide, including in car mode) requires the app to
  be set as the default digital assistant in Android settings, which
  has its own requirements and isn't guaranteed to work smoothly with
  a custom app.
- **Recommendation:** likely ends up being "the phone app, connected to
  the car's Bluetooth/Android Auto display" rather than a from-scratch
  car integration — lower risk, same practical result.

---

## SECURITY REQUIREMENTS (NON-NEGOTIABLE)

Since this thing will eventually place calls, access location, and hold
a running log of your life — security isn't an afterthought layer, it's
part of the initial build, starting with desktop.

1. **Network transport:** Tailscale handles encrypted transport between
   any remote client and Lazarus. This solves "don't expose your home
   network to the open internet" — it does NOT solve app-level
   authentication.

2. **App-level authentication:** Even inside your own Tailnet, the Flask
   backend needs to verify that a request actually came from a trusted
   client — a token or session-based auth layer, not just "if it can
   reach the server, trust it."

3. **API keys never live client-side.** Google Maps / Places / Search API
   keys stay server-side on Lazarus, inside the Flask app.

4. **Phone calls require explicit confirmation.** No autonomous calling,
   once that phase arrives. Tater should always confirm before the dialer
   Intent actually fires.

5. **Mic handling (once phone phase starts):** No raw audio streams
   continuously to the server. Wake-word detection happens locally
   on-device — only the actual command audio after activation gets sent.
   Clear visual indicator whenever the mic is actively capturing.

6. **Data at rest:** The SQLite database on Lazarus holds memory logs,
   argument history, and personal context — access-controlled at the OS
   level at minimum, encrypted at rest as a stretch goal.

7. **Sensitive Android permissions** (once phone phase starts): CALL_PHONE,
   contacts, location, background mic — requested individually, at time
   of first use, with a clear explanation.

8. **Dependency hygiene:** Flask app and its dependencies kept current.
   A home-hosted server reachable from anywhere is a real target if
   left stale.

9. **API keys in the repo (reviewer/teacher demo mode):** Never committed,
   ever — not yours, not a teacher's. Reviewer copies use their own Claude
   Platform key, entered once through the local first-run setup webview,
   written straight to a local `.env` that's gitignored. `setup.sh` handles
   venv/install/config; the key itself is the one manual, non-automatable
   step, by design.

---

## SUGGESTED BUILD ORDER (PHASED — REPRIORITIZED)

**Phase 1 — Desktop, both variants (PRIORITY — target: before end of summer semester)**
- Flask backend running: `/health`, `/chat/text` at minimum
- Local daily-driver path confirmed working against Ollama/Qwen3 on Lazarus
- `setup.sh` + first-run API-key webview working for the teacher reviewer path
- `REVIEWER_MODE` toggle (host binding, auth relaxation for local-only use) implemented
- Persona files loading correctly into `llm_adapter.py` context
- Voice pipeline (faster-whisper + Piper) added if time allows — text-only
  is an acceptable fallback to hit the deadline if voice isn't ready in time

**Phase 2 — Phone (Android/Kotlin)**
- Push-to-talk client first
- App-level auth token implemented for remote (Tailscale) access
- Wake-word added after push-to-talk is proven

**Phase 3 — Add capability across both platforms**
- Web search tool wired in (SearxNG)
- Maps/navigation via Intent handoff (phone-specific)
- Location-aware queries (Places API)

**Phase 4 — Phone calls**
- Contact resolution + confirmation flow
- CALL_PHONE permission handling

**Phase 5 — Car**
- Evaluate Android Auto constraints for real
- Likely extends the phone app rather than building a separate car app

---

## OPEN DECISIONS

- Desktop client polish: bare browser tab vs. a slightly nicer local
  frontend — not required for the deadline, worth revisiting after
  Phase 1 is functionally done
- Auth token scheme: simple shared secret vs. something more robust
  (matters more once Phase 2 introduces remote/phone access)
- Exact wake-word engine config — deferred, not relevant until Phase 2
