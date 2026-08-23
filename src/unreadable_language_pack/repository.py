"""Project layout and JSON data access."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import orjson

type StringMap = dict[str, str]


class DataFormatError(ValueError):
    """Raised when a JSON data file has an unexpected structure."""


@dataclass(frozen=True, slots=True)
class ProjectLayout:
    """Filesystem layout required by the generator."""

    root: Path

    @classmethod
    def from_root(cls, root: Path | str) -> "ProjectLayout":
        """Create a layout from a root directory and normalize the path."""
        return cls(Path(root).resolve())

    @property
    def data(self) -> Path:
        """Return the conversion-data directory."""
        return self.root / "data"

    @property
    def language_sources(self) -> Path:
        """Return the source Minecraft language-file directory."""
        return self.root / "mc_lang" / "full"

    @property
    def output(self) -> Path:
        """Return the generated language-file directory."""
        return self.root / "output"

    @property
    def archive(self) -> Path:
        """Return the resource-pack archive path."""
        return self.root / "unreadable_language_pack.zip"


def read_json(path: Path) -> Any:
    """Read a JSON file."""
    try:
        return orjson.loads(path.read_bytes())
    except (OSError, orjson.JSONDecodeError) as exc:
        raise DataFormatError(f"无法读取 JSON 数据：{path}") from exc


def read_string_map(path: Path) -> StringMap:
    """Read and validate a JSON object that maps strings to strings."""
    value = read_json(path)
    if not isinstance(value, dict) or not all(
        isinstance(key, str) and isinstance(item, str) for key, item in value.items()
    ):
        raise DataFormatError(f"预期字符串映射：{path}")
    return value


def read_string_set(path: Path) -> frozenset[str]:
    """Read and validate a JSON array of strings."""
    value = read_json(path)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise DataFormatError(f"预期字符串数组：{path}")
    return frozenset(value)


def write_json(path: Path, data: StringMap) -> None:
    """Write language JSON in a stable, readable format."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = orjson.dumps(data, option=orjson.OPT_INDENT_2 | orjson.OPT_APPEND_NEWLINE)
    path.write_bytes(payload)


def format_file_size(path: Path) -> str:
    """Return a human-readable file size for logging."""
    size = path.stat().st_size
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.2f} MB"
    return f"{size / 1024:.2f} KB"


class DataRepository:
    """Load and cache project data on demand without import-time I/O."""

    def __init__(self, layout: ProjectLayout) -> None:
        """Initialize the repository for a project layout."""
        self.layout = layout
        self._maps: dict[Path, StringMap] = {}
        self._sets: dict[Path, frozenset[str]] = {}

    def _map(self, path: Path) -> StringMap:
        if path not in self._maps:
            self._maps[path] = read_string_map(path)
        return self._maps[path]

    def _set(self, path: Path) -> frozenset[str]:
        if path not in self._sets:
            self._sets[path] = read_string_set(path)
        return self._sets[path]

    def language(self, name: str) -> StringMap:
        """Load a source Minecraft language file."""
        return self._map(self.layout.language_sources / f"{name}.json")

    def data_map(self, name: str, folder: str = "") -> StringMap:
        """Load a string mapping from the data directory."""
        return self._map(self.layout.data / folder / f"{name}.json")

    def replacements(self, language: str) -> StringMap:
        """Load a text-replacement table."""
        return self.data_map(f"rep_{language}", "rep")

    def pinyin_map(self, scheme: str) -> StringMap:
        """Load a mapping from Pinyin to another transcription scheme."""
        filenames = {
            "wadegiles": "py2wg",
            "romatzyh": "py2gr",
            "simp_romatzyh": "py2sgr",
            "mps2": "py2mps2",
            "tongyong": "py2ty",
            "yale": "py2yale",
            "ipa": "py2ipa",
            "katakana": "py2kk",
            "cyrillic": "py2cy",
            "xiaojing": "py2xj",
        }
        return self.data_map(filenames[scheme])

    def fixes(self, scheme: str) -> StringMap:
        """Load manual corrections for an output scheme."""
        fixes = self.data_map(f"fixed_zh_{scheme}", "fixed").copy()
        if scheme == "py":
            fixes.update(self.data_map("fixed_zh_py_manual", "fixed"))
        return fixes

    def universal_fixes(self) -> StringMap:
        """Load corrections shared by all Chinese output schemes."""
        return self.data_map("fixed_zh_universal", "fixed")

    def custom_phrases(self) -> StringMap:
        """Load manually reviewed Mandarin phrase pronunciations."""
        return self.data_map("phrases")

    def word_splits(self) -> StringMap:
        """Load shared word-boundary corrections for Minecraft text."""
        return self.data_map("word_splits")

    def force_wei_keys(self) -> frozenset[str]:
        """Load language keys where U+4E3A must use the falling-tone reading."""
        return self._set(self.layout.data / "wei.json")
