import unittest
import tempfile
from pathlib import Path
import shutil

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from scanner import TreeNode
from generator import MarkdownGenerator, GeneratorError


class TestMarkdownGenerator(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def _create_simple_tree(self) -> TreeNode:
        root = TreeNode(
            name='root',
            path=self.test_dir,
            is_dir=True,
            relative_path='.'
        )
        
        dir1 = TreeNode(
            name='dir1',
            path=self.test_dir / 'dir1',
            is_dir=True,
            relative_path='dir1'
        )
        
        file1 = TreeNode(
            name='file1.txt',
            path=self.test_dir / 'file1.txt',
            is_dir=False,
            relative_path='file1.txt'
        )
        
        file2 = TreeNode(
            name='file2.py',
            path=self.test_dir / 'dir1' / 'file2.py',
            is_dir=False,
            relative_path='dir1/file2.py'
        )
        
        dir1.children.append(file2)
        root.children = [dir1, file1]
        
        return root
    
    def test_tc_gen_001_normal_generate(self):
        tree = self._create_simple_tree()
        
        generator = MarkdownGenerator(
            project_path=self.test_dir,
            output_filename='test_output.md',
            description='desc'
        )
        
        output_path = generator.generate(tree)
        
        self.assertTrue(output_path.exists())
        
        content = output_path.read_text(encoding='utf-8')
        self.assertIn('# 项目目录树', content)
        self.assertIn('## 目录结构', content)
        self.assertIn('📁', content)
        self.assertIn('📄', content)
    
    def test_tc_gen_002_empty_tree(self):
        root = TreeNode(
            name='root',
            path=self.test_dir,
            is_dir=True,
            relative_path='.'
        )
        
        generator = MarkdownGenerator(
            project_path=self.test_dir,
            output_filename='empty.md'
        )
        
        output_path = generator.generate(root)
        
        content = output_path.read_text(encoding='utf-8')
        self.assertIn('# 项目目录树', content)
        self.assertIn('## 目录结构', content)
    
    def test_tc_gen_003_chinese_filename(self):
        root = TreeNode(
            name='root',
            path=self.test_dir,
            is_dir=True,
            relative_path='.'
        )
        
        chinese_file = TreeNode(
            name='中文文件.txt',
            path=self.test_dir / '中文文件.txt',
            is_dir=False,
            relative_path='中文文件.txt'
        )
        
        root.children.append(chinese_file)
        
        generator = MarkdownGenerator(
            project_path=self.test_dir,
            output_filename='chinese_test.md'
        )
        
        output_path = generator.generate(root)
        
        content = output_path.read_text(encoding='utf-8')
        self.assertIn('中文文件.txt', content)
    
    def test_tc_gen_004_special_chars_filename(self):
        root = TreeNode(
            name='root',
            path=self.test_dir,
            is_dir=True,
            relative_path='.'
        )
        
        special_file = TreeNode(
            name='file with spaces.txt',
            path=self.test_dir / 'file with spaces.txt',
            is_dir=False,
            relative_path='file with spaces.txt'
        )
        
        root.children.append(special_file)
        
        generator = MarkdownGenerator(
            project_path=self.test_dir,
            output_filename='special.md'
        )
        
        output_path = generator.generate(root)
        
        content = output_path.read_text(encoding='utf-8')
        self.assertIn('file with spaces.txt', content)
    
    def test_tc_gen_005_deep_nesting(self):
        root = TreeNode(
            name='root',
            path=self.test_dir,
            is_dir=True,
            relative_path='.'
        )
        
        level1 = TreeNode(name='level1', path=self.test_dir / 'level1', is_dir=True, relative_path='level1')
        level2 = TreeNode(name='level2', path=self.test_dir / 'level1' / 'level2', is_dir=True, relative_path='level1/level2')
        level3 = TreeNode(name='level3', path=self.test_dir / 'level1' / 'level2' / 'level3', is_dir=True, relative_path='level1/level2/level3')
        deep_file = TreeNode(name='deep.txt', path=self.test_dir / 'level1' / 'level2' / 'level3' / 'deep.txt', is_dir=False, relative_path='level1/level2/level3/deep.txt')
        
        level3.children.append(deep_file)
        level2.children.append(level3)
        level1.children.append(level2)
        root.children.append(level1)
        
        generator = MarkdownGenerator(
            project_path=self.test_dir,
            output_filename='deep.md'
        )
        
        output_path = generator.generate(root)
        
        content = output_path.read_text(encoding='utf-8')
        self.assertIn('deep.txt', content)
        
        lines = content.split('\n')
        deep_line = [l for l in lines if 'deep.txt' in l][0]
        self.assertTrue(deep_line.startswith('      -'))
    
    def test_tc_gen_007_windows_path(self):
        root = TreeNode(
            name='root',
            path=self.test_dir,
            is_dir=True,
            relative_path='.'
        )
        
        file_with_backslash = TreeNode(
            name='file.txt',
            path=self.test_dir / 'subdir' / 'file.txt',
            is_dir=False,
            relative_path='subdir\\file.txt'
        )
        
        root.children.append(file_with_backslash)
        
        generator = MarkdownGenerator(
            project_path=self.test_dir,
            output_filename='path_test.md'
        )
        
        output_path = generator.generate(root)
        
        content = output_path.read_text(encoding='utf-8')
        self.assertIn('./subdir/file.txt', content)
        self.assertNotIn('\\', content.split('](')[1].split(')')[0])
    
    def test_tc_gen_008_custom_description(self):
        root = TreeNode(
            name='root',
            path=self.test_dir,
            is_dir=True,
            relative_path='.'
        )
        
        file_node = TreeNode(
            name='test.txt',
            path=self.test_dir / 'test.txt',
            is_dir=False,
            relative_path='test.txt'
        )
        
        root.children.append(file_node)
        
        generator = MarkdownGenerator(
            project_path=self.test_dir,
            output_filename='custom_desc.md',
            description='自定义描述'
        )
        
        output_path = generator.generate(root)
        
        content = output_path.read_text(encoding='utf-8')
        self.assertIn('自定义描述', content)
    
    def test_folder_link_ends_with_slash(self):
        root = TreeNode(
            name='root',
            path=self.test_dir,
            is_dir=True,
            relative_path='.'
        )
        
        folder = TreeNode(
            name='myfolder',
            path=self.test_dir / 'myfolder',
            is_dir=True,
            relative_path='myfolder'
        )
        
        root.children.append(folder)
        
        generator = MarkdownGenerator(
            project_path=self.test_dir,
            output_filename='folder_test.md'
        )
        
        output_path = generator.generate(root)
        content = output_path.read_text(encoding='utf-8')
        
        self.assertIn('./myfolder/', content)
    
    def test_file_link_no_trailing_slash(self):
        root = TreeNode(
            name='root',
            path=self.test_dir,
            is_dir=True,
            relative_path='.'
        )
        
        file_node = TreeNode(
            name='testfile.txt',
            path=self.test_dir / 'testfile.txt',
            is_dir=False,
            relative_path='testfile.txt'
        )
        
        root.children.append(file_node)
        
        generator = MarkdownGenerator(
            project_path=self.test_dir,
            output_filename='file_test.md'
        )
        
        output_path = generator.generate(root)
        content = output_path.read_text(encoding='utf-8')
        
        self.assertIn('./testfile.txt)', content)
        self.assertNotIn('./testfile.txt/)', content)
    
    def test_set_description(self):
        generator = MarkdownGenerator(
            project_path=self.test_dir,
            output_filename='test.md',
            description='original'
        )
        
        self.assertEqual(generator.description, 'original')
        
        generator.set_description('updated')
        self.assertEqual(generator.description, 'updated')
    
    def test_header_contains_project_path(self):
        root = TreeNode(
            name='root',
            path=self.test_dir,
            is_dir=True,
            relative_path='.'
        )
        
        generator = MarkdownGenerator(
            project_path=self.test_dir,
            output_filename='header_test.md'
        )
        
        output_path = generator.generate(root)
        content = output_path.read_text(encoding='utf-8')
        
        path_str = str(self.test_dir).replace('\\', '/')
        self.assertIn(path_str, content)
    
    def test_header_contains_generation_time(self):
        root = TreeNode(
            name='root',
            path=self.test_dir,
            is_dir=True,
            relative_path='.'
        )
        
        generator = MarkdownGenerator(
            project_path=self.test_dir,
            output_filename='time_test.md'
        )
        
        output_path = generator.generate(root)
        content = output_path.read_text(encoding='utf-8')
        
        self.assertIn('**生成时间**:', content)
    
    def test_config_section_in_output(self):
        root = TreeNode(
            name='root',
            path=self.test_dir,
            is_dir=True,
            relative_path='.'
        )
        
        config_data = {
            'project_path': str(self.test_dir),
            'exclude_list': ['.git', '__pycache__'],
            'output_filename': 'test_output.md'
        }
        
        generator = MarkdownGenerator(
            project_path=self.test_dir,
            output_filename='config_test.md',
            config_data=config_data
        )
        
        output_path = generator.generate(root)
        content = output_path.read_text(encoding='utf-8')
        
        self.assertIn('## 配置信息', content)
        self.assertIn('```json', content)
        self.assertIn('"project_path"', content)
        self.assertIn('"exclude_list"', content)
    
    def test_set_config_data(self):
        generator = MarkdownGenerator(
            project_path=self.test_dir,
            output_filename='test.md'
        )
        
        self.assertEqual(generator.config_data, {})
        
        config_data = {'project_path': '/test/path'}
        generator.set_config_data(config_data)
        
        self.assertEqual(generator.config_data, config_data)


if __name__ == '__main__':
    unittest.main()
