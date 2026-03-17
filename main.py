import argparse
import logging
import sys
from pathlib import Path

from config import Config, ConfigError
from scanner import DirectoryScanner
from generator import MarkdownGenerator, GeneratorError


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    format_str = '%(asctime)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=level,
        format=format_str,
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description='项目目录转为md树文档工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python main.py --config config.json
  python main.py -c ./config.json
  python main.py -c config.json -v
        '''
    )
    parser.add_argument(
        '-c', '--config',
        type=str,
        required=True,
        help='配置文件路径 (JSON格式)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='显示详细日志'
    )
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
        logger.info(f"输出文件: {config.output_filename}")
        
        logger.info("开始扫描目录...")
        scanner = DirectoryScanner(config.project_path, config.exclude_list)
        tree = scanner.scan()
        logger.info(f"扫描完成: {scanner.get_file_count()} 个文件, {scanner.get_directory_count()} 个文件夹")
        
        logger.info("开始生成文档...")
        generator = MarkdownGenerator(
            project_path=config.project_path,
            output_filename=config.output_filename,
            config_data=config.to_dict()
        )
        output_path = generator.generate(tree)
        
        logger.info(f"文档生成成功: {output_path}")
        print(f"\n✅ 文档已生成: {output_path}")
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


if __name__ == '__main__':
    sys.exit(main())
