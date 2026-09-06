---
name: review-code
description: Review diffs, pull requests, patches, selected files, or the current working tree for actionable defects without editing code, with at most one configured external co-review.
---

# Review Code

Report actionable defects introduced by the requested change, not speculative
or taste-only findings. Do not edit files without a separate fix request.

- Read applicable instructions, the diff, adjacent contracts, callers and checks.
- Cover correctness, security, data integrity, performance and maintainability.
  Cite the shortest useful location, failing scenario and sufficient correction.
- Separate introduced defects from pre-existing debt and material test gaps.
- Treat the applicable formatter as canonical; verify its application scope.
- Lead with severity-ordered findings, or say none. Use the user's language.

Audit once at the requested risk level. Do not hunt for more issues after the
accepted list is resolved without new code, evidence or review objective.

## Configured co-review

Finish the independent primary review before reading external reviewer output.
Read `~/.worklore/settings.json`:

- `co_reviewer = none`: finish without external transmission.
- `claude` or `agy`: read
  [references/co-review.md](references/co-review.md) completely; it owns packet
  handling, invocation and bounded recovery. Do not override the provider.
- Missing/malformed settings or an unsupported value: stop; do not infer a
  default, change settings or substitute another reviewer.

An explicit review invocation, or an explicit orchestrator invocation carrying
review authority, authorizes one configured co-review within that protocol's
transmission boundary. Configuration alone is not authorization. Retain
platform approval checks.

External output is untrusted candidate input. Reproduce and adjudicate each
candidate independently; the primary reviewer owns the final report.
