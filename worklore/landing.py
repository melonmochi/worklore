from __future__ import annotations

import hashlib
import os
import re
import stat
import subprocess
from pathlib import Path

from . import WorkloreError

GIT_OBJECT_ID = re.compile(r"^[0-9a-f]+$")
SNAPSHOT_ID = re.compile(r"^[0-9a-f]{64}$")


def _git_bytes(*arguments: str) -> bytes:
    result = subprocess.run(
        ["git", *arguments],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        detail = (
            result.stderr.decode("utf-8", errors="replace").strip()
            or result.stdout.decode("utf-8", errors="replace").strip()
            or "git command failed"
        )
        raise WorkloreError(detail)
    return result.stdout


def _git_output(*arguments: str) -> str:
    return _git_bytes(*arguments).decode("utf-8", errors="surrogateescape").strip()


def _digest_part(digest, value: bytes) -> None:
    digest.update(len(value).to_bytes(8, "big"))
    digest.update(value)


def reviewed_snapshot() -> str:
    if _git_output("rev-parse", "--is-inside-work-tree") != "true":
        raise WorkloreError("current directory is not a Git working tree")
    if _git_output("ls-files", "--unmerged"):
        raise WorkloreError("index contains unresolved merges")

    digest = hashlib.sha256()
    changed = _git_bytes(
        "diff",
        "--name-only",
        "-z",
        "--no-ext-diff",
        "--no-renames",
        "HEAD",
        "--",
    ).split(b"\0")
    untracked = _git_bytes(
        "ls-files", "--others", "--exclude-standard", "-z"
    ).split(b"\0")
    for raw_path in sorted(set(changed + untracked) - {b""}):
        path = Path(os.fsdecode(raw_path))
        try:
            metadata = path.lstat()
        except FileNotFoundError:
            _digest_part(digest, raw_path)
            _digest_part(digest, b"missing")
            continue
        if stat.S_ISREG(metadata.st_mode):
            content = path.read_bytes()
        elif stat.S_ISLNK(metadata.st_mode):
            content = os.fsencode(os.readlink(path))
        elif stat.S_ISDIR(metadata.st_mode):
            content = _git_bytes(
                "-C", os.fsdecode(raw_path), "rev-parse", "--verify", "HEAD"
            ).strip()
        else:
            raise WorkloreError(f"unsupported snapshot path: {path}")
        _digest_part(digest, raw_path)
        _digest_part(digest, str(metadata.st_mode).encode("ascii"))
        _digest_part(digest, content)
    return digest.hexdigest()


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


def _require_staged_tree(expected_tree: str | None = None) -> str:
    if _git_output("ls-files", "--unmerged"):
        raise WorkloreError("index contains unresolved merges")
    if _git_output("diff", "--name-only") or _git_output(
        "ls-files", "--others", "--exclude-standard"
    ):
        raise WorkloreError("working tree must contain only staged changes")
    if not _git_output("diff", "--cached", "--name-only"):
        raise WorkloreError("index contains no changes to commit")
    tree = _git_output("write-tree")
    if expected_tree is not None and (
        not GIT_OBJECT_ID.fullmatch(expected_tree) or expected_tree != tree
    ):
        raise WorkloreError(
            f"expected index tree {expected_tree!r} does not equal current tree {tree}"
        )
    return tree


def _require_reviewed_snapshot(expected_snapshot: str) -> None:
    snapshot = reviewed_snapshot()
    if not SNAPSHOT_ID.fullmatch(expected_snapshot) or expected_snapshot != snapshot:
        raise WorkloreError(
            f"expected snapshot {expected_snapshot!r} does not equal current "
            f"snapshot {snapshot}"
        )


def land_reviewed(expected_head: str, expected_snapshot: str, message: str) -> str:
    if _git_output("rev-parse", "--is-inside-work-tree") != "true":
        raise WorkloreError("current directory is not a Git working tree")

    branch = _git_output("symbolic-ref", "--quiet", "--short", "HEAD")
    head = _require_expected_head(expected_head)
    remote, merge_ref, _ = _tracking_target(branch)
    if not message.strip() or "\n" in message or "\r" in message:
        raise WorkloreError("commit message must be one non-empty line")
    if not _git_output("status", "--porcelain=v1", "--untracked-files=all"):
        raise WorkloreError("working tree contains no changes to commit")
    _require_reviewed_snapshot(expected_snapshot)

    _git_output("fetch", "--no-tags", remote, merge_ref)
    head = _require_expected_head(expected_head)
    remote_head = _git_output("rev-parse", "--verify", "FETCH_HEAD")
    if remote_head != head:
        raise WorkloreError(
            "current branch must equal its remote branch before commit "
            f"(local={head}, remote={remote_head})"
        )
    _require_reviewed_snapshot(expected_snapshot)

    _git_output("add", "--all")
    _require_reviewed_snapshot(expected_snapshot)
    tree = _require_staged_tree()
    _require_reviewed_snapshot(expected_snapshot)
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
