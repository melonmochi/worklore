---
name: close-code
description: Close an implementation-complete working-tree change through bounded prune convergence before each fresh correctness review, one allowed fix generation, and land-code. Use only when the user explicitly invokes `$close-code` or `/close-code`; invocation delegates the child skills' declared edit, review, staging, commit, and push authority.
---

# Close Code

Close code; do not improve it. Treat the current working-tree change as the
intended change set only when its ownership is unambiguous.

## Authority

Load and follow the installed `prune-code`, `review-code`, `fix-code`, and
`land-code` skills. They retain authority over their own work, including
configuration decisions and transmission boundaries. Own only their sequence,
stopping, snapshot freshness, and the final summary. Commit naming, including
the Conventional Commits policy, remains wholly owned by `land-code`; do not
restate or independently enforce it here.

Explicit invocation delegates the edits, review activity, staging, committing,
and pushing already authorized by those child skills. Do not let orchestration
broaden authority that a child skill would not have when invoked directly. Do
not design, extend, or deploy the change. `organize-code` is not part of this
closure flow.

## Snapshot rule

Any code mutation invalidates both prune and review evidence. A fresh
correctness review is valid only after `prune-code` has converged on that exact
snapshot. Evidence may be reused across a pause in this closure run only while
the snapshot remains unchanged; do not persist or reuse it across sessions.

Use at most two review generations and at most one `fix-code` generation. In a
second generation, treat correctness findings accepted during the first
review/fix generation as frozen obligations. Pruning cannot remove the behavior
required by those findings.

## Flow

1. Stop if ownership of the working-tree change is ambiguous.
2. Begin a review generation by running `prune-code` to `RIGHT-SIZED`, scoped
   to the change and its directly affected surfaces. Stop on `OVERBUILT`,
   `BLOCKED`, architectural expansion, or any child stop condition.
3. Freeze that converged snapshot and run `review-code` once. If its configured
   co-review pauses before provider invocation to obtain explicit
   external-transmission approval or complete configured reviewer
   authentication, pause this same closure run. After approval or
   authentication, resume at the co-review invocation without repeating prune
   or the independent primary review, provided the reviewed snapshot is
   unchanged. The helper may complete browser authentication and its one
   allowed replacement invocation without an orchestration pause. Do not run
   `fix-code` or `land-code` while paused. If the user declines, or if the
   configured co-review remains incomplete after its allowed authentication
   recovery, stop `close-code` immediately. Do not run `fix-code` to repair
   review infrastructure within the same closure run, and do not proceed to
   `land-code`.
4. If the fresh review has no actionable findings, run `land-code`.
5. If the first review generation has actionable findings, run `fix-code` once.
   Continue only when it completes without a verified finding that the
   configured addressing policy requires it to fix.
6. If `fix-code` made no code mutation, the existing prune and review evidence
   remains fresh; run `land-code`. If it mutated code, discard both evidence
   sets, freeze its accepted correctness findings as obligations, and begin the
   second and final review generation at step 2.
7. If the second fresh review has any actionable finding, stop immediately.
   Do not run a second fix generation or a third review generation. Otherwise
   run `land-code`.

Do not insert a separate simplification pass or call an advisor directly;
`prune-code` wholly owns convergence and any optional advisor consultation.

## Stop

Honor every child skill's stop conditions. A pre-invocation permission request
or unresolved authentication requirement is a pause, not a closure blocker.
An incomplete co-review after the helper's allowed authentication recovery, or
declined permission, is a closure blocker rather than an actionable finding to
address inside the same run. Also stop when closure would require broader
product scope or a new owner decision.

## Report

Keep progress updates brief. Finish with one summary covering prune
generations, review generations, addressing, checks, commit, push, and any
genuine blocker.
