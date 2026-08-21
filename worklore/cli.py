from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from importlib import metadata, resources
from pathlib import Path
from typing import Any, Sequence

DEFAULT_SETTINGS = {
    "co_reviewer": "none",
    "address_mode": "default",
}
SETTING_VALUES = {
    "co_reviewer": ("none", "claude", "agy"),
    "address_mode": ("default", "strict"),
}
CLI_SETTING_NAMES = {
    "co-reviewer": "co_reviewer",
    "address-mode": "address_mode",
}
MANIFEST_NAME = ".worklore-manifest.json"
SKILL_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
GIT_OBJECT_ID = re.compile(r"^[0-9a-f]+$")


class WorkloreError(Exception):
    """An expected user-facing error."""


def package_version() -> str:
    return metadata.version("worklore")


def settings_path() -> Path:
    return Path.home() / ".worklore" / "settings.json"


def codex_skills_path() -> Path:
    return Path.home() / ".agents" / "skills"


def _validate_settings(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        raise WorkloreError("settings must be a JSON object")

    expected = set(SETTING_VALUES)
    actual = set(value)
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    if missing:
        raise WorkloreError(f"settings missing: {', '.join(missing)}")
    if unknown:
        raise WorkloreError(f"unknown settings: {', '.join(unknown)}")

    validated: dict[str, str] = {}
    for name, allowed in SETTING_VALUES.items():
        selected = value[name]
        if selected not in allowed:
            choices = ", ".join(allowed)
            raise WorkloreError(
                f"invalid {name}: {selected!r}; expected one of: {choices}"
            )
        validated[name] = selected
    return validated


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, indent=2)
            stream.write("\n")
        if os.name != "nt":
            temporary_path.chmod(0o600)
        os.replace(temporary_path, path)
    except BaseException:
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass
        raise


def load_settings(*, create: bool = False) -> dict[str, str]:
    path = settings_path()
    if not path.exists():
        if not create:
            raise WorkloreError(
                f"settings not found at {path}; run 'worklore sync' or "
                "'worklore config'"
            )
        save_settings(DEFAULT_SETTINGS)
        return dict(DEFAULT_SETTINGS)

    try:
        with path.open(encoding="utf-8") as stream:
            value = json.load(stream)
    except json.JSONDecodeError as error:
        raise WorkloreError(f"invalid JSON in {path}: {error}") from error
    return _validate_settings(value)


def save_settings(value: dict[str, str]) -> None:
    _write_json(settings_path(), _validate_settings(value))


def set_setting(cli_name: str, selected: str) -> dict[str, str]:
    try:
        name = CLI_SETTING_NAMES[cli_name]
    except KeyError as error:
        accepted = ", ".join(CLI_SETTING_NAMES)
        raise WorkloreError(
            f"unknown setting {cli_name!r}; expected one of: {accepted}"
        ) from error

    allowed = SETTING_VALUES[name]
    if selected not in allowed:
        choices = ", ".join(allowed)
        raise WorkloreError(
            f"invalid {cli_name}: {selected!r}; expected one of: {choices}"
        )

    current = load_settings(create=True)
    current[name] = selected
    save_settings(current)
    return current


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"package_version": None, "skills": []}

    try:
        with path.open(encoding="utf-8") as stream:
            value = json.load(stream)
    except json.JSONDecodeError as error:
        raise WorkloreError(f"invalid JSON in ownership manifest {path}: {error}") from error

    if not isinstance(value, dict) or set(value) != {"package_version", "skills"}:
        raise WorkloreError(f"invalid ownership manifest structure: {path}")
    if not isinstance(value["package_version"], str):
        raise WorkloreError(f"invalid package_version in ownership manifest: {path}")
    if not isinstance(value["skills"], list):
        raise WorkloreError(f"invalid skills list in ownership manifest: {path}")

    names = value["skills"]
    if (
        any(not isinstance(name, str) or not SKILL_NAME.fullmatch(name) for name in names)
        or len(names) != len(set(names))
    ):
        raise WorkloreError(f"invalid skill name in ownership manifest: {path}")
    return {"package_version": value["package_version"], "skills": list(names)}


def _packaged_skills() -> dict[str, Any]:
    root = resources.files("worklore").joinpath("skills")
    skills = {
        entry.name: entry
        for entry in root.iterdir()
        if entry.is_dir()
        and SKILL_NAME.fullmatch(entry.name)
        and entry.joinpath("SKILL.md").is_file()
    }
    if not skills:
        raise WorkloreError("the installed package contains no skills")
    return dict(sorted(skills.items()))


def _copy_resource_tree(source: Any, destination: Path) -> None:
    destination.mkdir()
    for child in source.iterdir():
        target = destination / child.name
        if child.is_dir():
            _copy_resource_tree(child, target)
            continue
        if not child.is_file():
            raise WorkloreError(f"unsupported packaged resource: {child}")
        with child.open("rb") as source_stream, target.open("wb") as target_stream:
            shutil.copyfileobj(source_stream, target_stream)


