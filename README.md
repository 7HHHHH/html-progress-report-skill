# html-progress-report

An agent skill that makes a coding agent keep **one living HTML page per project**,
so you can catch up on what it did in under a minute.

- **One page, not a pile of reports**: the agent rewrites a "Now" snapshot and adds a timeline entry for each milestone.
- **Plain language**: puts the conclusion first, defines jargon, uses analogies, and records failures honestly.
- **Visual-first**: KPI cards, progress bars, task board, flow diagrams, before/after, line/bar/hbar/donut charts, sortable tables, diffs, file trees. These need no dependencies and work offline.
- **Catch-up friendly**: entries added since your last visit get a **NEW** tag. You can filter by tag and search the timeline. Dark mode is supported.
- **Writes in your language**: the page uses whatever language you are talking to the agent in.
- **Agent-safe editing**: comment markers fence each region, and a stdlib-only validator (`scripts/check_page.py`) checks the page.

See [`examples/demo.html`](examples/demo.html) for a sample.

![demo](examples/screenshot.png)

## Install

Copy or symlink this folder into your agent's skills directory, for example:

```bash
git clone <this-repo> ~/.agents/skills/html-progress-report
# Antigravity / Gemini CLI
ln -s ~/.agents/skills/html-progress-report ~/.gemini/config/skills/html-progress-report
# Claude Code
ln -s ~/.agents/skills/html-progress-report ~/.claude/skills/html-progress-report
```

## Use

Ask the agent to report progress, for example "update the progress page" or "汇报一下进展".
Once a project has a page, the agent also updates it after meaningful milestones.
The page lives at `<repo>/.agent-progress/index.html` and is kept out of git through `.git/info/exclude`.

## Layout

```
SKILL.md                      instructions for the agent
assets/template.html          the page skeleton (CSS + tiny JS renderer, single file)
references/components.md      component catalog + "which visual for what"
references/writing-guide.md   how to write plain, scannable updates
scripts/check_page.py         validator (Python stdlib)
examples/demo.html            filled example
```

## License

MIT
