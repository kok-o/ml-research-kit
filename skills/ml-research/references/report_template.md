# Technical Report Template & Anti-Fluff Checklist

Use this structure for team-facing experiment and research reports.

## Anti-Fluff Rules (Strict)
1. **Verify every number directly from raw JSON/logs before writing it.** Never quote metrics,
   tracebacks, file paths, or line numbers from conversational memory.
2. **No marketing or AI filler words:** ban words like "breakthrough", "game-changer", "roadmap",
   "consensus", "explodes RAM", "confidently fits", "stably trains", "massive leap", and
   exclamation marks inside tables.
3. **Label evidence type explicitly:** distinguish `(measured)`, `(calculated)`, and
   `(extrapolated from proxy)`.
4. **Never hide failures or harness bugs.** If one arm failed due to a script typo, unsupported
   flag, or missing package (`causal_conv1d`, `xformers`, `offload_layers="auto"`), report it
   plainly in the Limitations section.

---

## Standard Report Skeleton

```markdown
# <Topic> — <Short Factual Subtitle> (<Hardware>: <Models>)

**Date:** <YYYY-MM-DD>

**Branch / PR:** `<branch>` (`<short_git_sha>`)

**Environment:** <exact GPU SKU & MiB, RAM, storage FS, OS, Python, PyTorch, Transformers, Triton, CUDA/ptxas>

---

## Summary (30 seconds)

3–5 tight bullets with exact numbers, verdict (`PASS` / `FAIL` / `INCONCLUSIVE`), and the
decision it unlocks.

---

## 1. Setup & Pre-Registered Gate

- Hypothesis, baseline, negative control, and `PASS / FAIL / INCONCLUSIVE` thresholds.
- Exact command / harness path and dataset split details.

---

## 2. Measured Results

Compact Markdown table(s) with direct links/paths to the raw JSON files.
Include wall-time, throughput, peak memory (`alloc / resv / nvml_peak`, `RSS` or cgroup
`memory.peak`), and numerical/quality checks (`bit_equal`, `grad_rel_l2`, `min_cos`, held-out NLL).

---

## 3. Honest Limitations, Bugs, and Caveats

- Differences between the test and target environments that could affect the decision, including
  memory limits, storage behavior and model size.
- Any skipped arms, harness fixes made mid-run, dataset constraints, or noise floor issues.

---

## 4. Verification & Artifacts

- Linter & test results (`ruff check`, `pytest`).
- Exact paths to harnesses, raw JSON/logs, and commit SHAs.
- Compute receipt (e.g., release status of this run's Vast instance IDs or the Kaggle kernel version).
```
