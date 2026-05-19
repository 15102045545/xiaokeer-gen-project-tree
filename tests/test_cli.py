import os
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class TestCliHelp(unittest.TestCase):
    def _run_cli(self, *args):
        repo_root = Path(__file__).parent.parent
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo_root / "src")
        return subprocess.run(
            [sys.executable, "-m", "xiaokeer.gen.project.tree", *args],
            cwd=repo_root,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_help_documents_exclude_paths_and_boundaries(self):
        result = self._run_cli("--help")

        self.assertEqual(result.returncode, 0)
        self.assertIn("exclude_paths", result.stdout)
        self.assertIn("exclude_list", result.stdout)
        self.assertIn("相对于 project_path 根目录", result.stdout)
        self.assertIn("不支持 glob", result.stdout)
        self.assertIn("--output-format", result.stdout)
        self.assertIn("none/md/html/both", result.stdout)
        self.assertIn("同 stem 的 .html", result.stdout)
        self.assertIn("xgentree -c config.json", result.stdout)
        self.assertIn("错误码", result.stdout)

    def test_version_outputs_package_version(self):
        result = self._run_cli("--version")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "xgentree 1.0.2")

    def test_invalid_output_format_is_rejected(self):
        result = self._run_cli("-c", "config.json", "--output-format", "pdf")

        self.assertEqual(result.returncode, 2)
        self.assertIn("invalid choice", result.stderr)

    def test_output_format_none_scans_without_writing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            (project / "README.md").write_text("readme", encoding="utf-8")
            config = Path(tmp) / "config.json"
            config.write_text(
                json.dumps(
                    {
                        "project_path": str(project),
                        "exclude_list": [],
                        "exclude_paths": [],
                        "output_filename": "tree.md",
                    }
                ),
                encoding="utf-8",
            )

            result = self._run_cli("-c", str(config), "--output-format", "none")

            self.assertEqual(result.returncode, 0)
            self.assertIn("dry-run", result.stdout)
            self.assertFalse((project / "tree.md").exists())
            self.assertFalse((project / "tree.html").exists())

    def test_output_format_both_generates_markdown_and_html(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            (project / "README.md").write_text("readme", encoding="utf-8")
            config = Path(tmp) / "config.json"
            config.write_text(
                json.dumps(
                    {
                        "project_path": str(project),
                        "exclude_list": [],
                        "exclude_paths": [],
                        "output_filename": "tree.md",
                    }
                ),
                encoding="utf-8",
            )

            result = self._run_cli("-c", str(config), "--output-format", "both")

            self.assertEqual(result.returncode, 0)
            self.assertTrue((project / "tree.md").exists())
            self.assertTrue((project / "tree.html").exists())


if __name__ == "__main__":
    unittest.main()
