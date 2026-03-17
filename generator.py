from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import json
import logging

from scanner import TreeNode

logger = logging.getLogger(__name__)


class GeneratorError(Exception):
    def __init__(self, message: str, error_code: int = 4):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)
    
    def __str__(self):
        return f"[错误码 {self.error_code}] {self.message}"


class MarkdownGenerator:
    DEFAULT_DESCRIPTION = 'desc'
    INDENT_SIZE = 2
    
    def __init__(
        self,
        project_path: Path,
        output_filename: str,
        description: str = DEFAULT_DESCRIPTION,
        config_data: Dict[str, Any] = None
    ):
        self.project_path = project_path
        self.output_filename = output_filename
        self.description = description
        self.config_data = config_data or {}
    
    def generate(self, tree: TreeNode) -> Path:
        content = self._build_content(tree)
        output_path = self._write_file(content)
        return output_path
    
    def set_description(self, description: str) -> None:
        self.description = description
    
    def set_config_data(self, config_data: Dict[str, Any]) -> None:
        self.config_data = config_data
    
    def _build_content(self, tree: TreeNode) -> str:
        parts = []
        
        parts.append(self._generate_header())
        parts.append('')
        parts.append(self._generate_config_section())
        parts.append('')
        parts.append('## 目录结构')
        parts.append('')
        
        for child in tree.children:
            tree_content = self._generate_tree(child)
            parts.append(tree_content)
        
        return '\n'.join(parts)
    
    def _generate_header(self) -> str:
        now = datetime.now()
        formatted_time = now.strftime('%Y-%m-%d %H:%M:%S')
        project_path_str = str(self.project_path).replace('\\', '/')
        
        return '\n'.join([
            '# 项目目录树',
            '',
            f'**生成时间**: {formatted_time}  ',
            f'**项目路径**: {project_path_str}',
            '',
            '---'
        ])
    
    def _generate_config_section(self) -> str:
        config_json = json.dumps(self.config_data, ensure_ascii=False, indent=2)
        
        return '\n'.join([
            '## 配置信息',
            '',
            '```json',
            config_json,
            '```'
        ])
    
    def _generate_tree(self, node: TreeNode, indent_level: int = 0) -> str:
        lines = []
        
        item_line = self._format_item(node, indent_level)
        lines.append(item_line)
        
        if node.is_dir:
            sorted_children = sorted(node.children, key=lambda x: (not x.is_dir, x.name.lower()))
            for child in sorted_children:
                child_content = self._generate_tree(child, indent_level + 1)
                lines.append(child_content)
        
        return '\n'.join(lines)
    
    def _format_item(self, node: TreeNode, indent_level: int) -> str:
        indent = ' ' * (self.INDENT_SIZE * indent_level)
        
        if node.is_dir:
            icon = '📁'
            relative_path = node.relative_path.replace('\\', '/')
            link_path = f"./{relative_path}/"
        else:
            icon = '📄'
            relative_path = node.relative_path.replace('\\', '/')
            link_path = f"./{relative_path}"
        
        return f"{indent}- {icon} [{node.name}]({link_path}) - {self.description}"
    
    def _write_file(self, content: str) -> Path:
        output_path = self.project_path / self.output_filename
        
        try:
            output_path.write_text(content, encoding='utf-8')
            logger.info(f"文档已生成: {output_path}")
            return output_path
        except PermissionError:
            logger.error(f"无权限写入文件: {output_path}")
            raise GeneratorError(f"无权限写入文件: {output_path}", error_code=4)
        except OSError as e:
            logger.error(f"写入文件失败: {e}")
            raise GeneratorError(f"写入文件失败: {e}", error_code=4)
