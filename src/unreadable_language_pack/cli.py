"""Command-line interface for the resource-pack generator."""

import argparse
from pathlib import Path

from unreadable_language_pack.build import ResourcePackBuilder
from unreadable_language_pack.repository import ProjectLayout


def create_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser.

    Returns:
        The configured argument parser.
    """
    parser = argparse.ArgumentParser(
        description="Generate unconventional Minecraft language resource packs."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory (default: current working directory).",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("build", help="Generate all language files and create the pack.")
    subcommands.add_parser(
        "generate-corrections",
        help="Regenerate correction data under data/corrections.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run a command-line command.

    Args:
        argv: Optional command-line arguments. Defaults to ``sys.argv``.

    Returns:
        The process exit code.
    """
    arguments = create_parser().parse_args(argv)
    builder = ResourcePackBuilder(ProjectLayout.from_root(arguments.root))

    if arguments.command == "build":
        builder.build()
    else:
        builder.generate_correction_data()
    return 0
