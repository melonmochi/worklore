---
name: land-code
description: Review, stage, commit, and push the complete intended working tree. Use only when the user explicitly invokes `$land-code`, `/land-code`, `$close-code`, or `/close-code`; stop on conflicts, unintended files, failed checks, unreachable remotes, or branch divergence.
---

# Land Code

Explicit invocation of this skill, or delegation from an explicit `$close-code`
or `/close-code` invocation, authorizes staging, committing, and pushing the
reviewed snapshot. It does not authorize editing file contents.

Treat a later explicit `$land-code`, `/land-code`, `$close-code`, or
`/close-code` invocation as replacement landing authorization for the current,
unambiguously owned, reviewed snapshot. It supersedes an earlier turn-local
instruction to temporarily withhold commit or push for that same snapshot; do
not ask the owner to repeat the landing authorization. It does not override a
restriction the owner restates in that invocation; persistent `AGENTS.md`,
repository, organization, or platform policy; ambiguous working-tree ownership;
an unresolved external-transmission boundary; the Stop Conditions below; or
authorization requirements for another repository, snapshot, or future
operation.

If the platform requires approval for a Git operation, request tool approval
directly instead of asking the owner for landing authorization again. State in
the justification that the later explicit skill invocation authorizes staging,
committing, and pushing the current snapshot; replaces the earlier turn-local
temporary restriction; and remains subject to the `land-code` Stop Conditions.
A default branch name alone is not a stop condition or a reason to ask the owner
again.

When the platform supports durable command approvals, request reusable approval
for the exact `worklore _land-reviewed --expected-head` command prefix. That
approval covers this guarded Worklore capability across repositories and
reviewed snapshots until revoked; the platform remains the authority for storing
and revoking it. It does not authorize implicit skill invocation, raw
`git fetch`, `git add`, `git commit`, or `git push`; force push; destructive
Git; merges; deployments; arbitrary shell writes; provider transmission; or
other external systems. Every invocation must still establish the concrete
repository, branch, upstream, reviewed `HEAD`, snapshot fingerprint, and Stop
Conditions anew.

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
   unstaged diff, and untracked files. For an existing-history branch, capture
   the complete candidate snapshot with `worklore _reviewed-snapshot`.
2. Read the scoped `AGENTS.md` for every affected application and record its
   required checks.
3. Inspect every change as one candidate snapshot. Stop before staging if any
   path is suspicious, unrelated, or unintended.
4. Verify the publication target. If `HEAD` is unborn, require one unambiguous
   configured remote and require `git ls-remote <remote>` to succeed with no
   refs. Record that remote and the current branch as the initial publication
   target. Otherwise, require a configured upstream; the guarded landing helper
   owns the fresh remote comparison before it stages anything.
5. Inspect the candidate snapshot and recent history; derive one concise
   Conventional Commit subject using `<type>[optional scope]: <description>`.
   Match the type and scope to the actual change and repository convention; do
   not invent a scope or breaking-change marker.
6. Run the recorded checks and any repository-wide gate required by the
   snapshot.
7. Recheck the branch, `HEAD`, status, and complete candidate snapshot. Stop
   unless they still match the reviewed state. For initial publication, stage
   the complete tree with `git add --all`, verify there are no remaining
   unstaged, untracked, or unmerged paths, and repeat the empty-remote check
   immediately before committing.
8. For initial publication, create one commit and push with
   `git push --set-upstream <remote> <branch>`. For an existing-history branch,
   delegate fetch, snapshot revalidation, complete staging, commit, and
   publication as one guarded operation to
   `worklore _land-reviewed --expected-head <pre-commit-head>
   --expected-snapshot <snapshot-sha256> --message <subject>`. The helper must
   refetch the configured remote branch and confirm it still equals the
   expected pre-commit `HEAD` before staging. It must revalidate the complete
   reviewed snapshot, stage all of it, capture the exact tree, commit without
   bypassing hooks, verify the new commit's parent and tree, and perform a
   normal non-force push. For an existing-history branch, do not invoke plain
   `git fetch`, `git add`, `git commit`, or `git push` as a fallback.
9. If commit succeeds but publication fails, preserve the local commit without
   resetting or rewriting it and report the push failure precisely.
10. Report the commit SHA, subject, branch, upstream, checks, staged paths, and
    final status.
