---
name: sanitize-code
description: Inspect the current repository for likely credentials, private information, or local/private environment residue before publication, and report findings without modifying files. Use for publication-safety checks, not automatic sanitization or compliance analysis.
---

# Sanitize Code

Read-only inspection of current publication candidates for accidental disclosure.
Do not edit, redact, stage, commit, alter ignore rules/configuration or scan
history. Do not execute inspected files, test credentials, contact discovered
endpoints or transmit suspected sensitive material.

Read applicable instructions. Include tracked and non-ignored untracked files;
exclude Git internals, caches/build output and ignored local files unless
intended for publication. Inspect relevant contents, filenames and symlink
targets for credentials, private keys, personal data, internal URLs/hosts,
private absolute paths and copied private context.

Treat search matches as leads: inspect context rather than labeling every name,
email, URL or example private. Never reproduce a complete suspected credential;
identify its kind/location and, only if needed, a short masked prefix.

Report only:

- `BLOCKER`: likely credentials or clearly sensitive data.
- `REVIEW`: personal/internal information that may be intentionally public.

Give each finding's path/location, what appears sensitive and why publication
is questionable. The owner decides ambiguous cases. With no findings, say no
concerning residue was found in the inspected current contents; do not imply
a broader guarantee.
