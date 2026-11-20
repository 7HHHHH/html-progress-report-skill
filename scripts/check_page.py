#!/usr/bin/env python3
"""Validate a living progress page produced by the html-progress-report skill.

Usage: python3 check_page.py path/to/index.html
Exit code 0 = OK (warnings may be printed), 1 = errors found.
Standard library only.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from html.parser import HTMLParser

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "source", "track", "wbr"}
REQUIRED_MARKERS = ["@header:start", "@header:end", "@snapshot:start",
                    "@snapshot:end", "@method:start", "@method:end",
                    "@timeline:insert"]
KNOWN_TAGS = {"feature", "fix", "experiment", "research", "refactor", "docs",
              "infra", "decision", "blocked"}
STATUSES = {"ok", "warn", "bad", "info"}


class Checker(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, int]] = []
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.entries: list[dict] = []
        self.charts = 0
        self.in_entry_depth: int | None = None
        self.entry_has_visual = False

    VISUAL_CLASSES = {"chart", "flow", "compare", "board", "kpis", "progress",
                      "diff", "tree", "mermaid", "sortable"}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        line = self.getpos()[0]
        cls = set((a.get("class") or "").split())
        if tag not in VOID:
            self.stack.append((tag, line))
        if tag == "article" and "entry" in cls:
            self.entries.append({"line": line, **a})
            self.in_entry_depth = len(self.stack)
            self.entry_has_visual = False
        elif self.in_entry_depth is not None and (cls & self.VISUAL_CLASSES or tag == "table"):
            self.entry_has_visual = True
        if "chart" in cls and "data-series" in a:
            self.charts += 1
            for key in ("data-series", "data-labels"):
                if key in a:
                    try:
                        val = json.loads(a[key])
                        if key == "data-series" and not (isinstance(val, list) and val and all("values" in s for s in val)):
                            self.errors.append(f"line {line}: {key} must be a non-empty list of objects with 'values'")
                    except json.JSONDecodeError as e:
                        self.errors.append(f"line {line}: {key} is not valid JSON ({e.msg})")

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        line = self.getpos()[0]
        if not self.stack:
            self.errors.append(f"line {line}: stray </{tag}>")
            return
        if self.stack[-1][0] == tag:
            if tag == "article" and self.in_entry_depth == len(self.stack):
                if not self.entry_has_visual:
                    self.warnings.append(f"entry at line {self.entries[-1]['line']}: no visual component")
                self.in_entry_depth = None
            self.stack.pop()
            return
        # tolerate implicitly closed tags (p, li, td, ...) by searching down the stack
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                for t, l in self.stack[i + 1:]:
                    if t not in {"p", "li", "td", "th", "tr", "option", "dt", "dd"}:
                        self.errors.append(f"line {l}: <{t}> not closed before </{tag}> at line {line}")
                del self.stack[i:]
                return
        self.errors.append(f"line {line}: </{tag}> has no matching open tag")


def main(path: str) -> int:
    try:
        text = open(path, encoding="utf-8").read()
    except OSError as e:
        print(f"ERROR: cannot read {path}: {e}")
        return 1
    c = Checker()
    for m in REQUIRED_MARKERS:
        n = text.count(f"<!-- {m} -->")
        if n != 1:
            c.errors.append(f"marker '<!-- {m} -->' found {n} times (expected 1)")
    if "{{" in text and "}}" in text:
        left = sorted(set(re.findall(r"\{\{[A-Z_]+\}\}", text)))
        if left:
            c.errors.append(f"unfilled placeholders: {', '.join(left)}")
    m = re.search(r"<!-- @method:start -->(.*?)<!-- @method:end -->", text, re.S)
    if m:
        body = m.group(1)
        has = lambda *cls: any(re.search(r'class="[^"]*\b%s\b' % k, body) for k in cls)
        if not has("analogy"):
            c.warnings.append("method: no .analogy block (explain the idea with an everyday analogy)")
        if not has("flow", "mermaid"):
            c.warnings.append("method: no diagram (.flow or .mermaid)")
        if not has("walk"):
            c.warnings.append("method: no .walk walkthrough (trace one concrete example)")
        if not has("why"):
            c.warnings.append("method: no .why block (key design choices and rejected alternatives)")
    c.feed(text)
    c.close()
    for t, l in c.stack:
        if t not in {"p", "li", "td", "th", "tr"}:
            c.errors.append(f"line {l}: <{t}> never closed")

    times = []
    for e in c.entries:
        where = f"entry at line {e['line']}"
        t = e.get("data-time")
        if not t:
            c.errors.append(f"{where}: missing data-time")
        else:
            try:
                dt = datetime.fromisoformat(t.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    c.warnings.append(f"{where}: data-time has no timezone")
                times.append(t)
            except ValueError:
                c.errors.append(f"{where}: data-time '{t}' is not ISO 8601")
        tags = (e.get("data-tags") or "").split()
        if not tags:
            c.warnings.append(f"{where}: no data-tags")
        unknown = set(tags) - KNOWN_TAGS
        if unknown:
            c.warnings.append(f"{where}: non-standard tags {sorted(unknown)}")
        if e.get("data-status") not in STATUSES:
            c.warnings.append(f"{where}: data-status should be one of {sorted(STATUSES)}")
        if not e.get("data-commit"):
            c.warnings.append(f"{where}: no data-commit")
    if times != sorted(times, reverse=True):
        c.warnings.append("timeline entries are not newest-first")
    if len(c.entries) > 30:
        c.warnings.append(f"{len(c.entries)} timeline entries; consider archiving old ones")

    for w in c.warnings:
        print(f"warn:  {w}")
    for err in c.errors:
        print(f"ERROR: {err}")
    print(f"{'FAIL' if c.errors else 'OK'}: {len(c.entries)} entries, {c.charts} charts, "
          f"{len(c.errors)} errors, {len(c.warnings)} warnings")
    return 1 if c.errors else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
