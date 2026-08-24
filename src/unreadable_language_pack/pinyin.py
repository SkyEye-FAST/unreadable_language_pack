"""Provide the shared Mandarin transcription pipeline for Chinese schemes."""

import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import cast

import jieba
from pypinyin import Style, lazy_pinyin, load_phrases_dict
from pypinyin.style import convert as convert_syllable
from pypinyin_dict.phrase_pinyin_data import cc_cedict, di

from unreadable_language_pack.conversion import capitalize_first_cased
from unreadable_language_pack.repository import StringMap

_HAN_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U0002fa1f]+")
_FORMAT_CODE_RE = re.compile(r"§[0-9A-FK-ORa-fk-or]")
_PLACEHOLDER_RE = re.compile(r"%(?:\d+\$)?[A-Za-z%]")
_ORDINAL_RE = re.compile(r"^第([〇零一二两三四五六七八九十百千万亿]+)(.*)$")
_PLACEHOLDER_ORDINAL_RE = re.compile(rf"\b([Dd]ì)\s+({_PLACEHOLDER_RE.pattern})")
_PINYIN_PUNCTUATION = {
    "，": ",",
    "、": ",",
    "。": ".",
    "？": "?",
    "！": "!",
    "：": ":",
    "；": ";",
    "（": "(",
    "）": ")",
}
_PINYIN_PUNCTUATION_WITH_TRAILING_SPACE = frozenset("，、。？！：；）")
_OPENING_PUNCTUATION = frozenset("([<{《“‘【（")
_CLOSING_PUNCTUATION = frozenset(",.;:!?)]}>》”’】、…，。？！：；）")
_TIGHT_PUNCTUATION = frozenset("—/_+×")
_SENTENCE_ENDINGS = frozenset(".!?。！？\n")
_ASPECT_PARTICLES = frozenset({"着", "了", "过"})
_ORIGINAL_TONE_PINYIN = {"一": "yī", "不": "bù"}
_STANDALONE_TECHNICAL_RE = re.compile(r"^[\[\]{}<>]+$")
_COMMAND_RE = re.compile(r"/[A-Za-z0-9_]")


@dataclass(frozen=True, slots=True)
class SegmentedWord:
    """A word produced by the project-configured segmenter.

    Attributes:
        text: Source text for the segmented word.
        syllables: Transcribed syllables aligned with the source characters.
    """

    text: str
    syllables: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class _Piece:
    kind: str
    text: str


def render_hanyu_pinyin_word(word: SegmentedWord) -> str:
    """Render one segmented word using Hanyu Pinyin orthography.

    Args:
        word: Segmented word and its transcribed syllables.

    Returns:
        The rendered Hanyu Pinyin word.
    """
    ordinal = _ORDINAL_RE.fullmatch(word.text)
    if ordinal:
        number, remainder = ordinal.groups()
        ordinal_end = len(number) + 1
        number_text = _join_hanyu_pinyin_syllables(word.syllables[1:ordinal_end])
        ordinal_text = f"{word.syllables[0]}-{number_text}"
        if remainder:
            remainder_text = _join_hanyu_pinyin_syllables(word.syllables[ordinal_end:])
            return f"{ordinal_text} {remainder_text}"
        return ordinal_text

    return _join_hanyu_pinyin_syllables(word.syllables)


def normalize_hanyu_pinyin_punctuation(text: str) -> str:
    """Convert Chinese prose punctuation without changing ASCII syntax.

    Args:
        text: Text containing source punctuation.

    Returns:
        The text with Hanyu Pinyin punctuation and spacing.
    """
    output: list[str] = []
    index = 0
    while index < len(text):
        if text.startswith("……", index):
            output.append("...")
            index += 2
            continue
        if text.startswith("——", index):
            output.append("—")
            index += 2
            continue

        char = text[index]
        output.append(_PINYIN_PUNCTUATION.get(char, char))
        if char in _PINYIN_PUNCTUATION_WITH_TRAILING_SPACE and index + 1 < len(text):
            following = text[index + 1]
            starts_emoticon = text.startswith(":(", index + 1)
            if not following.isspace() and (
                starts_emoticon or following not in _CLOSING_PUNCTUATION
            ):
                output.append(" ")
        index += 1
    return "".join(output)


