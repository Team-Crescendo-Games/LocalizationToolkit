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

## Test

```bash
pytest
```
