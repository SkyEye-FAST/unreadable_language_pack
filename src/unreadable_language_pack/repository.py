"""Project layout and JSON data access."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import orjson

type StringMap = dict[str, str]

_TRANSCRIPTION_MAPPING_FILES = {
    "wade_giles": "pinyin_to_wade_giles",
    "gwoyeu_romatzyh": "pinyin_to_gwoyeu_romatzyh",
    "simplified_gwoyeu_romatzyh": "pinyin_to_simplified_gwoyeu_romatzyh",
    "mandarin_phonetic_symbols_ii": "pinyin_to_mandarin_phonetic_symbols_ii",
    "tongyong_pinyin": "pinyin_to_tongyong_pinyin",
    "yale_romanization": "pinyin_to_yale_romanization",
    "ipa": "pinyin_to_ipa",
    "katakana": "pinyin_to_katakana",
    "cyrillic": "pinyin_to_cyrillic",
    "xiaoerjing": "pinyin_to_xiaoerjing",
}
_CORRECTION_FILES = {
    "source": "mandarin_source",
    "hanyu_pinyin": "mandarin_hanyu_pinyin",
    "hanyu_pinyin_manual": "mandarin_hanyu_pinyin_manual",
    "mandarin_phonetic_symbols_ii": "mandarin_phonetic_symbols_ii",
    "tongyong_pinyin": "mandarin_tongyong_pinyin",
    "yale_romanization": "mandarin_yale_romanization",
    "wade_giles": "mandarin_wade_giles",
    "gwoyeu_romatzyh": "mandarin_gwoyeu_romatzyh",
    "simplified_gwoyeu_romatzyh": "mandarin_simplified_gwoyeu_romatzyh",
    "cyrillic": "mandarin_cyrillic",
    "xiaoerjing": "mandarin_xiaoerjing",
    "universal": "mandarin_universal",
}


class DataFormatError(ValueError):
    """Raised when a JSON data file has an unexpected structure."""


@dataclass(frozen=True, slots=True)
class ProjectLayout:
    """Filesystem layout required by the generator.

    Attributes:
        root: Absolute project root directory.
    """

    root: Path

    @classmethod
    def from_root(cls, root: Path | str) -> "ProjectLayout":
        """Create a layout from a root directory and normalize the path.

        Args:
            root: Project root directory.

        Returns:
            The normalized project layout.
        """
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
    """Read a JSON file.

    Args:
        path: Path to the JSON file.

    Returns:
        The decoded JSON value.

    Raises:
        DataFormatError: If the file cannot be read or decoded.
    """
    try:
        return orjson.loads(path.read_bytes())
    except (OSError, orjson.JSONDecodeError) as exc:
        raise DataFormatError(f"Unable to read JSON data: {path}") from exc


def read_string_mapping(path: Path) -> StringMap:
    """Read and validate a JSON object that maps strings to strings.

    Args:
        path: Path to the JSON file.

    Returns:
        The validated string mapping.

    Raises:
        DataFormatError: If the JSON value is not a string mapping.
    """
    value = read_json(path)
    if not isinstance(value, dict) or not all(
        isinstance(key, str) and isinstance(item, str) for key, item in value.items()
    ):
        raise DataFormatError(f"Expected a string mapping: {path}")
    return value


def read_string_set(path: Path) -> frozenset[str]:
    """Read and validate a JSON array of strings.

    Args:
        path: Path to the JSON file.

    Returns:
        The validated strings as a frozen set.

    Raises:
        DataFormatError: If the JSON value is not an array of strings.
    """
    value = read_json(path)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise DataFormatError(f"Expected an array of strings: {path}")
    return frozenset(value)


def write_json(path: Path, data: StringMap) -> None:
    """Write language JSON in a stable, readable format.

    Args:
        path: Destination JSON file path.
        data: String mapping to write.

    Raises:
        OSError: If the destination cannot be created or written.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = orjson.dumps(data, option=orjson.OPT_INDENT_2 | orjson.OPT_APPEND_NEWLINE)
    path.write_bytes(payload)


