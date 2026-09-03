import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from worklore import WorkloreError, landing


class ReviewedPushTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.remote = self.root / "remote.git"
        self.repository = self.root / "repository"
        self._git("init", "--bare", str(self.remote), cwd=self.root)
        self._git("init", "-b", "main", str(self.repository), cwd=self.root)
        self._git("config", "user.name", "Worklore Test", cwd=self.repository)
        self._git("config", "user.email", "test@example.invalid", cwd=self.repository)
        (self.repository / "tracked.txt").write_text("initial\n", encoding="utf-8")
        self._git("add", "tracked.txt", cwd=self.repository)
        self._git("commit", "-m", "initial", cwd=self.repository)
        self._git("remote", "add", "origin", str(self.remote), cwd=self.repository)
        self._git("push", "--set-upstream", "origin", "main", cwd=self.repository)
        self.original_directory = Path.cwd()
        os.chdir(self.repository)

    def tearDown(self):
        os.chdir(self.original_directory)
        self.temporary.cleanup()

    def _git(self, *arguments, cwd=None):
        return subprocess.run(
            ["git", *arguments],
            cwd=cwd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ).stdout.strip()

    def _commit(self, content, message):
        (self.repository / "tracked.txt").write_text(content, encoding="utf-8")
        self._git("add", "tracked.txt", cwd=self.repository)
        self._git("commit", "-m", message, cwd=self.repository)
        return self._git("rev-parse", "HEAD", cwd=self.repository)

    def test_stages_commits_and_pushes_exact_reviewed_snapshot_on_default_branch(self):
        original_head = self._git("rev-parse", "HEAD", cwd=self.repository)
        (self.repository / "tracked.txt").write_text("reviewed\n", encoding="utf-8")
        (self.repository / "new.txt").write_text("included\n", encoding="utf-8")
        snapshot = landing.reviewed_snapshot()

        committed_head = landing.land_reviewed(
            original_head, snapshot, "refactor: land reviewed snapshot"
        )

        self.assertEqual(
            self._git("rev-parse", "refs/heads/main", cwd=self.remote),
            committed_head,
        )
        self.assertEqual(
            self._git("rev-parse", "HEAD^", cwd=self.repository), original_head
        )
        self.assertEqual(
            (self.repository / "tracked.txt").read_text(encoding="utf-8"),
            "reviewed\n",
        )
        self.assertEqual(
            (self.repository / "new.txt").read_text(encoding="utf-8"),
            "included\n",
        )
        self.assertEqual(
            self._git("status", "--porcelain=v1", cwd=self.repository), ""
        )

    def test_rejects_changed_snapshot_before_staging_commit_or_push(self):
        original_head = self._git("rev-parse", "HEAD", cwd=self.repository)
        (self.repository / "tracked.txt").write_text("reviewed\n", encoding="utf-8")
        snapshot = landing.reviewed_snapshot()
        (self.repository / "tracked.txt").write_text("changed again\n", encoding="utf-8")

        with self.assertRaisesRegex(WorkloreError, "expected snapshot"):
            landing.land_reviewed(
                original_head, snapshot, "refactor: must not land"
            )

        self.assertEqual(
            self._git("rev-parse", "HEAD", cwd=self.repository), original_head
        )
        self.assertEqual(
            self._git("rev-parse", "refs/heads/main", cwd=self.remote), original_head
        )
        self.assertEqual(
            self._git("diff", "--cached", "--name-only", cwd=self.repository), ""
        )

    def test_snapshot_binds_untracked_file_content(self):
        original_head = self._git("rev-parse", "HEAD", cwd=self.repository)
        untracked = self.repository / "new.txt"
        untracked.write_text("reviewed\n", encoding="utf-8")
        snapshot = landing.reviewed_snapshot()
        untracked.write_text("changed\n", encoding="utf-8")

        with self.assertRaisesRegex(WorkloreError, "expected snapshot"):
            landing.land_reviewed(
                original_head, snapshot, "refactor: must not land"
            )

        self.assertEqual(
            self._git("diff", "--cached", "--name-only", cwd=self.repository), ""
        )

    def test_snapshot_identity_is_stable_across_complete_staging(self):
        (self.repository / "tracked.txt").write_text("reviewed\n", encoding="utf-8")
        (self.repository / "new.txt").write_text("included\n", encoding="utf-8")
        snapshot = landing.reviewed_snapshot()

        self._git("add", "--all", cwd=self.repository)

        self.assertEqual(landing.reviewed_snapshot(), snapshot)

    @unittest.skipIf(os.name == "nt", "symlink creation is privilege-dependent")
    def test_snapshot_distinguishes_untracked_file_types(self):
        path = self.repository / "new.txt"
        path.symlink_to("target")
        symlink_snapshot = landing.reviewed_snapshot()
        path.unlink()
        path.write_text("target", encoding="utf-8")
        path.chmod(0o777)

        self.assertNotEqual(landing.reviewed_snapshot(), symlink_snapshot)

    def test_rejects_remote_drift_before_staging_or_commit(self):
        original_head = self._git("rev-parse", "HEAD", cwd=self.repository)
        (self.repository / "tracked.txt").write_text(
            "local reviewed\n", encoding="utf-8"
        )
        snapshot = landing.reviewed_snapshot()
        other = self.root / "other"
        self._git("clone", str(self.remote), str(other), cwd=self.root)
        self._git("config", "user.name", "Worklore Test", cwd=other)
        self._git("config", "user.email", "test@example.invalid", cwd=other)
        (other / "tracked.txt").write_text("remote change\n", encoding="utf-8")
        self._git("add", "tracked.txt", cwd=other)
        self._git("commit", "-m", "remote change", cwd=other)
        remote_head = self._git("rev-parse", "HEAD", cwd=other)
        self._git("push", "origin", "main", cwd=other)

        with self.assertRaisesRegex(WorkloreError, "must equal its remote branch"):
            landing.land_reviewed(
                original_head, snapshot, "refactor: must not land"
            )

        self.assertEqual(
            self._git("rev-parse", "HEAD", cwd=self.repository), original_head
        )
        self.assertEqual(
            self._git("rev-parse", "refs/heads/main", cwd=self.remote), remote_head
        )
        self.assertEqual(
            self._git("diff", "--cached", "--name-only", cwd=self.repository), ""
        )

    def test_pushes_exactly_one_clean_reviewed_commit_to_existing_upstream(self):
        head = self._commit("reviewed\n", "reviewed")

        landing.push_reviewed(head)

        self.assertEqual(
            self._git("rev-parse", "refs/heads/main", cwd=self.remote), head
        )

    def test_rejects_wrong_head_and_dirty_worktree(self):
        head = self._commit("reviewed\n", "reviewed")
        with self.assertRaisesRegex(WorkloreError, "does not equal"):
            landing.push_reviewed("0" * len(head))

        (self.repository / "untracked.txt").write_text("dirty\n", encoding="utf-8")
        with self.assertRaisesRegex(WorkloreError, "must be clean"):
            landing.push_reviewed(head)

    def test_rejects_more_than_one_commit_ahead(self):
        self._commit("first\n", "first")
        head = self._commit("second\n", "second")

        with self.assertRaisesRegex(WorkloreError, "exactly one commit ahead"):
            landing.push_reviewed(head)


if __name__ == "__main__":
    unittest.main()
