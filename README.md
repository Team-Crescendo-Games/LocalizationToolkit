# Localization Toolkit

Python CLIs for game localization JSON files:

- `locvalidate` — schema + semantic validation
- `loc2csv` — wide-CSV exporter (one column per locale)
- `csv2loc` — wide-CSV importer (spreadsheet export → JSON)

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
csv2loc out.csv -o roundtrip.loc.json
```

Flags:

- `locvalidate --strict` — promote warnings to errors.
- `locvalidate --source-locale CODE` — override the file's `sourceLocale`.
- `csv2loc --source-locale CODE` — which column is the source (default `en`).

## CSV import (`csv2loc`)

Turns a translator-facing spreadsheet export into a `.loc.json` the rest of the
toolkit (and `/localize`) can consume:

```bash
csv2loc "examples/Memoria Wake Localization - UI Text.csv" -o examples/ui-text.loc.json
```

Header dialects — both accepted, so a `loc2csv` export round-trips losslessly:

- sheet style, name plus parenthesised code: `Chinese (Simplified)(zh-Hans)`
- bare canonical codes: `zh-Hans`

Columns named `description`, `max_length`, and `placeholders` (pipe-separated)
are read as metadata; everything else must resolve to a locale code from
`schema/locales.json` or the import fails.

Behaviour worth knowing:

- **Blank locale cell → the locale is omitted**, never written as `""`. Absent is
  what marks a string as still needing translation; `""` reads as "already done"
  and `/localize` would skip it.
- **No `description` column → the key is used as the description** (the schema
  requires a non-empty one) and a warning reports the count. Descriptions are
  what `/localize` feeds translators, so add the column when you can.
- **No `placeholders` column → tokens are inferred** from the source cell:
  `{...}` and `<...>`, in first-appearance order, deduplicated. That covers
  TextMeshPro markup like `<sprite name="Sprt">` and
  `<action=UI_Exit, compositeId=0>`, so `locvalidate` then enforces their
  survival in every translation.
- Fatal (exit 1, nothing written): missing `key` column, no locale columns, an
  unrecognised header, an unknown locale code, or a key that violates the schema
  key pattern.
- Non-fatal warnings on stderr: duplicate keys (first row wins), rows with no
  translations at all (skipped), non-integer `max_length` (dropped), and a
  placeholder repeated within one source string (declared once, since the schema
  requires unique items).

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
