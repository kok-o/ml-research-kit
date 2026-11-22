---
name: ml-research
description: >-
  Review machine learning papers, design or run training experiments and GPU benchmarks,
  audit learning curves and benchmark scores from raw logs or JSON, and check branch or
  pull-request overlap when integrating ML code. Use for questions about model quality,
  training speed, or memory on a specific workload.
---

# ML Research & Experiment Workflow

Use the steps relevant to the requested decision. For an existing experiment, start with its
raw measurements and scoring code. For an integration, start with the target paths and branches.
For a paper review, find the experiment behind the claim. Identify the comparison method,
metric, and workload, then explain which differences matter for the user's question. Use the
paper and any available implementation or data. Propose a replication only if it would change
the decision. Keep each conclusion tied to an inspected source, a measurement, or a calculation.

## Step 1: Align With the Team Before Writing Code

When changing shared code on GitHub, run the optional team radar from the directory containing
this SKILL.md. It assumes a base of `origin/main`. For another host or base, use the project's
own Git and review tools to check the same files. Pass the absolute path of the worktree to the radar.

```bash
python scripts/team_radar.py --repo "<absolute_repo_path>" --paths "<comma_separated_target_paths>" --fetch
```

Summarize the output in **5 lines max**:
- Current branch, `HEAD`, divergence vs `origin/main`, and exact `git merge-tree` conflict files.
- Open PRs touching the same files (`[OVERLAP]`, including PRs >100 files via REST pagination) and who owns them.
- Which branch/PR this work depends on, and what can be verified independently without merge conflicts.

If a colleague already closed or is actively changing the same path, flag it immediately before coding.
If the host could only list some PRs or files, state which part of the overlap check is incomplete.

## Step 2: Pre-Register the Gate Before Coding or GPU Rental

Choose the analytical tool that fits the question (do not force one template on every problem):
- **Speed / throughput:** phase profile + Roofline (bytes, FLOPs, PCIe/NVMe/HBM) + Amdahl's law $S = 1 / (1 - p + p / r)$ before writing kernels.
- **Memory / OOM:** memory budget (weights, activations, gradients, allocator fragmentation, OS page cache) + peak measurement at the target context length and batch size.
- **Quality / convergence:** unsaturated held-out metric + negative control + multiple seeds or paired bootstrap (check both `final` and `best` metric on constant-LR runs, and compare wall-time to target metric when step costs differ).

Write down the gate **before** running code or renting compute:
1. **Hypothesis** (one falsifiable statement).
2. **Baseline & negative control** (bracket baseline hyperparameters fairly; avoid unbracketed LR or flat cosine-tail crossing artifacts).
3. **Target hardware & cap** (local GPU, free Kaggle CLI T4/P100, or Vast.ai; hard time and `$` limit, explicitly accounting for eval pass overhead).
4. **Three outcomes:**
   - `PASS`: concrete numeric threshold on primary metric + guardrails (VRAM/RAM/quality/invariance).
   - `FAIL`: threshold missed or guardrail broken.
   - `INCONCLUSIVE`: measured delta sits inside run-to-run noise/variance or seeds disagree (never force a win out of noise).
5. **Explicit 3-layer labeling:** mark every statement as **(measured/code)**, **(calculated)**, or **(proxy extrapolation / hypothesis)**—especially when a smaller proxy model stands in for a larger target model.

For literature/competitor research, inspect primary sources only (arXiv papers, official repos, actual kernel source lines, GitHub Issues/PRs) and bind every cited number to hardware, model, context length, batch size, and direct URL.

For time-to-target comparisons, run the actual verdict function on identical nonmonotonic curves
on CPU. Both arms must reach the same target by the same rule and show zero savings, including
when they first reach the target before the last checkpoint. Check a known faster arm and a
partial run as well. Report the first observed checkpoint alongside any interpolated crossing,
define what the timer includes, and identify a target already reached at step zero or still
unreached at the cutoff. Issue a final verdict only when the planned seeds and guardrails are available.

## Step 3: Isolated Skeptic Review (Before GPU Runs or Large Edits / PR Splits)

Before any paid GPU rental, Kaggle run >15 min, code change >100 lines, or multi-PR split:
1. Read [references/skeptic_prompt.md](./references/skeptic_prompt.md) (Mode A for experiments, Mode B for PR splits/integration).
2. When delegation is available and allowed, give a fresh agent only the filled prompt and the relevant evidence. If working alone, apply the same questions yourself and identify the review as a self-check.
3. Require the skeptic to return:
   - The **#1 false-positive / false-green risk**.
   - Hidden assumptions (CUDA/PTX/Triton mismatches, silent fallbacks like `O_DIRECT -> buffered`, `loraplus_weight_decay` overrides, skipped CI tests, OS portability, dataset saturation/truncation).
   - The **cheapest pre-check** to catch it before the main run.
4. Fix the plan or add the pre-check before proceeding.

## Step 4: Execute in an Isolated Branch and Ship a Factual Report

### Git & Branch Hygiene
- **Never commit directly to `main`.** Create a dedicated branch per feature or experiment (`feat/<slug>` or `exp/<slug>`).
- Use `git worktree` **only** when working on two or more independent tasks in parallel.
- Before committing: run the project's own linter and targeted tests (`ruff check`, `pytest`), verify `$LASTEXITCODE -eq 0` on Windows PowerShell before chaining `git commit`, and verify zero secrets/tokens in `git diff`.

### Harness & Compute Hygiene
- Commit the harness **before** launching remote compute so the exact `git_sha` is real (never `unknown`).
- Record in every raw JSON output: exact `git_sha`, `torch`/`transformers`/`triton`/CUDA versions, full run config, wall-clock phase timings (train vs eval separated), peak memory (20 ms NVML via `nvidia-ml-py` + RSS poller, cgroup `memory.peak` when applicable), and actual runtime flags (`direct=True/False`, `grad_scaler_skipped_steps`, allocator config).
- **Vast.ai:** record the instance IDs provisioned for this run. After downloading the raw outputs,
  destroy those instances and verify each recorded ID was released. Use the owner's instructions
  for borrowed or shared instances.
- **Kaggle CLI:** run a 1-arm timing smoke (including eval cost) before pushing >8 arms in one kernel; embed the committed harness via `base64` (never triple-quoted raw strings); compile-check the wrapper with `py_compile` before `kaggle kernels push`; install `nvidia-ml-py` instead of deprecated `pynvml`; download output JSON/logs locally and record the exact GPU SKU and kernel version.

### Report & Decision
- Read [references/report_template.md](./references/report_template.md) before writing any team report.
- **Zero-memory-quoting rule:** read the raw JSON/log file immediately before putting any metric, error message, or file path into a report.
- For a benchmark, report its limitations, the verdict under the agreed thresholds, and the next decision.
  For a paper review, state which claims the evidence supports and what remains uncertain.
