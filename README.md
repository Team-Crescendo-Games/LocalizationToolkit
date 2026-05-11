# Localization Toolkit

Python CLIs for game localization JSON files:

- `locvalidate` — schema + semantic validation
- `loc2csv` — wide-CSV exporter (one column per locale)

## Install (dev)

```bash
python3.11 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## Usage

```bash
locvalidate examples/sample.loc.json
loc2csv examples/sample.loc.json -o out.csv
```

Flags:

- `locvalidate --strict` — promote warnings to errors.
- `locvalidate --source-locale CODE` — override the file's `sourceLocale`.

## Test

```bash
pytest
```
