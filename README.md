# Localization Toolkit

Python CLIs for game localization JSON files:

- `locvalidate` — schema + semantic validation
- `loc2csv` — wide-CSV exporter (one column per locale)

## Quick start

```bash
./scripts/setup.sh    # creates .venv and installs the toolkit + UI + dev deps
./scripts/run-ui.sh   # launches the Streamlit UI
./scripts/test.sh     # runs the test suite
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

`./scripts/run-ui.sh` launches a local Streamlit app. Upload a `.loc.json` file to see validation issues and a wide table with missing translations highlighted (red = missing source, amber = missing target).

## Test

```bash
pytest
```
