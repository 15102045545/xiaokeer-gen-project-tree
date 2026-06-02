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
        self.assertIn("--check-distortion", result.stdout)
        self.assertIn("exclude_paths", result.stdout)
        self.assertIn("exclude_list", result.stdout)
        self.assertIn("相对于 project_path 根目录", result.stdout)
        self.assertIn("不支持 glob", result.stdout)
        self.assertIn("--output-format", result.stdout)
        self.assertIn("none/md/html/both", result.stdout)
        self.assertIn("同 stem 的 .html", result.stdout)
        self.assertIn("纯 Markdown 列表", result.stdout)
        self.assertIn("需要可折叠树时使用 html 或 both", result.stdout)
        self.assertIn("xgentree -c config.json", result.stdout)
        self.assertIn("错误码", result.stdout)
        self.assertIn("配置文件失真", result.stdout)
        self.assertIn("5", result.stdout)

    def test_version_outputs_package_version(self):
        result = self._run_cli("--version")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "xgentree 1.0.5")

    def test_help_warns_about_description_placeholder_and_overwrite_risk(self):
        result = self._run_cli("--help")

        self.assertEqual(result.returncode, 0)
        self.assertIn("${description}", result.stdout)
        self.assertIn("待补充占位符", result.stdout)
        self.assertIn("不会读取、合并或保留已有文档中人工填写的说明", result.stdout)
        self.assertIn("不要直接覆盖", result.stdout)
        self.assertIn("人工 diff", result.stdout)
        self.assertIn("已理解业务语义", result.stdout)

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

    def test_check_distortion_success_does_not_write_output_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            output_file = project / "tree.md"
            output_file.write_text("# existing tree", encoding="utf-8")
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

            result = self._run_cli("-c", str(config), "--check-distortion")

            self.assertEqual(result.returncode, 0)
            self.assertIn("未发现失真点", result.stdout)
            self.assertEqual(output_file.read_text(encoding="utf-8"), "# existing tree")

    def test_check_distortion_reports_points_and_returns_error_code_5(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            config = Path(tmp) / "config.json"
            config.write_text(
                json.dumps(
                    {
                        "project_path": str(project),
                        "exclude_list": ["missing.txt"],
                        "exclude_paths": ["src/generated/client.py"],
                        "output_filename": "tree.md",
                    }
                ),
                encoding="utf-8",
            )

            result = self._run_cli("-c", str(config), "--check-distortion")

            self.assertEqual(result.returncode, 5)
            self.assertIn("配置文件失真点", result.stdout)
            self.assertIn("exclude_list[0]", result.stdout)
            self.assertIn("exclude_paths[0]", result.stdout)
            self.assertIn("output_filename", result.stdout)
            self.assertFalse((project / "tree.md").exists())


if __name__ == "__main__":
    unittest.main()
