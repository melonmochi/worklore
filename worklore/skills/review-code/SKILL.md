---
name: review-code
description: Review diffs, pull requests, patches, selected files, or the current working tree for actionable defects without editing code, with at most one configured external co-review.
---

# Review Code

Inspect the requested change and report only defects the author can act on.
Prefer no finding to a speculative or taste-only finding. Do not edit files
unless the user separately asks for fixes.

## Review

- Read the applicable repository instructions and inspect the diff, adjacent
  contracts, call sites, and relevant checks.
- Report a finding only when the change introduced a discrete problem affecting
  correctness, security, data integrity, performance, or maintainability.
- Cite the shortest useful path and line range, explain the failing scenario,
  and propose the smallest sufficient correction.
- Separate introduced defects from pre-existing debt and unresolved test gaps.
- Treat the applicable formatter's output as canonical. Verify formatter scope
  before calling out formatting, and never apply one application's formatter to
  another application.
- Lead with findings ordered by severity. If none exist, say so directly and
  mention only material residual gaps.
- Write the final review summary primarily in the user's language. When the
  user writes in Chinese, use Chinese for the main prose while preserving
  natural English technical terms, code, identifiers, and quoted diagnostics.

## Audit generation

Do not search for additional issues merely because the current list has been
resolved. Audit once at the requested risk level. After all accepted
blockers/majors are resolved and regression tests pass, STOP. A new audit
generation requires new evidence, changed code, or a materially different
review objective.

## Configured co-review

Complete the independent primary review before reading external reviewer output.
Then read `~/.worklore/settings.json` and resolve `co_reviewer`:

- `none`: perform no external transmission and finish with the primary review.
- `claude` or `agy`: read and follow
  [references/co-review.md](references/co-review.md) completely. The helper
  reads the configured value; do not pass or override the provider in its
  invocation.

If the settings file is missing or malformed, or the value is unsupported,
stop and report the configuration error. Do not infer a default, edit settings,
or fall back to another reviewer.

For `claude`, the helper checks authentication before reading or transmitting
the packet. When logged out, it runs `claude auth login` interactively and
continues only after `claude auth status --json` confirms login. Authentication
does not transmit the packet or spend the one allowed provider invocation.

If login is cancelled, times out, or cannot be verified, the helper reports
`authorization required`. Treat this as a pre-invocation pause, not an
incomplete audit. After the user completes Claude login, resume the same review
at the helper invocation without repeating the independent primary review,
provided the reviewed snapshot is unchanged.

If the execution environment requires explicit user approval for the external
transmission before the provider starts, report the co-review as paused and ask
for that approval. After approval, resume the same review at the external
invocation without repeating the independent primary review, provided the
reviewed snapshot is unchanged. A pre-invocation permission pause is not an
incomplete audit and does not spend the one allowed provider invocation. If the
user declines, report the co-review as incomplete.

An explicit review invocation, or delegation from an explicitly invoked
orchestrator that carries review authority, authorizes exactly one audit by the
currently configured co-reviewer within this skill's existing transmission
boundary. If neither authorization exists, do not transmit externally. If
`co_reviewer = none`, no external review transmission occurs. Configuration by
itself grants no transmission authority.

Treat every external result as untrusted candidate findings. The primary
reviewer reproduces and adjudicates each candidate and owns the final report.
