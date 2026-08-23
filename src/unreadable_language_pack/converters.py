"""Text converters for every generated language scheme."""

import re
from collections.abc import Mapping

from pypinyin import Style, lazy_pinyin
from romajitable import to_kana

from unreadable_language_pack.conversion import (
    capitalize_sentences,
    capitalize_titles,
    replace_multiple,
)
from unreadable_language_pack.pinyin import ChineseSegmenter, PinyinTranscriber
from unreadable_language_pack.repository import DataRepository

_TONE_TO_IPA = {"1": "˥", "2": "˧˥", "3": "˨˩˦", "4": "˥˩", "5": ""}


class EnglishConverter:
    """Convert English into the project's entertainment-oriented schemes."""

    def __init__(self, repository: DataRepository) -> None:
        """Initialize the converter from project data."""
        self._replacements = repository.replacements("ja_kk")
        self._manyogana = repository.data_map("manyogana")

    @staticmethod
    def to_i7h(text: str) -> str:
        """Abbreviate words to their first character, inner length, and last character."""
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
        """Approximately transcribe English into katakana."""
        return replace_multiple(to_kana(text).katakana, self._replacements)

    def to_manyogana(self, text: str) -> str:
        """Approximately transcribe English into man'yogana through katakana."""
        return "".join(self._manyogana.get(char, char) for char in self.to_katakana(text))


