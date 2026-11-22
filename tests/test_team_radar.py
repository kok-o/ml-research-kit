"""Local Git and deterministic GitHub API controls for team radar."""

import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = (
    Path(__file__).resolve().parents[1] / "skills/ml-research/scripts/team_radar.py"
)
spec = importlib.util.spec_from_file_location("installed_radar", SCRIPT)
radar = importlib.util.module_from_spec(spec)
spec.loader.exec_module(radar)


def pr(number, paths=None, count=None, more=False):
    paths = [f"docs/path-{number}.md"] if paths is None else paths
    return {
        "number": number,
        "title": "Control",
        "author": {"login": "research"},
        "headRefName": "feature",
        "baseRefName": "main",
        "updatedAt": "2026-11-22T00:00:00Z",
        "changedFiles": len(paths) if count is None else count,
        "files": {
            "nodes": [{"path": path, "changeType": "MODIFIED"} for path in paths],
            "pageInfo": {"hasNextPage": more},
        },
    }


def page(prs, more=False, cursor=None):
    return (
        0,
        json.dumps(
            {
                "data": {
                    "repository": {
                        "pullRequests": {
                            "nodes": prs,
                            "pageInfo": {"hasNextPage": more, "endCursor": cursor},
                        }
                    }
                }
            }
        ),
        "",
    )


class RadarControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git("init", "-qb", "main")
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        self.file = self.repo / ".work in progress.txt"
        self.file.write_text("base", encoding="utf8")
        self.git("add", ".")
        self.git("commit", "-qm", "base")
        self.git("branch", "origin/main")
        self.git("checkout", "-qb", "topic")

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.repo, capture_output=True, check=True)

    def invoke(self, gh_responses, *args, targets="src/target.py"):
        real_run = radar._run
        calls = []
        returns = iter(gh_responses)

        def run(cmd, cwd, **kwargs):
            if cmd[0] == "gh":
                calls.append(cmd)
                return next(returns)
            return real_run(cmd, cwd, **kwargs)

        output = io.StringIO()
        argv = [str(SCRIPT), "--repo", str(self.repo), "--paths", targets, *args]
        with patch.object(sys, "argv", argv), patch.object(radar, "_run", run):
            with contextlib.redirect_stdout(output):
                result = radar.main()
        self.assertEqual(result, 0)
        self.assertIsNone(next(returns, None))
        return output.getvalue(), calls

    def test_real_modify_delete_returns_actual_dotpath_and_clean_case(self):
        self.assertEqual(radar._dry_run_merge_conflicts(self.repo), [])
        self.file.unlink()
        self.git("add", "-u")
        self.git("commit", "-qm", "delete")
        self.git("checkout", "-q", "main")
        self.file.write_text("modification")
        self.git("add", ".")
        self.git("commit", "-qm", "modify")
        self.git("branch", "-f", "origin/main", "HEAD")
        self.git("checkout", "-q", "topic")
        self.assertEqual(radar._dry_run_merge_conflicts(self.repo), [self.file.name])

    def test_ordinary_clean_and_overlap(self):
        output, _ = self.invoke([page([pr(1)])])
        self.assertIn("No open PRs touch", output)
        self.assertIn("clean (0 conflicts)", output)
        output, _ = self.invoke([page([pr(1, ["src/target.py"])])])
        self.assertIn("PR #1 (research, feature): src/target.py", output)
        self.assertNotIn("INCOMPLETE", output)

    def test_older_pr_and_paginated_changed_files(self):
        paths = [f"src/module_{i}.py" for i in range(100)]
        rest = [[{"filename": path} for path in paths], [{"filename": "src/target.py"}]]
        output, calls = self.invoke(
            [
                page([pr(i) for i in range(1, 26)], True, "next"),
                page([pr(26, paths, 101, more=True)]),
                (0, json.dumps(rest), ""),
            ]
        )
        self.assertIn("PR #26 (research, feature): src/target.py", output)
        self.assertIn("after=next", calls[1])
        self.assertIn("--paginate", calls[2])
        self.assertIn("--slurp", calls[2])
        self.assertNotIn("INCOMPLETE", output)

    def test_file_pagination_failure_preserves_known_matches(self):
        output, _ = self.invoke(
            [
                page([pr(31, ["src/target.py"], 127, more=True)]),
                (1, "", "rate limit"),
            ]
        )
        self.assertIn("PR #31 (research, feature): src/target.py", output)
        self.assertIn("rate limit", output)
        self.assertIn("INCOMPLETE", output)

    def test_file_pagination_short_success_cannot_prove_no_overlap(self):
        output, _ = self.invoke(
            [
                page([pr(32, ["a.py"], 3100, more=True)]),
                (0, json.dumps([[{"filename": "a.py"}]]), ""),
            ]
        )
        self.assertIn("listed 1 of 3100", output)
        self.assertIn("INCOMPLETE", output)
        self.assertNotIn("No open PRs", output)

    def test_failed_second_open_pr_page(self):
        output, _ = self.invoke([page([pr(1)], True, "abc"), (1, "", "timeout")])
        self.assertIn("timeout", output)
        self.assertIn("INCOMPLETE", output)
        self.assertNotIn("No open PRs", output)

    def test_limit_is_explicitly_partial(self):
        output, calls = self.invoke([page([pr(1)], True, "abc")], "--limit", "1")
        self.assertIn("size=1", calls[0])
        self.assertIn("--limit 1 reached", output)
        self.assertIn("INCOMPLETE", output)
        self.assertNotIn("No open PRs", output)

    def test_old_path_of_rename(self):
        entry = pr(33, ["new/path.py"])
        entry["files"]["nodes"][0]["changeType"] = "RENAMED"
        rest = [[{"filename": "new/path.py", "previous_filename": "src/target.py"}]]
        output, _ = self.invoke([page([entry]), (0, json.dumps(rest), "")])
        self.assertIn("PR #33 (research, feature): src/target.py", output)

    def test_default_paths_include_uncommitted_rename_and_unquoted_unicode(self):
        new_name = "обновлённый файл.txt"
        (self.repo / "новый файл.py").write_text("data")
        self.git("mv", "--", self.file.name, new_name)
        output, _ = self.invoke(
            [page([pr(41, [self.file.name]), pr(42, [new_name]), pr(43, ["новый файл.py"])])],
            targets="",
        )
        for number in (41, 42, 43):
            self.assertIn(f"PR #{number} (research, feature)", output)
        self.assertNotIn("No open PRs", output)


if __name__ == "__main__":
    unittest.main(verbosity=2)
