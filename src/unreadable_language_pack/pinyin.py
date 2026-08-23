"""Transcribe Simplified Chinese into orthographic Hanyu Pinyin."""

import re
import unicodedata
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import jieba
from pypinyin import Style, lazy_pinyin, load_phrases_dict
from pypinyin_dict.phrase_pinyin_data import cc_cedict, di

from unreadable_language_pack.conversion import capitalize_first_cased
from unreadable_language_pack.repository import StringMap

_HAN_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U0002fa1f]+")
_FORMAT_CODE_RE = re.compile(r"§[0-9A-FK-ORa-fk-or]")
_PLACEHOLDER_RE = re.compile(r"%(?:\d+\$)?[A-Za-z%]")
_ORDINAL_RE = re.compile(r"^第([〇零一二两三四五六七八九十百千万亿]+)(.*)$")
_PLACEHOLDER_ORDINAL_RE = re.compile(rf"\b([Dd]ì)\s+({_PLACEHOLDER_RE.pattern})")
_CHINESE_PUNCTUATION = str.maketrans(
    {
        "，": ",",
        "、": ",",
        "？": "?",
        "！": "!",
        "：": ":",
        "；": ";",
        "（": "(",
        "）": ")",
    }
)
_OPENING_PUNCTUATION = frozenset("([<{《“‘【")
_CLOSING_PUNCTUATION = frozenset(",.;:!?)]}>》”’】、…")
_TIGHT_PUNCTUATION = frozenset("—/_+×")
_SENTENCE_ENDINGS = frozenset(".!?。！？\n")
_ASPECT_PARTICLES = frozenset({"着", "了", "过"})


@dataclass(frozen=True, slots=True)
class SegmentedWord:
    """A word produced by the project-configured segmenter."""

    text: str


@dataclass(frozen=True, slots=True)
class _Piece:
    kind: str
    text: str


def _load_pronunciation_dictionaries(phrases: StringMap) -> None:
    """Load third-party dictionaries followed by project corrections."""
    cc_cedict.load()
    di.load()
    load_phrases_dict(
        {word: [[syllable] for syllable in value.split()] for word, value in phrases.items()}
    )


class ChineseSegmenter:
    """Segment Chinese with an isolated jieba tokenizer."""

    def __init__(self, user_dictionary: Path, *, enabled: bool = True) -> None:
        """Initialize an isolated tokenizer with a project dictionary."""
        self.enabled = enabled
        self._tokenizer = jieba.Tokenizer()
        self._tokenizer.load_userdict(str(user_dictionary))

    def words(self, text: str) -> list[SegmentedWord]:
        """Return segmented words."""
        if not self.enabled:
            return [SegmentedWord(text)] if text else []
        return [SegmentedWord(item) for item in self._tokenizer.lcut(text)]

    def strings(self, text: str) -> list[str]:
        """Return segmented words as plain strings."""
        if not self.enabled:
            return text.split()
        return self._tokenizer.lcut(text)


