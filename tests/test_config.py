import unittest
import json
import tempfile
import os
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config, ConfigError


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.test_dir)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def _create_config_file(self, config_data: dict, filename: str = 'config.json') -> Path:
        config_path = self.config_dir / filename
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False)
        return config_path
    
    def test_tc_cfg_001_normal_config(self):
        config_data = {
            'project_path': str(self.test_dir),
            'exclude_list': ['.git', '__pycache__'],
            'output_filename': 'test_output.md'
        }
        config_path = self._create_config_file(config_data)
        
        config = Config.from_file(str(config_path))
        
        self.assertEqual(config.project_path, Path(self.test_dir).resolve())
        self.assertEqual(config.exclude_list, ['.git', '__pycache__'])
        self.assertEqual(config.output_filename, 'test_output.md')
    
    def test_tc_cfg_002_missing_exclude_list(self):
        config_data = {
            'project_path': str(self.test_dir)
        }
        config_path = self._create_config_file(config_data)
        
        config = Config.from_file(str(config_path))
        
        self.assertEqual(config.exclude_list, [])
    
    def test_tc_cfg_003_missing_output_filename(self):
        config_data = {
            'project_path': str(self.test_dir)
        }
        config_path = self._create_config_file(config_data)
        
        config = Config.from_file(str(config_path))
        
        self.assertEqual(config.output_filename, 'xiaokeer_project_tree.md')
    
    def test_tc_cfg_004_project_path_not_exists(self):
        config_data = {
            'project_path': '/non/existent/path'
        }
        config_path = self._create_config_file(config_data)
        
        with self.assertRaises(ConfigError) as context:
            Config.from_file(str(config_path))
        
        self.assertEqual(context.exception.error_code, 2)
    
    def test_tc_cfg_005_project_path_is_file(self):
        file_path = self.config_dir / 'test_file.txt'
        file_path.write_text('test')
        
        config_data = {
            'project_path': str(file_path)
        }
        config_path = self._create_config_file(config_data)
        
        with self.assertRaises(ConfigError) as context:
            Config.from_file(str(config_path))
        
        self.assertEqual(context.exception.error_code, 3)
    
    def test_tc_cfg_006_config_file_not_exists(self):
        with self.assertRaises(ConfigError) as context:
            Config.from_file('/non/existent/config.json')
        
        self.assertEqual(context.exception.error_code, 1)
    
    def test_tc_cfg_007_invalid_json(self):
        config_path = self.config_dir / 'invalid.json'
        with open(config_path, 'w') as f:
            f.write('{ invalid json }')
        
        with self.assertRaises(ConfigError) as context:
            Config.from_file(str(config_path))
        
        self.assertEqual(context.exception.error_code, 1)
    
    def test_tc_cfg_008_exclude_list_with_empty_string(self):
        config_data = {
            'project_path': str(self.test_dir),
            'exclude_list': ['a', '', 'b']
        }
        config_path = self._create_config_file(config_data)
        
        config = Config.from_file(str(config_path))
        
        self.assertEqual(config.exclude_list, ['a', 'b'])
    
    def test_tc_cfg_009_chinese_path(self):
        chinese_dir = self.config_dir / '中文目录'
        chinese_dir.mkdir()
        
        config_data = {
            'project_path': str(chinese_dir)
        }
        config_path = self._create_config_file(config_data)
        
        config = Config.from_file(str(config_path))
        
        self.assertEqual(config.project_path, chinese_dir.resolve())
    
    def test_tc_cfg_010_relative_config_path(self):
        config_data = {
            'project_path': str(self.test_dir)
        }
        config_path = self._create_config_file(config_data)
        
        original_cwd = os.getcwd()
        try:
            os.chdir(self.config_dir)
            config = Config.from_file('config')
            self.assertEqual(config.project_path, Path(self.test_dir).resolve())
        finally:
            os.chdir(original_cwd)
    
    def test_output_path_property(self):
        config_data = {
            'project_path': str(self.test_dir),
            'output_filename': 'custom.md'
        }
        config_path = self._create_config_file(config_data)
        
        config = Config.from_file(str(config_path))
        
        expected_output_path = Path(self.test_dir).resolve() / 'custom.md'
        self.assertEqual(config.output_path, expected_output_path)
    
    def test_to_dict(self):
        config_data = {
            'project_path': str(self.test_dir),
            'exclude_list': ['.git'],
            'output_filename': 'test.md'
        }
        config_path = self._create_config_file(config_data)
        
        config = Config.from_file(str(config_path))
        result = config.to_dict()
        
        self.assertEqual(result['project_path'], str(Path(self.test_dir).resolve()))
        self.assertEqual(result['exclude_list'], ['.git'])
        self.assertEqual(result['output_filename'], 'test.md')
    
    def test_invalid_output_filename_chars(self):
        config_data = {
            'project_path': str(self.test_dir),
            'output_filename': 'test<file>.md'
        }
        config_path = self._create_config_file(config_data)
        
        with self.assertRaises(ConfigError) as context:
            Config.from_file(str(config_path))
        
        self.assertEqual(context.exception.error_code, 1)
    
    def test_project_path_not_string(self):
        config_data = {
            'project_path': 12345
        }
        config_path = self._create_config_file(config_data)
        
        with self.assertRaises(ConfigError) as context:
            Config.from_file(str(config_path))
        
        self.assertEqual(context.exception.error_code, 1)
    
    def test_exclude_list_not_list(self):
        config_data = {
            'project_path': str(self.test_dir),
            'exclude_list': 'not_a_list'
        }
        config_path = self._create_config_file(config_data)
        
        with self.assertRaises(ConfigError) as context:
            Config.from_file(str(config_path))
        
        self.assertEqual(context.exception.error_code, 1)


if __name__ == '__main__':
    unittest.main()
