from pathlib import Path
from typing import List, Optional, Set
from dataclasses import dataclass, field
import fnmatch
import logging

try:
    from pathspec import GitIgnoreSpec
except ImportError:
    GitIgnoreSpec = None

from gitignore_parser import parse_gitignore_file

logger = logging.getLogger(__name__)


@dataclass
class TreeNode:
    name: str
    path: Path
    is_dir: bool
    relative_path: str
    children: List['TreeNode'] = field(default_factory=list)
    
    @property
    def is_file(self) -> bool:
        return not self.is_dir
    
    @property
    def link_path(self) -> str:
        path = self.relative_path.replace('\\', '/')
        if self.is_dir:
            path = path.rstrip('/') + '/'
        return f"./{path}"
    
    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'is_dir': self.is_dir,
            'relative_path': self.relative_path,
            'children': [c.to_dict() for c in self.children]
        }


class DirectoryScanner:
    def __init__(self, project_path: Path, exclude_list: List[str]):
        self.project_path = project_path
        self.exclude_list = exclude_list
        self._simple_patterns: Set[str] = set()
        self._gitignore_spec: Optional['GitIgnoreSpec'] = None
        self._file_count: int = 0
        self._directory_count: int = 0
    
    def scan(self) -> TreeNode:
        self._build_exclude_spec()
        
        root = TreeNode(
            name=self.project_path.name,
            path=self.project_path,
            is_dir=True,
            relative_path="."
        )
        
        self._file_count = 0
        self._directory_count = 0
        
        root.children = self._scan_directory(self.project_path)
        
        logger.info(f"目录扫描完成，共 {self._file_count} 个文件，{self._directory_count} 个文件夹")
        return root
    
    def get_file_count(self) -> int:
        return self._file_count
    
    def get_directory_count(self) -> int:
        return self._directory_count
    
    def _build_exclude_spec(self) -> None:
        self._simple_patterns = set()
        self._gitignore_spec = None
        
        parse_gitignore = False
        
        for item in self.exclude_list:
            if item == '.gitignore':
                parse_gitignore = True
            else:
                self._simple_patterns.add(item)
        
        if parse_gitignore:
            gitignore_path = self.project_path / '.gitignore'
            if gitignore_path.exists():
                self._gitignore_spec = parse_gitignore_file(gitignore_path)
                if self._gitignore_spec:
                    logger.info("成功加载.gitignore规则")
            else:
                logger.warning(".gitignore文件不存在")
    
    def _is_excluded(self, path: Path) -> bool:
        name = path.name
        
        for pattern in self._simple_patterns:
            if self._matches_pattern(name, pattern):
                return True
        
        if self._gitignore_spec is not None:
            try:
                relative = path.relative_to(self.project_path)
                relative_str = relative.as_posix()
                if path.is_dir():
                    relative_str += '/'
                if self._gitignore_spec.match_file(relative_str):
                    return True
            except ValueError:
                pass
        
        return False
    
    def _matches_pattern(self, name: str, pattern: str) -> bool:
        if any(c in pattern for c in '*?['):
            return fnmatch.fnmatch(name, pattern)
        return name == pattern
    
    def _scan_directory(self, dir_path: Path, relative_prefix: str = "") -> List[TreeNode]:
        children: List[TreeNode] = []
        
        try:
            items = sorted(dir_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            logger.warning(f"无权限访问目录: {dir_path}")
            return children
        
        for item in items:
            if item.is_symlink():
                logger.debug(f"跳过符号链接: {item.name}")
                continue
            
            if self._is_excluded(item):
                logger.debug(f"排除: {item.name}")
                continue
            
            relative_path = f"{relative_prefix}/{item.name}" if relative_prefix else item.name
            
            if item.is_dir():
                node = TreeNode(
                    name=item.name,
                    path=item,
                    is_dir=True,
                    relative_path=relative_path
                )
                node.children = self._scan_directory(item, relative_path)
                children.append(node)
                self._directory_count += 1
            else:
                node = TreeNode(
                    name=item.name,
                    path=item,
                    is_dir=False,
                    relative_path=relative_path
                )
                children.append(node)
                self._file_count += 1
        
        return children
