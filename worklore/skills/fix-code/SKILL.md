---
name: fix-code
description: Verify and fix code-review findings according to the configured addressing policy without staging changes, while preserving the existing Git index.
---

# Fix Code

Treat each finding as a hypothesis. Verify it against the current code,
instructions, call sites, and relevant checks before editing.

## Configured policy

Before editing, read `~/.worklore/settings.json` and resolve `address_mode`:

- `default`: fix only verified merge blockers.
- `strict`: fix every verified actionable finding, including non-blocking
  maintainability findings.

If the settings file is missing or malformed, or the value is unsupported,
stop before editing and report the configuration error. Do not infer a default,
edit settings, or accept an invocation argument as a substitute. The setting
selects the policy; this skill defines what each policy means.

## Workflow

1. Resolve the configured policy and use the most recent review report when the
   user refers to the previous or latest review.
2. Capture the working-tree state and an index fingerprint. Preserve every
   existing user change and staged byte exactly.
3. Reproduce each in-scope finding. Reject obsolete, speculative, incorrect, or
   scope-expanding findings with evidence.
4. Apply the smallest verified correction in the working tree. Never run
   `git add`, commit, push, reset, restore, or rewrite history.
5. Run proportionate checks from the affected application directory.
6. Confirm the index fingerprint is unchanged and report fixes, rejections,
   checks, external prerequisites, and unstaged paths.
