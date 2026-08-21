import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from worklore import cli


class IsolatedHomeTestCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.home = self.root / "home"
        self.skills_directory = self.home / ".agents" / "skills"
        self.home.mkdir()
        self.home_path = mock.patch(
            "worklore.cli.Path.home", return_value=self.home
        )
        self.package_version = mock.patch(
            "worklore.cli.package_version", return_value="test-version"
        )
        self.home_path.start()
        self.package_version.start()

    def tearDown(self):
        self.package_version.stop()
        self.home_path.stop()
        self.temporary.cleanup()

    def write_settings(self, value):
        path = cli.settings_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")


class SettingsTests(IsolatedHomeTestCase):
    def test_initial_settings_use_safe_defaults(self):
        expected = {"co_reviewer": "none", "address_mode": "default"}
        self.assertEqual(cli.load_settings(create=True), expected)
        self.assertEqual(
            json.loads(cli.settings_path().read_text(encoding="utf-8")),
            expected,
        )

    def test_all_allowed_setting_states_round_trip(self):
        cli.load_settings(create=True)
        for reviewer in ("none", "claude", "agy"):
            updated = cli.set_setting("co-reviewer", reviewer)
            self.assertEqual(updated["co_reviewer"], reviewer)
            self.assertEqual(cli.load_settings()["co_reviewer"], reviewer)
        for mode in ("default", "strict"):
            updated = cli.set_setting("address-mode", mode)
            self.assertEqual(updated["address_mode"], mode)
            self.assertEqual(cli.load_settings()["address_mode"], mode)

    def test_interactive_config_writes_the_same_file(self):
        cli.load_settings(create=True)
        with mock.patch("builtins.input", side_effect=["agy", "default"]):
            self.assertEqual(
                cli.configure(),
                {"co_reviewer": "agy", "address_mode": "default"},
            )
        self.assertEqual(
            json.loads(cli.settings_path().read_text(encoding="utf-8")),
            {"co_reviewer": "agy", "address_mode": "default"},
        )

    def test_cancelled_initial_config_does_not_create_settings(self):
        with mock.patch("builtins.input", side_effect=EOFError):
            with self.assertRaisesRegex(cli.WorkloreError, "not changed"):
                cli.configure()
        self.assertFalse(cli.settings_path().exists())

    def test_status_is_read_only_before_initialization(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            cli.show_status()
        self.assertIn("settings.json (not initialized)", output.getvalue())
        self.assertFalse(cli.settings_path().exists())

    def test_invalid_or_unknown_settings_fail_explicitly(self):
        invalid_values = (
            {"co_reviewer": "other", "address_mode": "strict"},
            {"co_reviewer": "none"},
            {
                "co_reviewer": "none",
                "address_mode": "strict",
                "profile": "extra",
            },
        )
        for value in invalid_values:
            with self.subTest(value=value):
                self.write_settings(value)
                with self.assertRaises(cli.WorkloreError):
                    cli.load_settings()

    def test_unknown_name_and_invalid_value_return_errors(self):
        with self.assertRaises(cli.WorkloreError):
            cli.set_setting("provider", "claude")
        with self.assertRaises(cli.WorkloreError):
            cli.set_setting("co-reviewer", "other")


class SyncTests(IsolatedHomeTestCase):
    def test_sync_uses_the_codex_user_skill_location(self):
        self.assertEqual(cli.codex_skills_path(), self.skills_directory)

    def test_sync_installs_ordinary_skills_and_preserves_unrelated_skill(self):
        unrelated = self.skills_directory / "my-local-skill"
        unrelated.mkdir(parents=True)
        marker = unrelated / "marker.txt"
        marker.write_text("mine", encoding="utf-8")

        installed, removed, destination = cli.sync_skills()

        self.assertEqual(destination, self.skills_directory)
        self.assertEqual(removed, [])
        self.assertEqual(
            installed,
            [
                "close-code",
                "fix-code",
                "land-code",
                "prune-code",
                "review-code",
                "sanitize-code",
            ],
        )
        for name in installed:
            skill = destination / name
            self.assertTrue((skill / "SKILL.md").is_file())
            self.assertFalse(skill.is_symlink())
        self.assertEqual(marker.read_text(encoding="utf-8"), "mine")

        manifest = json.loads(
            (destination / cli.MANIFEST_NAME).read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["skills"], installed)

    def test_sync_refuses_an_unmanaged_collision_without_partial_install(self):
        collision = self.skills_directory / "review-code"
        collision.mkdir(parents=True)
        marker = collision / "marker.txt"
        marker.write_text("unmanaged", encoding="utf-8")

        with self.assertRaisesRegex(cli.WorkloreError, "unmanaged"):
            cli.sync_skills()

        self.assertEqual(marker.read_text(encoding="utf-8"), "unmanaged")
        self.assertFalse((self.skills_directory / "land-code").exists())

    def test_sync_replaces_owned_skills_and_removes_only_stale_owned_skill(self):
        cli.sync_skills()
        skills = self.skills_directory
        review = skills / "review-code" / "SKILL.md"
        review.write_text("locally changed", encoding="utf-8")

        stale = skills / "address-code-review"
        stale.mkdir()
        (stale / "marker.txt").write_text("old", encoding="utf-8")
        unrelated = skills / "unrelated"
        unrelated.mkdir()
        (unrelated / "marker.txt").write_text("mine", encoding="utf-8")

        manifest_path = skills / cli.MANIFEST_NAME
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["skills"].append("address-code-review")
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        _, removed, _ = cli.sync_skills()

        self.assertEqual(removed, ["address-code-review"])
        self.assertFalse(stale.exists())
        self.assertEqual(
            (unrelated / "marker.txt").read_text(encoding="utf-8"), "mine"
        )
        self.assertIn("# Review Code", review.read_text(encoding="utf-8"))

    def test_post_commit_stage_cleanup_cannot_fail_sync(self):
        def cleanup(_path, *, ignore_errors=False):
            if not ignore_errors:
                raise OSError("cleanup failed")

        with mock.patch("worklore.cli.shutil.rmtree", side_effect=cleanup):
            installed, removed, destination = cli.sync_skills()

        self.assertEqual(len(installed), 6)
        self.assertEqual(removed, [])
        self.assertTrue((destination / cli.MANIFEST_NAME).is_file())
        self.assertTrue((destination / "review-code" / "SKILL.md").is_file())

    def test_status_detects_managed_skill_drift(self):
        cli.sync_skills()
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            cli.show_status()
        self.assertIn("sync: current", output.getvalue())

        (self.skills_directory / "review-code" / "SKILL.md").write_text(
            "locally changed", encoding="utf-8"
        )
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            cli.show_status()
        self.assertIn("sync: sync needed", output.getvalue())

    def test_internal_co_review_command_is_not_in_public_help(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            with self.assertRaises(SystemExit) as result:
                cli.main(["--help"])
        self.assertEqual(result.exception.code, 0)
        self.assertNotIn("_co-review", output.getvalue())

    def test_internal_co_review_command_dispatches_to_runner(self):
        with mock.patch("worklore.audit.main", return_value=7) as audit_main:
            self.assertEqual(cli.main(["_co-review", "--packet", "packet.md"]), 7)
        audit_main.assert_called_once_with(["--packet", "packet.md"])


class SkillContractTests(unittest.TestCase):
    def skill_text(self, name):
        return (
            Path(__file__).parents[1]
            / "worklore"
            / "skills"
            / name
            / "SKILL.md"
        ).read_text(encoding="utf-8")

    def test_public_skills_do_not_expose_deployment_arguments(self):
        self.assertNotIn("--with-claude", self.skill_text("review-code"))
        self.assertNotIn("--mode", self.skill_text("fix-code"))

    def test_close_code_contains_only_child_orchestration_knowledge(self):
        close_code = self.skill_text("close-code").lower()
        for forbidden in ("claude", "agy", "strict", "default"):
            self.assertNotIn(forbidden, close_code)

    def test_close_code_pauses_for_approval_and_stops_on_incomplete_review(self):
        close_code = self.skill_text("close-code")
        self.assertIn("co-review pauses before provider\n   invocation", close_code)
        self.assertIn("resume at the co-review invocation", close_code)
        self.assertIn("complete browser authentication", close_code)
        self.assertIn("one allowed replacement invocation", close_code)
        self.assertIn("Do\n   not run `fix-code` or `land-code` while paused", close_code)
        self.assertIn(
            "remains incomplete after its allowed authentication\n   recovery",
            close_code,
        )


if __name__ == "__main__":
    unittest.main()
