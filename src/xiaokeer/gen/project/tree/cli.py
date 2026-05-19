import argparse
import logging
import sys

from . import __version__
from .config import Config, ConfigError
from .generator import GeneratorError, MarkdownGenerator
from .scanner import DirectoryScanner


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    format_str = "%(asctime)s - %(levelname)s - %(message)s"

    logging.basicConfig(level=level, format=format_str, datefmt="%Y-%m-%d %H:%M:%S")


def parse_args():
    parser = argparse.ArgumentParser(
        description="xgentree: 将项目目录结构生成带跳转链接的 Markdown/HTML 树文档",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
快速开始:
  1. 创建 config.json:
     {
       "project_path": "/absolute/path/to/project",
       "exclude_list": [".git", ".gitignore", "__pycache__", "*.pyc"],
       "exclude_paths": ["src/generated/client.py", "dist/assets"],
       "output_filename": "xiaokeer_project_tree.md"
     }

  2. 生成目录树:
     xgentree -c config.json
     xgentree -c config.json --output-format both

常用命令:
  xgentree --help
  xgentree --version
  xgentree --config config.json
  xgentree -c ./config.json --verbose
  xgentree -c config.json --output-format none
  xgentree -c config.json --output-format html

配置字段:
  project_path      必填。要扫描的项目目录。建议使用绝对路径；相对路径会按当前工作目录解析。
  output_filename   可选。输出 Markdown 文件名，默认 xiaokeer_project_tree.md。文件写入 project_path 下。
  exclude_list      可选。按文件名/目录名排除，作用于任意层级的同名项。
                    支持精确 name，例如 ".git"；支持 name 通配，例如 "*.pyc"。
                    特殊值 ".gitignore" 表示读取 project_path 根目录下的 .gitignore 规则。
  exclude_paths     可选。相对于 project_path 根目录的精确相对路径排除。
                    支持 / 和 Windows 风格 \\，内部统一为 /。
                    命中文件时只排除该文件；命中目录时排除该目录整棵子树。
                    不支持 glob、正则、否定规则、绝对路径、.. 或项目根目录 "."。

排除边界:
  exclude_list=["file.txt"] 会排除所有层级中名为 file.txt 的文件。
  exclude_paths=["src/file.txt"] 只排除 project_path/src/file.txt。
  需要 src/**/*.py、!important.py 这类通配或否定规则时，请写入 .gitignore，
  并在 exclude_list 中加入 ".gitignore"。

扫描与输出行为:
  - 符号链接会被跳过。
  - 无权限访问的目录会被跳过并记录警告。
  - --output-format 可选 none/md/html/both，默认 md。
  - none 是 dry-run：只扫描并打印统计，不写文件。
  - md 生成 project_path/output_filename，保持原有纯 Markdown 列表目录树。
  - html 生成同 stem 的 .html 文件，例如 tree.md -> tree.html，目录树使用 HTML details/summary，可折叠。
  - both 同时生成 md 和 html。
  - 输出文档包含项目路径、配置 JSON 和带跳转链接的目录树。
  - Markdown 输出不包含 HTML details/summary；需要可折叠树时使用 html 或 both。

重要风险:
  - 新生成的节点说明默认是字面量 ${description}，它只是待补充占位符，不代表真实业务语义。
  - xgentree 不会读取、合并或保留已有文档中人工填写的说明；同名输出文件会被重新写入。
  - 如果已有 tree.md/xiaokeer_project_tree.md 已经被人或 agent 补充过业务说明，不要直接覆盖。
  - 建议先运行 --output-format none 检查扫描范围，再输出到新的文件名，人工 diff 后再决定是否替换旧文档。

适合使用:
  - 首次为项目生成目录树骨架。
  - 项目结构变化后，生成新的候选树用于人工对比。
  - CI 或 agent 只需要最新结构快照，且不依赖已有说明文本。

不适合直接覆盖:
  - 旧文档里的 ${description} 已经被替换成模块职责、接口含义、业务边界等人工说明。
  - agent 准备把生成结果当成“已理解业务语义”的事实来源。
  - 当前输出文件没有进入版本控制、无法通过 git diff 找回旧说明。

错误码:
  1  配置文件错误，例如文件不存在、JSON 错误、字段类型错误、非法 exclude_paths。
  2  project_path 不存在。
  3  project_path 不是目录。
  4  输出文件无写入权限。
  99 未知错误。
        """,
    )
    parser.add_argument("-c", "--config", type=str, required=True, help="配置文件路径 (JSON格式)")
    parser.add_argument(
        "--output-format",
        choices=("none", "md", "html", "both"),
        default="md",
        help="输出格式: none/md/html/both。默认 md；html 使用同 stem 的 .html 文件。",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="显示详细日志")
    parser.add_argument("--version", action="version", version=f"xgentree {__version__}")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        logger.info("开始加载配置...")
        config = Config.from_file(args.config)
        logger.info(f"项目路径: {config.project_path}")
        logger.info(f"排除列表: {config.exclude_list}")
        logger.info(f"排除路径: {config.exclude_paths}")
        logger.info(f"输出文件: {config.output_filename}")

        logger.info("开始扫描目录...")
        scanner = DirectoryScanner(config.project_path, config.exclude_list, config.exclude_paths)
        tree = scanner.scan()
        logger.info(f"扫描完成: {scanner.get_file_count()} 个文件, {scanner.get_directory_count()} 个文件夹")

        if args.output_format == "none":
            logger.info("dry-run 模式，不生成文件")
            print(
                f"\n✅ dry-run 完成: 扫描到 {scanner.get_file_count()} 个文件, "
                f"{scanner.get_directory_count()} 个文件夹，未写入输出文件"
            )
            return 0

        logger.info(f"开始生成文档，输出格式: {args.output_format}")
        generator = MarkdownGenerator(
            project_path=config.project_path,
            output_filename=config.output_filename,
            config_data=config.to_dict(),
        )
        output_paths = generator.generate_outputs(tree, args.output_format)

        for output_path in output_paths:
            logger.info(f"文档生成成功: {output_path}")
        output_list = "\n".join(f"  - {path}" for path in output_paths)
        print(f"\n✅ 文档已生成:\n{output_list}")
        return 0

    except ConfigError as e:
        logger.error(str(e))
        print(f"\n❌ 配置错误: {e}", file=sys.stderr)
        return e.error_code
    except GeneratorError as e:
        logger.error(str(e))
        print(f"\n❌ 生成错误: {e}", file=sys.stderr)
        return e.error_code
    except Exception as e:
        logger.exception(f"未知错误: {e}")
        print(f"\n❌ 未知错误: {e}", file=sys.stderr)
        return 99
