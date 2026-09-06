---
name: prune-code
description: Remove obsolete code, concepts, workflows, abstractions, compatibility surfaces, tests, commands, and documentation through a bounded convergence audit. Use when asked to right-size a repository, run an anti-audit, delete superseded or one-off machinery, or challenge accidental complexity while preserving current behavior and real persistence, compatibility, security, integration, and operational obligations.
---

# Prune Code

Challenge necessity in the requested scope. Prefer deletion over replacement;
do not turn pruning into modernization, redesign or aesthetic refactoring.

## Freeze current obligations

Read applicable instructions and inspect semantics, callers, tests, persisted
formats, integrations and operations. Preserve promised APIs, reachable
historical data/migrations, security/accessibility boundaries and current user
workflows. Preserve the Git index and unrelated work; do not commit or push
without explicit authorization.

A seam survives for real semantic authority, persistence, transport, failure
lifecycle or an independently changing responsibility—not its name, pattern,
file size, mock convenience or hypothetical future backend.

Ask: if built today for these requirements and persisted data, would this
concept exist? Do not invent obligations to avoid deletion.

## Audit and adjudicate

Classify complexity as necessary, transitional with a current purpose, or
obsolete/duplicated/one-off. Inspect dead semantics, duplicate paths, completed
migration/study machinery, speculative extension points, custom substitutes
for existing platform capabilities, and their tests/documentation.

Historical readers can remain necessary while historical writers and workflow
APIs need separate justification. Tests show intent, not permanent obligation.

Use an existing simplification advisor only when explicitly requested or
delegated by the current task, at most once per pass. Never install/configure
one or let its absence block work. Its output is candidate input; independently
judge it against frozen obligations. The advisor cannot edit or expand scope.
Do not introduce a new authorization or external-transmission boundary.

## Mutation boundary

Delete unjustified machinery and tests/docs/commands serving only that
machinery. Repair surviving callers only as needed. Retain historical readers
and migration tests required by reachable data.

Do not replace deletions with abstractions, shims, configuration switches,
registries, manifests, evidence directories, frameworks or dependencies.
Avoid unrelated renaming, formatting, moves, upgrades and hardening.
Change tests only to protect surviving behavior. A net production-code increase
requires a concrete surviving invariant, not a LOC argument.

## Converge

Allow at most two mutation rounds. Each audits, adjudicates the in-scope
candidates, applies the accepted set and validates. Any mutation invalidates
prune evidence: re-audit before claiming convergence. Failed validation stops
as `BLOCKED`; do not stack changes on an unvalidated result.

Keep only transient intent/path notes. Do not reverse an earlier deletion
without a newly discovered frozen obligation. Conflicting obligations stop
the pass rather than creating an oscillation.

After the second round, perform a terminal read-only audit; no third mutation.
Run declared repository checks and diff check. Inspect for unrelated edits,
replacement complexity, secrets and damaged protected surfaces.

- `RIGHT-SIZED`: latest audit has no accepted remaining candidate.
- `OVERBUILT`: verified unjustified complexity remains after two rounds.
- `BLOCKED`: failed validation, unclear/conflicting obligations or missing
  authority prevents safe deletion.

Report result, rounds, advisor use/skipping, removals, preserved obligations,
validation, net diff and concrete residue. Do not create a reporting artifact.
