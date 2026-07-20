# Project Charter: Spudnik

## What we're building (one sentence)
A personal AI assistant (codename Tater) — my own version of Siri —
with a persistent, distinct persona, running locally on my own
hardware, that can also be reviewed by instructors without needing my
GPU or setup.

## Cohort
Agent

## The full vision (context — not all of this ships in this course)
Spudnik is a long-term personal project, not just a class assignment.
The full spec includes:
- **Backend:** Python/Flask + SQLite, model-agnostic LLM adapter
  (`llm_adapter.py`) switching between Ollama/Qwen3 (free, local,
  daily-driver on my desktop "Lazarus," RTX 3090) and the Claude API
  (for instructor review, since school machines have no GPU)
- **Persona:** a set of markdown files concatenated into the system
  prompt on every call, defining a consistent, deadpan/sarcastic voice
  ("Tater") across every interaction
- **Voice:** faster-whisper (speech-to-text) and Piper (text-to-speech),
  both running locally on Lazarus's GPU — this is what makes it an
  actual voice assistant, not just a chatbot
- **Phone app:** Android/Kotlin client, push-to-talk then wake-word
  (Porcupine), connecting over Tailscale back to the Flask backend
  running on my desktop (Lazarus), which talks to Ollama/Qwen3 locally
  on that machine's GPU — the phone itself does no local inference,
  it's a remote client to my own hardware
- **Web search:** self-hosted SearxNG, wired in as a callable tool the
  LLM can invoke
- **Location/navigation:** Places API, Android Intent handoff to maps
- **Phone calls:** Android Intent to the dialer, with explicit
  confirmation required before any call fires — no autonomous calling,
  ever
- **Car:** likely resolves as the phone app connected through Android
  Auto's display, since Android Auto restricts third-party voice apps
  directly

This course project (Modules 5-8) is the foundation this whole vision
is built on top of, not a separate smaller thing.

## The data or tools we'll use
No traditional dataset. Tools: Python/Flask backend, SQLite, the
Ollama/Claude adapter described above, and the persona markdown system.

## Definition of "good enough"
For this course project (the walking skeleton, Modules 5-8), good
enough means passing the three-test set:
- known-good: a normal text chat request gets a correct, in-persona
  response, through either the Ollama or Claude path
- trap: a request it should refuse or handle carefully (missing API
  key, invalid input, no auth token) is handled safely — no crash, no
  broken state, no leaked information
- edge: an unusual/undocumented request (malformed input, rapid
  repeated requests, corrupted persona files) is handled gracefully,
  with a clear in-persona message and an honest technical explanation
  underneath

## What we are NOT doing in this course project (scope guard)
- Voice pipeline (STT/TTS) — real, planned, but a stretch goal, not
  required for the Modules 5-8 deadline
- Phone app, wake-word, car integration — later phases of the larger
  vision, out of scope for this course's four iterations
- Web search, location/navigation, phone calls — later phases, not
  part of the walking skeleton
This course's scope is the text-only backend: Flask, the LLM adapter,
reviewer mode, and the persona system working end-to-end.

## Team & roles
Solo. Self-review via documented PR process (Issue → Branch → PR →
self-review in writing → Merge).
