#!/usr/bin/env python3
"""Derive the zh-Hant ink set from the current zh-Hans files on disk.

OpenCC s2twp does the script + phrase conversion; PROTECT pins terms whose
Hant form is fixed by the project glossary, and OVERRIDES applies the Taiwan
vocabulary choices s2twp gets wrong or leaves as mainland usage.
"""
import os
import sys

from opencc import OpenCC

SRC = "Dialogue Assets - Already Translated/ZH-HANS"
DST = "Dialogue Assets - Already Translated/ZH-HANT"

# Glossary-fixed terms s2twp would convert wrongly (棋后, not 棋後).
PROTECT = {"棋后": "棋后"}

# Applied after conversion, longest key first.
OVERRIDES = [
    ("臺", "台"),          # 舞臺/平臺/這臺 -> game text uses 台
    ("想象", "想像"),
    ("怎麼劃都", "怎麼划都"),  # paddling, not 劃
    ("壓根", "根本"),        # mainland colloquialism
    ("外賣", "外送"),
    ("誒", "欸"),
    # s2twp misses these in context (converts them correctly in isolation).
    ("干勁", "幹勁"),
    ("廢墟里", "廢墟裡"),
    ("東西里", "東西裡"),
    ("這會兒", "現在"),
    ("詞兒", "詞"),
    ("哪兒", "哪裡"),
    ("這兒", "這裡"),
    ("那兒", "那裡"),
]

# Per-file overrides: 演講 (a speech) vs 報告 (a class presentation).
FILE_OVERRIDES = {
    "ink_PipsqueakLibrary-zh-Hans.ink": [("演講", "報告")],
}


def convert(text, filename, cc):
    for i, term in enumerate(PROTECT):
        text = text.replace(term, f"\x00{i}\x00")
    text = cc.convert(text)
    for i, term in enumerate(PROTECT):
        text = text.replace(f"\x00{i}\x00", PROTECT[term])
    for old, new in OVERRIDES + FILE_OVERRIDES.get(filename, []):
        text = text.replace(old, new)
    return text


def main():
    cc = OpenCC("s2twp")
    os.makedirs(DST, exist_ok=True)
    written = 0
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(".ink"):
            continue
        if "-zh-Hans" not in f:
            sys.exit(f"unexpected source filename: {f}")
        src = open(os.path.join(SRC, f), encoding="utf-8").read()
        out = os.path.join(DST, f.replace("-zh-Hans", "-zh-Hant"))
        open(out, "w", encoding="utf-8").write(convert(src, f, cc))
        written += 1
    print(f"wrote {written} file(s) to {DST}")


if __name__ == "__main__":
    main()
