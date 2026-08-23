"""Shared workflow for converting language dictionaries."""

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from time import perf_counter

from unreadable_language_pack.repository import StringMap

type TextTransform = Callable[[str], str]
type TextPreprocessor = Callable[[str, str], str]


class ConversionError(RuntimeError):
    """Raised when a language entry cannot be converted."""


@dataclass(frozen=True, slots=True)
class ConversionResult:
    """Result of converting one language dictionary."""

    data: StringMap
    elapsed_seconds: float


def convert_language(
    source: Mapping[str, str],
    transform: TextTransform,
    *,
    fixes: Mapping[str, str] | None = None,
    universal_fixes: Mapping[str, str] | None = None,
    preprocess: TextPreprocessor | None = None,
) -> ConversionResult:
    """Convert a language dictionary while retaining the failing key in errors."""
    started = perf_counter()
    output: StringMap = {}

    for key, value in source.items():
        try:
            prepared = preprocess(key, value) if preprocess else value
            output[key] = transform(prepared)
        except Exception as exc:
            raise ConversionError(f"转换语言键 {key!r} 失败：{exc}") from exc

    if universal_fixes:
        output.update(universal_fixes)
    if fixes:
        output.update(fixes)

    return ConversionResult(output, perf_counter() - started)


def replace_multiple(text: str, replacements: Mapping[str, str]) -> str:
    """Apply text replacements in the order stored by the data file."""
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def capitalize_first_cased(text: str) -> str:
    """Uppercase the first cased character without changing the remainder."""
    for index, char in enumerate(text):
        if char.isalpha():
            return f"{text[:index]}{char.upper()}{text[index + 1 :]}"
    return text


def capitalize_sentences(text: str) -> str:
    """Capitalize the first letter of each line and after an ellipsis."""

    def capitalize_ellipsis(segment: str) -> str:
        parts: list[str] = []
        for part in segment.split("..."):
            if not part:
                parts.append(part)
            elif part.startswith(" ") and len(part) > 1:
                parts.append(f" {part[1].upper()}{part[2:]}")
            else:
                parts.append(f"{part[0].upper()}{part[1:]}")
        return "...".join(parts)

    if not text:
        return text
    return "\n".join(capitalize_ellipsis(line) for line in text.split("\n"))


def capitalize_titles(text: str) -> str:
    """Capitalize each space-delimited unit inside Chinese title marks."""

    def capitalize_match(match: re.Match[str]) -> str:
        words = (capitalize_first_cased(word) for word in match.group(1).split())
        return f"《{' '.join(words)}》"

    return re.sub(
        r"《(.*?)》",
        capitalize_match,
        text,
    )
