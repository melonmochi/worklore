---
name: close-code
description: Close an implementation-complete working-tree change through one scoped prune, one bounded review, resolution of actionable findings when present, and land-code. Use only when the user explicitly invokes `$close-code` or `/close-code`; invocation delegates the child skills' declared edit, review, staging, commit, and push authority.
---

# Close Code

Close code; do not improve it. Treat the current working-tree change as the
intended change set only when its ownership is unambiguous.

## Authority

Load and follow the installed `prune-code`, `review-code`,
`fix-code`, and `land-code` skills. They retain authority over their own
work, including configuration decisions and transmission boundaries. Own only
their sequence, stopping, and the final summary.

Explicit invocation delegates the edits, review activity, staging, committing,
and pushing already authorized by those child skills. Do not let orchestration
broaden authority that a child skill would not have when invoked directly. Do
not design, extend, or deploy the change.

## Flow

1. Stop if ownership of the working-tree change is ambiguous.
2. Run `prune-code` once, scoped to the change and its directly affected
   surfaces. Continue only when pruning completes without a blocker or
   architectural expansion.
3. Run `review-code` once. If its configured co-review pauses before provider
   invocation solely to obtain explicit external-transmission approval, pause
   this same closure run and ask the user. After approval, resume at the
   co-review invocation without repeating prune or the independent primary
   review, provided the reviewed snapshot is unchanged. Do not run `fix-code`
   or `land-code` while paused. If the user declines, or if the configured
   co-review is incomplete after invocation begins, stop `close-code`
   immediately. Do not run `fix-code` to repair review infrastructure within
   the same closure run, and do not proceed to `land-code`.
4. If actionable findings exist, run `fix-code`. Continue only when it completes
   without a verified finding that the configured addressing policy requires it
   to fix.
5. Run `land-code`.

Do not repeat prune or full review. Once the configured addressing policy is
satisfied, proceed directly to the checks owned by `land-code`.

## Stop

Honor every child skill's stop conditions. A pre-invocation permission request
is a pause, not a closure blocker. An incomplete configured co-review after
invocation starts or permission is declined is a closure blocker, not an
actionable finding to address inside the same run. Also stop when closure would
require broader product scope or a new owner decision.

## Report

Keep progress updates brief. Finish with one summary covering prune, review,
addressing, checks, commit, push, and any genuine blocker.
