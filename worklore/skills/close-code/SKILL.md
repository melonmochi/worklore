---
name: close-code
description: Close an implementation-complete working-tree change through bounded prune convergence before each fresh correctness review, one allowed fix generation, and land-code. Use only when the user explicitly invokes `$close-code` or `/close-code`; invocation delegates the child skills' declared edit, review, staging, commit, and push authority.
---

# Close Code

Close an implementation-complete, unambiguously owned change; do not extend or
deploy it. Load and follow `prune-code`, `review-code`, `fix-code`, and
`land-code`. They own their settings, authority, transmission, recovery,
checks, and commit policy. This skill owns only sequence and snapshot freshness.
`organize-code` is not part of closure.

## Snapshot and generation limits

Any code mutation invalidates both prune and review evidence. A correctness
review must follow prune convergence on that exact snapshot. Reuse evidence
only during an unchanged pause in this run, never across sessions.

Allow at most two review generations and one fix generation. Accepted
correctness findings become frozen obligations for subsequent pruning.

## Flow

1. Stop on ambiguous ownership. Run `prune-code` on the change and directly
   affected surfaces; continue only at `RIGHT-SIZED`.
2. Freeze the converged snapshot and run `review-code` once.
   Follow its co-review pause/recovery protocol without repeating an unchanged
   primary review. Do not fix or land while review is paused or incomplete;
   review-infrastructure repair is outside this closure run.
3. With no actionable findings, run `land-code`.
4. For first-generation findings, run `fix-code` once. Stop if any verified
   finding required by its addressing policy remains.
5. If fixing did not mutate code, land using the still-fresh evidence.
   Otherwise discard the evidence and repeat steps 1–2 for the final generation,
   preserving accepted correctness findings.
6. Any actionable finding in the second review stops closure. Otherwise land.
   No second fix or third review generation.

Honor all child stop conditions. Do not add a separate simplification pass,
consult an advisor directly, or broaden scope to avoid a stop.

Report prune/review generations, addressing, checks, commit/push outcome, and
any blocker in one compact summary.