class PinyinTranscriber:
    """Write Pinyin by word while preserving Minecraft text tokens."""

    def __init__(
        self,
        segmenter: ChineseSegmenter,
        phrase_pronunciations: StringMap,
        word_splits: StringMap,
    ) -> None:
        """Initialize the transcriber with segmentation and orthography data."""
        _load_pronunciation_dictionaries(phrase_pronunciations)
        self._segmenter = segmenter
        self._phrase_pronunciations = phrase_pronunciations
        self._word_splits = {word: tuple(parts.split()) for word, parts in word_splits.items()}
        invalid_splits = [
            word for word, parts in self._word_splits.items() if "".join(parts) != word
        ]
        if invalid_splits:
            raise ValueError(f"Invalid Pinyin word splits: {', '.join(invalid_splits)}")
        self._phrases_by_initial: dict[str, tuple[str, ...]] = {}
        for phrase in phrase_pronunciations:
            if len(phrase) < 2:
                continue
            self._phrases_by_initial.setdefault(phrase[0], ())
            self._phrases_by_initial[phrase[0]] += (phrase,)
        self._phrases_by_initial = {
            initial: tuple(sorted(phrases, key=len, reverse=True))
            for initial, phrases in self._phrases_by_initial.items()
        }
        self._partition_cache: dict[str, tuple[tuple[str, bool], ...]] = {}

    def transcribe(self, text: str) -> str:
        """Transcribe the Han characters in text into Hanyu Pinyin."""
        pieces: list[_Piece] = []
        cursor = 0
        sentence_start = True
        title_depth = 0

        matches = list(_HAN_RE.finditer(text))
        for match_index, match in enumerate(matches):
            raw = text[cursor : match.start()]
            if raw:
                pieces.append(_Piece("raw", raw.translate(_CHINESE_PUNCTUATION)))
                sentence_start, title_depth = self._scan_raw(raw, sentence_start, title_depth)

            next_start = (
                matches[match_index + 1].start() if match_index + 1 < len(matches) else len(text)
            )
            following = text[match.end() : next_start]
            clause_ends = not following or any(char in _SENTENCE_ENDINGS for char in following)
            rendered = self._transcribe_han(
                match.group(),
                capitalize=sentence_start,
                capitalize_all=title_depth > 0,
                clause_ends=clause_ends,
            )
            pieces.append(_Piece("han", rendered))
            sentence_start = False
            cursor = match.end()

        tail = text[cursor:]
        if tail:
            pieces.append(_Piece("raw", tail.translate(_CHINESE_PUNCTUATION)))

        return self._normalize_spacing(self._join_pieces(pieces)).strip()

    @staticmethod
    def _scan_raw(raw: str, sentence_start: bool, title_depth: int) -> tuple[bool, int]:
        visible = _FORMAT_CODE_RE.sub("", raw)
        for char in visible:
            if char == "《":
                title_depth += 1
            elif char == "》":
                title_depth = max(0, title_depth - 1)

            if char in _SENTENCE_ENDINGS:
                sentence_start = True
            elif not char.isspace() and char not in _OPENING_PUNCTUATION:
                sentence_start = False
        return sentence_start, title_depth

    def _transcribe_han(
        self,
        text: str,
        *,
        capitalize: bool,
        capitalize_all: bool,
        clause_ends: bool,
    ) -> str:
        words = self._refine_words(self._segmenter.words(text))
        output: list[str] = []

        for index, word in enumerate(words):
            rendered = self._render_word(word)
            if capitalize_all or (capitalize and index == 0):
                rendered = capitalize_first_cased(rendered)

            if index:
                is_clause_final_le = word.text == "了" and index == len(words) - 1 and clause_ends
                separator = "" if word.text in _ASPECT_PARTICLES and not is_clause_final_le else " "
                output.append(separator)
            output.append(rendered)

        return "".join(output)

    def _refine_words(self, words: list[SegmentedWord]) -> list[SegmentedWord]:
        refined: list[SegmentedWord] = []
        for word in words:
            if parts := self._word_splits.get(word.text):
                refined.extend(SegmentedWord(part) for part in parts)
                continue
            partition = self._phrase_partition(word.text)
            if (
                len(partition) > 1
                and all(known for _, known in partition)
                and word.text not in self._phrase_pronunciations
            ):
                refined.extend(SegmentedWord(part) for part, _ in partition)
            else:
                refined.append(word)
        return refined

    def _render_word(self, word: SegmentedWord) -> str:
        ordinal = _ORDINAL_RE.fullmatch(word.text)
        if ordinal:
            number, remainder = ordinal.groups()
            ordinal_text = self._join_syllables(self._syllables(f"第{number}"))
            ordinal_text = ordinal_text.replace("dì", "dì-", 1)
            if remainder:
                return f"{ordinal_text} {self._join_syllables(self._syllables(remainder))}"
            return ordinal_text

        return self._join_syllables(self._syllables(word.text))

    def _syllables(self, word: str) -> list[str]:
        partition = self._phrase_partition(word)
        output: list[str] = []
        for part, _ in partition:
            output.extend(
                lazy_pinyin(
                    part,
                    style=Style.TONE,
                    errors=lambda value: list(value),
                    strict=True,
                    v_to_u=True,
                    tone_sandhi=False,
                )
            )
        return output

    def _phrase_partition(self, word: str) -> tuple[tuple[str, bool], ...]:
        if word in self._partition_cache:
            return self._partition_cache[word]
        if word in self._phrase_pronunciations or len(word) < 2:
            result = ((word, word in self._phrase_pronunciations),)
            self._partition_cache[word] = result
            return result

        @cache
        def solve(index: int) -> tuple[int, int, tuple[tuple[str, bool], ...]]:
            if index == len(word):
                return 0, 0, ()

            candidates: list[tuple[int, int, tuple[tuple[str, bool], ...]]] = []
            for phrase in self._phrases_by_initial.get(word[index], ()):
                if word.startswith(phrase, index):
                    covered, chunks, suffix = solve(index + len(phrase))
                    candidates.append(
                        (covered + len(phrase), chunks + 1, ((phrase, True), *suffix))
                    )

            covered, chunks, suffix = solve(index + 1)
            candidates.append((covered, chunks + 1, ((word[index], False), *suffix)))
            return max(candidates, key=lambda candidate: (candidate[0], -candidate[1]))

        _, _, raw_parts = solve(0)
        merged: list[tuple[str, bool]] = []
        for part, known in raw_parts:
            if merged and not known and not merged[-1][1]:
                merged[-1] = (merged[-1][0] + part, False)
            else:
                merged.append((part, known))
        result = tuple(merged)
        self._partition_cache[word] = result
        return result

    @staticmethod
    def _join_syllables(syllables: list[str]) -> str:
        output: list[str] = []
        for syllable in syllables:
            first = unicodedata.normalize("NFD", syllable[:1]).casefold()[:1]
            if output and first in {"a", "e", "o"} and output[-1][-1:].isalpha():
                output.append("'")
            output.append(syllable)
        return "".join(output)

    @staticmethod
    def _join_pieces(pieces: list[_Piece]) -> str:
        output: list[str] = []
        for index, piece in enumerate(pieces):
            if index:
                left = pieces[index - 1]
                separator = PinyinTranscriber._piece_separator(left, piece)
                if separator:
                    output.append(separator)
            output.append(piece.text)
        return "".join(output)

    @staticmethod
    def _piece_separator(left: _Piece, right: _Piece) -> str:
        if not left.text or not right.text or left.text[-1].isspace() or right.text[0].isspace():
            return ""
        if left.kind == right.kind:
            return ""

        raw = left.text if left.kind == "raw" else right.text
        if left.kind == "raw" and _FORMAT_CODE_RE.search(raw):
            match = tuple(_FORMAT_CODE_RE.finditer(raw))[-1]
            if match.end() == len(raw):
                return ""
        if right.kind == "raw":
            match = _FORMAT_CODE_RE.match(raw)
            if match:
                return ""

        if left.kind == "raw" and _PLACEHOLDER_RE.search(raw):
            match = tuple(_PLACEHOLDER_RE.finditer(raw))[-1]
            if match.end() == len(raw):
                return " "
        if right.kind == "raw" and _PLACEHOLDER_RE.match(raw):
            return " "

        left_char = left.text[-1]
        right_char = right.text[0]
        if left_char in _TIGHT_PUNCTUATION or right_char in _TIGHT_PUNCTUATION:
            return ""
        if left_char in _OPENING_PUNCTUATION or right_char in _CLOSING_PUNCTUATION:
            return ""
        if left_char in _CLOSING_PUNCTUATION or right_char in _OPENING_PUNCTUATION:
            return " "
        if left_char.isalnum() or right_char.isalnum():
            return " "
        return ""

    @staticmethod
    def _normalize_spacing(text: str) -> str:
        text = text.replace("。", ". ").replace("……", "…").replace("——", "—")
        text = _PLACEHOLDER_ORDINAL_RE.sub(r"\1-\2", text)
        text = re.sub(rf"({_PLACEHOLDER_RE.pattern})(?=[(\[])", r"\1 ", text)
        text = re.sub(r"\. +", ". ", text)
        text = re.sub(r"[ \t]+([,.;:!?…\)\]\}>》”’】])", r"\1", text)
        text = re.sub(r"([\(\[\{<《“‘【])[ \t]+", r"\1", text)
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n[ \t]+", "\n", text)

        output: list[str] = []
        for index, char in enumerate(text):
            output.append(char)
            if char not in ",.;:!?":
                continue
            previous = text[index - 1] if index else ""
            following = text[index + 1] if index + 1 < len(text) else ""
            if not following or following.isspace() or following in _CLOSING_PUNCTUATION:
                continue
            if char in ".," and previous.isdigit() and following.isdigit():
                continue
            output.append(" ")
        return "".join(output)
