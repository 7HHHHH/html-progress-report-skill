---
name: html-progress-report
description: >-
  Maintain ONE living, single-file HTML progress page per project so the user can
  quickly catch up on what a coding agent did, why, and what's next — with
  plain-language explanations and rich visuals (KPI cards, task board, charts,
  flow diagrams, before/after, diffs, timeline). Use when the user asks to
  report / summarize / show progress or methods ("汇报", "进展", "总结一下做了什么",
  "update the progress page", "status report", "what changed"), or after
  finishing a meaningful milestone in a project that already has a progress page
  (.agent-progress/index.html). Do not use for one-off answers that need no record.
---

# HTML Progress Report

You keep a **single living HTML page** per project that lets the user catch up on
a coding agent's work in under a minute. It is not a new report each time: you
**update the snapshot** and **prepend one timeline entry**.

The reader is the user themself: technical, short on time, possibly coming back
after hours away. Optimize for *fast re-orientation*, not formality.

## Page anatomy

```
┌ header      status badge · last updated · branch@commit        (rewrite)
├ 📍 Now      TL;DR · KPIs · task board · ⚠ needs your decision   (rewrite)
├ 🧭 Method   analogy · diagram · worked example · why-this-design (edit only when the approach changes)
└ 🕒 Timeline newest first; one entry per milestone               (prepend, never delete)
```

Each region is fenced by HTML comment markers. **Only edit inside markers.**

| Region | Markers | Update rule |
|---|---|---|
| Header | `<!-- @header:start -->` … `<!-- @header:end -->` | Every update |
| Now | `<!-- @snapshot:start -->` … `<!-- @snapshot:end -->` | Every update (replace whole block) |
| Method | `<!-- @method:start -->` … `<!-- @method:end -->` | Only when the approach/architecture changed |
| Timeline | insert right after `<!-- @timeline:insert -->` | Prepend one `<article class="entry">` |
| Archive | `<!-- @archive:start -->` … `<!-- @archive:end -->` | Links to archived pages |

## Workflow

### 1. Locate or create the page
- Root = `git rev-parse --show-toplevel` (fallback: current working directory).
- Page = `<root>/.agent-progress/index.html` (unless the user or project rules name another path).
- If missing: copy `assets/template.html` (path relative to this SKILL.md) there,
  fill the `{{...}}` placeholders, set `<html lang>` to the output language, and
  add `.agent-progress/` to `<root>/.git/info/exclude` (local-only ignore, does not touch
  the repo) unless the user wants it committed.
- If it exists: read the header, the Now block and the **top 2 timeline entries** only
  (not the whole history) to learn the last recorded state and `data-commit`.

### 2. Gather facts (never invent)
- `git log --oneline <last data-commit>..HEAD`, `git diff --stat <last>..HEAD`, current branch/commit.
- Test/lint/build results you actually ran; metric files (csv/json/logs) the work produced.
- What was tried and failed, and decisions made in the conversation.
- Every number on the page must come from a command output or file. If unverified, label it
  `<span class="badge warn">unverified</span>`.

### 3. Decide what to write
- **New entry vs. update:** if the top entry covers the same task in the same session,
  update it in place instead of adding a near-duplicate.
- One entry = one milestone (feature landed, bug fixed, experiment finished, direction changed),
  not one tool call.
- Rewrite **Now** to reflect the present state — it must make sense without reading the timeline.
- Touch **Method** only if the design changed; then mention it in the entry ("method updated").
- When you write or rewrite **Method**, it must be *vivid*: follow the 6-step recipe in
  `references/writing-guide.md` §2b: one-sentence problem+idea → everyday **analogy** (`.analogy`) →
  **diagram** (`.flow`/`.mermaid`) → **walkthrough of one real example with real values** (`ol.walk`) →
  **why this design** with rejected alternatives (`.why`) → limits. The validator warns if any are missing.

### 4. Write it (directly in HTML, using components)
- Follow `references/writing-guide.md` for language and structure (conclusion first,
  what → why → result → next, define jargon, analogies, honest failures).
- Pick visuals from `references/components.md`. **Every entry gets at least one visual**
  (flow, chart, compare, board, diff, table, tree). Prefer pictures over paragraphs.
- Use the file-edit tool on marker regions; never regenerate the whole file once it exists.
- Output language = **the language the user is currently using in the conversation**.
  Keep code identifiers, paths, commands and metric names as-is.

### 5. Validate
Run `python3 <skill_dir>/scripts/check_page.py <page>` and fix all errors (markers, JSON in
charts, entry attributes, tag balance). It needs only the Python standard library.

### 5b. Keep it small
If the timeline has more than ~30 entries, move the oldest ones to
`.agent-progress/archive-YYYY-MM.html` (copy the template, put them in its timeline) and add a
link inside the archive markers.

### 6. Hand back
Reply in chat with a clickable link to the page plus ≤3 lines: what changed and any
decision the user must make. Don't repeat the page content.

## Timeline entry contract

```html
<article class="entry" data-time="2026-11-20T21:30:00+08:00" data-tags="feature" data-status="ok" data-commit="a1b2c3d">
  <div class="panel">
    <header>
      <h3>Short outcome-first title</h3>
      <span class="badge ok">done</span>
      <span class="when">11-20 21:30</span>
    </header>
    <p><b>What:</b> … <b>Why:</b> … <b>Result:</b> …</p>
    <!-- ≥1 visual component -->
    <details><summary>Details</summary> commands, files, caveats </details>
    <div class="facts"><span>commit <code>a1b2c3d</code></span><span>+120 −34 in 5 files</span><span>tests 48/48 ✅</span></div>
  </div>
</article>
```

- `data-time`: ISO 8601 with timezone (drives the "NEW since last visit" highlight).
- `data-tags`: space-separated from `feature fix experiment research refactor docs infra decision blocked`.
- `data-status`: `ok | warn | bad | info`.
- `data-commit`: HEAD short hash at time of writing (next update diffs from it).

## Don'ts
- Don't create a new page per report; don't delete history.
- Don't paste raw logs or long code; summarize and put essentials in `<details>`.
- Don't add external dependencies beyond the optional Mermaid CDN already wired in the template;
  the built-in CSS components and `.chart` renderer work offline.
- Don't claim success without evidence; show failures and dead ends — they are the most useful part.
