# Component catalog

All components are pure HTML + the CSS/JS already inside `assets/template.html`.
No dependencies; everything works offline (except optional Mermaid).

## Which visual for what?

| You want to show… | Use |
|---|---|
| Headline numbers and their change | **KPI cards** |
| How far along a plan / sub-tasks are | **Progress bars**, **donut** |
| What's done / in progress / next | **Task board** |
| How a method or pipeline works | **Flow** (offline) or **Mermaid** |
| Old vs. new behaviour / design | **Compare** |
| Metric over time / steps / epochs | **Line chart** |
| Comparing variants, ablations | **Bar chart** / **hbar** / **sortable table** |
| Where time/cost goes | **hbar** or **donut** |
| Which files changed | **File tree** |
| The key code change | **Diff** (≤20 lines) |
| A decision / risk / win / side note | **Callouts** |
| Long details (commands, logs, configs) | `<details>` |

---

## Status badges
```html
<span class="badge ok"><span class="dot"></span>On track</span>
<span class="badge warn">At risk</span>
<span class="badge bad">Blocked</span>
<span class="badge info">Exploring</span>
<span class="badge neutral">paused</span>
```

## KPI cards
```html
<div class="kpis">
  <div class="kpi"><div class="label">Tests passing</div><div class="value">48/48</div><div class="delta up">▲ +6 since last</div></div>
  <div class="kpi"><div class="label">Val AUROC</div><div class="value">0.947</div><div class="delta up">▲ +3.5 pt</div></div>
  <div class="kpi"><div class="label">Epoch time</div><div class="value">41 s</div><div class="delta up">▼ 2.3× faster</div></div>
  <div class="kpi"><div class="label">Open issues</div><div class="value">2</div><div class="delta flat">— unchanged</div></div>
</div>
```
`delta up` = good (green), `down` = bad (red), regardless of arrow direction.

## Progress bars
```html
<div class="progress-row"><span>Data pipeline</span><div class="progress"><span class="ok" style="width:100%"></span></div><span class="small muted">100%</span></div>
<div class="progress-row"><span>Model</span><div class="progress"><span style="width:60%"></span></div><span class="small muted">60%</span></div>
<div class="progress-row"><span>Eval</span><div class="progress"><span class="warn" style="width:20%"></span></div><span class="small muted">20%</span></div>
```

## Task board
```html
<div class="board">
  <div class="col"><h4>✅ Done</h4><div class="card">Loader rewrite<span class="small muted">a1b2c3d</span></div></div>
  <div class="col"><h4>🔄 Doing</h4><div class="card">Ablation on prompt length<span class="small muted">3/5 runs</span></div></div>
  <div class="col"><h4>⏭ Next</h4><div class="card">Write README</div></div>
</div>
```

## Callouts
```html
<div class="callout decision"><strong>🤔 Needs your decision</strong>
  Use backbone A or B?
  <ol><li><b>A</b> — faster, −1 pt accuracy</li><li><b>B</b> — +1 pt, 2× memory</li></ol>
  Recommendation: <b>A</b> (fits GPU budget). Default if no reply: A.</div>
<div class="callout risk"><strong>⚠ Risk</strong> Eval set may overlap with train (checking).</div>
<div class="callout win"><strong>🎉 Win</strong> CI is green for the first time this week.</div>
<div class="callout note"><strong>ℹ Note</strong> Numbers below use seed 0 only.</div>
```

## Flow diagram (offline, CSS only)
```html
<div class="flow">
  <div class="step"><b>1. Load</b><span class="small muted">images → tensors</span></div>
  <div class="step hl new"><b>2. Cache features</b><span class="small muted">computed once, reused</span></div>
  <div class="step"><b>3. Score</b><span class="small muted">distance to prompts</span></div>
  <div class="step"><b>4. Report</b><span class="small muted">AUROC / PRO</span></div>
</div>
```
`hl` highlights a step, `new` adds a NEW tag (use for what changed).

## Mermaid (richer diagrams; needs network, shows source text offline)
```html
<pre class="mermaid">
flowchart LR
  A[Input] --> B{Cached?}
  B -- yes --> C[Load cache]
  B -- no --> D[Compute] --> C
</pre>
```

## Compare (before / after)
```html
<div class="compare">
  <div><h4>Before</h4><p>Features recomputed every epoch (≈95 s).</p></div>
  <div><h4>After</h4><p>Computed once and memory-mapped (≈41 s).</p></div>
</div>
```

## Charts (built-in SVG renderer)
Attributes: `data-type` = `line | bar | hbar | donut`; `data-labels` = JSON array;
`data-series` = JSON array of `{"name","values",["color"],["dashed"]}`;
optional `data-title`, `data-unit`, `data-min`, `data-max`, `data-height`, `data-target` (line only),
`data-center` / `data-center-label` (donut). Use single quotes around JSON attributes.

```html
<div class="chart" data-type="line" data-title="Val AUROC per epoch" data-target="0.95"
  data-labels='["1","2","3","4","5"]'
  data-series='[{"name":"baseline","values":[0.88,0.90,0.91,0.91,0.912],"dashed":true},{"name":"ours","values":[0.89,0.92,0.94,0.945,0.947]}]'></div>

<div class="chart" data-type="bar" data-title="Ablation"
  data-labels='["full","−cache","−prompt ens."]'
  data-series='[{"name":"AUROC","values":[94.7,94.6,92.1]}]' data-unit="%"></div>

<div class="chart" data-type="hbar" data-title="Where epoch time goes (s)"
  data-labels='["data loading","forward","backward","logging"]'
  data-series='[{"values":[12,15,11,3]}]' data-unit=" s"></div>

<div class="chart" data-type="donut" data-center="7/10" data-center-label="tasks done"
  data-labels='["done","doing","todo"]' data-series='[{"values":[7,2,1]}]'></div>
```

## Sortable table
```html
<table class="sortable">
  <thead><tr><th>Variant</th><th class="num">AUROC</th><th class="num">Time (s)</th></tr></thead>
  <tbody>
    <tr class="best"><td>ours</td><td class="num">94.7</td><td class="num">41</td></tr>
    <tr><td>baseline</td><td class="num">91.2</td><td class="num">95</td></tr>
  </tbody>
</table>
```

## File tree
```html
<pre class="tree">
src/
├── <span class="mod">loader.py</span>        ~ memory-mapped reads
├── <span class="add">cache.py</span>         + new
└── <span class="del">old_loader.py</span>    − removed
</pre>
```

## Diff (keep ≤20 lines; escape &lt; &gt; &amp;)
```html
<pre class="diff"><code>@@ loader.py @@
-feats = model(x)
+feats = cache.get(key) or cache.put(key, model(x))
</code></pre>
```

## Details (collapse everything non-essential)
```html
<details><summary>Commands & files</summary>
<pre><code>python train.py --cfg cfg/a.yaml</code></pre>
</details>
```
