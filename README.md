# 项目目录转为md树文档工具

一个将项目目录结构转换为Markdown格式文档的命令行工具，支持排除规则和.gitignore解析。

## 功能特性

- 递归扫描项目目录结构
- 支持普通排除规则（精确匹配、通配符匹配）
- 自动解析.gitignore文件规则
- 生成带跳转链接的Markdown文档
- 支持中文文件名和路径
- 输出文档包含配置信息区块

## 安装依赖

```bash
pip install -r requirements.txt
```

或直接安装：

```bash
pip install pathspec>=1.0.0
```

## 快速开始

### 1. 创建配置文件

在工具目录下创建 `config.json` 文件：

```json
{
    "project_path": "C:/your/project/path",
    "exclude_list": [
        ".git",
        ".gitignore",
        "__pycache__",
        "*.pyc"
    ],
    "output_filename": "xiaokeer_project_tree.md"
}
```

### 2. 运行工具

```bash
python main.py -c config.json
```

### 3. 查看结果

生成的Markdown文档将保存在项目根目录下，文件名为 `xiaokeer_project_tree.md`。

## 配置说明

### 配置文件格式

| 配置项 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| project_path | string | 是 | 无 | 项目目录的绝对路径 |
| exclude_list | list | 否 | [] | 需要排除的文件/文件夹名称列表 |
| output_filename | string | 否 | xiaokeer_project_tree.md | 输出文件名 |

### 排除规则说明

#### 普通排除规则

| 模式类型 | 示例 | 匹配规则 |
|----------|------|----------|
| 精确匹配 | `.git` | 完全匹配文件名或目录名 |
| 通配符匹配 | `*.pyc` | 使用通配符匹配文件名 |

#### .gitignore规则

当排除列表中包含 `.gitignore` 时，工具会自动读取项目根目录下的 `.gitignore` 文件，并将其中的规则合并到排除列表中。

支持的.gitignore语法：
- 简单文件名: `error.log`
- 目录模式: `build/`
- 通配符: `*.pyc`
- 双星号: `**/node_modules`
- 否定模式: `!important.log`

## 命令行参数

```
usage: main.py [-h] -c CONFIG [-v]

项目目录转为md树文档工具

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        配置文件路径 (JSON格式)
  -v, --verbose         显示详细日志
```

## 使用示例

### 基本使用

```bash
python main.py -c config.json
```

### 显示详细日志

```bash
python main.py -c config.json -v
```

### 使用相对路径配置文件

```bash
python main.py -c ./config.json
```

## 输出示例

生成的Markdown文档格式：

```markdown
# 项目目录树

**生成时间**: 2026-03-13 12:00:00  
**项目路径**: C:/your/project/path

---

## 配置信息

```json
{
  "project_path": "C:/your/project/path",
  "exclude_list": [
    ".git",
    ".gitignore",
    "__pycache__",
    "*.pyc"
  ],
  "output_filename": "xiaokeer_project_tree.md"
}
```

## 目录结构

- 📁 [src](./src/) - desc
  - 📁 [utils](./src/utils/) - desc
    - 📄 [helper.py](./src/utils/helper.py) - desc
  - 📄 [main.py](./src/main.py) - desc
- 📄 [README.md](./README.md) - desc
```

## 文件结构

```
gen_project_tree/
├── main.py              # 主入口
├── config.py            # 配置管理模块
├── scanner.py           # 目录扫描模块
├── gitignore_parser.py  # .gitignore解析模块
├── generator.py         # Markdown生成模块
├── config.json          # 默认配置文件模板
├── requirements.txt     # 依赖清单
└── tests/               # 测试文件目录
    ├── test_config.py
    ├── test_scanner.py
    └── test_generator.py
```

## 错误码说明

| 错误码 | 含义 |
|--------|------|
| 1 | 配置文件错误（文件不存在、格式错误、字段类型错误） |
| 2 | 项目路径不存在 |
| 3 | 项目路径无效（不是目录） |
| 4 | 输出权限错误（无写入权限） |
| 99 | 未知错误 |

## 运行测试

```bash
cd gen_project_tree
python -m unittest discover tests -v
```

## 注意事项

1. 建议使用绝对路径配置 `project_path`
2. 输出文件将保存在项目根目录下
3. 符号链接将被自动跳过
4. 无权限访问的目录将被跳过并记录警告日志

## 版本历史

### v0.1.1 (2026-03-13)
- 新增：输出文档包含配置信息区块
- 新增：`config_data` 参数支持
- 新增：`set_config_data()` 方法

### v0.1.0 (2026-03-13)
- 初始版本
- 支持基本目录扫描和Markdown生成
- 支持.gitignore规则解析
- 支持通配符排除规则
