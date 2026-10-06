#!/usr/bin/env python3
"""Word-count translatable dialogue text in .ink files.

Strips ink syntax (declarations, knots, diverts, logic, tags) and counts only
the prose a translator would actually see.
"""
import argparse
import re
import sys
from pathlib import Path

DECL = re.compile(r'^\s*(VAR|CONST|LIST|EXTERNAL|INCLUDE)\b')
KNOT = re.compile(r'^\s*=+')
TILDE = re.compile(r'^\s*~')
BLOCK_COMMENT = re.compile(r'/\*.*?\*/', re.S)
LINE_COMMENT = re.compile(r'/{2,}.*$')
TAGS = re.compile(r'#.*$')
SEQ_OPEN = re.compile(r'\{\s*(shuffle|stopping|cycle|once)\s*(&\s*)?:')
COND_OPEN = re.compile(r'\{[^{}|]*?:')
INSERT = re.compile(r'\{[^{}]*\}')
GLUE = re.compile(r'<>')
HTML = re.compile(r'</?[a-zA-Z][^>]*>')
DIVERT = re.compile(r'(->|<-)\s*[\w.]*')
CHOICE_MARK = re.compile(r'^\s*[*+]+\s*')
GATHER_MARK = re.compile(r'^\s*-\s*')
LABEL = re.compile(r'^\s*\(\s*\w+\s*\)\s*')
CONDITION = re.compile(r':\s*$')


def extract_text(source: str) -> list[str]:
    source = BLOCK_COMMENT.sub('', source)
    out = []
    for raw in source.splitlines():
        line = LINE_COMMENT.sub('', raw)
        if DECL.match(line) or KNOT.match(line) or TILDE.match(line):
            continue

        # diverts first: otherwise "-> END" loses its "-" to the gather mark
        line = DIVERT.sub(' ', line)

        is_choice = bool(CHOICE_MARK.match(line))
        line = CHOICE_MARK.sub('', line, count=1)
        is_branch = not is_choice and bool(GATHER_MARK.match(line))
        if is_branch:
            line = GATHER_MARK.sub('', line, count=1)
        line = LABEL.sub('', line, count=1)

        # peel logic scaffolding but keep alternative text: a translator
        # still has to translate every branch of {cond: a|b}
        line = SEQ_OPEN.sub(' ', line)
        prev = None
        while prev != line:
            prev = line
            line = COND_OPEN.sub(' ', line)
            line = INSERT.sub(' ', line)

        # "- someVar > 0:" is a switch branch condition, not prose
        if is_branch and CONDITION.search(line):
            continue

        line = TAGS.sub(' ', line)
        line = GLUE.sub(' ', line)
        line = HTML.sub(' ', line)
        for ch in '[]{}|':
            line = line.replace(ch, ' ')
        line = line.replace('__', ' ')
        line = re.sub(r'\s+', ' ', line).strip()

        if not line or not re.search(r'[A-Za-zÀ-ɏ一-鿿]', line):
            continue
        out.append(line)
    return out


def count_words(lines: list[str]) -> int:
    total = 0
    for line in lines:
        latin = re.sub(r'[　-鿿＀-￯]', ' ', line)
        total += len(latin.split())
        total += len(re.findall(r'[一-鿿]', line))
    return total


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('paths', nargs='+', type=Path)
    ap.add_argument('--show-text', action='store_true',
                    help='dump extracted lines instead of counting')
    args = ap.parse_args()

    files = []
    for p in args.paths:
        files.extend(sorted(p.rglob('*.ink')) if p.is_dir() else [p])

    if args.show_text:
        for f in files:
            for line in extract_text(f.read_text(encoding='utf-8')):
                print(line)
        return 0

    grand_words = grand_lines = grand_chars = 0
    print(f'{"file":<58}{"lines":>7}{"words":>8}{"chars":>8}')
    print('-' * 81)
    for f in files:
        lines = extract_text(f.read_text(encoding='utf-8'))
        words = count_words(lines)
        chars = sum(len(l) for l in lines)
        grand_words += words
        grand_lines += len(lines)
        grand_chars += chars
        print(f'{f.name[:57]:<58}{len(lines):>7}{words:>8}{chars:>8}')
    print('-' * 81)
    print(f'{f"TOTAL ({len(files)} files)":<58}{grand_lines:>7}{grand_words:>8}{grand_chars:>8}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
