"""Streamlit UI for the localization toolkit.

Run with:
    streamlit run app.py
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

from loctoolkit.locales import LocaleCatalog, load_locales
from loctoolkit.validate import Severity, has_errors, validate_file


META_COLUMNS = ["key", "description", "max_length", "placeholders"]
_SCHEMA_PATH = Path(__file__).parent / "schema" / "localization.schema.json"
_EXAMPLE_PATH = Path(__file__).parent / "examples" / "sample.loc.json"


def build_dataframe(data: dict, catalog: LocaleCatalog) -> pd.DataFrame:
    rows = []
    for key in sorted(data.get("strings", {}).keys()):
        entry = data["strings"][key]
        translations = entry.get("translations", {}) or {}
        placeholders = entry.get("placeholders", []) or []
        max_length = entry.get("maxLength")

        row = {
            "key": key,
            "description": entry.get("description", ""),
            "max_length": "" if max_length is None else str(max_length),
            "placeholders": "|".join(placeholders),
        }
        for code in catalog.codes:
            row[code] = translations.get(code, "")
        rows.append(row)

    columns = META_COLUMNS + list(catalog.codes)
    return pd.DataFrame(rows, columns=columns)


def style_missing(df: pd.DataFrame, locale_codes: list[str], source_locale: str):
    def highlight(row: pd.Series) -> list[str]:
        styles: list[str] = []
        for col in df.columns:
            if col in locale_codes and (row[col] is None or row[col] == ""):
                if col == source_locale:
                    styles.append("background-color: #fecaca")  # red — source missing
                else:
                    styles.append("background-color: #fde68a")  # amber — target missing
            else:
                styles.append("")
        return styles

    styler = df.style.apply(highlight, axis=1)
    styler = styler.set_properties(
        **{
            "white-space": "normal",
            "word-break": "break-word",
            "vertical-align": "top",
            "font-size": "0.78rem",
            "line-height": "1.25",
            "padding": "4px 6px",
            "max-width": "320px",
        }
    )
    styler = styler.set_table_styles(
        [
            {
                "selector": "th",
                "props": [
                    ("font-size", "0.75rem"),
                    ("text-align", "left"),
                    ("padding", "4px 6px"),
                    ("position", "sticky"),
                    ("top", "0"),
                    ("background-color", "#f3f4f6"),
                ],
            },
            {
                "selector": "table",
                "props": [
                    ("border-collapse", "collapse"),
                    ("width", "100%"),
                ],
            },
            {
                "selector": "td, th",
                "props": [("border", "1px solid #e5e7eb")],
            },
        ]
    )
    return styler


def render_locale_panel(
    data: dict,
    catalog: LocaleCatalog,
    source_locale: str,
    locale: str,
) -> None:
    strings = data.get("strings", {})
    total = len(strings)
    if total == 0:
        st.info("No strings to analyze.")
        return

    missing_keys: list[str] = []
    overflow: list[tuple[str, int, int]] = []
    lengths: list[int] = []

    for key, entry in strings.items():
        translations = entry.get("translations", {}) or {}
        max_length = entry.get("maxLength")
        text = translations.get(locale)

        if not isinstance(text, str) or text == "":
            missing_keys.append(key)
            continue

        lengths.append(len(text))
        if isinstance(max_length, int) and len(text) > max_length:
            overflow.append((key, len(text), max_length))

    translated = total - len(missing_keys)
    completion = (translated / total * 100) if total else 0.0

    name = catalog.name_for(locale) if catalog.contains(locale) else locale
    role = "source" if locale == source_locale else "target"

    cols = st.columns(4)
    cols[0].metric("Locale", f"{locale}", help=name)
    cols[1].metric("Completion", f"{completion:.0f}%", f"{translated}/{total}")
    cols[2].metric(
        "Avg length", f"{(sum(lengths) / len(lengths)):.0f}" if lengths else "—"
    )
    cols[3].metric("Role", role)

    if missing_keys:
        with st.expander(f"Missing translations ({len(missing_keys)})", expanded=False):
            st.dataframe(
                pd.DataFrame({"key": missing_keys}),
                width="stretch",
                hide_index=True,
            )
    else:
        st.success("All keys translated.")

    if overflow:
        with st.expander(
            f"Exceeds maxLength ({len(overflow)})", expanded=False
        ):
            st.dataframe(
                pd.DataFrame(
                    overflow, columns=["key", "length", "max_length"]
                ),
                width="stretch",
                hide_index=True,
            )

    rows = []
    for key in sorted(strings.keys()):
        entry = strings[key]
        translations = entry.get("translations", {}) or {}
        placeholders = entry.get("placeholders", []) or []
        max_length = entry.get("maxLength")
        text = translations.get(locale, "")
        length = len(text) if isinstance(text, str) else 0

        rows.append(
            {
                "key": key,
                "description": entry.get("description", ""),
                "max_length": "" if max_length is None else str(max_length),
                "placeholders": "|".join(placeholders),
                locale: text if isinstance(text, str) else "",
                "length": length,
            }
        )

    df = pd.DataFrame(
        rows,
        columns=["key", "description", "max_length", "placeholders", locale, "length"],
    )

    overflow_keys = {k for k, _, _ in overflow}
    missing_set = set(missing_keys)

    def highlight(row: pd.Series) -> list[str]:
        styles: list[str] = []
        for col in df.columns:
            if col == locale and row["key"] in missing_set:
                bg = "#fecaca" if locale == source_locale else "#fde68a"
                styles.append(f"background-color: {bg}")
            elif col == "length" and row["key"] in overflow_keys:
                styles.append("background-color: #fecaca; font-weight: 600")
            else:
                styles.append("")
        return styles

    styler = df.style.apply(highlight, axis=1)
    styler = styler.set_properties(
        **{
            "white-space": "normal",
            "word-break": "break-word",
            "vertical-align": "top",
            "font-size": "0.78rem",
            "line-height": "1.25",
            "padding": "4px 6px",
            "max-width": "480px",
        }
    )
    styler = styler.set_table_styles(
        [
            {
                "selector": "th",
                "props": [
                    ("font-size", "0.75rem"),
                    ("text-align", "left"),
                    ("padding", "4px 6px"),
                    ("background-color", "#f3f4f6"),
                ],
            },
            {
                "selector": "table",
                "props": [("border-collapse", "collapse"), ("width", "100%")],
            },
            {"selector": "td, th", "props": [("border", "1px solid #e5e7eb")]},
        ]
    )

    st.markdown(styler.to_html(), unsafe_allow_html=True)


def write_temp_file(uploaded) -> Path:
    suffix = Path(uploaded.name).suffix or ".json"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(uploaded.getvalue())
    tmp.close()
    return Path(tmp.name)


def render_issues_summary(issues, source_locale: str):
    errors = [i for i in issues if i.severity is Severity.ERROR]
    warnings = [i for i in issues if i.severity is Severity.WARN]

    cols = st.columns(3)
    cols[0].metric("Errors", len(errors))
    cols[1].metric("Warnings", len(warnings))
    cols[2].metric("Source locale", source_locale)

    if not issues:
        st.success("No issues found.")
        return

    with st.expander(f"{len(issues)} issue(s)", expanded=bool(errors)):
        rows = [
            {
                "severity": i.severity.value,
                "key": i.key or "-",
                "message": i.message,
            }
            for i in issues
        ]
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


_COMPACT_CSS = """
<style>
html, body { font-size: 13px; }
.block-container { padding-top: 3.5rem !important; padding-bottom: 1rem; max-width: 100%; }
[data-testid="stHeader"] { height: auto; }
h1, h2, h3, [data-testid="stHeading"] h1, [data-testid="stHeading"] h2, [data-testid="stHeading"] h3 {
    overflow: visible !important;
}
h1, [data-testid="stHeading"] h1 {
    font-size: 1.4rem !important;
    line-height: 1.6 !important;
    padding: 0.4rem 0 0.4rem 0 !important;
    margin: 0 0 0.4rem 0 !important;
}
h2 { font-size: 1.1rem !important; line-height: 1.4 !important; margin: 0.4rem 0; padding-top: 0.2rem !important; }
h3 { font-size: 1rem !important; line-height: 1.4 !important; margin: 0.3rem 0; padding-top: 0.2rem !important; }
.stMarkdown p { margin-bottom: 0.4rem; }
.stCaption, [data-testid="stCaptionContainer"] { font-size: 0.72rem !important; }
[data-testid="stMetric"] { padding: 4px 6px; }
[data-testid="stMetricLabel"] { font-size: 0.7rem !important; }
[data-testid="stMetricValue"] { font-size: 1.1rem !important; }
[data-testid="stMetricDelta"] { font-size: 0.7rem !important; }
.stTabs [data-baseweb="tab"] { padding: 4px 10px; font-size: 0.78rem; }
.stTabs [data-baseweb="tab-list"] { gap: 2px; }
.stButton button, .stDownloadButton button { padding: 0.25rem 0.6rem; font-size: 0.78rem; }
.stTextInput input, .stSelectbox div[data-baseweb="select"] { font-size: 0.8rem; }
.stCheckbox label { font-size: 0.8rem; }
[data-testid="stExpander"] summary { font-size: 0.8rem; }
[data-testid="stFileUploader"] section { padding: 0.6rem; }
section[data-testid="stSidebar"] { min-width: 280px; }
section[data-testid="stSidebar"] .block-container { padding-top: 0.6rem; }
[data-testid="stHorizontalBlock"] { gap: 0.4rem; }
div[data-testid="stVerticalBlock"] { gap: 0.4rem; }
</style>
"""


def main() -> None:
    st.set_page_config(page_title="Localization Toolkit", layout="wide")
    st.markdown(_COMPACT_CSS, unsafe_allow_html=True)
    st.title("Localization Toolkit")

    catalog = load_locales()

    with st.sidebar:
        st.header("Options")
        options_tab, schema_tab, example_tab = st.tabs(
            ["Settings", "Schema", "Example"]
        )

        with options_tab:
            strict = st.checkbox("Strict mode (warnings → errors)", value=False)
            source_override = st.text_input(
                "Source locale override",
                value="",
                help="Leave empty to use the file's sourceLocale.",
            )
            st.caption(f"Canonical locales: {', '.join(catalog.codes)}")

        with schema_tab:
            st.caption("JSON Schema that uploaded files are validated against.")
            try:
                schema_text = _SCHEMA_PATH.read_text(encoding="utf-8")
                st.code(schema_text, language="json", line_numbers=True)
            except OSError as e:
                st.error(f"Could not load schema: {e}")

        with example_tab:
            st.caption("Minimal valid localization file.")
            try:
                example_text = _EXAMPLE_PATH.read_text(encoding="utf-8")
                st.code(example_text, language="json", line_numbers=True)
            except OSError as e:
                st.error(f"Could not load example: {e}")

    uploaded = st.file_uploader(
        "Upload a .loc.json file", type=["json"], accept_multiple_files=False
    )
    if uploaded is None:
        st.info("Upload a localization JSON file to begin.")
        return

    tmp_path = write_temp_file(uploaded)
    try:
        try:
            data = json.loads(tmp_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON: {e}")
            return

        override: Optional[str] = source_override.strip() or None
        issues = validate_file(
            tmp_path,
            strict=strict,
            source_locale_override=override,
            catalog=catalog,
        )

        source_locale = override or data.get("sourceLocale", catalog.source_default)
        render_issues_summary(issues, source_locale)

        if not isinstance(data, dict) or not isinstance(data.get("strings"), dict):
            st.warning("File has no `strings` object to display.")
            return

        df = build_dataframe(data, catalog)
        locale_codes = list(catalog.codes)

        translations_tab, locale_tab, json_tab = st.tabs(
            ["Translations", "Per-locale", "JSON"]
        )

        with translations_tab:
            st.caption(
                "Empty cells are highlighted: red = missing source-locale string, "
                "amber = missing target-locale translation. Hover or expand a row "
                "to read wrapped text."
            )

            styled = style_missing(df, locale_codes, source_locale)
            st.markdown(styled.to_html(), unsafe_allow_html=True)

            if has_errors(issues):
                st.error("Schema or semantic errors found. CSV export disabled.")
            else:
                csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    "Download CSV",
                    data=csv_bytes,
                    file_name=f"{Path(uploaded.name).stem}.csv",
                    mime="text/csv",
                )

        with locale_tab:
            options = locale_codes
            default_index = (
                options.index(source_locale) if source_locale in options else 0
            )
            selected = st.selectbox(
                "Locale",
                options=options,
                index=default_index,
                format_func=lambda c: (
                    f"{c} — {catalog.name_for(c)}" if catalog.contains(c) else c
                ),
            )
            render_locale_panel(data, catalog, source_locale, selected)

        with json_tab:
            pretty = json.dumps(data, indent=2, ensure_ascii=False, sort_keys=False)
            st.caption(f"{uploaded.name} — {len(pretty):,} chars")
            st.code(pretty, language="json", line_numbers=True)
    finally:
        try:
            tmp_path.unlink()
        except OSError:
            pass


if __name__ == "__main__":
    main()
