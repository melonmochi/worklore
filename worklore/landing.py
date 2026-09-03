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


def _tracking_target(branch: str) -> tuple[str, str, str]:
    remote = _git_output("config", "--get", f"branch.{branch}.remote")
    merge_ref = _git_output("config", "--get", f"branch.{branch}.merge")
    if remote == "." or not merge_ref.startswith("refs/heads/"):
        raise WorkloreError("current branch must track a remote branch")
    upstream = _git_output(
        "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"
    )
    return remote, merge_ref, upstream


def _require_expected_head(expected_head: str) -> str:
    head = _git_output("rev-parse", "--verify", "HEAD")
    if not GIT_OBJECT_ID.fullmatch(expected_head) or expected_head != head:
        raise WorkloreError(
            f"expected HEAD {expected_head!r} does not equal current HEAD {head}"
        )
    return head


def _require_staged_tree(expected_tree: str) -> str:
    if _git_output("ls-files", "--unmerged"):
        raise WorkloreError("index contains unresolved merges")
    if _git_output("diff", "--name-only") or _git_output(
        "ls-files", "--others", "--exclude-standard"
    ):
        raise WorkloreError("working tree must contain only staged changes")
    if not _git_output("diff", "--cached", "--name-only"):
        raise WorkloreError("index contains no changes to commit")
    tree = _git_output("write-tree")
    if not GIT_OBJECT_ID.fullmatch(expected_tree) or expected_tree != tree:
        raise WorkloreError(
            f"expected index tree {expected_tree!r} does not equal current tree {tree}"
        )
    return tree


def land_reviewed(expected_head: str, expected_tree: str, message: str) -> str:
    if _git_output("rev-parse", "--is-inside-work-tree") != "true":
        raise WorkloreError("current directory is not a Git working tree")

    branch = _git_output("symbolic-ref", "--quiet", "--short", "HEAD")
    head = _require_expected_head(expected_head)
    remote, merge_ref, _ = _tracking_target(branch)
    if not message.strip() or "\n" in message or "\r" in message:
        raise WorkloreError("commit message must be one non-empty line")
    tree = _require_staged_tree(expected_tree)

    _git_output("fetch", "--no-tags", remote, merge_ref)
    head = _require_expected_head(expected_head)
    remote_head = _git_output("rev-parse", "--verify", "FETCH_HEAD")
    if remote_head != head:
        raise WorkloreError(
            "current branch must equal its remote branch before commit "
            f"(local={head}, remote={remote_head})"
        )
    _require_staged_tree(tree)

    _git_output("commit", "-m", message)
    committed_head = _git_output("rev-parse", "--verify", "HEAD")
    if _git_output("rev-parse", "--verify", "HEAD^") != head:
        raise WorkloreError("new commit does not have the expected parent")
    if _git_output("rev-parse", "--verify", "HEAD^{tree}") != tree:
        raise WorkloreError("new commit does not contain the expected index tree")

    push_reviewed(committed_head)
    return committed_head


def push_reviewed(expected_head: str) -> None:
    if _git_output("rev-parse", "--is-inside-work-tree") != "true":
        raise WorkloreError("current directory is not a Git working tree")

    branch = _git_output("symbolic-ref", "--quiet", "--short", "HEAD")
    head = _require_expected_head(expected_head)
    if _git_output("status", "--porcelain=v1", "--untracked-files=all"):
        raise WorkloreError("working tree must be clean before push")

    remote, merge_ref, upstream = _tracking_target(branch)
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
