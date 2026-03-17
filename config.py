from pathlib import Path
from typing import Dict, List, Any
import json
import logging

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    def __init__(self, message: str, error_code: int = 1):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)
    
    def __str__(self):
        return f"[错误码 {self.error_code}] {self.message}"


class Config:
    DEFAULT_EXCLUDE_LIST: List[str] = []
    DEFAULT_OUTPUT_FILENAME: str = 'xiaokeer_project_tree.md'
    
    def __init__(self, config_path: str):
        self._raw_config: Dict[str, Any] = {}
        self._project_path: Path = None
        self._exclude_list: List[str] = []
        self._output_filename: str = self.DEFAULT_OUTPUT_FILENAME
        
        self._load_config(config_path)
        self._validate_and_apply()
    
    @property
    def project_path(self) -> Path:
        return self._project_path
    
    @property
    def exclude_list(self) -> List[str]:
        return self._exclude_list.copy()
    
    @property
    def output_filename(self) -> str:
        return self._output_filename
    
    @property
    def output_path(self) -> Path:
        return self._project_path / self._output_filename
    
    @classmethod
    def from_file(cls, config_path: str) -> 'Config':
        return cls(config_path)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'project_path': str(self._project_path),
            'exclude_list': self._exclude_list,
            'output_filename': self._output_filename
        }
    
    def _load_config(self, config_path: str) -> None:
        path = Path(config_path)
        
        if not path.suffix:
            path = path.with_suffix('.json')
        
        if not path.is_absolute():
            path = Path.cwd() / path
        
        if not path.exists():
            raise ConfigError(f"配置文件不存在: {path}", error_code=1)
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self._raw_config = json.load(f)
            logger.info(f"成功加载配置文件: {path}")
        except json.JSONDecodeError as e:
            raise ConfigError(f"配置文件JSON格式错误: {e}", error_code=1)
        except PermissionError:
            raise ConfigError(f"无权限读取配置文件: {path}", error_code=1)
    
    def _validate_and_apply(self) -> None:
        self._validate_project_path()
        self._validate_exclude_list()
        self._validate_output_filename()
        logger.info("配置验证通过")
    
    def _validate_project_path(self) -> None:
        if 'project_path' not in self._raw_config:
            raise ConfigError("配置错误: project_path 不能为空", error_code=1)
        
        path_str = self._raw_config['project_path']
        
        if not isinstance(path_str, str):
            raise ConfigError("配置错误: project_path 必须为字符串类型", error_code=1)
        
        if not path_str.strip():
            raise ConfigError("配置错误: project_path 不能为空", error_code=1)
        
        path = Path(path_str)
        
        if not path.exists():
            raise ConfigError(f"路径错误: 项目路径 '{path}' 不存在", error_code=2)
        
        if not path.is_dir():
            raise ConfigError(f"路径错误: '{path}' 不是有效的目录", error_code=3)
        
        if not path.is_absolute():
            logger.warning("建议使用绝对路径，当前使用相对路径可能产生歧义")
        
        self._project_path = path.resolve()
    
    def _validate_exclude_list(self) -> None:
        if 'exclude_list' not in self._raw_config:
            self._exclude_list = self.DEFAULT_EXCLUDE_LIST.copy()
            return
        
        exclude_list = self._raw_config['exclude_list']
        
        if not isinstance(exclude_list, list):
            raise ConfigError("配置错误: exclude_list 必须为列表类型", error_code=1)
        
        validated_list = []
        for item in exclude_list:
            if not isinstance(item, str):
                raise ConfigError("配置错误: exclude_list 中的元素必须为字符串", error_code=1)
            if item.strip():
                validated_list.append(item)
            else:
                logger.warning("exclude_list 中包含空字符串，将被忽略")
        
        self._exclude_list = validated_list
    
    def _validate_output_filename(self) -> None:
        if 'output_filename' not in self._raw_config:
            self._output_filename = self.DEFAULT_OUTPUT_FILENAME
            return
        
        filename = self._raw_config['output_filename']
        
        if not isinstance(filename, str):
            raise ConfigError("配置错误: output_filename 必须为字符串类型", error_code=1)
        
        if not filename.strip():
            self._output_filename = self.DEFAULT_OUTPUT_FILENAME
            return
        
        illegal_chars = ['<', '>', ':', '"', '|', '?', '*']
        for char in illegal_chars:
            if char in filename:
                raise ConfigError(f"配置错误: output_filename 包含非法字符 '{char}'", error_code=1)
        
        if not filename.endswith('.md'):
            logger.warning("output_filename 建议以 .md 结尾")
        
        self._output_filename = filename
