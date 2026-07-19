import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


class SkillDiscoveryTests(unittest.TestCase):
    def make_repo(self, directory, *skill_directories):
        repo = Path(directory) / "repo"
        scripts = repo / "scripts"
        scripts.mkdir(parents=True)
        for name in ("list-skills.sh", "link-skills.sh"):
            shutil.copy2(ROOT / "scripts" / name, scripts / name)

        for skill_directory in skill_directories:
            skill = repo / "skills" / skill_directory
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("---\nname: fixture\n---\n", encoding="utf-8")
        return repo

    def run_linker(self, repo, codex_home):
        env = {**os.environ, "CODEX_HOME": str(codex_home)}
        return subprocess.run(
            [str(repo / "scripts" / "link-skills.sh")],
            cwd=repo,
            env=env,
            text=True,
            capture_output=True,
        )

    def test_list_skills_finds_nested_active_skill_and_excludes_deprecated(self):
        result = subprocess.run(
            [str(ROOT / "scripts" / "list-skills.sh")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        lines = result.stdout.splitlines()
        self.assertIn("skills/music/research-music/SKILL.md", lines)
        self.assertFalse(any("/deprecated/" in line for line in lines))

    def test_link_skills_uses_codex_home_and_does_not_replace_regular_files(self):
        with tempfile.TemporaryDirectory() as directory:
            env = {**os.environ, "CODEX_HOME": directory}
            subprocess.run(
                [str(ROOT / "scripts" / "link-skills.sh")],
                cwd=ROOT,
                env=env,
                check=True,
            )
            target = Path(directory) / "skills" / "research-music"
            self.assertTrue(target.is_symlink())
            target.unlink()
            target.write_text("user-owned", encoding="utf-8")

            result = subprocess.run(
                [str(ROOT / "scripts" / "link-skills.sh")],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
            )

            self.assertNotEqual(0, result.returncode)
            self.assertEqual("user-owned", target.read_text(encoding="utf-8"))

    def test_link_skills_does_not_replace_foreign_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            foreign = root / "foreign"
            foreign.mkdir()
            target_dir = root / "skills"
            target_dir.mkdir()
            target = target_dir / "research-music"
            target.symlink_to(foreign, target_is_directory=True)

            result = self.run_linker(ROOT, root)

            self.assertNotEqual(0, result.returncode)
            self.assertEqual(foreign.resolve(), target.resolve())

    def test_duplicate_leaf_names_are_rejected_before_any_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = self.make_repo(
                root,
                "a/alpha",
                "b/duplicate",
                "z/duplicate",
            )
            codex_home = root / "codex-home"
            codex_home.mkdir()

            result = self.run_linker(repo, codex_home)

            self.assertNotEqual(0, result.returncode)
            self.assertIn("duplicate active skill name: duplicate", result.stderr)
            self.assertFalse((codex_home / "skills").exists())

    def test_regular_file_conflict_is_rejected_without_partial_links(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = self.make_repo(root, "group/alpha", "group/zulu")
            target_dir = root / "codex-home" / "skills"
            target_dir.mkdir(parents=True)
            conflict = target_dir / "zulu"
            conflict.write_text("user-owned", encoding="utf-8")

            result = self.run_linker(repo, root / "codex-home")

            self.assertNotEqual(0, result.returncode)
            self.assertFalse((target_dir / "alpha").exists())
            self.assertEqual("user-owned", conflict.read_text(encoding="utf-8"))

    def test_foreign_symlink_conflict_is_rejected_without_partial_links(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = self.make_repo(root, "group/alpha", "group/zulu")
            target_dir = root / "codex-home" / "skills"
            target_dir.mkdir(parents=True)
            foreign = root / "foreign"
            foreign.mkdir()
            conflict = target_dir / "zulu"
            conflict.symlink_to(foreign, target_is_directory=True)

            result = self.run_linker(repo, root / "codex-home")

            self.assertNotEqual(0, result.returncode)
            self.assertFalse((target_dir / "alpha").exists())
            self.assertEqual(foreign.resolve(), conflict.resolve())

    def test_symlink_to_another_repo_skill_is_foreign(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = self.make_repo(root, "group/alpha", "group/zulu")
            target_dir = root / "codex-home" / "skills"
            target_dir.mkdir(parents=True)
            conflict = target_dir / "zulu"
            alpha_source = repo / "skills" / "group" / "alpha"
            conflict.symlink_to(alpha_source, target_is_directory=True)

            result = self.run_linker(repo, root / "codex-home")

            self.assertNotEqual(0, result.returncode)
            self.assertFalse((target_dir / "alpha").exists())
            self.assertEqual(alpha_source.resolve(), conflict.resolve())

    def test_correct_existing_link_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = self.make_repo(root, "group/research-music")
            codex_home = root / "codex-home"

            first = self.run_linker(repo, codex_home)
            target = codex_home / "skills" / "research-music"
            first_inode = target.lstat().st_ino
            second = self.run_linker(repo, codex_home)

            self.assertEqual(0, first.returncode, first.stderr)
            self.assertEqual(0, second.returncode, second.stderr)
            self.assertTrue(target.is_symlink())
            expected = repo / "skills" / "group" / "research-music"
            self.assertEqual(expected.resolve(), target.resolve())
            self.assertEqual(first_inode, target.lstat().st_ino)


if __name__ == "__main__":
    unittest.main()
