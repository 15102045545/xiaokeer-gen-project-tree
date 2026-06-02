from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
import fnmatch
import json
import logging

from .config import Config, ConfigError, load_raw_config

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DistortionPoint:
    location: str
    value: Any
    message: str

    def value_for_output(self) -> str:
        return json.dumps(self.value, ensure_ascii=False)


class ConfigDistortionChecker:
    KNOWN_KEYS = {"project_path", "exclude_list", "exclude_paths", "output_filename"}

    def __init__(self, config_path: Path, raw_config: Dict[str, Any]):
        self.config_path = config_path
        self.raw_config = raw_config

    @classmethod
    def from_file(cls, config_path: str) -> "ConfigDistortionChecker":
        resolved_path, raw_config = load_raw_config(config_path)
        if not isinstance(raw_config, dict):
            raise ConfigError("配置错误: 配置文件顶层必须为 JSON 对象", error_code=1)
        return cls(resolved_path, raw_config)

    def check(self) -> List[DistortionPoint]:
        points: List[DistortionPoint] = []
        project_path = self._read_project_path(points)

        if project_path is not None:
            project_items = list(self._iter_project_items(project_path))
            self._check_exclude_list(project_path, project_items, points)
            self._check_exclude_paths(project_path, points)
            self._check_output_filename(project_path, points)

        self._check_unknown_keys(points)
        return points

    def _read_project_path(self, points: List[DistortionPoint]) -> Optional[Path]:
        if "project_path" not in self.raw_config:
            raise ConfigError("配置错误: project_path 不能为空", error_code=1)

        path_str = self.raw_config["project_path"]

        if not isinstance(path_str, str):
            raise ConfigError("配置错误: project_path 必须为字符串类型", error_code=1)

        if not path_str.strip():
            raise ConfigError("配置错误: project_path 不能为空", error_code=1)

        path = Path(path_str)

        if not path.exists():
            points.append(DistortionPoint("project_path", path_str, f"项目路径不存在: {path}"))
            return None

        if not path.is_dir():
            points.append(DistortionPoint("project_path", path_str, f"项目路径不是目录: {path}"))
            return None

        if not path.is_absolute():
            logger.warning("建议使用绝对路径，当前使用相对路径可能产生歧义")

        return path.resolve()

    def _check_exclude_list(
        self,
        project_path: Path,
        project_items: List[Path],
        points: List[DistortionPoint],
    ) -> None:
        for index, item in self._read_exclude_list_items():
            if item == ".gitignore":
                if not (project_path / ".gitignore").exists():
                    points.append(
                        DistortionPoint(
                            f"exclude_list[{index}]",
                            item,
                            "配置为读取项目根目录 .gitignore，但该文件不存在",
                        )
                    )
                continue

            if not any(self._matches_pattern(path.name, item) for path in project_items):
                points.append(
                    DistortionPoint(
                        f"exclude_list[{index}]",
                        item,
                        "项目中不存在匹配该名称或 basename 通配规则的文件/文件夹",
                    )
                )

    def _read_exclude_list_items(self) -> List[Tuple[int, str]]:
        if "exclude_list" not in self.raw_config:
            return []

        exclude_list = self.raw_config["exclude_list"]

        if not isinstance(exclude_list, list):
            raise ConfigError("配置错误: exclude_list 必须为列表类型", error_code=1)

        items: List[Tuple[int, str]] = []
        for index, item in enumerate(exclude_list):
            if not isinstance(item, str):
                raise ConfigError("配置错误: exclude_list 中的元素必须为字符串", error_code=1)
            if item.strip():
                items.append((index, item))
            else:
                logger.warning("exclude_list 中包含空字符串，将被忽略")

        return items

    def _check_exclude_paths(self, project_path: Path, points: List[DistortionPoint]) -> None:
        for index, raw_path, normalized_path in self._read_exclude_paths_items():
            target_path = project_path / normalized_path
            if not target_path.exists():
                points.append(
                    DistortionPoint(
                        f"exclude_paths[{index}]",
                        raw_path,
                        f"项目根目录下不存在该相对路径: {normalized_path}",
                    )
                )

    def _read_exclude_paths_items(self) -> List[Tuple[int, str, str]]:
        if "exclude_paths" not in self.raw_config:
            return []

        exclude_paths = self.raw_config["exclude_paths"]

        if not isinstance(exclude_paths, list):
            raise ConfigError("配置错误: exclude_paths 必须为列表类型", error_code=1)

        items: List[Tuple[int, str, str]] = []
        for index, item in enumerate(exclude_paths):
            if not isinstance(item, str):
                raise ConfigError("配置错误: exclude_paths 中的元素必须为字符串", error_code=1)

            stripped = item.strip()
            if not stripped:
                logger.warning("exclude_paths 中包含空字符串，将被忽略")
                continue

            normalized = Config._normalize_exclude_path(stripped)
            items.append((index, item, normalized))

        return items

    def _check_output_filename(self, project_path: Path, points: List[DistortionPoint]) -> None:
        output_filename = self._read_output_filename()
        markdown_path = project_path / output_filename
        html_path = markdown_path.with_suffix(".html")

        if not markdown_path.exists() and not html_path.exists():
            points.append(
                DistortionPoint(
                    "output_filename",
                    output_filename,
                    f"未找到已存在的输出树文件: {markdown_path} 或 {html_path}",
                )
            )

    def _read_output_filename(self) -> str:
        if "output_filename" not in self.raw_config:
            return Config.DEFAULT_OUTPUT_FILENAME

        filename = self.raw_config["output_filename"]

        if not isinstance(filename, str):
            raise ConfigError("配置错误: output_filename 必须为字符串类型", error_code=1)

        if not filename.strip():
            return Config.DEFAULT_OUTPUT_FILENAME

        illegal_chars = ["<", ">", ":", '"', "|", "?", "*"]
        for char in illegal_chars:
            if char in filename:
                raise ConfigError(f"配置错误: output_filename 包含非法字符 '{char}'", error_code=1)

        if not filename.endswith(".md"):
            logger.warning("output_filename 建议以 .md 结尾")

        return filename

    def _check_unknown_keys(self, points: List[DistortionPoint]) -> None:
        for key in sorted(self.raw_config.keys()):
            if key not in self.KNOWN_KEYS:
                points.append(
                    DistortionPoint(
                        key,
                        self.raw_config[key],
                        "未被 xgentree 使用，无法检查该配置项是否符合项目现状",
                    )
                )

    def _iter_project_items(self, project_path: Path) -> Iterable[Path]:
        stack = [project_path]

        while stack:
            current = stack.pop()
            try:
                children = sorted(current.iterdir(), key=lambda path: (not path.is_dir(), path.name.lower()))
            except PermissionError:
                logger.warning(f"无权限访问目录: {current}")
                continue

            for child in children:
                if child.is_symlink():
                    continue
                yield child
                if child.is_dir():
                    stack.append(child)

    def _matches_pattern(self, name: str, pattern: str) -> bool:
        if any(char in pattern for char in "*?["):
            return fnmatch.fnmatch(name, pattern)
        return name == pattern
