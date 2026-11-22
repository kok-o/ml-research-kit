#!/usr/bin/env python3
"""Team radar: inspect local git state, merge-tree conflicts, and open PR overlaps."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def _run(cmd: list[str], cwd: Path, *, strip_leading: bool = True) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        out = proc.stdout.strip() if strip_leading else proc.stdout.rstrip("\r\n")
        return proc.returncode, out, proc.stderr.strip()
    except FileNotFoundError:
        return 127, "", f"command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, "", f"timeout running: {' '.join(cmd)}"


def _normalize(path: str) -> str:
    return path.replace("\\", "/").removeprefix("./")


def _parse_paths(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [_normalize(p.strip()) for p in raw.split(",") if p.strip()]


def _matches(pr_files: list[str], targets: list[str]) -> list[str]:
    if not targets:
        return []
    hits: list[str] = []
    for pf in pr_files:
        norm = _normalize(pf)
        for t in targets:
            if norm == t or norm.endswith("/" + t) or t in norm:
                hits.append(norm)
                break
    return hits


_OPEN_PRS = """
query($owner: String!, $name: String!, $size: Int!, $after: String) {
  repository(owner: $owner, name: $name) {
    pullRequests(states: OPEN, first: $size, after: $after,
                 orderBy: {field: CREATED_AT, direction: DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number title author { login } headRefName baseRefName updatedAt changedFiles
        files(first: 100) { nodes { path changeType } pageInfo { hasNextPage } }
      }
    }
  }
}
"""


def _list_open_prs(repo: Path, limit: int | None) -> tuple[list[dict[str, Any]], str]:
    prs: list[dict[str, Any]] = []
    cursors: set[str] = set()
    after: str | None = None
    while True:
        size = min(25, limit - len(prs)) if limit is not None else 25
        cmd = [
            "gh",
            "api",
            "graphql",
            "-f",
            f"query={_OPEN_PRS}",
            "-F",
            "owner={owner}",
            "-F",
            "name={repo}",
            "-F",
            f"size={size}",
        ]
        if after:
            cmd.extend(["-f", f"after={after}"])
        rc, out, err = _run(cmd, repo)
        if rc:
            return prs, f"GitHub PR listing failed: {err}"
        try:
            response = json.loads(out)
            if response.get("errors"):
                return prs, f"GitHub PR listing failed: {response['errors']}"
            page = response["data"]["repository"]["pullRequests"]
            prs.extend(page["nodes"])
            if not page["pageInfo"]["hasNextPage"]:
                return prs, ""
            if limit is not None and len(prs) >= limit:
                return prs, f"--limit {limit} reached; more open PRs exist."
            after = page["pageInfo"]["endCursor"]
            if not after or after in cursors:
                return prs, "GitHub returned a missing or repeated pagination cursor."
            cursors.add(after)
        except (ValueError, KeyError, TypeError) as exc:
            return prs, f"Invalid GitHub PR response: {exc}"


def _pr_files(repo: Path, pr: dict[str, Any]) -> tuple[list[str], str]:
    """Keep known matches, and report when the full changed-file list is unavailable."""
    preview = pr.get("files") or {}
    entries = preview.get("nodes") or []
    paths = [entry["path"] for entry in entries]
    expected = pr.get("changedFiles")
    if (
        preview
        and not preview["pageInfo"]["hasNextPage"]
        and (expected is None or len(entries) == expected)
        and all(entry["changeType"] != "RENAMED" for entry in entries)
    ):
        return paths, ""

    number = pr["number"]
    endpoint = f"repos/{{owner}}/{{repo}}/pulls/{number}/files?per_page=100"
    rc, out, err = _run(["gh", "api", "--paginate", "--slurp", endpoint], repo)
    if rc:
        return paths, f"PR #{number} file pagination failed: {err}"
    try:
        files = [entry for page in json.loads(out) for entry in page]
        for entry in files:
            paths.append(entry["filename"])
            if entry.get("previous_filename"):
                paths.append(entry["previous_filename"])
        paths = list(dict.fromkeys(paths))
    except (ValueError, KeyError, TypeError) as exc:
        return paths, f"Invalid GitHub file list for PR #{number}: {exc}"
    if expected is not None and len(files) != expected:
        return paths, f"PR #{number}: GitHub listed {len(files)} of {expected} changed files."
    if expected is None and (len(files) >= 3000 or len(files) < len(entries)):
        return paths, f"PR #{number}: completeness of {len(files)} returned files is unknown."
    return paths, ""


def _dry_run_merge_conflicts(repo: Path, base_ref: str = "origin/main") -> list[str] | None:
    """Run read-only git merge-tree to list files that actually conflict with base_ref."""
    rc, out, _ = _run(
        [
            "git",
            "merge-tree",
            "--write-tree",
            "--name-only",
            "--no-messages",
            "-z",
            base_ref,
            "HEAD",
        ],
        repo,
    )
    if rc == 0:
        return []
    if rc == 1 and out:
        # The first NUL-terminated field is the merged tree ID.
        conflicts = out.rstrip("\0").split("\0")[1:]
        return sorted(set(conflicts)) or None
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Summarize git state, dry-run conflicts, and open GitHub PR overlaps."
    )
    parser.add_argument("--repo", default=".", help="Path to git repository or worktree.")
    parser.add_argument(
        "--paths",
        default="",
        help="Comma-separated target file paths or substrings to check for PR overlap.",
    )
    parser.add_argument("--limit", type=int, help="Max open PRs to fetch (default: all).")
    parser.add_argument(
        "--fetch",
        action="store_true",
        help="Run 'git fetch origin main' before checking divergence.",
    )
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive.")

    repo = Path(args.repo).resolve()
    if not repo.exists():
        print(f"[error] repo path does not exist: {repo}", file=sys.stderr)
        return 2

    if args.fetch:
        rc, _, err = _run(["git", "fetch", "origin", "main", "--quiet"], repo)
        if rc:
            print(f"[warn] fetch failed; using cached origin/main: {err}")

    rc_branch, branch, err_branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo)
    if rc_branch != 0:
        print(f"[error] not a git repo ({repo}): {err_branch}", file=sys.stderr)
        return 2

    _, head_sha, _ = _run(["git", "rev-parse", "--short", "HEAD"], repo)
    # Preserve leading space in porcelain v1 format (" M path").
    status_rc, status_out, status_err = _run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        repo,
        strip_leading=False,
    )
    if status_rc:
        print(f"[error] could not inspect working tree paths: {status_err}", file=sys.stderr)
        return 2
    _, div_out, _ = _run(["git", "rev-list", "--left-right", "--count", "origin/main...HEAD"], repo)
    _, main_log, _ = _run(["git", "log", "origin/main", "-n", "5", "--oneline"], repo)

    dirty_files: list[str] = []
    records = iter(status_out.rstrip("\0").split("\0"))
    for record in records:
        if record:
            dirty_files.append(_normalize(record[3:]))
            if "R" in record[:2] or "C" in record[:2]:
                dirty_files.append(_normalize(next(records)))

    targets = _parse_paths(args.paths)
    if not targets and dirty_files:
        targets = dirty_files

    print("=== LOCAL GIT STATE ===")
    print(f"repo:   {repo}")
    print(f"branch: {branch} ({head_sha})")
    if div_out:
        parts = div_out.split()
        if len(parts) == 2:
            print(f"vs origin/main: behind={parts[0]}, ahead={parts[1]}")
    dirty_preview = ", ".join(dirty_files[:8]) if dirty_files else "clean"
    print(f"dirty files ({len(dirty_files)}): {dirty_preview}")
    if targets:
        print(f"checking overlap against: {', '.join(targets)}")

    conflicts = _dry_run_merge_conflicts(repo, "origin/main")
    if conflicts is not None:
        if conflicts:
            print(f"merge-tree conflicts vs origin/main ({len(conflicts)}):")
            for path in conflicts[:15]:
                print(f"  - {path}")
        else:
            print("merge-tree vs origin/main: clean (0 conflicts)")
    else:
        print("[warn] merge-tree conflict paths could not be determined.")

    if main_log:
        print("\n=== RECENT origin/main COMMITS ===")
        print(main_log)

    print("\n=== OPEN GITHUB PRs ===")
    prs, listing_warning = _list_open_prs(repo, args.limit)
    incomplete = bool(listing_warning)
    if listing_warning:
        print(f"[warn] {listing_warning}")

    overlaps: list[tuple[int, str, str, list[str]]] = []
    for pr in prs:
        num = int(pr.get("number", 0))
        author = (pr.get("author") or {}).get("login", "?")
        head = pr.get("headRefName", "?")
        base = pr.get("baseRefName", "?")
        title = pr.get("title", "")
        updated = (pr.get("updatedAt") or "")[:10]
        pr_files, warning = _pr_files(repo, pr) if targets else ([], "")
        if warning:
            incomplete = True
            print(f"[warn] {warning}")
        hits = _matches(pr_files, targets)
        tag = " [OVERLAP]" if hits else ""
        print(f"#{num} ({author}, {updated}) {head} -> {base}: {title}{tag}")
        if hits:
            overlaps.append((num, author, head, hits))
            print(f"    overlapping files: {', '.join(hits[:8])}")

    print("\n=== OVERLAP SUMMARY ===")
    if not targets:
        print("No target paths specified and tree is clean (pass --paths to check overlaps).")
    elif not overlaps and not incomplete:
        print("No open PRs touch the target paths.")
    else:
        for num, author, head, hits in overlaps:
            print(f"- PR #{num} ({author}, {head}): {', '.join(hits)}")
    if incomplete:
        print("INCOMPLETE: PR coverage is partial; additional overlaps may exist.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
