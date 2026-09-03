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
