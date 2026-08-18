import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from worklore import audit


class PacketTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def packet(self, content=b"# Review packet\n\nSafe evidence.\n"):
        path = self.root / "packet.md"
        path.write_bytes(content)
        return path

    def test_reads_exact_bounded_bytes(self):
        content = b"# Review packet\r\n\xff\n"
        self.assertEqual(audit.read_packet(self.packet(content)), content)
        with mock.patch.object(audit, "MAX_PACKET_BYTES", 4):
            with self.assertRaisesRegex(audit.CoReviewError, "larger"):
                audit.read_packet(self.packet(b"12345"))

    def test_rejects_non_regular_and_empty_packets(self):
        with self.assertRaisesRegex(audit.CoReviewError, "regular file"):
            audit.read_packet(self.root)
        with self.assertRaisesRegex(audit.CoReviewError, "empty"):
            audit.read_packet(self.packet(b" \n"))

    @unittest.skipIf(os.name == "nt", "symlink creation is not portable on Windows")
    def test_rejects_symbolic_links(self):
        target = self.packet()
        link = self.root / "link.md"
        link.symlink_to(target)
        with self.assertRaisesRegex(audit.CoReviewError, "symbolic link"):
            audit.read_packet(link)

    def test_obvious_credentials_fail_closed(self):
        values = (
            b"-----BEGIN PRIVATE " + b"KEY-----",
            b"AK" + b"IA" + b"0123456789ABCDEF",
            b"password=" + b"abcdefghijklmnopqrstuvwx",
        )
        for value in values:
            with self.subTest(value=value[:12]):
                with self.assertRaisesRegex(audit.CoReviewError, "credential"):
                    audit.reject_obvious_secrets(value)
        audit.reject_obvious_secrets(b"password = example")


