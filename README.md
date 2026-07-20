# Spudnik

A personal AI assistant built to replace commercial voice assistants (Siri, Google Assistant) across desktop, phone, and car contexts — developed as a project for **Artificial Intelligence I** at FTCC.

The persona running on top of Spudnik is **Tater** (full system name: *Potato.wiz Beta*, currently V2) — a sarcastic, opinionated tech genius running on what the lore describes as "a mentally unstable potato computer." Tater isn't a generic assistant skin — he pushes back, keeps a memory of past decisions, and has an actual personality baked into how he responds.

---

## What it does

- **Chat with Tater** — a persistent conversational assistant with its own voice and memory
- **Model-agnostic backend** — switches between a local Ollama model (free, runs on your own hardware) and the Claude API (paid, your own key), controlled by a single Reviewer Mode toggle
- **Persistent memory** — Tater remembers things across sessions via a SQLite-backed memory system, browsable from the dashboard
- **Protocol system** — individual behavior rules (file-creation gate, tangent-handling, etc.) that can be toggled on/off, individually or all at once
- **Session management** — every conversation is a named, resumable session; pin the ones you want to find again fast
- **Hardware inventory + tech news** — a dashboard section for tracking your own devices and a live-pulled tech news feed
- **Usage tracking** — real Claude API rate-limit data surfaced directly in the UI, not just theoretical

---

## Tech stack

| Layer | Tech |
|---|---|
| Backend | Python / Flask |
| Database | SQLite |
| LLM layer | Model-agnostic `llm_adapter.py` — switches between local Ollama (Qwen3) and the Claude API |
| Frontend | PWA (Progressive Web App), designed for desktop, phone, and car use |
| Voice | Chatterbox TTS (cloned voice reference, pre-generated clips) |

---

## Getting started

### 1. Clone the repo

```bash
git clone https://github.com/SarahAyresSpudnik/Spudnik.git
cd Spudnik
```

### 2. Set up a virtual environment

```bash
python -m venv pretend_spudnik
source pretend_spudnik/bin/activate      # Windows: pretend_spudnik\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your environment

Copy the example env file and fill in your own values:

```bash
cp .env.example .env
```

At minimum, you'll need:

```
ANTHROPIC_API_KEY=sk-ant-...
FLASK_SECRET_KEY=some-random-string
```

> **You do not need a Claude API key to run Spudnik day-to-day.** Reviewer Mode (off by default) is what forces Claude; leave it off and Spudnik runs on the local Ollama model instead, at zero cost. See [Reviewer Mode](#reviewer-mode) below.

### 5. Run it

```bash
python backend/app.py
```

Visit `http://127.0.0.1:5000` in your browser.

---

## Reviewer Mode

Reviewer Mode is a toggle in the dashboard sidebar (and Settings page) that **forces Claude regardless of any other configuration** — this is a hard override in code, not just a UI suggestion, specifically so a reviewer or instructor can't accidentally end up hitting a local Ollama model that isn't installed on their machine.

- **Off** (default): runs on the local Ollama model. Free, no API key required.
- **On**: routes every message through the Claude API using the key entered in the sidebar's API Key Status card. **This will use your Anthropic API credits.**

If you're grading or demoing this project without wanting to set up Ollama locally, turn Reviewer Mode on and paste in a Claude API key via the sidebar — no code changes needed.

---

## A note on the API key

- Only a **Claude Platform API key** (`sk-ant-api03-...`) works here — a Claude Code OAuth token (`sk-ant-oat01-...`) will not.
- The key is stored in your local `.env` file and is never logged, printed, or transmitted anywhere besides Anthropic's API.
- **Never share your API key** or commit it to a public repository. If you're not sure how to get one, the in-app Help page walks through it.

---

## Project structure

```
backend/          Flask app, routes, LLM adapter, database logic
frontend/         Templates, static assets, dashboard UI
```

---

## Status & what's next

This is an actively developed personal project as well as a course deliverable — expect ongoing changes. Core chat, memory, protocol toggling, session management, and sidebar functionality are working; some dashboard sections (Logs, Help) are newer and still being refined.

**To come:**

- Resolve a known rendering bug in the Presence page's particle-sphere animation (per-particle color binding currently renders black instead of amber/potato-brown)
- Live TTS playback in the dashboard (pre-generated clips are the current approach; real-time generation is too slow on CPU)
- faster-whisper speech-to-text integration
- CatDog companion widget (Rouge and Mage) — deferred, scoped separately
- Continued refinement of the Logs and Help pages
- Ollama-side usage/reserves tracking (currently Claude-only)
- A native Kotlin Android app for Potato/Tater

---

*Built by Sarah Ayres.*
