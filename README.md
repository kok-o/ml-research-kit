# ML Research Kit

Two independent agent skills for questions that need evidence. Each can be installed on its own.

| Skill | Use it when |
| --- | --- |
| [research](skills/research/SKILL.md) | You need a sourced explanation, a comparison under specific constraints, or a way to resolve conflicting accounts. |
| [ml-research](skills/ml-research/SKILL.md) | You need to review an ML paper, design an experiment, or interpret measurements of model quality, speed, or memory. |

When sources disagree, `research` checks whether they describe the same conditions. Its final **Decision Flip Trigger** names the fact or changed requirement that would reverse the conclusion. If that fact requires training a model, the question, baseline, and metric can carry over to `ml-research`.

## Install

From your project directory, run the command for the skill you want. Select your agent when prompted. Add `-g` for a user-wide install. [Skills CLI](https://github.com/vercel-labs/skills#install-a-skill)

```sh
npx skills add kok-o/ml-research-kit --skill research
npx skills add kok-o/ml-research-kit --skill ml-research
```

For manual installation, copy or link the chosen folder from [skills/](skills/) into the skills directory your agent reads. Keep its contents together. Both folders follow the [Agent Skills specification](https://agentskills.io/specification).

## Example questions

| Ask your agent | What to expect |
| --- | --- |
| “Can we publish a checksum for a GitHub source archive and rely on it six months later?” | Use `research` to check the documented guarantee, test a real archive, and recommend a distribution method. [Worked example](examples/research/github-archive-checksums.md) |
| “This paper reports a 2× speedup. Would it apply to our workload?” | Trace the claim to the original experiment, identify the baseline and hardware, and name the cheapest check for the biggest difference. |
| “How should we compare two optimizers by time to target loss?” | Define the target, timing window, and decision thresholds before training. Test the scorer on two identical curves that reach the target early and then rebound. Both should show zero time saved. |
| “Here are the raw runs. Is the change worth shipping?” | Check the scoring code against the measurements, report how much the result varies across runs, and say what decision the evidence supports. |

## Optional tools

The general research skill works with the evidence your agent can access, including local files. The ML skill also bundles a **PR radar** for shared GitHub repositories. It checks which open pull requests touch your target files and which paths conflict with `origin/main`. It uses Python 3.10+, Git with `merge-tree --write-tree` support, and an authenticated GitHub CLI. Run it from this checkout:

```sh
python skills/ml-research/scripts/team_radar.py --repo /path/to/worktree --paths src/train.py --fetch
```

For Antigravity users who want both skills and the bundled ML engineering rules, run `agy plugin install .` from this checkout.

## Test

```sh
python -m unittest discover -s tests -v
```