def _resource_tree_matches(source: Any, destination: Path) -> bool:
    if destination.is_symlink() or not destination.is_dir():
        return False

    source_entries = {child.name: child for child in source.iterdir()}
    destination_entries = {child.name: child for child in destination.iterdir()}
    if set(source_entries) != set(destination_entries):
        return False

    for name, child in source_entries.items():
        installed = destination_entries[name]
        if child.is_dir():
            if not _resource_tree_matches(child, installed):
                return False
        elif (
            not child.is_file()
            or installed.is_symlink()
            or not installed.is_file()
            or child.read_bytes() != installed.read_bytes()
        ):
            return False
    return True


def _path_exists(path: Path) -> bool:
    return os.path.lexists(path)


def _remove_path(path: Path) -> None:
    if path.is_symlink() or not path.is_dir():
        path.unlink()
    else:
        shutil.rmtree(path)


def sync_skills() -> tuple[list[str], list[str], Path]:
    load_settings(create=True)
    packaged = _packaged_skills()
    skills_directory = codex_skills_path()
    skills_directory.mkdir(parents=True, exist_ok=True)
    manifest_path = skills_directory / MANIFEST_NAME
    previous = _load_manifest(manifest_path)
    managed = set(previous["skills"])

    collisions = [
        name
        for name in packaged
        if _path_exists(skills_directory / name) and name not in managed
    ]
    if collisions:
        names = ", ".join(collisions)
        raise WorkloreError(
            f"refusing to replace unmanaged skill directories: {names}"
        )

    stage = Path(tempfile.mkdtemp(prefix=".worklore-sync-", dir=skills_directory))
    staged_new = stage / "new"
    staged_old = stage / "old"
    staged_new.mkdir()
    staged_old.mkdir()
    backups: list[str] = []
    installed: list[str] = []

    try:
        for name, source in packaged.items():
            _copy_resource_tree(source, staged_new / name)

        for name in sorted(managed):
            destination = skills_directory / name
            if _path_exists(destination):
                os.replace(destination, staged_old / name)
                backups.append(name)

        for name in packaged:
            os.replace(staged_new / name, skills_directory / name)
            installed.append(name)

        removed = sorted(managed - set(packaged))
        manifest = {
            "package_version": package_version(),
            "skills": list(packaged),
        }
        _write_json(manifest_path, manifest)
    except BaseException as error:
        rollback_errors: list[str] = []
        for name in reversed(installed):
            destination = skills_directory / name
            try:
                if _path_exists(destination):
                    _remove_path(destination)
            except OSError as rollback_error:
                rollback_errors.append(f"remove {name}: {rollback_error}")
        for name in reversed(backups):
            destination = skills_directory / name
            backup = staged_old / name
            try:
                if not _path_exists(destination) and _path_exists(backup):
                    os.replace(backup, destination)
            except OSError as rollback_error:
                rollback_errors.append(f"restore {name}: {rollback_error}")
        if rollback_errors:
            details = "; ".join(rollback_errors)
            raise WorkloreError(
                f"sync failed and rollback was incomplete; backups remain at "
                f"{stage}: {details}"
            ) from error
        shutil.rmtree(stage, ignore_errors=True)
        raise

    shutil.rmtree(stage, ignore_errors=True)
    return list(packaged), removed, skills_directory


def _select(name: str, choices: tuple[str, ...], current: str) -> str:
    prompt = f"{name} [{'/'.join(choices)}] ({current}): "
    while True:
        try:
            selected = input(prompt).strip()
        except (EOFError, KeyboardInterrupt) as error:
            raise WorkloreError("configuration cancelled; settings were not changed") from error
        if not selected:
            return current
        if selected in choices:
            return selected
        print(f"Invalid value. Choose one of: {', '.join(choices)}", file=sys.stderr)


def configure() -> dict[str, str]:
    path = settings_path()
    current = load_settings() if path.exists() else dict(DEFAULT_SETTINGS)
    updated = {
        "co_reviewer": _select(
            "co-reviewer", SETTING_VALUES["co_reviewer"], current["co_reviewer"]
        ),
        "address_mode": _select(
            "address-mode", SETTING_VALUES["address_mode"], current["address_mode"]
        ),
    }
    save_settings(updated)
    return updated


def _sync_state(manifest: dict[str, Any], packaged: dict[str, Any], root: Path) -> str:
    expected = list(packaged)
    installed = manifest["skills"]
    skills_match = all(
        _resource_tree_matches(packaged[name], root / name) for name in expected
    )
    if (
        manifest["package_version"] == package_version()
        and installed == expected
        and skills_match
    ):
        return "current"
    return "sync needed"