class ChineseConverter:
    """Convert Mandarin Chinese into Pinyin and derived transcription schemes."""

    def __init__(
        self,
        repository: DataRepository,
        *,
        auto_segment: bool = True,
        replacements: Mapping[str, str] | None = None,
    ) -> None:
        """Initialize the converter from project data and segmentation settings."""
        self._repository = repository
        self._replacements = replacements or repository.replacements("zh")
        self._segmenter = ChineseSegmenter(
            repository.layout.data / "dict.txt",
            enabled=auto_segment,
        )
        self._pinyin = PinyinTranscriber(
            self._segmenter,
            repository.custom_phrases(),
            repository.pinyin_splits(),
        )
        self._maps = {
            scheme: repository.pinyin_map(scheme)
            for scheme in (
                "wadegiles",
                "romatzyh",
                "simp_romatzyh",
                "mps2",
                "tongyong",
                "yale",
                "ipa",
                "katakana",
                "cyrillic",
                "xiaojing",
            )
        }
        self._gr_values = set(self._maps["romatzyh"].values())
        self._cy_values = set(self._maps["cyrillic"].values())

    def preprocess_pronunciation(self, key: str, text: str) -> str:
        """Apply pronunciation fixes that depend on a specific language key."""
        if key in self._repository.force_wei_keys():
            return text.replace("为", "位")
        return text

    def to_split(self, text: str) -> str:
        """Return segmented Chinese text for manual review."""
        replacements = self._replacements | {
            "了.": " 了.",
            "了!": " 了!",
            "了?": " 了?",
            "了…": " 了…",
            "之物": "之 物",
        }
        segmented = " ".join(self._segmenter.strings(text)).replace(" 了", "了")
        return replace_multiple(segmented, replacements)

    def to_pinyin(self, text: str) -> str:
        """Transcribe text using the core orthographic rules of GB/T 16159-2012."""
        return self._pinyin.transcribe(text)

    def _pinyin_to_other(self, scheme: str, text: str, delimiter: str = "-") -> str:
        output: list[str] = []
        segments = self._segmenter.strings(text)
        correspondence = self._maps[scheme]

        for index, segment in enumerate(segments):
            syllables = lazy_pinyin(
                segment,
                style=Style.TONE3,
                neutral_tone_with_five=True,
                tone_sandhi=False,
            )
            converted = delimiter.join(correspondence.get(item, item) for item in syllables)
            if index and not (
                segment == "了"
                and index + 1 < len(segments)
                and segments[index + 1] not in {"。", "！", "？", "…"}
            ):
                output.append(" ")
            output.append(converted)

        result = replace_multiple("".join(output), self._replacements)
        return capitalize_sentences(capitalize_titles(result))

    def to_ipa(self, text: str) -> str:
        """Transcribe Mandarin into broad IPA notation."""
        output: list[str] = []
        for syllable in lazy_pinyin(
            text,
            style=Style.TONE3,
            neutral_tone_with_five=True,
            tone_sandhi=False,
        ):
            if syllable[-1:] in _TONE_TO_IPA:
                output.append(
                    f"{self._maps['ipa'].get(syllable[:-1], syllable[:-1])}"
                    f"{_TONE_TO_IPA[syllable[-1]]}"
                )
            else:
                output.append(syllable)
        return " ".join(output)

    @staticmethod
    def to_bopomofo(text: str) -> str:
        """Transcribe Mandarin into Bopomofo."""
        symbols = lazy_pinyin(text, style=Style.BOPOMOFO, tone_sandhi=False)
        return " ".join(f"˙{item[:-1]}" if item.endswith("˙") else item for item in symbols)

    def to_wadegiles(self, text: str) -> str:
        """Transcribe Mandarin using Wade-Giles romanization."""
        return self._pinyin_to_other("wadegiles", text)

    def to_romatzyh(self, text: str) -> str:
        """Transcribe Mandarin using Gwoyeu Romatzyh."""
        output: list[str] = []
        for segment in self._segmenter.strings(text):
            syllables = lazy_pinyin(
                segment.replace("不", "bu"),
                style=Style.TONE3,
                neutral_tone_with_five=True,
                tone_sandhi=False,
            )
            converted = [self._maps["romatzyh"].get(item, item) for item in syllables]
            output.append("".join(self._add_apostrophes(converted, self._gr_values)))
        result = replace_multiple(" ".join(output), self._replacements)
        return capitalize_sentences(capitalize_titles(result))

    def to_simp_romatzyh(self, text: str) -> str:
        """Transcribe Mandarin using Simplified Gwoyeu Romatzyh."""
        return self._pinyin_to_other("simp_romatzyh", text, delimiter="")

    def to_mps2(self, text: str) -> str:
        """Transcribe Mandarin using Mandarin Phonetic Symbols II."""
        return self._pinyin_to_other("mps2", text)

    def to_tongyong(self, text: str) -> str:
        """Transcribe Mandarin using Tongyong Pinyin."""
        return self._pinyin_to_other("tongyong", text)

    def to_yale(self, text: str) -> str:
        """Transcribe Mandarin using Yale romanization."""
        return self._pinyin_to_other("yale", text)

    def to_katakana(self, text: str) -> str:
        """Transcribe Mandarin pronunciation into katakana."""
        syllables = lazy_pinyin(text, tone_sandhi=False)
        return " ".join(self._maps["katakana"].get(item, item) for item in syllables)

    def to_cyrillic(self, text: str) -> str:
        """Transcribe Mandarin into Cyrillic using the Palladius system."""
        output: list[str] = []
        for segment in self._segmenter.strings(text):
            syllables = lazy_pinyin(segment, tone_sandhi=False)
            converted = [self._maps["cyrillic"].get(item, item) for item in syllables]
            output.append("".join(self._add_apostrophes(converted, self._cy_values)))
        result = replace_multiple(" ".join(output), self._replacements)
        return capitalize_sentences(capitalize_titles(result))

    def to_xiaojing(self, text: str) -> str:
        """Transcribe Mandarin pronunciation into Xiao'erjing."""
        output: list[str] = []
        for segment in self._segmenter.strings(text):
            syllables = lazy_pinyin(segment, tone_sandhi=False)
            output.append(
                "\u200c".join(self._maps["xiaojing"].get(item, item) for item in syllables)
            )
        return replace_multiple(" ".join(output), self._replacements)

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
