---
name: sanitize-code
description: Inspect the current repository for likely credentials, private information, or local/private environment residue before publication, and report findings without modifying files. Use for publication-safety checks, not automatic sanitization or compliance analysis.
---

# Sanitize Code

Inspect publication-relevant contents in the current repository for obvious
accidental disclosure. This is an advisory, read-only inspection.

## Boundary

- Do not edit, redact, delete, rename, stage, or commit anything. Do not change
  ignore rules, configuration, or Git history.
- Inspect only the current repository state. Do not scan history or add
  machinery for possible future history scanning.
- Do not execute repository files, source configuration, test credentials, or
  contact discovered endpoints. Do not transmit suspected sensitive material
  to another reviewer or service.
- Never reproduce a complete suspected credential in the report. Identify its
  kind and location; use a short masked prefix only when needed to distinguish
  findings.

## Inspect

Read applicable repository instructions, then determine the current
publication candidates. In a Git repository, include tracked and untracked
non-ignored files. Exclude Git internals, dependency caches, build output, and
other generated material unless it is itself intended for publication. Do not
assume that ignored local files are publication candidates.

Inspect filenames, symlink targets, and relevant text or file types. Look
especially for:

- API keys, access tokens, passwords, private keys, credential files, and
  `.env`-style secrets;
- private email addresses, phone numbers, home addresses, or other clearly
  personal data;
- absolute local paths containing usernames or private directory names;
- private repository URLs, internal hostnames or endpoints, and accidental
  private company, customer, or project information;
- copied chats, prompts, fixtures, examples, tests, docs, or config containing
  real credentials or personal context.

Use small read-only searches for obvious private-key headers, known token
shapes, credential assignments, sensitive filenames, home-directory paths, and
internal-looking URLs. Treat matches as leads and inspect their context. Apply
normal semantic judgment to ambiguous personal or internal information. Do not
assume every name, email, URL, path, placeholder, or example is private.

## Report

If nothing concerning is found, say plainly that no concerning publication
residue was found in the current repository contents inspected.

Otherwise, report concise findings using only these severities:

- `BLOCKER`: likely credentials, private keys, passwords, tokens, or clearly
  sensitive data.
- `REVIEW`: personal or internal information that may or may not be
  intentionally public.

For every finding include:

```text
severity
path
line or nearby location
what appears private/sensitive
why it may be inappropriate for a public repository
```

Report exact locations where possible. Do not add confidence scores, expand
the severity taxonomy, flood the report with generic possibilities, or decide
that ambiguous information must be removed. The owner decides what to change.