def finalize_hanyu_pinyin(text: str) -> str:
    """Apply Hanyu Pinyin rules that depend on the fully rendered text.

    Args:
        text: Fully rendered Hanyu Pinyin text.

    Returns:
        The finalized Hanyu Pinyin text.
    """
    return _PLACEHOLDER_ORDINAL_RE.sub(r"\1-\2", text)


def _join_hanyu_pinyin_syllables(syllables: tuple[str, ...]) -> str:
    output: list[str] = []
    for syllable in syllables:
        first = unicodedata.normalize("NFD", syllable[:1]).casefold()[:1]
        if output and first in {"a", "e", "o"} and output[-1][-1:].isalpha():
            output.append("'")
        output.append(syllable)
    return "".join(output)


def _load_pronunciation_dictionaries(phrases: StringMap) -> None:
    """Load third-party dictionaries followed by project corrections."""
    cc_cedict.load()
    di.load()
    load_phrases_dict(
        {
            word: [[syllable] for syllable in value.split()]
            for word, value in phrases.items()
            if " " not in word
        }
    )


class MandarinSegmenter:
    """Segment Chinese with an isolated jieba tokenizer."""

    def __init__(
        self,
        user_dictionary: Path,
        word_boundary_corrections: StringMap,
        *,
        enabled: bool = True,
    ) -> None:
        """Initialize an isolated tokenizer with project segmentation data.

        Args:
            user_dictionary: Path to the jieba user dictionary.
            word_boundary_corrections: Reviewed word splits for project text.
            enabled: Whether to use automatic jieba segmentation.

        Raises:
            ValueError: If a corrected word boundary changes the source text.
        """
        self.enabled = enabled
        self._tokenizer = jieba.Tokenizer()
        self._tokenizer.load_userdict(str(user_dictionary))
        self._word_boundary_corrections = {
            word: tuple(parts.split()) for word, parts in word_boundary_corrections.items()
        }
        invalid_splits = [
            word
            for word, parts in self._word_boundary_corrections.items()
            if "".join(parts) != word
        ]
        if invalid_splits:
            raise ValueError(f"Invalid Mandarin word splits: {', '.join(invalid_splits)}")

    def words(self, text: str) -> list[SegmentedWord]:
        """Return segmented words.

        Args:
            text: Mandarin text to segment.

        Returns:
            The segmented words.
        """
        if not self.enabled:
            return [SegmentedWord(text)] if text else []
        output: list[SegmentedWord] = []
        for item in self._tokenizer.lcut(text):
            parts = self._word_boundary_corrections.get(item, (item,))
            output.extend(SegmentedWord(part) for part in parts)
        return output

    def strings(self, text: str) -> list[str]:
        """Return segmented words as plain strings.

        Args:
            text: Mandarin text to segment.

        Returns:
            The segmented word text.
        """
        if not self.enabled:
            return text.split()
        return [word.text for word in self.words(text)]


