from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import fnmatch
import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _Rule:
    pattern: str
    negated: bool
    is_dir: bool
    anchored: bool


class GitIgnoreSpec:
    def __init__(self, rules: List[_Rule]):
        self._rules = rules

    @classmethod
    def from_lines(cls, lines: List[str]) -> "GitIgnoreSpec":
        rules: List[_Rule] = []
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            negated = stripped.startswith("!")
            if negated:
                stripped = stripped[1:].strip()
                if not stripped:
                    continue

            anchored = stripped.startswith("/")
            if anchored:
                stripped = stripped[1:]

            is_dir = stripped.endswith("/")
            pattern = stripped
            rules.append(_Rule(pattern=pattern, negated=negated, is_dir=is_dir, anchored=anchored))

        return cls(rules)

    def match_file(self, path: str) -> bool:
        p = path.replace("\\", "/").lstrip("./")
        matched = False

        for rule in self._rules:
            if self._match_rule(rule, p):
                matched = not rule.negated

        return matched

    def _match_rule(self, rule: _Rule, path: str) -> bool:
        if rule.is_dir:
            prefix = rule.pattern
            if rule.anchored:
                return path == prefix or path.startswith(prefix)
            return f"/{prefix}" in f"/{path}" or path == prefix or path.startswith(prefix)

        pattern = rule.pattern

        if "/" not in pattern:
            base = path.rstrip("/").split("/")[-1]
            return fnmatch.fnmatch(base, pattern)

        if rule.anchored:
            return fnmatch.fnmatch(path, pattern)

        return fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(f"/{path}", f"*/{pattern}")


def parse_gitignore_file(path: Path) -> Optional[GitIgnoreSpec]:
    if not path.exists():
        logger.warning(f".gitignore文件不存在: {path}")
        return None

    lines = _read_with_fallback_encoding(path)
    patterns = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            patterns.append(stripped)

    if not patterns:
        return None

    try:
        spec = GitIgnoreSpec.from_lines(patterns)
        logger.info(f"成功解析.gitignore，共 {len(patterns)} 条规则")
        return spec
    except Exception as e:
        logger.error(f"解析.gitignore失败: {e}")
        return None


def _read_with_fallback_encoding(path: Path) -> List[str]:
    encodings = ["utf-8", "gbk", "gb2312", "latin-1"]

    for encoding in encodings:
        try:
            content = path.read_text(encoding=encoding)
            return content.splitlines()
        except UnicodeDecodeError:
            continue
        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            break

    return []
