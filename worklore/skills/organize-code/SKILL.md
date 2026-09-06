---
name: organize-code
description: Reorganize necessary code without changing product behavior when real ownership, authority, or reason-to-change boundaries are mixed, misplaced, or fragmented. Use for explicit structural moves, splits, or merges, not pruning, general cleanup, or architecture-pattern enforcement.
---

# Organize Code

Reorganize necessary code only where current ownership or reasons to change
are mixed, misplaced or fragmented. Pruning belongs to `prune-code`.

An explicit invocation authorizes one coherent move, split or merge and its
required import/test/documentation repairs. It does not authorize product
changes, dependencies, unrelated cleanup, staging, committing or pushing.

Read applicable instructions and freeze public behavior/APIs, persisted
formats, security and operational contracts. Preserve the Git index and
unrelated work.

## Decide by evidence

Inspect callers, tests, dependency direction and actual lifecycle/change
evidence. A boundary must isolate current semantic authority, persistence,
transport, failure lifecycle or an independently changing responsibility.
File length, architectural taxonomy, symmetry, mock convenience and hypothetical
backends do not justify it.

- `KEEP`: placement is cohesive or no change is earned.
- `MOVE`: ownership is clear but placement is wrong.
- `SPLIT`: independent responsibilities share one location.
- `MERGE`: one responsibility is needlessly fragmented.

For a change, state the mixed ownership, independent reason to change and
smallest correction while naming the contract that stays stable. Stop if it
requires a product decision or an abstraction without a current obligation.

Apply only that correction, run focused validation, and re-read ownership and
dependency direction. Then stop; do not continue reorganizing.

Report the decision, evidence, changed paths, preserved contracts and checks.
With no finding, return `KEEP (RIGHT-SIZED)` without editing.
