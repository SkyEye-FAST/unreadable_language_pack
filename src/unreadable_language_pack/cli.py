"""Command-line interface for the resource-pack generator."""

import argparse
from pathlib import Path

from unreadable_language_pack.build import PackBuilder
from unreadable_language_pack.repository import ProjectLayout


def create_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(description="生成 Minecraft 难视语言资源包")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="项目根目录（默认：当前工作目录）",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("build", help="生成所有语言文件并打包")
    subcommands.add_parser("fix-data", help="重新生成 data/fixed 下的修正数据")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run a command-line command and return its exit code."""
    arguments = create_parser().parse_args(argv)
    builder = PackBuilder(ProjectLayout.from_root(arguments.root))

    if arguments.command == "build":
        builder.build()
    else:
        builder.generate_fix_data()
    return 0
