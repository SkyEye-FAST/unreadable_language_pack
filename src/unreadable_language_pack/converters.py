"""Text converters for every generated language scheme."""

import re

from pypinyin import Style
from romajitable import to_kana

from unreadable_language_pack.conversion import replace_multiple
from unreadable_language_pack.pinyin import (
    MandarinSegmenter,
    MandarinTranscriber,
    SegmentedWord,
    finalize_hanyu_pinyin,
    normalize_hanyu_pinyin_punctuation,
    render_hanyu_pinyin_word,
)
from unreadable_language_pack.repository import LanguageDataRepository

_TONE_TO_IPA = {"1": "˥", "2": "˧˥", "3": "˨˩˦", "4": "˥˩", "5": ""}


class EnglishConverter:
    """Convert English into the project's entertainment-oriented schemes."""

    def __init__(self, repository: LanguageDataRepository) -> None:
        """Initialize the converter from project data.

        Args:
            repository: Repository containing transcription mappings.
        """
        self._replacements = repository.replacement_mapping("english_to_katakana")
        self._manyogana = repository.data_mapping("katakana_to_manyogana")

    @staticmethod
    def to_numeronym(text: str) -> str:
        """Abbreviate words to their first character, inner length, and last character.

        Args:
            text: Text to abbreviate.

        Returns:
            Text with words longer than two characters converted to numeronyms.
        """
        return re.sub(
            r"[^\W_]+",
            lambda match: (
                f"{match.group()[0]}{len(match.group()) - 2}{match.group()[-1]}"
                if len(match.group()) > 2
                else match.group()
            ),
            text,
        )

    def to_katakana(self, text: str) -> str:
        """Approximately transcribe English into katakana.

        Args:
            text: English text to transcribe.

        Returns:
            The katakana transcription.
        """
        return replace_multiple(to_kana(text).katakana, self._replacements)

    def to_manyogana(self, text: str) -> str:
        """Approximately transcribe English into man'yogana through katakana.

        Args:
            text: English text to transcribe.

        Returns:
            The man'yogana transcription.
        """
        return "".join(self._manyogana.get(char, char) for char in self.to_katakana(text))


