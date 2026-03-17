import unittest
import tempfile
import os
from pathlib import Path
import shutil

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from scanner import DirectoryScanner, TreeNode
from gitignore_parser import parse_gitignore_file


class TestDirectoryScanner(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self._create_test_structure()
    
    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def _create_test_structure(self):
        (self.test_dir / 'dir1').mkdir()
        (self.test_dir / 'dir1' / 'file1.txt').write_text('content1')
        (self.test_dir / 'dir1' / 'file2.py').write_text('content2')
        
        (self.test_dir / 'dir2').mkdir()
        (self.test_dir / 'dir2' / 'subdir').mkdir()
        (self.test_dir / 'dir2' / 'subdir' / 'file3.txt').write_text('content3')
        
        (self.test_dir / '.git').mkdir()
        (self.test_dir / '.git' / 'config').write_text('git config')
        
        (self.test_dir / '__pycache__').mkdir()
        (self.test_dir / '__pycache__' / 'module.pyc').write_text('compiled')
        
        (self.test_dir / 'test.pyc').write_text('compiled')
        (self.test_dir / 'README.md').write_text('readme')
    
    def test_tc_scan_001_empty_directory(self):
        empty_dir = self.test_dir / 'empty'
        empty_dir.mkdir()
        
        scanner = DirectoryScanner(empty_dir, [])
        tree = scanner.scan()
        
        self.assertEqual(len(tree.children), 0)
    
    def test_tc_scan_002_normal_exclude(self):
        scanner = DirectoryScanner(self.test_dir, ['.git'])
        tree = scanner.scan()
        
        git_found = any(child.name == '.git' for child in tree.children)
        self.assertFalse(git_found)
    
    def test_tc_scan_003_wildcard_exclude(self):
        scanner = DirectoryScanner(self.test_dir, ['*.pyc'])
        tree = scanner.scan()
        
        pyc_count = self._count_files_by_extension(tree, '.pyc')
        self.assertEqual(pyc_count, 0)
    
    def test_tc_scan_004_gitignore_parsing(self):
        gitignore_content = "*.log\ntemp/\n"
        (self.test_dir / '.gitignore').write_text(gitignore_content)
        (self.test_dir / 'test.log').write_text('log content')
        (self.test_dir / 'temp').mkdir()
        (self.test_dir / 'temp' / 'file.txt').write_text('temp file')
        
        scanner = DirectoryScanner(self.test_dir, ['.gitignore'])
        tree = scanner.scan()
        
        log_found = self._find_file_in_tree(tree, 'test.log')
        temp_found = self._find_dir_in_tree(tree, 'temp')
        
        self.assertFalse(log_found)
        self.assertFalse(temp_found)
    
    def test_tc_scan_005_no_gitignore(self):
        scanner = DirectoryScanner(self.test_dir, ['.gitignore'])
        tree = scanner.scan()
        
        self.assertIsNotNone(tree)
    
    def test_tc_scan_007_chinese_filename(self):
        chinese_file = self.test_dir / '中文文件.txt'
        chinese_file.write_text('中文内容')
        
        scanner = DirectoryScanner(self.test_dir, [])
        tree = scanner.scan()
        
        found = self._find_file_in_tree(tree, '中文文件.txt')
        self.assertTrue(found)
    
    def test_tc_scan_010_deep_nesting(self):
        deep_dir = self.test_dir / 'a' / 'b' / 'c' / 'd'
        deep_dir.mkdir(parents=True)
        (deep_dir / 'deep_file.txt').write_text('deep')
        
        scanner = DirectoryScanner(self.test_dir, [])
        tree = scanner.scan()
        
        found = self._find_file_in_tree(tree, 'deep_file.txt')
        self.assertTrue(found)
    
    def test_folder_priority_over_files(self):
        scanner = DirectoryScanner(self.test_dir, [])
        tree = scanner.scan()
        
        if len(tree.children) >= 2:
            first_is_dir = tree.children[0].is_dir
            for i in range(len(tree.children) - 1):
                curr_is_dir = tree.children[i].is_dir
                next_is_dir = tree.children[i + 1].is_dir
                if curr_is_dir and not next_is_dir:
                    pass
                elif not curr_is_dir and next_is_dir:
                    self.fail("文件夹应该排在文件前面")
    
    def test_file_count(self):
        scanner = DirectoryScanner(self.test_dir, [])
        tree = scanner.scan()
        
        self.assertGreater(scanner.get_file_count(), 0)
    
    def test_directory_count(self):
        scanner = DirectoryScanner(self.test_dir, [])
        tree = scanner.scan()
        
        self.assertGreater(scanner.get_directory_count(), 0)
    
    def test_tree_node_properties(self):
        scanner = DirectoryScanner(self.test_dir, [])
        tree = scanner.scan()
        
        for child in tree.children:
            self.assertIsNotNone(child.name)
            self.assertIsNotNone(child.path)
            self.assertIsNotNone(child.relative_path)
            if child.is_dir:
                self.assertTrue(child.link_path.endswith('/'))
            else:
                self.assertFalse(child.link_path.endswith('/'))
    
    def test_tree_node_to_dict(self):
        scanner = DirectoryScanner(self.test_dir, [])
        tree = scanner.scan()
        
        result = tree.to_dict()
        
        self.assertIn('name', result)
        self.assertIn('is_dir', result)
        self.assertIn('relative_path', result)
        self.assertIn('children', result)
    
    def _count_files_by_extension(self, node: TreeNode, ext: str) -> int:
        count = 0
        if not node.is_dir and node.name.endswith(ext):
            count = 1
        for child in node.children:
            count += self._count_files_by_extension(child, ext)
        return count
    
    def _find_file_in_tree(self, node: TreeNode, filename: str) -> bool:
        if not node.is_dir and node.name == filename:
            return True
        for child in node.children:
            if self._find_file_in_tree(child, filename):
                return True
        return False
    
    def _find_dir_in_tree(self, node: TreeNode, dirname: str) -> bool:
        if node.is_dir and node.name == dirname:
            return True
        for child in node.children:
            if self._find_dir_in_tree(child, dirname):
                return True
        return False


class TestGitignoreParser(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_parse_simple_patterns(self):
        gitignore = self.test_dir / '.gitignore'
        gitignore.write_text("*.log\ntemp/\n# comment\n\n*.pyc\n")
        
        spec = parse_gitignore_file(gitignore)
        
        self.assertIsNotNone(spec)
        self.assertTrue(spec.match_file('test.log'))
        self.assertTrue(spec.match_file('temp/'))
        self.assertTrue(spec.match_file('module.pyc'))
    
    def test_nonexistent_file(self):
        spec = parse_gitignore_file(self.test_dir / 'nonexistent.gitignore')
        self.assertIsNone(spec)
    
    def test_empty_gitignore(self):
        gitignore = self.test_dir / '.gitignore'
        gitignore.write_text("# only comments\n\n")
        
        spec = parse_gitignore_file(gitignore)
        self.assertIsNone(spec)
    
    def test_chinese_encoding(self):
        gitignore = self.test_dir / '.gitignore'
        gitignore.write_text("*.log\n# 中文注释\n", encoding='utf-8')
        
        spec = parse_gitignore_file(gitignore)
        
        self.assertIsNotNone(spec)
        self.assertTrue(spec.match_file('test.log'))
    
    def test_negation_pattern(self):
        gitignore = self.test_dir / '.gitignore'
        gitignore.write_text("*.log\n!important.log\n")
        
        spec = parse_gitignore_file(gitignore)
        
        self.assertIsNotNone(spec)
        self.assertTrue(spec.match_file('test.log'))
        self.assertFalse(spec.match_file('important.log'))


if __name__ == '__main__':
    unittest.main()