class ProviderBoundaryTests(unittest.TestCase):
    def test_provider_resolution_uses_path_only(self):
        with mock.patch("worklore.audit.shutil.which", return_value="/bin/claude"):
            self.assertEqual(
                audit.resolve_provider("claude"), str(Path("/bin/claude").resolve())
            )
        with mock.patch("worklore.audit.shutil.which", return_value=None):
            with self.assertRaisesRegex(audit.CoReviewError, "PATH"):
                audit.resolve_provider("claude")

    def test_provider_commands_preserve_narrow_authority(self):
        claude = audit._claude_command("claude", "policy")
        self.assertEqual(claude[claude.index("--tools") + 1], "")
        self.assertIn("--safe-mode", claude)
        self.assertNotIn("--add-dir", claude)

        agy = audit._agy_command("agy")
        self.assertIn("--sandbox", agy)
        self.assertEqual(agy[agy.index("--input-format") + 1], "stream-json")
        self.assertEqual(agy[agy.index("--output-format") + 1], "stream-json")
        self.assertEqual(agy[agy.index("--print") + 1], "")
        self.assertNotIn("--continue", agy)

    def test_provider_runs_in_ephemeral_directory_with_exact_packet(self):
        packet = b"# Packet\r\nexact bytes\n"
        for provider in ("claude", "agy"):
            with self.subTest(provider=provider):
                observed = None

                def fake_run(command, *, cwd, input_bytes=None):
                    nonlocal observed
                    observed = cwd
                    self.assertEqual(
                        [path.name for path in cwd.iterdir()],
                        [audit.PACKET_FILENAME],
                    )
                    self.assertEqual((cwd / audit.PACKET_FILENAME).read_bytes(), packet)
                    if provider == "claude":
                        self.assertEqual(input_bytes, packet)
                        return "No candidate findings."
                    assert input_bytes is not None
                    payload = json.loads(input_bytes)
                    self.assertEqual(payload["type"], "user")
                    content = payload["message"]["content"]
                    self.assertTrue(content.startswith("policy\n\n"))
                    self.assertTrue(content.endswith(packet.decode("utf-8")))
                    return json.dumps(
                        {
                            "event": "result",
                            "result": {
                                "status": "SUCCESS",
                                "response": "No candidate findings.",
                            },
                        }
                    )

                with mock.patch("worklore.audit.review_policy", return_value="policy"):
                    with mock.patch("worklore.audit._run", side_effect=fake_run):
                        result = audit.invoke_provider(provider, provider, packet)
                self.assertEqual(result, "No candidate findings.")
                assert observed is not None
                self.assertFalse(observed.exists())

    def test_timeout_and_nonzero_exit_are_explicit(self):
        timeout = subprocess.TimeoutExpired("claude", 600)
        with mock.patch("worklore.audit.subprocess.run", side_effect=timeout):
            with self.assertRaisesRegex(audit.CoReviewError, "timed out"):
                audit._run(["claude"], cwd=Path.cwd())

        failed = subprocess.CompletedProcess(["agy"], 3, b"", b"failure")
        with mock.patch("worklore.audit.subprocess.run", return_value=failed):
            with self.assertRaisesRegex(audit.CoReviewError, "code 3"):
                audit._run(["agy"], cwd=Path.cwd())

        empty = subprocess.CompletedProcess(["agy"], 0, b"", b"permission denied")
        with mock.patch("worklore.audit.subprocess.run", return_value=empty):
            with self.assertRaisesRegex(audit.CoReviewError, "permission denied"):
                audit._run(["agy"], cwd=Path.cwd())

    def test_agy_stream_failures_are_explicit(self):
        with self.assertRaisesRegex(audit.CoReviewError, "UTF-8"):
            audit._agy_input("policy", b"\xff")
        failure = json.dumps(
            {
                "event": "result",
                "result": {"status": "ERROR", "response": "provider failed"},
            }
        )
        with self.assertRaisesRegex(audit.CoReviewError, "provider failed"):
            audit._agy_result(failure)

    def test_provider_execution_never_inherits_stdin(self):
        completed = subprocess.CompletedProcess(["provider"], 0, b"audit", b"")
        with mock.patch("worklore.audit.subprocess.run", return_value=completed) as run:
            audit._run(["agy"], cwd=Path.cwd())
        call = run.call_args
        assert call is not None
        self.assertEqual(call.kwargs["stdin"], subprocess.DEVNULL)

        with mock.patch("worklore.audit.subprocess.run", return_value=completed) as run:
            audit._run(["claude"], cwd=Path.cwd(), input_bytes=b"packet")
        call = run.call_args
        assert call is not None
        self.assertIsNone(call.kwargs["stdin"])
        self.assertEqual(call.kwargs["input"], b"packet")

    def test_setting_selects_one_provider_and_hashes_exact_bytes(self):
        packet = b"# Packet\r\nexact bytes\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "packet.md"
            path.write_bytes(packet)
            with mock.patch(
                "worklore.audit.load_settings", return_value={"co_reviewer": "agy"}
            ):
                with mock.patch(
                    "worklore.audit.resolve_provider", return_value="agy"
                ) as resolve:
                    with mock.patch(
                        "worklore.audit.invoke_provider", return_value="audit"
                    ) as invoke:
                        result = audit.co_review(path)

        self.assertEqual(result["provider"], "agy")
        self.assertEqual(result["snapshotSha256"], hashlib.sha256(packet).hexdigest())
        self.assertEqual(result["audit"], "audit")
        resolve.assert_called_once_with("agy")
        invoke.assert_called_once_with("agy", "agy", packet)

    def test_disabled_setting_never_invokes_a_provider(self):
        with mock.patch(
            "worklore.audit.load_settings", return_value={"co_reviewer": "none"}
        ):
            with mock.patch("worklore.audit.read_packet") as read_packet:
                result = audit.co_review(Path("unused"))
        self.assertEqual(result, {"provider": "none", "status": "disabled"})
        read_packet.assert_not_called()


if __name__ == "__main__":
    unittest.main()
