# Agent Guardrails: Spudnik

Rules that keep AI assistants (Claude Code, Claude chat) on task while
working on this project.

## What Claude Code is allowed to do
- Write boilerplate/repetitive code (config files, templates, standard
  scaffolding like issue/PR templates and labels)
- Make suggestions on structure, architecture, and implementation
- Run read-only or low-risk commands (like `gh label create`) after I
  approve the specific action

## What Claude Code must never do
- Never commit, push, or manage branches on its own — I handle all git
  operations manually so I stay the one who understands my own repo
  history
- Never make structural or architectural decisions unprompted — those
  are mine to make, Claude Code implements what I've already decided
- Never touch API keys or `.env` contents directly, and never commit
  secrets of any kind, regardless of whose key it is
- Never make live API calls to a paid model without my explicit
  go-ahead, since testing may use a borrowed key (a teacher's) that
  should be used sparingly

## How I check its work
- I review every file Claude Code creates before committing it myself
- Logic gets verified offline / by inspection first; live API calls
  are reserved for a single deliberate confirmation, not repeated
  debugging
- Claude Sonnet is the default model for this kind of task (boilerplate,
  not high-stakes reasoning) — I explicitly avoid burning tokens on
  Opus-level tasks I don't need
- Full updated files are requested as output, not diffs/snippets,
  so I can see the whole picture of what changed

## Why these rules exist
An AI partner without guardrails tends to "help" by doing more than
asked — rewriting things unprompted, or making decisions that should
be mine. These rules keep Claude Code doing the repetitive heavy
lifting while I stay the one who understands and owns the actual
project structure, decisions, and history.
