#!/usr/bin/env python3
"""Validate a living progress page produced by the html-progress-report skill.

Usage: python3 check_page.py path/to/index.html
Exit code 0 = OK (warnings may be printed), 1 = errors found.
Standard library only.
"""
from __future__ import annotations

import json
import os
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
CLAIM_KINDS = {"decision", "assumption", "deviation", "question"}
EVIDENCE = {"run", "code", "doc", "guess"}


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
        self.images: list[tuple[int, str]] = []
        self.pages: list[tuple[int, str | None, str | None]] = []
        self.diagrams = 0
        self.claims: list[dict] = []
        self.has_goal = False

    VISUAL_CLASSES = {"chart", "flow", "compare", "board", "kpis", "progress",
                      "diff", "tree", "mermaid", "sortable", "diagram", "imgflow",
                      "tokens", "formula", "figure", "why"}

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
        if "claim" in cls:
            self.claims.append({"line": line, **a})
        if "goal" in cls:
            self.has_goal = True
        if tag == "img" and a.get("src"):
            self.images.append((line, a["src"]))
        if tag == "section" and "page" in cls:
            self.pages.append((line, a.get("id"), a.get("data-nav")))
        if "diagram" in cls and "data-nodes" in a:
            self.diagrams += 1
            try:
                nodes = json.loads(a["data-nodes"])
                ids = {n["id"] for n in nodes}
                for n in nodes:
                    if n.get("img"):
                        self.images.append((line, n["img"]))
                edges = json.loads(a.get("data-edges") or "[]")
                for e in edges:
                    ends = e[:2] if isinstance(e, list) else [e.get("from"), e.get("to")]
                    bad = [x for x in ends if x not in ids]
                    if bad:
                        self.errors.append(f"line {line}: diagram edge refers to unknown node(s) {bad}")
                for g in json.loads(a.get("data-groups") or "[]"):
                    bad = [x for x in g.get("nodes", []) if x not in ids]
                    if bad:
                        self.errors.append(f"line {line}: diagram group refers to unknown node(s) {bad}")
            except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as e:
                self.errors.append(f"line {line}: diagram data-nodes/edges/groups invalid ({e})")
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


class ProseCounter(HTMLParser):
    """Counts visible text that sits outside visual components (the 'wall of text' budget)."""
    COMPONENTS = Checker.VISUAL_CLASSES | {"analogy", "walk", "idea", "callout", "page-head",
                                           "tablewrap", "legend"}
    SKIP_TAGS = {"pre", "table", "details", "code", "script", "style"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[bool] = []
        self.chars = 0

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        cls = set((dict(attrs).get("class") or "").split())
        inside = (self.stack[-1] if self.stack else False) or bool(cls & self.COMPONENTS) or tag in self.SKIP_TAGS
        self.stack.append(inside)

    def handle_endtag(self, tag):
        if tag not in VOID and self.stack:
            self.stack.pop()

    def handle_data(self, data):
        if not (self.stack and self.stack[-1]):
            # CJK chars count 1 each; latin words count ~ 2 chars each
            cjk = len(re.findall(r"[\u3000-\u9fff\uff00-\uffef]", data))
            words = len(re.findall(r"[A-Za-z0-9_]+", data))
            self.chars += cjk + 2 * words


PROSE_BUDGET = 450  # method page: text outside components (≈ 450 CJK chars / 225 words)


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
        if not has("diagram", "flow", "mermaid"):
            c.warnings.append("method: no diagram (.diagram, .flow or .mermaid)")
        if not has("diagram", "mermaid"):
            c.warnings.append("method: no architecture picture (.diagram) — a chain of boxes alone rarely explains the design")
        if not has("walk", "imgflow"):
            c.warnings.append("method: no worked example (.imgflow with real outputs, or .walk)")
        if not has("why"):
            c.warnings.append("method: no .why block (key design choices and rejected alternatives)")
        if not has("idea", "analogy"):
            c.warnings.append("method: no .idea / .analogy (state the core intuition in one line)")
        pc = ProseCounter()
        pc.feed(body)
        if pc.chars > PROSE_BUDGET:
            c.warnings.append(f"method: ~{pc.chars} chars of prose outside visual components "
                              f"(budget {PROSE_BUDGET}); turn paragraphs into diagrams/cards")
    c.feed(text)
    c.close()
    for t, l in c.stack:
        if t not in {"p", "li", "td", "th", "tr"}:
            c.errors.append(f"line {l}: <{t}> never closed")

    if not c.pages:
        c.warnings.append("no <section class=\"page\"> found: old single-scroll layout; migrate to the paged template")
    ids = [pid for _, pid, _ in c.pages]
    for l, pid, nav in c.pages:
        if not pid:
            c.errors.append(f"line {l}: page section has no id")
        elif ids.count(pid) > 1:
            c.errors.append(f"line {l}: duplicate page id '{pid}'")
        if not nav:
            c.warnings.append(f"line {l}: page '{pid}' has no data-nav label")
    if c.pages and not any(pid == "align" for _, pid, _ in c.pages):
        c.warnings.append("no alignment page (#align): goal card + decisions/assumptions/deviations for the user to confirm")
    elif c.pages and not c.has_goal:
        c.warnings.append("alignment page has no .goal card")
    seen_ids: set[str] = set()
    for cl in c.claims:
        where = f"claim at line {cl['line']}"
        cid = cl.get("data-id")
        if not cid:
            c.errors.append(f"{where}: missing data-id (feedback is keyed on it)")
        elif cid in seen_ids:
            c.errors.append(f"{where}: duplicate data-id '{cid}'")
        else:
            seen_ids.add(cid)
        if cl.get("data-kind") not in CLAIM_KINDS:
            c.errors.append(f"{where}: data-kind must be one of {sorted(CLAIM_KINDS)}")
        if cl.get("data-evidence") not in EVIDENCE:
            c.warnings.append(f"{where}: data-evidence should be one of {sorted(EVIDENCE)}")
        if not cl.get("data-since"):
            c.warnings.append(f"{where}: no data-since commit (needed to spot stale claims)")
    pending = [cl for cl in c.claims if cl.get("data-user") != "confirmed"]
    guesses = [cl for cl in pending if cl.get("data-evidence") == "guess"]
    if len(pending) > 15:
        c.warnings.append(f"{len(pending)} unconfirmed claims; keep ≤15 so the user can actually review them")
    if pending and len(guesses) / len(pending) > 0.5:
        c.warnings.append(f"{len(guesses)}/{len(pending)} open claims are guesses; verify some before asking the user")
    base = os.path.dirname(os.path.abspath(path))
    for l, src in c.images:
        if re.match(r"^(https?:|data:|//)", src):
            continue
        if not os.path.exists(os.path.join(base, src.split("#")[0].split("?")[0])):
            c.errors.append(f"line {l}: image not found: {src}")

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
    print(f"{'FAIL' if c.errors else 'OK'}: {len(c.pages)} pages, {len(c.entries)} entries, "
          f"{c.charts} charts, {c.diagrams} diagrams, {len(c.claims)} claims, "
          f"{len(c.errors)} errors, {len(c.warnings)} warnings")
    return 1 if c.errors else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
