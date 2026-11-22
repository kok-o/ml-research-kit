# ML Research Kit — Always-On Rules

Follow these rules across ML research, benchmarking, and feature work:

1. **Branch isolation:** Never commit directly to `main`. Create a dedicated branch (`feat/<slug>` or `exp/<slug>`) per feature or experiment; use `git worktree` only when working on 2+ tasks in parallel.
2. **Team awareness before coding:** Before editing shared files or starting a new track, check `origin/main`, open PR overlaps, and dry-run merge conflicts.
3. **Three evidence layers & three outcomes:** Explicitly distinguish **(measured/code)**, **(calculated)**, and **(proxy extrapolation / hypothesis)**. When an experiment's effect sits inside noise or disagrees across seeds, report **`INCONCLUSIVE`** instead of forcing a `PASS`.
4. **Zero-memory-quoting & anti-fluff reporting:** Read raw JSON/log outputs immediately before quoting any metric, traceback, or path. Write dry, factual reports without marketing filler, and always include an honest Limitations/Caveats section.
5. **Compute & commit hygiene.** Commit the experiment harness before launching remote GPU runs and record its SHA. On PowerShell, check `$LASTEXITCODE` before chaining `git commit`. Run the project's linter and targeted tests and check the diff for secrets. After collecting outputs, release and verify the specific Vast.ai instance IDs provisioned by this run.
