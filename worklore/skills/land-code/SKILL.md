---
name: land-code
description: Review, stage, commit, and push the complete intended working tree. Use only when the user explicitly invokes `$land-code`, `/land-code`, `$close-code`, or `/close-code`; stop on conflicts, unintended files, failed checks, unreachable remotes, or branch divergence.
---

# Land Code

Explicit invocation of this skill, or delegation from an explicit `$close-code`
or `/close-code` invocation, authorizes staging, committing, and pushing the
reviewed snapshot. It does not authorize editing file contents.

## Stop Conditions

Stop before committing when any of these is true:

- there is nothing to land;
- a conflict or Git sequencer operation is active;
- `HEAD` is detached;
- an existing-history branch has a missing or unreachable upstream;
- an existing-history branch is not exactly synchronized with its upstream
  before commit;
- `HEAD` is unborn and there is no single unambiguous reachable remote, or that
  remote contains any refs;
- the snapshot contains a secret, generated accident, unrelated change, or
  other unintended artifact; or
- a required check fails or modifies tracked files.

Report the evidence and take no corrective action when stopped. Do not stage a
partially accepted working tree.

## Workflow

1. Capture the branch, `HEAD` state, remotes, upstream, status, staged diff,
   unstaged diff, untracked files, and an index fingerprint.
2. Read the scoped `AGENTS.md` for every affected application and record its
   required checks.
3. Inspect every change as one candidate snapshot. Stop before staging if any
   path is suspicious, unrelated, or unintended.
4. Verify the publication target before staging:
   - If `HEAD` is unborn, require one unambiguous configured remote and require
     `git ls-remote <remote>` to succeed with no refs. Record that remote and the
     current branch as the initial publication target.
   - Otherwise, fetch the configured upstream and stop unless the local branch
     and its upstream point to the same commit.
5. Stage the complete reviewed working tree with `git add --all`. Verify that no
   unstaged or untracked paths remain and that the staged diff matches the
   reviewed snapshot. Capture a new index fingerprint.
6. Inspect the staged content and recent history; derive one concise commit
   message that matches repository convention.
7. Run the recorded checks and any repository-wide gate required by the
   snapshot.
8. Recheck status and the post-staging index fingerprint. Stop unless the working
   tree has no unstaged, untracked, or unmerged paths and the index is unchanged.
   For initial publication, repeat the empty-remote check immediately before
   committing.
9. Create one new commit. Never amend or bypass hooks.
10. For initial publication, push with
    `git push --set-upstream <remote> <branch>`. Otherwise, push with plain
    `git push` to the verified upstream.
11. Report the commit SHA, subject, branch, upstream, checks, staged paths, and
    final status.

If commit succeeds but push fails, preserve the local commit, do not reset or
rewrite it, and report the push failure precisely.
