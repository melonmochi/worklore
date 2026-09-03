---
name: organize-code
description: Reorganize necessary code without changing product behavior when real ownership, authority, or reason-to-change boundaries are mixed, misplaced, or fragmented. Use for explicit structural moves, splits, or merges, not pruning, general cleanup, or architecture-pattern enforcement.
---

# Organize Code

Put necessary code in the right place without changing what the product does.
Reduce structural entropy only when current evidence supports a clearer owner,
boundary, or reason to change.

## Boundary

An explicit invocation authorizes the code and file moves, splits, merges, and
directly required import, test, or documentation adjustments for one coherent
structural change. It does not authorize product changes, new dependencies,
unrelated cleanup, staging, committing, or pushing.

Read the applicable repository instructions and preserve the existing Git
index, unrelated work, public behavior, public APIs, persisted formats,
security properties, and operational contracts. Stop when the proposed
structure requires a product decision or a new abstraction without a current
obligation.

Do not remove code merely because it looks unnecessary; that belongs to
`prune-code`. Do not enforce Clean Architecture, SOLID, DDD, MVC, repository
templates, target file sizes, or any other architecture taxonomy.

## Decide by ownership

Look for one bounded structural problem:

- a file or module owns responsibilities with genuinely independent reasons to
  change;
- one authority or source of truth is jointly owned by multiple locations;
- semantic code depends directly on persistence, transport, framework, or UI
  representation that changes independently;
- infrastructure detail crosses an otherwise stable authority or failure
  boundary;
- one responsibility is fragmented across locations without a real boundary;
- a helper, wrapper, adapter, or indirection chain has no clear owner; or
- dependency direction lets a lower-level representation define higher-level
  semantics.

A boundary is justified when it isolates real semantic authority, persistence,
transport, failure lifecycle, or an independently changing responsibility.
File length, aesthetic symmetry, easier mocking, or a possible future backend
is not enough.

Use only these decisions:

- `KEEP`: the current placement is cohesive or no structural change is earned;
- `MOVE`: ownership is clear but the code is in the wrong location;
- `SPLIT`: one location contains independently changing ownerships;
- `MERGE`: one responsibility is needlessly fragmented.

For `MOVE` or `SPLIT`, state the mixed ownership, the independent reason to
change, the smallest structural correction, and the behavior or API that must
remain unchanged. Apply at most one coherent structural change per invocation.
If there is no real finding, return `KEEP (RIGHT-SIZED)` without editing.

## Decision guidance

- A long module with one cohesive authority and lifecycle is `KEEP`.
- One current backend with no real replacement or failure seam does not earn a
  generic interface; keep the direct dependency.
- Domain policy and persistence mapping that change for different reasons earn
  `SPLIT` or `MOVE` when their existing contract can remain stable.
- One responsibility scattered across files without independent ownership
  earns `MERGE` or `MOVE`.

## Workflow

1. Freeze the behavior, APIs, data, security, and operational obligations that
   the change must preserve.
2. Inspect callers, tests, dependency direction, and actual change history or
   lifecycle evidence relevant to the suspected boundary.
3. Choose one decision and stop if no minimal behavior-preserving change is
   supported.
4. Apply the smallest move, split, or merge and repair only directly affected
   imports, tests, and documentation.
5. Run focused validation for the moved boundary.
6. Re-read the resulting ownership and dependency direction. Stop after this
   one structural change; do not continue reorganizing the repository.

Report the decision, evidence, changed paths, preserved behavior or APIs,
validation, and any remaining candidate that was deliberately left for a
separate invocation.