class MandarinTranscriber:
    """Render Mandarin by word while preserving Minecraft text tokens."""

    def __init__(
        self,
        segmenter: MandarinSegmenter,
        phrase_pronunciations: StringMap,
    ) -> None:
        """Initialize the transcriber with segmentation and orthography data.

        Args:
            segmenter: Project-configured Mandarin word segmenter.
            phrase_pronunciations: Reviewed pronunciations for words and contexts.

        Raises:
            ValueError: If a pronunciation does not contain one syllable per Han character.
        """
        _load_pronunciation_dictionaries(phrase_pronunciations)
        self._segmenter = segmenter
        self._phrase_pronunciations = {
            phrase: pronunciation
            for phrase, pronunciation in phrase_pronunciations.items()
            if " " not in phrase
        }
        invalid_pronunciations = [
            phrase
            for phrase, pronunciation in phrase_pronunciations.items()
            if len(pronunciation.split()) != len(phrase.replace(" ", ""))
        ]
        if invalid_pronunciations:
            raise ValueError(
                f"Expected one syllable per Han character: {', '.join(invalid_pronunciations)}"
            )
        self._phrases_by_initial: dict[str, tuple[str, ...]] = {}
        for phrase in self._phrase_pronunciations:
            if len(phrase) < 2:
                continue
            self._phrases_by_initial.setdefault(phrase[0], ())
            self._phrases_by_initial[phrase[0]] += (phrase,)
        self._phrases_by_initial = {
            initial: tuple(sorted(phrases, key=len, reverse=True))
            for initial, phrases in self._phrases_by_initial.items()
        }
        self._contexts_by_initial: dict[
            str, tuple[tuple[tuple[str, ...], tuple[str, ...]], ...]
        ] = {}
        for phrase, pronunciation in phrase_pronunciations.items():
            words = tuple(phrase.split())
            if len(words) < 2:
                continue
            self._contexts_by_initial.setdefault(words[0], ())
            self._contexts_by_initial[words[0]] += ((words, tuple(pronunciation.split())),)
        self._contexts_by_initial = {
            initial: tuple(sorted(contexts, key=lambda item: len(item[0]), reverse=True))
            for initial, contexts in self._contexts_by_initial.items()
        }
        self._partition_cache: dict[str, tuple[tuple[str, bool], ...]] = {}

    def transcribe(
        self,
        text: str,
        renderer: Callable[[SegmentedWord], str],
        *,
        style: Style,
        neutral_tone_with_five: bool,
        v_to_u: bool,
        capitalize: bool,
        attach_aspect_particles: bool,
        lexical_tones: bool,
        raw_transform: Callable[[str], str] | None = None,
    ) -> str:
        """Transcribe Han spans with a scheme-specific word renderer.

        Args:
            text: Source text containing Mandarin and Minecraft syntax.
            renderer: Function that renders one segmented word.
            style: Pypinyin output style used to produce word syllables.
            neutral_tone_with_five: Whether tone 5 marks neutral-tone syllables.
            v_to_u: Whether ``v`` should be converted to ``ü``.
            capitalize: Whether sentence- and title-initial words are capitalized.
            attach_aspect_particles: Whether medial aspect particles attach to a word.
            lexical_tones: Whether to restore the lexical tones of ``一`` and ``不``.
            raw_transform: Optional transformation for non-Han text spans.

        Returns:
            The rendered transcription with Minecraft syntax preserved.
        """
        pieces: list[_Piece] = []
        cursor = 0
        sentence_start = True
        title_start = False
        transform_raw = raw_transform or _preserve_raw

        matches = list(_HAN_RE.finditer(text))
        for match_index, match in enumerate(matches):
            raw = text[cursor : match.start()]
            if raw:
                pieces.append(_Piece("raw", transform_raw(raw)))
                sentence_start, title_start = self._scan_raw(
                    raw,
                    sentence_start,
                    title_start,
                )

            next_start = (
                matches[match_index + 1].start() if match_index + 1 < len(matches) else len(text)
            )
            following = text[match.end() : next_start]
            clause_ends = not following or any(char in _SENTENCE_ENDINGS for char in following)
            rendered = self._transcribe_han(
                match.group(),
                renderer,
                style=style,
                neutral_tone_with_five=neutral_tone_with_five,
                v_to_u=v_to_u,
                capitalize=capitalize and (sentence_start or title_start),
                clause_ends=clause_ends,
                attach_aspect_particles=attach_aspect_particles,
                lexical_tones=lexical_tones,
            )
            pieces.append(_Piece("han", rendered))
            sentence_start = False
            title_start = False
            cursor = match.end()

        tail = text[cursor:]
        if tail:
            pieces.append(_Piece("raw", transform_raw(tail)))

        return self._join_pieces(pieces)

    @staticmethod
    def _scan_raw(raw: str, sentence_start: bool, title_start: bool) -> tuple[bool, bool]:
        visible = _FORMAT_CODE_RE.sub("", raw)
        for char in visible:
            if char == "《":
                title_start = True
                continue
            elif char == "》":
                title_start = False

            if char in _SENTENCE_ENDINGS:
                sentence_start = True
            elif not char.isspace() and char not in _OPENING_PUNCTUATION:
                sentence_start = False
                title_start = False
        return sentence_start, title_start

    def _transcribe_han(
        self,
        text: str,
        renderer: Callable[[SegmentedWord], str],
        *,
        style: Style,
        neutral_tone_with_five: bool,
        v_to_u: bool,
        capitalize: bool,
        clause_ends: bool,
        attach_aspect_particles: bool,
        lexical_tones: bool,
    ) -> str:
        words = self._refine_words(self._segmenter.words(text))
        syllables: list[str] = []
        for word in words:
            word_syllables = lazy_pinyin(
                word.text,
                style=style,
                # Pypinyin accepts list[str] here, although its type stub only declares str.
                errors=cast(Callable[[str], str], _split_untranscribed_characters),
                strict=True,
                v_to_u=v_to_u,
                neutral_tone_with_five=neutral_tone_with_five,
                tone_sandhi=False,
            )
            if len(word_syllables) != len(word.text):
                raise ValueError(f"Expected one syllable per Han character in {word.text!r}")
            syllables.extend(word_syllables)

        syllables = self._apply_context_pronunciations(
            text,
            words,
            syllables,
            style=style,
            neutral_tone_with_five=neutral_tone_with_five,
        )
        if lexical_tones:
            syllables = self._apply_original_tones(text, syllables, style=style)
        if len(syllables) != len(text):
            raise ValueError(f"Expected one syllable per Han character in {text!r}")
        output: list[str] = []
        syllable_index = 0

        for index, word in enumerate(words):
            end = syllable_index + len(word.text)
            word = SegmentedWord(word.text, tuple(syllables[syllable_index:end]))
            syllable_index = end
            rendered = renderer(word)
            if capitalize and index == 0:
                rendered = capitalize_first_cased(rendered)

            if index:
                is_clause_final_le = word.text == "了" and index == len(words) - 1 and clause_ends
                attach_particle = (
                    attach_aspect_particles
                    and word.text in _ASPECT_PARTICLES
                    and not is_clause_final_le
                )
                separator = "" if attach_particle else " "
                output.append(separator)
            output.append(rendered)

        return "".join(output)

    def _apply_context_pronunciations(
        self,
        text: str,
        words: list[SegmentedWord],
        syllables: list[str],
        *,
        style: Style,
        neutral_tone_with_five: bool,
    ) -> list[str]:
        output = syllables.copy()
        word_index = 0
        character_index = 0
        while word_index < len(words):
            context = next(
                (
                    item
                    for item in self._contexts_by_initial.get(words[word_index].text, ())
                    if tuple(word.text for word in words[word_index : word_index + len(item[0])])
                    == item[0]
                ),
                None,
            )
            if context is None:
                character_index += len(words[word_index].text)
                word_index += 1
                continue

            context_words, pronunciation = context
            for offset, pinyin in enumerate(pronunciation):
                converted = convert_syllable(
                    pinyin,
                    style,
                    strict=True,
                    neutral_tone_with_five=neutral_tone_with_five,
                    han=text[character_index + offset],
                )
                if style == Style.TONE3 and neutral_tone_with_five and converted[-1:] not in "1234":
                    converted = f"{converted}5"
                output[character_index + offset] = converted
            matched_length = sum(len(word) for word in context_words)
            character_index += matched_length
            word_index += len(context_words)
        return output

    @staticmethod
    def _apply_original_tones(text: str, syllables: list[str], *, style: Style) -> list[str]:
        """Restore the lexical tones of yi and bu for written transcription."""
        output = syllables.copy()
        for index, char in enumerate(text):
            if pinyin := _ORIGINAL_TONE_PINYIN.get(char):
                output[index] = convert_syllable(pinyin, style, strict=True, han=char)
        return output

    def _refine_words(self, words: list[SegmentedWord]) -> list[SegmentedWord]:
        refined: list[SegmentedWord] = []
        for word in words:
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
    def _join_pieces(pieces: list[_Piece]) -> str:
        output: list[str] = []
        for index, piece in enumerate(pieces):
            if index:
                left = pieces[index - 1]
                separator = MandarinTranscriber._piece_separator(left, piece)
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

        if _is_standalone_technical(raw):
            return " "
        if right.kind == "raw" and _COMMAND_RE.match(raw):
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


def _preserve_raw(text: str) -> str:
    return text


def _split_untranscribed_characters(text: str) -> list[str]:
    return list(text)


def _is_standalone_technical(text: str) -> bool:
    return _STANDALONE_TECHNICAL_RE.fullmatch(text.strip()) is not None
