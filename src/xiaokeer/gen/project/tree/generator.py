from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List
from html import escape
import json
import logging

from .scanner import TreeNode

logger = logging.getLogger(__name__)


class GeneratorError(Exception):
    def __init__(self, message: str, error_code: int = 4):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

    def __str__(self):
        return f"[错误码 {self.error_code}] {self.message}"


class MarkdownGenerator:
    DEFAULT_DESCRIPTION = "${description}"
    INDENT_SIZE = 2

    def __init__(
        self,
        project_path: Path,
        output_filename: str,
        description: str = DEFAULT_DESCRIPTION,
        config_data: Dict[str, Any] = None,
    ):
        self.project_path = project_path
        self.output_filename = output_filename
        self.description = description
        self.config_data = config_data or {}

    def generate(self, tree: TreeNode) -> Path:
        content = self._build_content(tree)
        output_path = self._write_file(content)
        return output_path

    def generate_outputs(self, tree: TreeNode, output_format: str = "md") -> List[Path]:
        if output_format == "none":
            return []
        if output_format == "md":
            return [self.generate(tree)]
        if output_format == "html":
            return [self.generate_html(tree)]
        if output_format == "both":
            return [self.generate(tree), self.generate_html(tree)]

        raise ValueError(f"不支持的输出格式: {output_format}")

    def generate_html(self, tree: TreeNode) -> Path:
        content = self._build_html_content(tree)
        output_path = self._html_output_path()
        return self._write_file(content, output_path)

    def set_description(self, description: str) -> None:
        self.description = description

    def set_config_data(self, config_data: Dict[str, Any]) -> None:
        self.config_data = config_data

    def _build_content(self, tree: TreeNode) -> str:
        parts = []

        parts.append(self._generate_header())
        parts.append("")
        parts.append(self._generate_config_section())
        parts.append("")
        parts.append("## 目录结构")
        parts.append("")

        for child in tree.children:
            tree_content = self._generate_tree(child)
            parts.append(tree_content)

        return "\n".join(parts)

    def _generate_header(self) -> str:
        now = datetime.now()
        formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
        project_path_str = str(self.project_path).replace("\\", "/")

        return "\n".join(
            [
                "# 项目目录树",
                "",
                f"**生成时间**: {formatted_time}  ",
                f"**项目路径**: {project_path_str}",
                "",
                "---",
            ]
        )

    def _generate_config_section(self) -> str:
        config_json = json.dumps(self.config_data, ensure_ascii=False, indent=2)

        return "\n".join(["## 配置信息", "", "```json", config_json, "```"])

    def _generate_tree(self, node: TreeNode, indent_level: int = 0) -> str:
        lines = []

        item_line = self._format_item(node, indent_level)
        lines.append(item_line)

        if node.is_dir:
            sorted_children = sorted(node.children, key=lambda x: (not x.is_dir, x.name.lower()))
            for child in sorted_children:
                child_content = self._generate_tree(child, indent_level + 1)
                lines.append(child_content)

        return "\n".join(lines)

    def _generate_html_tree(self, node: TreeNode, indent_level: int = 0) -> str:
        indent = " " * (self.INDENT_SIZE * indent_level)
        label = self._format_html_label(node)

        if not node.is_dir:
            return f'{indent}<li>{label}</li>'

        lines = [
            f"{indent}<li>",
            f"{indent}  <details open>",
            f"{indent}    <summary>{label}</summary>",
        ]

        sorted_children = sorted(node.children, key=lambda x: (not x.is_dir, x.name.lower()))
        if sorted_children:
            lines.append(f"{indent}    <ul>")
            for child in sorted_children:
                lines.append(self._generate_html_tree(child, indent_level + 3))
            lines.append(f"{indent}    </ul>")

        lines.extend(
            [
                f"{indent}  </details>",
                f"{indent}</li>",
            ]
        )
        return "\n".join(lines)

    def _format_item(self, node: TreeNode, indent_level: int) -> str:
        indent = " " * (self.INDENT_SIZE * indent_level)

        if node.is_dir:
            icon = "📁"
            relative_path = node.relative_path.replace("\\", "/")
            link_path = f"./{relative_path}/"
        else:
            icon = "📄"
            relative_path = node.relative_path.replace("\\", "/")
            link_path = f"./{relative_path}"

        return f"{indent}- {icon} [{node.name}]({link_path}) - {self.description}"

    def _format_html_label(self, node: TreeNode) -> str:
        if node.is_dir:
            icon = "📁"
            relative_path = node.relative_path.replace("\\", "/").rstrip("/")
            link_path = f"./{relative_path}/"
        else:
            icon = "📄"
            relative_path = node.relative_path.replace("\\", "/")
            link_path = f"./{relative_path}"

        name = escape(node.name, quote=True)
        href = escape(link_path, quote=True)
        description = escape(self.description, quote=True)
        return f'{icon} <a href="{href}">{name}</a> - {description}'

    def _build_html_content(self, tree: TreeNode) -> str:
        project_path_str = escape(str(self.project_path).replace("\\", "/"), quote=True)
        config_json = escape(json.dumps(self.config_data, ensure_ascii=False, indent=2), quote=False)
        tree_html = "\n".join(self._generate_html_tree(child) for child in tree.children)

        return "\n".join(
            [
                "<!doctype html>",
                '<html lang="zh-CN">',
                "<head>",
                '  <meta charset="utf-8">',
                "  <title>项目目录树</title>",
                "  <style>",
                "    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.55; margin: 24px; }",
                "    a { color: #0b57d0; text-decoration: none; }",
                "    a:hover { text-decoration: underline; }",
                "    ul { list-style: none; margin: 0; padding-left: 1.4rem; }",
                "    li { margin: 0.18rem 0; }",
                "    summary { cursor: pointer; }",
                "    pre { background: #f6f8fa; padding: 12px; overflow: auto; }",
                "  </style>",
                "</head>",
                "<body>",
                "  <h1>项目目录树</h1>",
                f"  <p><strong>项目路径</strong>: {project_path_str}</p>",
                "  <h2>配置信息</h2>",
                f"  <pre><code>{config_json}</code></pre>",
                "  <h2>目录结构</h2>",
                '  <ul class="xgentree-tree">',
                tree_html,
                "  </ul>",
                "</body>",
                "</html>",
            ]
        )

    def _html_output_path(self) -> Path:
        return (self.project_path / self.output_filename).with_suffix(".html")

    def _write_file(self, content: str, output_path: Path = None) -> Path:
        if output_path is None:
            output_path = self.project_path / self.output_filename

        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8")
            logger.info(f"文档已生成: {output_path}")
            return output_path
        except PermissionError:
            logger.error(f"无权限写入文件: {output_path}")
            raise GeneratorError(f"无权限写入文件: {output_path}", error_code=4)
        except OSError as e:
            logger.error(f"写入文件失败: {e}")
            raise GeneratorError(f"写入文件失败: {e}", error_code=4)