def format_file_size(path: Path) -> str:
    """Return a human-readable file size for logging.

    Args:
        path: Path to the file whose size should be formatted.

    Returns:
        The formatted file size.
    """
    size = path.stat().st_size
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.2f} MB"
    return f"{size / 1024:.2f} KB"


class LanguageDataRepository:
    """Load and cache project data on demand without import-time I/O."""

    def __init__(self, layout: ProjectLayout) -> None:
        """Initialize the repository for a project layout.

        Args:
            layout: Filesystem layout containing language and conversion data.
        """
        self.layout = layout
        self._maps: dict[Path, StringMap] = {}
        self._sets: dict[Path, frozenset[str]] = {}

    def _mapping(self, path: Path) -> StringMap:
        if path not in self._maps:
            self._maps[path] = read_string_mapping(path)
        return self._maps[path]

    def _set(self, path: Path) -> frozenset[str]:
        if path not in self._sets:
            self._sets[path] = read_string_set(path)
        return self._sets[path]

    def language_source(self, name: str) -> StringMap:
        """Load a source Minecraft language file.

        Args:
            name: Language file name without the ``.json`` suffix.

        Returns:
            The source language entries.
        """
        return self._mapping(self.layout.language_sources / f"{name}.json")

    def data_mapping(self, name: str, folder: str = "") -> StringMap:
        """Load a string mapping from the data directory.

        Args:
            name: JSON file name without the ``.json`` suffix.
            folder: Optional subdirectory under the data directory.

        Returns:
            The loaded string mapping.
        """
        return self._mapping(self.layout.data / folder / f"{name}.json")

    def replacement_mapping(self, name: str) -> StringMap:
        """Load a named text-replacement mapping.

        Args:
            name: Logical replacement mapping name.

        Returns:
            The requested replacement mapping.
        """
        return self.data_mapping(name, "replacements")

    def transcription_mapping(self, scheme: str) -> StringMap:
        """Load a mapping from Pinyin to another transcription scheme.

        Args:
            scheme: Logical transcription scheme name.

        Returns:
            The requested Pinyin transcription mapping.
        """
        return self.data_mapping(
            _TRANSCRIPTION_MAPPING_FILES[scheme],
            "transcription_mappings",
        )

    def correction_path(self, scheme: str) -> Path:
        """Return the path to a named language-correction file.

        Args:
            scheme: Logical correction scheme name.

        Returns:
            The correction file path.
        """
        return self.layout.data / "corrections" / f"{_CORRECTION_FILES[scheme]}.json"

    def corrections(self, scheme: str) -> StringMap:
        """Load manual corrections for an output scheme.

        Args:
            scheme: Logical correction scheme name.

        Returns:
            The corrections for the requested scheme.
        """
        corrections = self._mapping(self.correction_path(scheme)).copy()
        if scheme == "hanyu_pinyin":
            corrections.update(self._mapping(self.correction_path("hanyu_pinyin_manual")))
        return corrections

    def universal_corrections(self) -> StringMap:
        """Load corrections shared by all Mandarin-derived output schemes.

        Returns:
            Corrections shared by all Mandarin-derived output schemes.
        """
        return self.corrections("universal")

    def mandarin_phrase_pronunciations(self) -> StringMap:
        """Load manually reviewed Mandarin phrase pronunciations.

        Returns:
            The phrase pronunciation mapping.
        """
        return self.data_mapping("mandarin_phrase_pronunciations")

    def mandarin_word_boundary_corrections(self) -> StringMap:
        """Load shared word-boundary corrections for Minecraft text.

        Returns:
            The word-boundary correction mapping.
        """
        return self.data_mapping("mandarin_word_boundary_corrections")

    def falling_tone_wei_language_keys(self) -> frozenset[str]:
        """Load language keys where U+4E3A must use the falling-tone reading.

        Returns:
            Language keys requiring the falling-tone pronunciation.
        """
        return self._set(self.layout.data / "falling_tone_wei_language_keys.json")
