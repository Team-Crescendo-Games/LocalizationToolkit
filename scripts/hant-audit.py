#!/usr/bin/env python3
"""Print every zh-Hant occurrence of a simplified->traditional one-to-many
character, in context, so each choice can be eyeballed. Empty output for a
character means it was fully converted away.

Characters listed here are the ones where the correct traditional form depends
on meaning, so an automated converter can silently pick wrong.
"""
import os
import re

D = "Dialogue Assets - Already Translated/ZH-HANT"
AMBIGUOUS = "干后发里台只制复尽划象采冲折表钟历于云系发准板蒙恶脏苏"

for ch in AMBIGUOUS:
    hits = []
    for f in sorted(os.listdir(D)):
        if not f.endswith(".ink"):
            continue
        txt = open(os.path.join(D, f), encoding="utf-8").read()
        for m in re.finditer(re.escape(ch), txt):
            hits.append(f"  {f}: ...{txt[max(0, m.start()-8):m.start()+9]}...")
    if hits:
        print(f"=== {ch} ({len(hits)}) ===")
        print("\n".join(sorted(set(hits))))
print("\n(no output above a character = fully converted)")
