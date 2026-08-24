import re
from pathlib import Path

import pytest

from unreadable_language_pack.build import ResourcePackBuilder
from unreadable_language_pack.cli import create_parser
from unreadable_language_pack.conversion import ConversionError, convert_language_entries
from unreadable_language_pack.repository import DataFormatError, ProjectLayout, read_json

_HAN_CHARACTER_RE = re.compile(r"[\u3400-\u9fff]")


def test_cli_help_is_english() -> None:
    help_text = create_parser().format_help()

    assert "Generate unconventional Minecraft language resource packs." in help_text
    assert _HAN_CHARACTER_RE.search(help_text) is None


def test_build_status_messages_are_english(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    builder = ResourcePackBuilder(ProjectLayout.from_root(tmp_path))
    monkeypatch.setattr(builder, "generate_language_files", lambda: ([], 1.25))
    monkeypatch.setattr(builder, "create_resource_pack", lambda _outputs: ("2.00 KB", 0.5))

    builder.build()

    output = capsys.readouterr().out
    assert "Language file generation completed in 1.25 s." in output
    assert "Resource pack created (2.00 KB) in 0.50 s." in output
    assert _HAN_CHARACTER_RE.search(output) is None


def test_errors_exposed_by_the_cli_are_english(tmp_path: Path) -> None:
    with pytest.raises(DataFormatError) as data_error:
        read_json(tmp_path / "missing.json")

    def fail_conversion(_text: str) -> str:
        raise ValueError("invalid input")

    with pytest.raises(ConversionError) as conversion_error:
        convert_language_entries({"example.key": "text"}, fail_conversion)

    messages = f"{data_error.value}\n{conversion_error.value}"
    assert "Unable to read JSON data:" in messages
    assert "Failed to convert language key 'example.key': invalid input" in messages
    assert _HAN_CHARACTER_RE.search(messages) is None
