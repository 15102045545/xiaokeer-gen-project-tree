from pathlib import Path
from typing import List, Optional
import logging

try:
    from pathspec import GitIgnoreSpec
except ImportError:
    GitIgnoreSpec = None

logger = logging.getLogger(__name__)


def parse_gitignore_file(path: Path) -> Optional['GitIgnoreSpec']:
    if GitIgnoreSpec is None:
        logger.error("pathspec库未安装，无法解析.gitignore")
        return None
    
    if not path.exists():
        logger.warning(f".gitignore文件不存在: {path}")
        return None
    
    lines = _read_with_fallback_encoding(path)
    
    patterns = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
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
    encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
    
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
