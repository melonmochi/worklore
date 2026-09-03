from __future__ import annotations

import re
import subprocess

from . import WorkloreError

GIT_OBJECT_ID = re.compile(r"^[0-9a-f]+$")


def _git_output(*arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise WorkloreError(detail)
    return result.stdout.strip()


def push_reviewed(expected_head: str) -> None:
    if _git_output("rev-parse", "--is-inside-work-tree") != "true":
        raise WorkloreError("current directory is not a Git working tree")

    branch = _git_output("symbolic-ref", "--quiet", "--short", "HEAD")
    head = _git_output("rev-parse", "--verify", "HEAD")
    if not GIT_OBJECT_ID.fullmatch(expected_head) or expected_head != head:
        raise WorkloreError(
            f"expected HEAD {expected_head!r} does not equal current HEAD {head}"
        )
    if _git_output("status", "--porcelain=v1", "--untracked-files=all"):
        raise WorkloreError("working tree must be clean before push")

    remote = _git_output("config", "--get", f"branch.{branch}.remote")
    merge_ref = _git_output("config", "--get", f"branch.{branch}.merge")
    if remote == "." or not merge_ref.startswith("refs/heads/"):
        raise WorkloreError("current branch must track a remote branch")
    upstream = _git_output(
        "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"
    )
    upstream_head = _git_output("rev-parse", "--verify", "@{upstream}")
    counts = _git_output(
        "rev-list", "--left-right", "--count", "@{upstream}...HEAD"
    ).split()
    if counts != ["0", "1"]:
        raise WorkloreError(
            "current branch must be exactly one commit ahead of its upstream "
            f"(found behind={counts[0] if counts else '?'}, "
            f"ahead={counts[1] if len(counts) > 1 else '?'})"
        )

    print(
        f"publishing {head} from {branch} to {upstream} "
        f"(previously {upstream_head})"
    )
    result = subprocess.run(
        ["git", "push", remote, f"HEAD:{merge_ref}"],
        check=False,
    )
    if result.returncode != 0:
        raise WorkloreError(f"git push failed with exit code {result.returncode}")

    remote_lines = _git_output("ls-remote", "--refs", remote, merge_ref).splitlines()
    expected_line = f"{head}\t{merge_ref}"
    if remote_lines != [expected_line]:
        raise WorkloreError(
            f"remote verification failed for {remote}/{merge_ref} after push"
        )
    if _git_output("status", "--porcelain=v1", "--untracked-files=all"):
        raise WorkloreError("working tree changed during push")
    print(f"published: {remote}/{merge_ref} = {head}")
