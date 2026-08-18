"""Transport one explicitly prepared packet to the configured co-reviewer."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from importlib import resources
from pathlib import Path
from typing import Sequence

from .cli import WorkloreError, load_settings


MAX_PACKET_BYTES = 1_500_000
AUTH_STATUS_TIMEOUT_SECONDS = 30
PROVIDER_TIMEOUT_SECONDS = 10 * 60
PACKET_FILENAME = "REVIEW_PACKET.md"

SECRET_PATTERNS = (
    (
        "private key",
        re.compile(rb"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----"),
    ),
    (
        "known API token",
        re.compile(
            rb"\b(?:AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{32,}|"
            rb"sk-ant-[A-Za-z0-9_-]{20,}|sk-(?:proj-)?[A-Za-z0-9_-]{32,})\b"
        ),
    ),
    (
        "assigned credential",
        re.compile(
            rb"(?:api[_-]?key|client[_-]?secret|access[_-]?token|password)"
            rb"\s*[:=]\s*[\"']?[^\s\"']{20,}",
            re.IGNORECASE,
        ),
    ),
)


class CoReviewError(Exception):
    """An expected packet-safety or provider-execution error."""


class ClaudeAuthorizationRequired(CoReviewError):
    """Claude login did not complete before provider invocation."""


def read_packet(path: Path) -> bytes:
    if path.is_symlink():
        raise CoReviewError(f"packet must not be a symbolic link: {path}")
    if not path.is_file():
        raise CoReviewError(f"packet is not a regular file: {path}")
    with path.open("rb") as stream:
        packet = stream.read(MAX_PACKET_BYTES + 1)
    if len(packet) > MAX_PACKET_BYTES:
        raise CoReviewError(
            f"packet is larger than {MAX_PACKET_BYTES} bytes: {path}"
        )
    if not packet.strip():
        raise CoReviewError("packet is empty")
    return packet


def reject_obvious_secrets(packet: bytes) -> None:
    detected = [label for label, pattern in SECRET_PATTERNS if pattern.search(packet)]
    if detected:
        raise CoReviewError(
            "potential credential material detected "
            f"({', '.join(detected)}); sanitize the packet before sending"
        )


def review_policy() -> str:
    return (
        resources.files("worklore")
        .joinpath("skills", "review-code", "references", "co-review-prompt.md")
        .read_text(encoding="utf-8")
    )


def resolve_provider(provider: str) -> str:
    executable = shutil.which(provider)
    if executable is None:
        raise CoReviewError(f"{provider} executable was not found on PATH")
    return str(Path(executable).resolve())


def _claude_auth_status(executable: str) -> bool:
    command = [executable, "auth", "status", "--json"]
    try:
        completed = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=AUTH_STATUS_TIMEOUT_SECONDS,
            check=False,
        )
    except FileNotFoundError as error:
        raise CoReviewError(f"executable not found: {executable}") from error
    except subprocess.TimeoutExpired as error:
        raise CoReviewError(
            "claude auth status timed out after "
            f"{AUTH_STATUS_TIMEOUT_SECONDS} seconds"
        ) from error

    output = completed.stdout.decode("utf-8", errors="replace").strip()
    try:
        status = json.loads(output)
    except json.JSONDecodeError as error:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        suffix = f": {detail}" if detail else ""
        raise CoReviewError(
            f"claude auth status returned invalid JSON{suffix}"
        ) from error
    if not isinstance(status, dict) or not isinstance(status.get("loggedIn"), bool):
        raise CoReviewError("claude auth status omitted loggedIn")
    return status["loggedIn"]


def _ensure_claude_authenticated(executable: str) -> None:
    try:
        if _claude_auth_status(executable):
            return
    except CoReviewError as error:
        raise ClaudeAuthorizationRequired(
            f"could not verify Claude authentication: {error}"
        ) from error

    raise ClaudeAuthorizationRequired(
        "Claude is logged out; run `claude auth login` in a "
        "user-controlled terminal, keep the one-time authorization code "
        "in that terminal, then resume"
    )


def _run(command: Sequence[str], *, cwd: Path, input_bytes: bytes | None = None) -> str:
    try:
        completed = subprocess.run(
            list(command),
            cwd=cwd,
            input=input_bytes,
            stdin=subprocess.DEVNULL if input_bytes is None else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=PROVIDER_TIMEOUT_SECONDS,
            check=False,
        )
    except FileNotFoundError as error:
        raise CoReviewError(f"executable not found: {command[0]}") from error
    except subprocess.TimeoutExpired as error:
        raise CoReviewError(
            f"{Path(command[0]).name} timed out after "
            f"{PROVIDER_TIMEOUT_SECONDS} seconds"
        ) from error

    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).decode(
            "utf-8", errors="replace"
        ).strip()
        if len(detail) > 4_000:
            detail = f"{detail[:4_000]}..."
        suffix = f": {detail}" if detail else ""
        raise CoReviewError(
            f"{Path(command[0]).name} exited with code "
            f"{completed.returncode}{suffix}"
        )
    output = completed.stdout.decode("utf-8", errors="replace").strip()
    if not output:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        if len(detail) > 4_000:
            detail = f"{detail[:4_000]}..."
        suffix = f": {detail}" if detail else ""
        raise CoReviewError(f"{Path(command[0]).name} returned no output{suffix}")
    return output


def _claude_command(executable: str, policy: str) -> list[str]:
    return [
        executable, "--print",
        "--model", "sonnet",
        "--effort", "high",
        "--safe-mode",
        "--permission-mode", "dontAsk",
        "--tools", "",
        "--disable-slash-commands",
        "--strict-mcp-config",
        "--no-session-persistence",
        "--output-format", "text",
        "--system-prompt", policy,
    ]


def _agy_command(executable: str) -> list[str]:
    return [
        executable,
        "--input-format", "stream-json",
        "--output-format", "stream-json",
        "--print-timeout", "10m",
        "--sandbox",
        "--disable-slash-commands",
        "--effort", "high",
        "--print", "",
    ]


def _agy_input(policy: str, packet: bytes) -> bytes:
    try:
        packet_text = packet.decode("utf-8")
    except UnicodeDecodeError as error:
        raise CoReviewError("agy requires a UTF-8 review packet") from error
    message = {
        "type": "user",
        "message": {
            "role": "user",
            "content": f"{policy}\n\n# Frozen review packet\n\n{packet_text}",
        },
    }
    return (json.dumps(message, ensure_ascii=False) + "\n").encode("utf-8")


def _agy_result(output: str) -> str:
    terminal: object = None
    for line in output.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError as error:
            raise CoReviewError("agy returned invalid stream-json") from error
        if isinstance(event, dict) and event.get("event") == "result":
            terminal = event.get("result")
    if not isinstance(terminal, dict):
        raise CoReviewError("agy returned no terminal result")
    response = terminal.get("response")
    if terminal.get("status") != "SUCCESS":
        detail = (
            response
            if isinstance(response, str) and response.strip()
            else "unknown error"
        )
        raise CoReviewError(f"agy audit failed: {detail}")
    if not isinstance(response, str) or not response.strip():
        raise CoReviewError("agy returned an empty audit")
    return response.strip()


def invoke_provider(provider: str, executable: str, packet: bytes) -> str:
    policy = review_policy()
    with tempfile.TemporaryDirectory(prefix="worklore-co-review-") as name:
        directory = Path(name)
        (directory / PACKET_FILENAME).write_bytes(packet)
        if provider == "claude":
            command = _claude_command(executable, policy)
            input_bytes = packet
        elif provider == "agy":
            command = _agy_command(executable)
            input_bytes = _agy_input(policy, packet)
        else:
            raise CoReviewError(f"unsupported co-reviewer: {provider}")
        result = _run(command, cwd=directory, input_bytes=input_bytes)
    return _agy_result(result) if provider == "agy" else result


def co_review(packet_path: Path) -> dict[str, object]:
    provider = load_settings()["co_reviewer"]
    if provider == "none":
        return {"provider": provider, "status": "disabled"}
    executable: str | None = None
    if provider == "claude":
        executable = resolve_provider(provider)
        _ensure_claude_authenticated(executable)
    packet = read_packet(packet_path)
    reject_obvious_secrets(packet)
    digest = hashlib.sha256(packet).hexdigest()
    result: dict[str, object] = {
        "provider": provider,
        "snapshotSha256": digest,
    }
    if executable is None:
        executable = resolve_provider(provider)
    result["audit"] = invoke_provider(provider, executable, packet)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="worklore _co-review")
    parser.add_argument("--packet", type=Path, required=True)
    arguments = parser.parse_args(argv)
    try:
        print(json.dumps(co_review(arguments.packet), indent=2, ensure_ascii=False))
        return 0
    except ClaudeAuthorizationRequired as error:
        print(
            f"worklore co-review: authorization required: {error}",
            file=sys.stderr,
        )
        return 3
    except (CoReviewError, WorkloreError, OSError) as error:
        print(f"worklore co-review: error: {error}", file=sys.stderr)
        return 2