class MandarinConverter:
    """Convert Mandarin Chinese into Pinyin and derived transcription schemes."""

    def __init__(
        self,
        repository: LanguageDataRepository,
        *,
        auto_segment: bool = True,
    ) -> None:
        """Initialize the converter from project data and segmentation settings.

        Args:
            repository: Repository containing Mandarin transcription data.
            auto_segment: Whether to segment Mandarin text automatically.
        """
        self._repository = repository
        self._split_replacements = repository.replacement_mapping("mandarin_segmentation")
        self._segmenter = MandarinSegmenter(
            repository.layout.data / "mandarin_segmentation_dictionary.txt",
            repository.mandarin_word_boundary_corrections(),
            enabled=auto_segment,
        )
        self._mandarin = MandarinTranscriber(
            self._segmenter,
            repository.mandarin_phrase_pronunciations(),
        )
        self._maps = {
            scheme: repository.transcription_mapping(scheme)
            for scheme in (
                "wade_giles",
                "gwoyeu_romatzyh",
                "simplified_gwoyeu_romatzyh",
                "mandarin_phonetic_symbols_ii",
                "tongyong_pinyin",
                "yale_romanization",
                "ipa",
                "katakana",
                "cyrillic",
                "xiaoerjing",
            )
        }
        self._gr_values = set(self._maps["gwoyeu_romatzyh"].values())
        self._cy_values = set(self._maps["cyrillic"].values())

    def apply_key_specific_pronunciation(self, key: str, text: str) -> str:
        """Apply pronunciation corrections that depend on a language key.

        Args:
            key: Minecraft language key for the text.
            text: Mandarin source text.

        Returns:
            The text with key-specific pronunciation corrections applied.
        """
        if key in self._repository.falling_tone_wei_language_keys():
            return text.replace("为", "位")
        return text

    def to_split(self, text: str) -> str:
        """Return segmented Chinese text for manual review.

        Args:
            text: Mandarin text to segment.

        Returns:
            The segmented text.
        """
        replacements = self._split_replacements | {
            "了.": " 了.",
            "了!": " 了!",
            "了?": " 了?",
            "了…": " 了…",
            "之物": "之 物",
        }
        segmented = " ".join(self._segmenter.strings(text)).replace(" 了", "了")
        return replace_multiple(segmented, replacements)

    def to_hanyu_pinyin(self, text: str) -> str:
        """Transcribe text using the core orthographic rules of GB/T 16159-2012.

        Args:
            text: Mandarin text to transcribe.

        Returns:
            The Hanyu Pinyin transcription.
        """
        result = self._mandarin.transcribe(
            text,
            render_hanyu_pinyin_word,
            style=Style.TONE,
            neutral_tone_with_five=False,
            v_to_u=True,
            capitalize=True,
            attach_aspect_particles=True,
            lexical_tones=True,
            raw_transform=normalize_hanyu_pinyin_punctuation,
        )
        return finalize_hanyu_pinyin(result)

    def _transcribe_from_pinyin_mapping(
        self,
        scheme: str,
        text: str,
        delimiter: str = "-",
    ) -> str:
        correspondence = self._maps[scheme]

        def render(word: SegmentedWord) -> str:
            return delimiter.join(correspondence.get(item, item) for item in word.syllables)

        result = self._mandarin.transcribe(
            text,
            render,
            style=Style.TONE3,
            neutral_tone_with_five=True,
            v_to_u=False,
            capitalize=True,
            attach_aspect_particles=True,
            lexical_tones=True,
        )
        return result

    def to_ipa(self, text: str) -> str:
        """Transcribe Mandarin into broad IPA notation.

        Args:
            text: Mandarin text to transcribe.

        Returns:
            The broad IPA transcription.
        """

        def render(word: SegmentedWord) -> str:
            output: list[str] = []
            for syllable in word.syllables:
                if syllable[-1:] in _TONE_TO_IPA:
                    output.append(
                        f"{self._maps['ipa'].get(syllable[:-1], syllable[:-1])}"
                        f"{_TONE_TO_IPA[syllable[-1]]}"
                    )
                else:
                    output.append(syllable)
            return " ".join(output)

        return self._mandarin.transcribe(
            text,
            render,
            style=Style.TONE3,
            neutral_tone_with_five=True,
            v_to_u=False,
            capitalize=False,
            attach_aspect_particles=False,
            lexical_tones=False,
        )

    def to_bopomofo(self, text: str) -> str:
        """Transcribe Mandarin into Bopomofo.

        Args:
            text: Mandarin text to transcribe.

        Returns:
            The Bopomofo transcription.
        """

        def render(word: SegmentedWord) -> str:
            return " ".join(
                f"˙{item[:-1]}" if item.endswith("˙") else item for item in word.syllables
            )

        return self._mandarin.transcribe(
            text,
            render,
            style=Style.BOPOMOFO,
            neutral_tone_with_five=False,
            v_to_u=False,
            capitalize=False,
            attach_aspect_particles=False,
            lexical_tones=True,
        )

    def to_wade_giles(self, text: str) -> str:
        """Transcribe Mandarin using Wade-Giles romanization.

        Args:
            text: Mandarin text to transcribe.

        Returns:
            The Wade-Giles transcription.
        """
        return self._transcribe_from_pinyin_mapping("wade_giles", text)

    def to_gwoyeu_romatzyh(self, text: str) -> str:
        """Transcribe Mandarin using Gwoyeu Romatzyh.

        Args:
            text: Mandarin text to transcribe.

        Returns:
            The Gwoyeu Romatzyh transcription.
        """

        def render(word: SegmentedWord) -> str:
            converted = [self._maps["gwoyeu_romatzyh"].get(item, item) for item in word.syllables]
            return "".join(self._add_apostrophes(converted, self._gr_values))

        result = self._mandarin.transcribe(
            text,
            render,
            style=Style.TONE3,
            neutral_tone_with_five=True,
            v_to_u=False,
            capitalize=True,
            attach_aspect_particles=False,
            lexical_tones=True,
        )
        return result

    def to_simplified_gwoyeu_romatzyh(self, text: str) -> str:
        """Transcribe Mandarin using Simplified Gwoyeu Romatzyh.

        Args:
            text: Mandarin text to transcribe.

        Returns:
            The Simplified Gwoyeu Romatzyh transcription.
        """
        return self._transcribe_from_pinyin_mapping(
            "simplified_gwoyeu_romatzyh",
            text,
            delimiter="",
        )

    def to_mandarin_phonetic_symbols_ii(self, text: str) -> str:
        """Transcribe Mandarin using Mandarin Phonetic Symbols II.

        Args:
            text: Mandarin text to transcribe.

        Returns:
            The Mandarin Phonetic Symbols II transcription.
        """
        return self._transcribe_from_pinyin_mapping("mandarin_phonetic_symbols_ii", text)

    def to_tongyong_pinyin(self, text: str) -> str:
        """Transcribe Mandarin using Tongyong Pinyin.

        Args:
            text: Mandarin text to transcribe.

        Returns:
            The Tongyong Pinyin transcription.
        """
        return self._transcribe_from_pinyin_mapping("tongyong_pinyin", text)

    def to_yale_romanization(self, text: str) -> str:
        """Transcribe Mandarin using Yale romanization.

        Args:
            text: Mandarin text to transcribe.

        Returns:
            The Yale romanization.
        """
        return self._transcribe_from_pinyin_mapping("yale_romanization", text)

    def to_katakana(self, text: str) -> str:
        """Transcribe Mandarin pronunciation into katakana.

        Args:
            text: Mandarin text to transcribe.

        Returns:
            The katakana transcription.
        """

        def render(word: SegmentedWord) -> str:
            return " ".join(self._maps["katakana"].get(item, item) for item in word.syllables)

        return self._mandarin.transcribe(
            text,
            render,
            style=Style.NORMAL,
            neutral_tone_with_five=False,
            v_to_u=False,
            capitalize=False,
            attach_aspect_particles=False,
            lexical_tones=False,
        )

    def to_cyrillic(self, text: str) -> str:
        """Transcribe Mandarin into Cyrillic using the Palladius system.

        Args:
            text: Mandarin text to transcribe.

        Returns:
            The Palladius-system Cyrillic transcription.
        """

        def render(word: SegmentedWord) -> str:
            converted = [self._maps["cyrillic"].get(item, item) for item in word.syllables]
            return "".join(self._add_apostrophes(converted, self._cy_values))

        result = self._mandarin.transcribe(
            text,
            render,
            style=Style.NORMAL,
            neutral_tone_with_five=False,
            v_to_u=False,
            capitalize=True,
            attach_aspect_particles=False,
            lexical_tones=False,
        )
        return result

    def to_xiaoerjing(self, text: str) -> str:
        """Transcribe Mandarin pronunciation into Xiao'erjing.

        Args:
            text: Mandarin text to transcribe.

        Returns:
            The Xiao'erjing transcription.
        """

        def render(word: SegmentedWord) -> str:
            return "\u200c".join(
                self._maps["xiaoerjing"].get(item, item) for item in word.syllables
            )

        result = self._mandarin.transcribe(
            text,
            render,
            style=Style.NORMAL,
            neutral_tone_with_five=False,
            v_to_u=False,
            capitalize=False,
            attach_aspect_particles=False,
            lexical_tones=False,
        )
        return result

    @staticmethod
    def _add_apostrophes(items: list[str], values: set[str]) -> list[str]:
        output = items.copy()
        for index in range(1, len(output)):
            previous = output[index - 1]
            for offset in range(len(previous)):
                prefix = previous[: -offset - 1]
                suffix = previous[-offset:]
                if prefix in values and f"{suffix}{output[index]}" in values:
                    output[index] = f"'{output[index]}"
                    break
        return output
