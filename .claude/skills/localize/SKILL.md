---
name: localize
description: Use when the user wants to translate/localize a .loc.json file into one or more target languages using Claude. Dispatches one translation subagent per locale (chunked for large files), runs a validation gate, drives a per-locale human review loop, then merges deterministically with the locmerge CLI.
---

# Localize a .loc.json file with Claude

Translate a source localization file into target locales using subagents, with a
human-in-the-loop revision loop. You orchestrate; you do NOT translate yourself.

**Invocation:** `/localize <source.loc.json> --targets zh-Hans,ja --brief brief.md`

- `--targets`: comma-separated locale codes (must exist in `schema/locales.json`).
- `--brief`: path to a creative-context brief the user hands over. Read it fully.

## Phase 1 — Plan

1. Read and parse the source file. Confirm it is valid: run
   `.venv/bin/python -m loctoolkit.cli.locvalidate <source>` and fix-blocking
   errors with the user before continuing.
2. Validate every requested target against `schema/locales.json`. If any code is
   unknown, STOP and list the valid codes.
3. Read the `--brief` file. If it has real gaps for translation quality (tone,
   audience, do-not-translate terms, formality for ja/ko, zh-Hans vs zh-Hant
   conventions), ask the user concise interview-style follow-ups. Otherwise
   proceed.
4. Build the **rolling glossary** (session-only): start from the brief's terms
   and decisions. You will append user review decisions to it. Never write it to
   disk unless asked.
5. For each target locale, collect the **missing** keys only — keys whose
   `translations` map lacks that locale. Never plan to overwrite existing
   translations (fill-missing). If the user asked to retranslate specific keys,
   include exactly those.
6. If a locale has many missing keys, split them into chunks (~40-50 keys per
   chunk) so each subagent handles a manageable slice.

## Phase 2 — Translate (dispatch subagents)

For each (locale × chunk), dispatch a `general-purpose` subagent IN PARALLEL
(one message, multiple Agent tool calls). Each subagent prompt MUST contain:

- Role: "You are an expert game translator localizing into <locale name>."
- The full brief content, inlined verbatim.
- The current rolling glossary / locked decisions.
- A JSON array of items, one per key:
  `{"key": ..., "description": ..., "placeholders": [...], "maxLength": ..., "sourceText": ...}`
- Hard rules:
  - Preserve every placeholder token EXACTLY (e.g. `{score}` stays `{score}`).
  - Respect `maxLength` as a character count when present.
  - Return ONLY a JSON object mapping `key` -> translated string for THIS chunk
    and THIS locale. No prose, no markdown, no file structure.

Assemble all chunk returns for a locale into one `key -> translation` map.

## Phase 3 — Validation gate (per locale)

1. Build the per-language file beside the source, inserting the locale code
   before the `.loc.json` suffix — e.g. for `examples/sample.loc.json` and
   locale `zh-Hans`, write `examples/sample.zh-Hans.loc.json` (NOT
   `sample.loc.zh-Hans.loc.json`). Each string's `translations` map carries the
   **source locale + this one target only** (copy source text + the new
   translation).
2. Validate it: `.venv/bin/python -m loctoolkit.cli.locvalidate <per-lang-file>`.
   Run WITHOUT `--strict`. Expect many `WARN: missing translation for target
   locale '...'` lines — a per-language file intentionally omits every other
   catalog locale, so those warnings are normal and NOT blocking. Only ERRORs
   (placeholder mismatch, maxLength overflow, bad JSON) gate the result.
3. If there are ERRORS (placeholder mismatch, maxLength overflow, bad JSON),
   re-dispatch a subagent for ONLY the failing keys with the validator output
   included, asking it to correct. Cap at 2 self-correct rounds. If errors
   remain, carry them into review and let the user decide.

## Phase 4 — Review (per locale, human-in-loop)

1. Show the user the locale's translations (source vs target, side by side).
   Flag any remaining validation issues and any keys you could not translate
   (e.g. missing source text).
2. Take feedback. When the user locks a decision ("keep 'Ink' untranslated",
   "less formal"), append it to the rolling glossary so it persists across
   rounds and locales.
3. Re-dispatch ONLY the affected keys for the affected locale with the updated
   glossary; re-run the gate; re-show. Repeat until the user approves the locale.
4. The user may approve some locales and keep iterating others (partial
   approval).

## Phase 5 — Merge (deterministic — NOT agentic)

1. Once all requested locales are approved (or the user explicitly says to merge
   what's approved), and only if MORE THAN ONE target was produced, run:

       .venv/bin/python -m loctoolkit.cli.locmerge <source> \
         -t <per-lang-1> <per-lang-2> ... \
         -o <combined>

   where `<combined>` inserts `localized` before the `.loc.json` suffix — e.g.
   for `examples/sample.loc.json`, write `examples/sample.localized.loc.json`.

   Surface any `locmerge` warnings to the user.
2. Validate the combined file:
   `.venv/bin/python -m loctoolkit.cli.locvalidate <combined>`.
3. Report all written files: each per-language file and (if applicable) the
   combined file.

## Notes

- The merge is always deterministic via `locmerge`. Never hand-merge JSON.
- If only one target locale is requested, there is no combined file — the single
  per-language file is the deliverable.
