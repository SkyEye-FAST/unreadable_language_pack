"""Shared workflow for converting language dictionaries."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from time import perf_counter

from unreadable_language_pack.repository import StringMap

type TextTransform = Callable[[str], str]
type LanguageEntryPreprocessor = Callable[[str, str], str]


class ConversionError(RuntimeError):
    """Raised when a language entry cannot be converted."""


@dataclass(frozen=True, slots=True)
class LanguageConversionResult:
    """Result of converting one language dictionary.

    Attributes:
        data: Converted language entries.
        elapsed_seconds: Conversion duration in seconds.
    """

    data: StringMap
    elapsed_seconds: float


def convert_language_entries(
    source: Mapping[str, str],
    transform: TextTransform,
    *,
    corrections: Mapping[str, str] | None = None,
    universal_corrections: Mapping[str, str] | None = None,
    preprocess_entry: LanguageEntryPreprocessor | None = None,
) -> LanguageConversionResult:
    """Convert a language dictionary while retaining the failing key in errors.

    Args:
        source: Source language dictionary.
        transform: Function applied to each source value.
        corrections: Optional corrections for specific language entries.
        universal_corrections: Optional corrections shared by all output schemes.
        preprocess_entry: Optional function applied to each key and value before conversion.

    Returns:
        The converted data and elapsed time.

    Raises:
        ConversionError: If a language entry cannot be converted.
    """
    started = perf_counter()
    output: StringMap = {}

    for key, value in source.items():
        try:
            prepared = preprocess_entry(key, value) if preprocess_entry else value
            output[key] = transform(prepared)
        except Exception as exc:
            raise ConversionError(f"Failed to convert language key {key!r}: {exc}") from exc

    if universal_corrections:
        output.update(universal_corrections)
    if corrections:
        output.update(corrections)

    return LanguageConversionResult(output, perf_counter() - started)


def replace_multiple(text: str, replacements: Mapping[str, str]) -> str:
    """Apply text replacements in the order stored by the data file.

    Args:
        text: Text to modify.
        replacements: Mapping of source strings to replacement strings.

    Returns:
        The text after applying every replacement.
    """
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def capitalize_first_cased(text: str) -> str:
    """Uppercase the first cased character without changing the remainder.

    Args:
        text: Text to capitalize.

    Returns:
        The text with its first cased character uppercased.
    """
    for index, char in enumerate(text):
        if char.isalpha():
            return f"{text[:index]}{char.upper()}{text[index + 1 :]}"
    return text
