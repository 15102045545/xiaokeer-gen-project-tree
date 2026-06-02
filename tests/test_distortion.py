import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from xiaokeer.gen.project.tree.distortion import ConfigDistortionChecker


class TestConfigDistortionChecker(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.project = self.test_dir / "project"
        self.project.mkdir()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _write_config(self, config_data: dict) -> Path:
        config_path = self.test_dir / "config.json"
        config_path.write_text(json.dumps(config_data, ensure_ascii=False), encoding="utf-8")
        return config_path

    def _check(self, config_data: dict):
        config_path = self._write_config(config_data)
        return ConfigDistortionChecker.from_file(str(config_path)).check()

    def test_no_distortion_when_configured_items_exist(self):
        (self.project / ".gitignore").write_text("*.tmp\n", encoding="utf-8")
        (self.project / "src").mkdir()
        (self.project / "src" / "existing.py").write_text("print('ok')", encoding="utf-8")
        (self.project / "dist").mkdir()
        (self.project / "dist" / "assets").mkdir()
        (self.project / "tree.md").write_text("# tree", encoding="utf-8")

        points = self._check(
            {
                "project_path": str(self.project),
                "exclude_list": [".gitignore", "existing.py", "*.py"],
                "exclude_paths": ["src/existing.py", "dist/assets"],
                "output_filename": "tree.md",
            }
        )

        self.assertEqual(points, [])

    def test_project_path_not_exists_is_reported_as_distortion(self):
        missing_project = self.test_dir / "missing"

        points = self._check({"project_path": str(missing_project), "output_filename": "tree.md"})

        self.assertEqual(len(points), 1)
        self.assertEqual(points[0].location, "project_path")
        self.assertEqual(points[0].value, str(missing_project))

    def test_project_path_file_is_reported_as_distortion(self):
        project_file = self.test_dir / "project.txt"
        project_file.write_text("not a dir", encoding="utf-8")

        points = self._check({"project_path": str(project_file), "output_filename": "tree.md"})

        self.assertEqual(len(points), 1)
        self.assertEqual(points[0].location, "project_path")
        self.assertIn("不是目录", points[0].message)

    def test_exclude_list_exact_name_not_found_is_reported_with_index(self):
        (self.project / "tree.md").write_text("# tree", encoding="utf-8")

        points = self._check(
            {
                "project_path": str(self.project),
                "exclude_list": ["missing.txt"],
                "output_filename": "tree.md",
            }
        )

        self.assertEqual([point.location for point in points], ["exclude_list[0]"])
        self.assertEqual(points[0].value, "missing.txt")

    def test_exclude_list_glob_not_found_is_reported_with_index(self):
        (self.project / "README.md").write_text("readme", encoding="utf-8")
        (self.project / "tree.md").write_text("# tree", encoding="utf-8")

        points = self._check(
            {
                "project_path": str(self.project),
                "exclude_list": ["*.pyc"],
                "output_filename": "tree.md",
            }
        )

        self.assertEqual([point.location for point in points], ["exclude_list[0]"])
        self.assertEqual(points[0].value, "*.pyc")

    def test_gitignore_switch_requires_root_gitignore_file(self):
        (self.project / "tree.md").write_text("# tree", encoding="utf-8")

        points = self._check(
            {
                "project_path": str(self.project),
                "exclude_list": [".gitignore"],
                "output_filename": "tree.md",
            }
        )

        self.assertEqual([point.location for point in points], ["exclude_list[0]"])
        self.assertIn(".gitignore", points[0].message)

    def test_exclude_paths_not_found_is_reported_with_index(self):
        (self.project / "tree.md").write_text("# tree", encoding="utf-8")

        points = self._check(
            {
                "project_path": str(self.project),
                "exclude_paths": ["src/generated/client.py"],
                "output_filename": "tree.md",
            }
        )

        self.assertEqual([point.location for point in points], ["exclude_paths[0]"])
        self.assertEqual(points[0].value, "src/generated/client.py")

    def test_output_filename_missing_md_and_html_is_reported(self):
        points = self._check({"project_path": str(self.project), "output_filename": "tree.md"})

        self.assertEqual([point.location for point in points], ["output_filename"])
        self.assertEqual(points[0].value, "tree.md")

    def test_output_filename_is_not_distorted_when_html_exists(self):
        (self.project / "tree.html").write_text("<!doctype html>", encoding="utf-8")

        points = self._check({"project_path": str(self.project), "output_filename": "tree.md"})

        self.assertEqual(points, [])

    def test_unknown_top_level_config_item_is_reported(self):
        (self.project / "tree.md").write_text("# tree", encoding="utf-8")

        points = self._check(
            {
                "project_path": str(self.project),
                "output_filename": "tree.md",
                "unused_path": "missing",
            }
        )

        self.assertEqual([point.location for point in points], ["unused_path"])
        self.assertIn("无法检查", points[0].message)


if __name__ == "__main__":
    unittest.main()
