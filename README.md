# Worklore

Small, opinionated engineering workflows for coding agents, distributed as a
user-level tool. The current package installs them into Codex; consuming
repositories require no configuration, vendoring, submodules, or dependencies.

```text
skills    = stable behavior
settings  = user preference
package   = cross-device distribution
```

## Install

`worklore` is installed with [uv](https://docs.astral.sh/uv/), which supports
macOS, Linux, and Windows. Install `uv` once per machine:

macOS with Homebrew:

```bash
brew install uv
```

Linux or macOS with the official installer:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows with PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Open a new terminal if requested, then verify the installation:

```bash
uv --version
```

Install and sync `worklore`:

```bash
uv tool install "worklore @ git+https://github.com/melonmochi/worklore.git"
uv tool update-shell
```

Open a new terminal so the updated `PATH` takes effect, then run:

```bash
worklore sync
worklore status
```

Update explicitly:

```bash
uv tool upgrade worklore
worklore sync
```

`sync` copies packaged skills to Codex's user-level skill directory,
`$HOME/.agents/skills`. It never deletes unrelated skills. If same-name skills were
installed manually, move them aside before the first sync.

External audits use the package's Python standard-library runner on macOS,
Linux, and Windows; no platform-specific audit binary is bundled.

## Configure

Settings live at `~/.worklore/settings.json`. Initial values are:

```json
{
  "co_reviewer": "none",
  "address_mode": "default"
}
```

```bash
worklore status
worklore config
worklore set co-reviewer VALUE  # none, claude, or agy
worklore set address-mode VALUE # default or strict
```

Selecting `claude` invokes the Claude Code CLI directly and uses its existing
OAuth session. `worklore` does not store provider credentials; a missing or
unauthenticated provider fails explicitly.

The installed skills expose stable invocations:

```text
/prune-code
/review-code
/fix-code
/land-code
/close-code
/sanitize-code
```

## Develop

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q worklore tests
git diff --check
```
