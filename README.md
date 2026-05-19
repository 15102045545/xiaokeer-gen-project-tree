# xgentree

`xgentree` 是一个将项目目录结构转换为 Markdown / HTML 树文档的命令行工具。它支持按名称排除、按项目根相对路径精确排除、读取 `.gitignore` 规则，并生成带跳转链接的目录树。

## 功能特性

- 递归扫描项目目录结构
- `exclude_list`：按文件名/目录名排除，支持 basename 精确匹配和 basename 通配
- `exclude_paths`：按相对于 `project_path` 根目录的精确相对路径排除
- 可读取项目根目录 `.gitignore` 规则
- Markdown 输出保持原有纯 Markdown 列表格式
- HTML 输出生成基于 `<details>/<summary>` 的可折叠目录树
- 支持 `none` / `md` / `html` / `both` 四种命令行输出模式
- 支持中文文件名和路径
- 输出文档包含本次生成使用的配置
- 默认节点描述为字面量 `${description}`，方便后续人工或工具替换
- `xgentree --help` 内置完整使用说明

## 安装

```bash
pip install xiaokeer.gen.project.tree
```

PyPI: https://pypi.org/project/xiaokeer.gen.project.tree/

推荐作为全局命令安装：

```bash
pipx install xiaokeer.gen.project.tree
```

从源码安装（开发者）：

```bash
pip install -e .
```

## 快速开始

创建 `config.json`：

```json
{
  "project_path": "/absolute/path/to/project",
  "exclude_list": [
    ".git",
    ".gitignore",
    "__pycache__",
    "*.pyc"
  ],
  "exclude_paths": [
    "src/generated/client.py",
    "dist/assets"
  ],
  "output_filename": "xiaokeer_project_tree.md"
}
```

运行。默认生成 Markdown：

```bash
xgentree -c config.json
```

只验证配置和扫描结果、不写文件：

```bash
xgentree -c config.json --output-format none
```

同时生成 Markdown 和 HTML：

```bash
xgentree -c config.json --output-format both
```

生成文件会写入：

```text
project_path/output_filename
```

选择 `html` 或 `both` 时，会额外生成同 stem 的 `.html` 文件。例如：

```text
/absolute/path/to/project/xiaokeer_project_tree.md
/absolute/path/to/project/xiaokeer_project_tree.html
```

## 命令

```bash
xgentree --help
xgentree --version
xgentree -c config.json
xgentree -c ./config.json --verbose
xgentree -c config.json --output-format none
xgentree -c config.json --output-format html
xgentree -c config.json --output-format both
```

`--help` 会输出完整配置模板、字段说明、排除规则边界、错误码和注意事项。安装后不读源码文档也可以通过一次 help 理解基本用法：

```bash
xgentree --help
```

## 配置字段

| 配置项 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `project_path` | string | 是 | 无 | 要扫描的项目目录。建议使用绝对路径；相对路径按当前工作目录解析 |
| `exclude_list` | list[string] | 否 | `[]` | 按文件名/目录名排除，作用于任意层级的同名项 |
| `exclude_paths` | list[string] | 否 | `[]` | 相对于 `project_path` 根目录的精确相对路径排除 |
| `output_filename` | string | 否 | `xiaokeer_project_tree.md` | 输出 Markdown 文件名，写入 `project_path` 下 |

## 输出格式

`--output-format` 是命令行参数，不写入配置文件。

| 参数值 | 行为 |
|--------|------|
| `none` | dry-run，只加载配置、扫描目录并打印统计，不写任何输出文件 |
| `md` | 生成 `output_filename` 指定的 Markdown 文件，默认值 |
| `html` | 生成同 stem 的 `.html` 文件，例如 `tree.md -> tree.html` |
| `both` | 同时生成 Markdown 和 HTML |

Markdown 文件保持原有纯 Markdown 列表格式，不包含 HTML `<details>/<summary>`。HTML 文件包含完整 HTML 文档、最小 CSS 和基于 `<details>/<summary>` 的可折叠目录树。HTML 目录默认展开，便于打开后直接浏览，也可以手动折叠。

## 排除规则

### `exclude_list`：按名称排除

`exclude_list` 只表达 basename 规则，不表达路径规则。

```json
{
  "exclude_list": [".git", "__pycache__", "*.pyc", "file.txt"]
}
```

匹配边界：

| 示例 | 行为 |
|------|------|
| `.git` | 排除任意层级下名为 `.git` 的目录或文件 |
| `__pycache__` | 排除任意层级下名为 `__pycache__` 的目录或文件 |
| `*.pyc` | 排除任意层级下 basename 匹配 `*.pyc` 的文件 |
| `file.txt` | 排除所有层级中名为 `file.txt` 的文件 |

### `exclude_paths`：按根相对路径精确排除

`exclude_paths` 只表达相对于 `project_path` 根目录的精确相对路径。

```json
{
  "exclude_paths": [
    "src/generated/client.py",
    "dist/assets"
  ]
}
```

匹配边界：

| 示例 | 行为 |
|------|------|
| `src/generated/client.py` | 只排除 `project_path/src/generated/client.py` |
| `dist/assets` | 如果是目录，排除 `project_path/dist/assets` 整棵子树 |
| `file.txt` | 只排除项目根目录下的 `file.txt`，不会排除 `src/file.txt` |

