# ML Research Kit

**`ml-research`** is a standalone agent skill for reviewing machine learning papers, designing experiments, and interpreting benchmark results. Use it when a decision depends on a measurement, such as whether an optimizer reaches the same validation loss in less training time.

## Install

From your project directory, run the following command and select your agent when prompted. Add `-g` for a user-wide install. [Skills CLI](https://github.com/vercel-labs/skills#install-a-skill)

```sh
npx skills add kok-o/ml-research-kit --skill ml-research
```

For manual installation, copy or link the entire [ml-research directory](skills/ml-research/) into the skills directory your agent reads. Keep `SKILL.md`, `references/`, and `scripts/` together. The folder follows the [Agent Skills specification](https://agentskills.io/specification).

## What it does

| Ask your agent | What to expect |
| --- | --- |
| “This paper reports a 2× speedup. Would it apply to our workload?” | Trace the claim to the original experiment, identify the baseline and hardware, and name the cheapest check for the biggest difference. |
| “How should we compare two optimizers by time to target loss?” | Define the target, timing window, and decision thresholds before training. Test the scorer on two identical curves that reach the target early and then rebound. Both should show zero time saved. |
| “Here are the raw runs. Is the change worth shipping?” | Check the scoring code against the measurements, report how much the result varies across runs, and say what decision the evidence supports. |

## Optional tools

The paper-review and experiment-planning workflows can run from the skill text alone. For work in a shared GitHub repository, the bundled **PR radar** checks which open pull requests touch your target files and which paths conflict with `origin/main`. It uses Python 3.10+, Git with `merge-tree --write-tree` support, and an authenticated GitHub CLI. Run it from this checkout:

```sh
python skills/ml-research/scripts/team_radar.py --repo /path/to/worktree --paths src/train.py --fetch
```

For Antigravity users who also want the bundled repository rules, run `agy plugin install .` from this checkout. The skill itself lives entirely in [skills/ml-research](skills/ml-research/).

## Test

```sh
python -m unittest discover -s tests -v
```
