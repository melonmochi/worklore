---
name: prune-code
description: Remove obsolete code, concepts, workflows, abstractions, compatibility surfaces, tests, commands, and documentation through a bounded convergence audit. Use when asked to right-size a repository, run an anti-audit, delete superseded or one-off machinery, or challenge accidental complexity while preserving current behavior and real persistence, compatibility, security, integration, and operational obligations.
---

# Prune Code

Right-size the requested repository by challenging necessity. Prefer deletion
over replacement. Do not turn pruning into cleanup, modernization, redesign,
generalization, or aesthetic refactoring.

## Establish the boundary

- Read the applicable repository instructions and inspect the current product
  semantics, callers, persisted formats, integrations, operational paths,
  tests, and documentation.
- Freeze the current obligations for the full invocation: public interfaces
  still promised, persisted data that must remain readable, migrations needed
  by real historical state, active integrations, security and accessibility
  boundaries, current user workflows, operations, and tests that encode a real
  requirement.
- Preserve seams supported by current semantic authority, persistence,
  transport, failure lifecycle, or an independently changing responsibility.
  Naming, patterns, file length, mock convenience, or a hypothetical future
  backend do not protect a seam by themselves.
- Preserve the existing Git index and unrelated work. Do not commit or push
  unless the user explicitly requests it.
- Do not invent protected surfaces merely to avoid deletion. Less code never
  outranks a concrete product, authority, data, security, or lifecycle
  obligation.

## Challenge necessity

For each meaningful piece of complexity, ask which current invariant,
user-visible behavior, external contract, persisted-data obligation, security
boundary, or operational constraint requires it.

Apply the greenfield test:

> If this repository were implemented today against only its current
> requirements and persisted-data obligations, would this concept be added?

Inspect especially:

- dead or superseded domain semantics and workflow states;
- duplicate APIs, representations, commands, helpers, wrappers, tests,
  fixtures, or execution paths;
- one-off migration, reconciliation, remediation, generation, UI, CLI, batch,
  study, scaffold, or orchestration machinery whose job is complete;
- speculative strategies, factories, plugins, policy layers, configuration
  modes, and generic extension points without real alternatives;
- historical write paths, workflow APIs, and commands that survive after their
  compatibility purpose ended;
- custom machinery replaced by the standard library, platform, or an existing
  dependency; and
- tests and documentation that keep obsolete semantics looking alive.

Classify each inspected surface as:

1. necessary for a protected current obligation;
2. transitional but still serving a concrete current purpose;
3. obsolete, superseded, duplicated, or one-off and eligible for deletion.

Treat compatibility asymmetrically. Reading real historical data can justify
survival; writing old formats, exposing old workflow APIs, and preserving old
commands usually require separate current justification. Tests demonstrate
historical intent, not a permanent requirement.

## Optional simplification advisor

When the environment already provides an applicable simplification advisor,
it may be consulted at most once per audit pass. Do not search for, install,
configure, vendor, or depend on one, and never let its absence block pruning.
Skip it if consultation would introduce an unapproved external-transmission or
authorization boundary.

Advisor output is candidate input only. Independently accept or reject every
candidate against the frozen obligations; Worklore owns the decision and the
mutation. The advisor cannot expand scope, override a protected seam, or make
its own edits.

## Prune

- Delete category 3 production machinery directly.
- Delete tests whose only purpose was to preserve the removed semantics.
- Delete obsolete commands, documentation, and compatibility write paths tied
  only to the removed behavior.
- Repair surviving callers only as required by the deletion.
- Retain historical readers and migration tests when reachable persisted data
  still requires them.
- Prefer one canonical surviving path when duplicate semantics exist.

Do not introduce a replacement abstraction, compatibility shim, configuration
switch, migration framework, registry, manifest, evidence directory, or new
dependency to make the deletion look cleaner. Do not broaden into unrelated
renaming, formatting, directory moves, upgrades, hardening, or adjacent-system
redesign. Add or modify tests only when needed to protect surviving behavior.

Concept reduction matters more than deleted line count. If production code has
a net increase, treat it as presumptive evidence that the work became a
refactor; continue only with a concrete explanation tied to a surviving
invariant.

## Converge and stop

Use at most two mutation rounds. A round audits the current snapshot,
adjudicates all in-scope candidates, applies the smallest coherent accepted
set, and runs focused validation. If no candidate is accepted, the current
snapshot is a fixed point and the result is `RIGHT-SIZED`.

Any code mutation invalidates the current prune evidence. After a successful
mutation round, re-audit the resulting snapshot before claiming convergence.
If validation fails, stop as `BLOCKED`; do not stack another mutation on an
unvalidated result.

Keep only a transient record of accepted intent and affected paths for this
invocation. Reject a later candidate that merely restores or reverses an
earlier mutation unless a newly discovered frozen obligation requires it. If
the obligations genuinely conflict, stop as `BLOCKED` rather than oscillating.

After the second mutation round, perform one terminal read-only audit. If an
accepted candidate still remains, stop as `OVERBUILT`, report the residue, and
do not begin a third mutation round. Otherwise report `RIGHT-SIZED`.

Run the repository's declared validation commands and diff check before the
final result. Review the final diff for unrelated edits, replacement
complexity, leaked secrets, and accidental changes to protected surfaces.

Report compactly:

```text
ANTI-AUDIT: RIGHT-SIZED | OVERBUILT | BLOCKED

Rounds:
- audit/adjudication/mutation/validation: ...
- advisor: absent | skipped | candidates accepted/rejected

Removed:
- ...

Preserved:
- ...

Validation:
- existing check: PASS/FAIL
- diff check: PASS/FAIL
- production diff: +X / -Y
- no new architectural concepts

Unresolved:
- none | concrete blocker or terminal residue
```

Use `RIGHT-SIZED` only when the current snapshot's latest audit has no accepted
candidate, including when all candidates were rejected. Use `OVERBUILT` only
when verified unjustified complexity remains after two mutation rounds. Use
`BLOCKED` only for failed validation, unclear or conflicting obligations, or
missing authority that prevents safe deletion.