输入边界：

- 支持 `/` 和 Windows 风格 `\\`，内部统一为 `/`
- 不支持 glob，例如 `src/**/*.py`
- 不支持正则
- 不支持否定规则，例如 `!important.py`
- 不允许绝对路径
- 不允许 `..`
- 不允许 `.` 指向项目根目录

需要路径通配或否定规则时，请使用 `.gitignore`。

### `.gitignore` 规则

当 `exclude_list` 中包含 `.gitignore` 时，工具会读取 `project_path/.gitignore` 并合并其规则。

```json
{
  "exclude_list": [".gitignore"]
}
```

支持的常见规则：

- 简单文件名：`error.log`
- 目录模式：`build/`
- 通配符：`*.pyc`
- 路径模式：`src/generated/*.py`
- 否定模式：`!important.log`

注意：`.gitignore` 在当前版本里是一个“开启读取根目录 .gitignore 的开关”。如果你也想在输出树里排除 `.gitignore` 文件本身，可以继续把 `.gitignore` 写入项目自己的 `.gitignore`，或使用 `exclude_paths: [".gitignore"]`。

## 输出示例

````markdown
# 项目目录树

**生成时间**: 2026-03-13 12:00:00  
**项目路径**: /absolute/path/to/project

---

## 配置信息

```json
{
  "project_path": "/absolute/path/to/project",
  "exclude_list": [
    ".git",
    ".gitignore",
    "__pycache__",
    "*.pyc"
  ],
  "exclude_paths": [
    "src/generated/client.py",
    "dist/assets"
  ],
  "output_filename": "xiaokeer_project_tree.md"
}
```

## 目录结构

- 📁 [src](./src/) - ${description}
  - 📁 [utils](./src/utils/) - ${description}
    - 📄 [helper.py](./src/utils/helper.py) - ${description}
  - 📄 [main.py](./src/main.py) - ${description}
- 📄 [README.md](./README.md) - ${description}
````

## 错误码

| 错误码 | 含义 |
|--------|------|
| 1 | 配置文件错误，例如文件不存在、JSON 错误、字段类型错误、非法 `exclude_paths` |
| 2 | `project_path` 不存在 |
| 3 | `project_path` 不是目录 |
| 4 | 输出文件无写入权限 |
| 99 | 未知错误 |

## 注意事项

1. 建议使用绝对路径配置 `project_path`。
2. 默认输出文件会保存在 `project_path/output_filename`。
3. 符号链接会被自动跳过。
4. 无权限访问的目录会被跳过并记录警告日志。
5. `exclude_list` 是按名称排除，可能影响多个同名文件或目录。
6. `exclude_paths` 是按项目根相对路径精确排除，更适合只排除某一个具体文件或目录。
7. 需要路径 glob 或否定规则时，请使用 `.gitignore`。
8. Markdown 输出保持纯 Markdown 列表；需要可折叠目录树时，请使用 `--output-format html` 或 `--output-format both` 查看独立 HTML 文件。

## 运行测试

```bash
python -m unittest discover tests -v
```

## 发布到 PyPI

正式发布前先清理旧产物、构建并检查：

```bash
rm -rf dist build *.egg-info src/*.egg-info
python -m pip install -U build twine
python -m build
python -m twine check dist/*
python -m twine upload dist/*
```

建议使用 PyPI API Token，并通过本地未跟踪的 `.env` 或环境变量传入：

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD="pypi-..."
python -m twine upload dist/*
```

不要把 PyPI token 写入 README、发布指南、源码或任何会提交的文件。

## 版本历史

### v1.0.3 (2026-05-19)

- 修复：`md` 输出误用 HTML `<details>/<summary>` 树，恢复为原有纯 Markdown 列表格式
- 保留：`html` 输出继续提供可折叠目录树
- 新增：回归测试覆盖 Markdown 列表格式，防止 md/html 渲染逻辑再次混淆
- 更新：README 和 `xgentree --help` 明确 Markdown 与 HTML 输出边界

### v1.0.2 (2026-05-19)

- 新增：`--output-format {none,md,html,both}`，默认 `md`
- 新增：可生成独立 HTML 文件，命名规则为同 stem 改 `.html`
- 新增：HTML 目录树基于 `<details>/<summary>` 提供可折叠结构
- 变更：默认节点描述从 `desc` 改为字面量 `${description}`
- 增强：`xgentree --help` 补充输出格式、折叠边界和命名规则

### v1.0.1 (2026-05-19)

- 新增：`exclude_paths` 支持相对于项目根路径的精确路径排除
- 保留：`exclude_list` 按单 name 和 name 通配排除的旧能力
- 新增：`xgentree --version`
- 增强：`xgentree --help` 内置完整使用说明、配置模板、边界说明和错误码
- 更新：README、示例配置和 PyPI 发布指南

### v0.1.1 (2026-03-13)

- 新增：输出文档包含配置信息区块
- 新增：`config_data` 参数支持
- 新增：`set_config_data()` 方法

### v0.1.0 (2026-03-13)

- 初始版本
- 支持基本目录扫描和 Markdown 生成
- 支持 `.gitignore` 规则解析
- 支持通配符排除规则
