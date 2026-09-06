---
name: land-code
description: Review, stage, commit, and push the complete intended working tree. Use only when the user explicitly invokes `$land-code`, `/land-code`, `$close-code`, or `/close-code`; stop on conflicts, unintended files, failed checks, unreachable remotes, or branch divergence.
---

# Land Code

Explicit `land-code` or delegated explicit `close-code` authorizes stage,
commit and normal push of the current unambiguously owned reviewed snapshot,
not content edits. A later invocation replaces an earlier turn-local hold for
that snapshot; it does not override a restated/persistent restriction, platform
policy, ambiguous ownership, an unresolved external-transmission boundary or
another operation's authorization.

Do not ask for landing authorization again. If required, request platform tool
approval for the exact `worklore _land-reviewed --expected-head` prefix.
Durable approval belongs to the platform; each use still verifies repository,
branch, upstream, HEAD, snapshot and stop conditions. No raw Git fallback,
force push, destructive Git, merge, deployment or external-service authority
is conferred. Never bypass hooks. A default branch name alone is not a stop
condition.

## Stop conditions

Stop without corrective action or partial staging for:

- nothing to land, conflicts, active Git sequencer or detached HEAD;
- existing-history branch with missing/unreachable upstream or not exactly
  synchronized with it before commit;
- unborn HEAD without one unambiguous reachable remote containing no refs;
- secrets, generated accidents, unrelated/unintended changes;
- required checks failing or modifying tracked files.

## Landing

1. Inspect branch/HEAD, remotes/upstream, status, staged/unstaged diffs and
   untracked files as one complete candidate. Capture existing-history
   candidates with `worklore _reviewed-snapshot`.
2. Read every affected app's instructions, inspect all changes and run its
   required checks plus applicable repository-wide gates.
3. Derive one concise Conventional Commit subject:
   `<type>[optional scope]: <description>`, matching the actual change and
   repository convention. Do not invent scope or breaking-change markers.
4. Recheck branch, HEAD and complete snapshot; stop if reviewed state changed.
5. For existing history, invoke only:

   ```sh
   worklore _land-reviewed --expected-head <exact-head> --expected-snapshot <snapshot-sha256> --message <subject>
   ```

   The guard owns fresh upstream comparison, snapshot validation, complete
   staging, commit/tree verification and normal push. Do not fall back to raw
   `git fetch/add/commit/push`.
6. Initial publication only: require `git ls-remote <remote>` to succeed with
   no refs; stage the complete tree using `git add --all`, verify no remaining
   unstaged/untracked/unmerged paths and repeat the empty-remote check
   immediately before the first commit. Create one commit, then push with
   `git push --set-upstream <remote> <branch>`.
7. If commit succeeds but push fails, preserve the commit; never reset/rewrite
   it to conceal failure.

Report SHA, subject, branch/upstream, checks, staged paths and final status.
