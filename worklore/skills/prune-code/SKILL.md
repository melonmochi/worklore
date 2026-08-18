---
name: prune-code
description: Remove obsolete code, concepts, workflows, abstractions, compatibility surfaces, tests, commands, and documentation that no longer justify their existence. Use when asked to right-size a repository, run an anti-audit, delete superseded or one-off machinery, or challenge accidental complexity while preserving current behavior and real persistence, compatibility, security, integration, and operational obligations.
---

# Prune Code

Right-size the requested repository by challenging necessity. Prefer deletion
over replacement. Do not turn pruning into cleanup, modernization, redesign,
generalization, or aesthetic refactoring.

## Establish the boundary

- Read the applicable repository instructions and inspect the current product
  semantics, callers, persisted formats, integrations, operational paths,
  tests, and documentation.
- Identify only protected surfaces supported by concrete current obligations:
  public interfaces still promised, persisted data that must remain readable,
  migrations needed by real historical state, active integrations, security
  boundaries, current user workflows, and current operations.
- Preserve the existing Git index and unrelated work. Do not commit or push
  unless the user explicitly requests it.
- Do not invent protected surfaces merely to avoid deletion.

## Challenge necessity

For each meaningful piece of complexity, ask which current invariant,
user-visible behavior, external contract, persisted-data obligation, security
boundary, or operational constraint requires it.

Apply the greenfield test:

> If this repository were implemented today against only its current
> requirements and persisted-data obligations, would this concept be added?

Inspect especially:

- dead or superseded domain semantics and workflow states;
- duplicate APIs, representations, commands, or execution paths;
- one-off migration, reconciliation, remediation, generation, UI, CLI, batch,
  or orchestration machinery whose job is complete;
- speculative strategies, factories, plugins, policy layers, configuration
  modes, and generic extension points without real alternatives;
- historical write paths, workflow APIs, and commands that survive after their
  compatibility purpose ended;
- tests and documentation that keep obsolete semantics looking alive.

Classify each inspected surface as:

1. necessary for a protected current obligation;
2. transitional but still serving a concrete current purpose;
3. obsolete, superseded, duplicated, or one-off and eligible for deletion.

Treat compatibility asymmetrically. Reading real historical data can justify
survival; writing old formats, exposing old workflow APIs, and preserving old
commands usually require separate current justification. Tests demonstrate
historical intent, not a permanent requirement.

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

## Validate and stop

- Run the repository's declared validation commands and its diff check.
- Review the final diff for unrelated edits, replacement complexity, leaked
  secrets, and accidental changes to protected surfaces.
- Stop when the explicitly identified obsolete surfaces are gone. Do not use
  deletion as permission to discover replacement work or redesign neighboring
  live code.

Report compactly:

```text
ANTI-AUDIT: RIGHT-SIZED | OVERBUILT | BLOCKED

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
- none | concrete blocker
```

Use `RIGHT-SIZED` when no unjustified in-scope complexity remains, including
when inspection proves no material deletion is warranted. Use `OVERBUILT` only
when verified obsolete complexity remains. Use `BLOCKED` only when a concrete
missing contract, data obligation, or authority prevents safe deletion.