def show_status() -> None:
    path = settings_path()
    settings = load_settings() if path.exists() else None
    skills_directory = codex_skills_path()
    manifest = _load_manifest(skills_directory / MANIFEST_NAME)
    packaged = _packaged_skills()
    managed = ", ".join(manifest["skills"]) or "none"
    print(f"worklore {package_version()}")
    print(f"settings: {path}{'' if settings else ' (not initialized)'}")
    if settings:
        print(f"co-reviewer: {settings['co_reviewer']}")
        print(f"address-mode: {settings['address_mode']}")
    else:
        print("co-reviewer: not configured")
        print("address-mode: not configured")
    print(f"skills: {skills_directory}")
    print(f"managed: {managed}")
    print(f"sync: {_sync_state(manifest, packaged, skills_directory)}")


def _git_output(*arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise WorkloreError(detail)
    return result.stdout.strip()


def push_reviewed(expected_head: str) -> None:
    if _git_output("rev-parse", "--is-inside-work-tree") != "true":
        raise WorkloreError("current directory is not a Git working tree")

    branch = _git_output("symbolic-ref", "--quiet", "--short", "HEAD")
    head = _git_output("rev-parse", "--verify", "HEAD")
    if not GIT_OBJECT_ID.fullmatch(expected_head) or expected_head != head:
        raise WorkloreError(
            f"expected HEAD {expected_head!r} does not equal current HEAD {head}"
        )
    if _git_output("status", "--porcelain=v1", "--untracked-files=all"):
        raise WorkloreError("working tree must be clean before push")

    remote = _git_output("config", "--get", f"branch.{branch}.remote")
    merge_ref = _git_output("config", "--get", f"branch.{branch}.merge")
    if remote == "." or not merge_ref.startswith("refs/heads/"):
        raise WorkloreError("current branch must track a remote branch")
    upstream = _git_output(
        "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"
    )
    upstream_head = _git_output("rev-parse", "--verify", "@{upstream}")
    counts = _git_output(
        "rev-list", "--left-right", "--count", "@{upstream}...HEAD"
    ).split()
    if counts != ["0", "1"]:
        raise WorkloreError(
            "current branch must be exactly one commit ahead of its upstream "
            f"(found behind={counts[0] if counts else '?'}, "
            f"ahead={counts[1] if len(counts) > 1 else '?'})"
        )

    print(
        f"publishing {head} from {branch} to {upstream} "
        f"(previously {upstream_head})"
    )
    result = subprocess.run(
        ["git", "push", remote, f"HEAD:{merge_ref}"],
        check=False,
    )
    if result.returncode != 0:
        raise WorkloreError(f"git push failed with exit code {result.returncode}")

    remote_lines = _git_output("ls-remote", "--refs", remote, merge_ref).splitlines()
    expected_line = f"{head}\t{merge_ref}"
    if remote_lines != [expected_line]:
        raise WorkloreError(
            f"remote verification failed for {remote}/{merge_ref} after push"
        )
    if _git_output("status", "--porcelain=v1", "--untracked-files=all"):
        raise WorkloreError("working tree changed during push")
    print(f"published: {remote}/{merge_ref} = {head}")


def _push_reviewed_main(arguments: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(prog="worklore _push-reviewed")
    parser.add_argument("--expected-head", required=True)
    parsed = parser.parse_args(arguments)
    try:
        push_reviewed(parsed.expected_head)
    except (WorkloreError, OSError) as error:
        print(f"worklore: error: {error}", file=sys.stderr)
        return 2
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="worklore")
    parser.add_argument("--version", action="version", version=package_version())
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status", help="show settings and synchronization status")
    commands.add_parser("config", help="configure settings interactively")

    set_parser = commands.add_parser("set", help="set one preference")
    set_parser.add_argument("name", choices=tuple(CLI_SETTING_NAMES))
    set_parser.add_argument("value")

    commands.add_parser("sync", help="copy packaged skills into Codex")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    raw_arguments = list(sys.argv[1:] if argv is None else argv)
    if raw_arguments[:1] == ["_co-review"]:
        from .audit import main as audit_main

        return audit_main(raw_arguments[1:])
    if raw_arguments[:1] == ["_push-reviewed"]:
        return _push_reviewed_main(raw_arguments[1:])

    arguments = _parser().parse_args(raw_arguments)
    try:
        if arguments.command == "status":
            show_status()
        elif arguments.command == "config":
            updated = configure()
            print(
                "saved: "
                f"co-reviewer={updated['co_reviewer']}, "
                f"address-mode={updated['address_mode']}"
            )
        elif arguments.command == "set":
            updated = set_setting(arguments.name, arguments.value)
            internal_name = CLI_SETTING_NAMES[arguments.name]
            print(f"{arguments.name}: {updated[internal_name]}")
        elif arguments.command == "sync":
            installed, removed, destination = sync_skills()
            print(f"synced {len(installed)} skills to {destination}")
            if removed:
                print(f"removed previously managed skills: {', '.join(removed)}")
        else:
            raise AssertionError(f"unhandled command: {arguments.command}")
    except (WorkloreError, OSError) as error:
        print(f"worklore: error: {error}", file=sys.stderr)
        return 2
    return 0
