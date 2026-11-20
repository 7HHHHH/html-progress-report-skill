# Writing guide: clear, plain, fast to scan

The reader wants to answer three questions in under a minute:
**Where are we? What changed since I last looked? Do I need to do anything?**

## 1. Structure: conclusion first

Every block follows **What → Why → Result → Next**.

| Bad | Good |
|---|---|
| "I explored the codebase, then looked at the loader, then tried several things…" | "Training is 2.3× faster: the data loader was the bottleneck; I switched to memory-mapped files." |

- Titles are outcomes, not activities: "Login works with SSO" not "Worked on auth".
- First sentence of the TL;DR answers "are we on track?".
- One idea per paragraph, ≤3 sentences. Use lists for anything enumerable.

## 2. Plain language

- **Define jargon on first use**, inline: "AUROC (how well scores separate normal vs. defective; 1.0 = perfect)".
- **Use an analogy for any non-trivial mechanism**, in one sentence:
  "The cache works like a bookmark: instead of re-reading the whole book, we jump to the last page we read."
- Prefer concrete over abstract: "3 of 48 tests fail, all in `parser/`" beats "some tests are failing".
- Numbers always come with a comparison: `0.912 → 0.947 (+3.5 pt)`, not just `0.947`.
- Say *why it matters*: "…so the nightly job now finishes before 8 am."

## 2b. The Method section: vivid, concrete, visual

The Method block is where the reader builds a mental model. A good one lets them
explain the approach to a colleague afterwards. A list of module names doesn't do that.
**Test:** could a smart engineer from a *different* field retell it after one read?

Follow this recipe in order. Each step maps to a component:

| # | Step | Component | Rule of thumb |
|---|---|---|---|
| 1 | **Problem + idea in one sentence** | `p.tldr` | "X is slow/wrong because Y; we fix it by Z." No jargon. |
| 2 | **Everyday analogy** | `.analogy` | A familiar scene (kitchen, library, post office, traffic…) that maps to the mechanism. Then say **where the analogy breaks**, one clause. |
| 3 | **Picture of the pipeline** | `.flow` or `.mermaid` | 3–6 boxes, each with a short label and a muted one-line role. Mark changed parts `hl new`. |
| 4 | **Walk one real example through it** | `ol.walk` | Follow one concrete input step by step with *real values* from the project (a file name, a tensor shape, a score). This is what makes it click. |
| 5 | **Why this design** | `.why` | 2–4 cards: the choice, the reason, and the alternative that was rejected and why. |
| 6 | **Limits** | `callout note` / `risk` | When it fails or what it assumes. Keep it honest and short. |

Vividness rules:
- **Concrete beats abstract.** Say "a 1024×1024 photo of a scratched screw", not "an input sample".
- **Verbs over nouns.** Say "the cache *remembers* features", not "feature memoization is applied".
- **One analogy, used consistently.** Don't switch metaphors halfway through.
- **Name the "aha".** One bold sentence for the key insight: "**The trick:** we only pay the expensive step once."
- **Show the numbers flowing.** Put intermediate values in `<code>` inside the walkthrough, e.g. `[1, 768]` → `0.83`.
- **Avoid:** a wall of module names, unexplained acronyms, copying the code structure as the explanation, marketing words ("powerful", "robust", "novel").

## 3. Honest status

- Use status colours consistently: ok = done/working, warn = partial/risky/unverified, bad = failed/blocked, info = neutral.
- Failures and dead ends get entries too (`data-tags="experiment" data-status="bad"`): what was tried, why it failed, what we learned.
- Separate **facts** (measured) from **guesses** (hypotheses). Mark guesses: "Hypothesis: …".
- Anything unverified gets `<span class="badge warn">unverified</span>`.

## 4. "Needs your decision" is sacred

If the user must decide something, put it in the Now block as a `callout decision`, with:
1. The question in one line.
2. 2–3 options, each with a one-line trade-off.
3. Your recommendation and why.
4. What you'll do by default if no answer.

Remove it once decided (record the decision as a `decision`-tagged timeline entry).

## 5. Visual-first

Rule of thumb: if you wrote more than ~5 lines of prose, a visual is probably missing.
See `components.md` for the "what to show → which component" table.

## 6. Language

- Write in the language the user is currently using in the conversation. If they switch, write new content in the new language (don't translate old entries).
- Keep code, file paths, commands, metric/API names untranslated.
- Dates: `MM-DD HH:mm` for display, full ISO in `data-time`.
