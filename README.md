# Localization Toolkit

Python CLIs for game localization JSON files:

- `locvalidate` — schema + semantic validation
- `loc2csv` — wide-CSV exporter (one column per locale)

## Quick start

```bash
./scripts/setup.sh    # creates .venv and installs the toolkit + UI + dev deps
./scripts/run-json.sh # launches the Streamlit UI (localization JSON)
./scripts/run-ink.sh  # launches the Ink dialogue validator SPA
```

`setup.sh` uses `python3.11` by default — override with `PYTHON=python3.12 ./scripts/setup.sh` if needed.

## Manual install

```bash
python3.11 -m venv .venv
.venv/bin/pip install -e ".[dev,ui]"
```

## CLI usage

```bash
source .venv/bin/activate
locvalidate examples/sample.loc.json
loc2csv examples/sample.loc.json -o out.csv
```

Flags:

- `locvalidate --strict` — promote warnings to errors.
- `locvalidate --source-locale CODE` — override the file's `sourceLocale`.

## UI

`./scripts/run-json.sh` launches a local Streamlit app. Upload a `.loc.json` file to see validation issues and a wide table with missing translations highlighted (red = missing source, amber = missing target).

## Ink dialogue validator

A separate Vite + React SPA at `ink-app/` compiles `.ink` files in the browser
using [inkjs](https://github.com/y-lohse/inkjs) and lets you step through the
dialogue. Requires Node 18+.

```bash
./scripts/run-ink.sh   # http://localhost:5173
```

See `ink-app/README.md` for details.

## AI localization (`/localize`)

`/localize` is a Claude Code skill that translates a source `.loc.json` into one
or more target locales using Claude subagents, with a human-in-the-loop review
loop. You hand it a creative brief; it dispatches one translation subagent per
locale (chunked for large files), validates each result, lets you revise per
locale, and finally merges deterministically.

```text
/localize examples/sample.loc.json --targets zh-Hans,ja --brief brief.md
```

- `--targets`: comma-separated locale codes from `schema/locales.json`.
- `--brief`: a markdown file describing the game, tone, audience, and any
  do-not-translate terms. The skill reads it and may ask follow-up questions.

It only fills **missing** translations (never overwrites existing ones) and
writes, beside the source file:

- `sample.zh-Hans.loc.json`, `sample.ja.loc.json` — one per target (source +
  that one locale). Each is valid against the schema and `locvalidate` in its
  default (non-strict) mode; it intentionally omits the other catalog locales,
  so non-strict validation reports those as warnings, not errors.
- `sample.localized.loc.json` — combined file with all targets (only when more
  than one target is requested).

## Merge per-language files (`locmerge`)

The combine step is deterministic (pure JSON, no AI) and also available as a
standalone CLI:

```bash
source .venv/bin/activate
locmerge examples/sample.loc.json \
  -t examples/sample.zh-Hans.loc.json examples/sample.ja.loc.json \
  -o examples/sample.localized.loc.json
```

The source file is the structural authority; each `-t` file contributes only its
non-source-locale translations. CJK is written literally (`ensure_ascii=False`).

## Test

```bash
pytest
```
