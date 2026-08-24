"""Generate language files and assemble the Minecraft resource pack."""

from collections.abc import Mapping
from dataclasses import dataclass
from time import perf_counter
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from unreadable_language_pack.conversion import (
    LanguageConversionResult,
    LanguageEntryPreprocessor,
    TextTransform,
    convert_language_entries,
)
from unreadable_language_pack.converters import EnglishConverter, MandarinConverter
from unreadable_language_pack.repository import (
    LanguageDataRepository,
    ProjectLayout,
    format_file_size,
    write_json,
)


@dataclass(frozen=True, slots=True)
class LanguageFileBuild:
    """Configuration for generating one language file.

    Attributes:
        output_name: Base name of the generated language file.
        source: Source language entries.
        transform: Transformation applied to each source value.
        corrections: Corrections for specific language entries.
        universal_corrections: Corrections shared by all Mandarin schemes.
        preprocess_entry: Optional preprocessing for each key and value.
    """

    output_name: str
    source: Mapping[str, str]
    transform: TextTransform
    corrections: Mapping[str, str] | None = None
    universal_corrections: Mapping[str, str] | None = None
    preprocess_entry: LanguageEntryPreprocessor | None = None


class ResourcePackBuilder:
    """Orchestrate conversions and create a reproducible resource pack."""

    def __init__(self, layout: ProjectLayout) -> None:
        """Initialize the builder for a project layout.

        Args:
            layout: Filesystem layout of the project.
        """
        self.layout = layout
        self.repository = LanguageDataRepository(layout)

    def generate_language_files(self) -> tuple[list[str], float]:
        """Generate all language files.

        Returns:
            The generated output names and elapsed time in seconds.
        """
        started = perf_counter()
        outputs: list[str] = []

        for task in self._language_file_builds():
            result = convert_language_entries(
                task.source,
                task.transform,
                corrections=task.corrections,
                universal_corrections=task.universal_corrections,
                preprocess_entry=task.preprocess_entry,
            )
            self._write_language_file(task.output_name, result)
            outputs.append(task.output_name)

        return outputs, perf_counter() - started

    def create_resource_pack(self, output_names: list[str]) -> tuple[str, float]:
        """Create a reproducible ZIP with stable member order and timestamps.

        Args:
            output_names: Names of the generated language files to include.

        Returns:
            The human-readable archive size and elapsed time in seconds.
        """
        started = perf_counter()
        members = [
            (self.layout.root / "pack.mcmeta", "pack.mcmeta"),
            (self.layout.root / "pack.png", "pack.png"),
        ]
        members.extend(
            (self.layout.output / f"{name}.json", f"assets/minecraft/lang/{name}.json")
            for name in sorted(output_names)
            if name != "zh_split"
        )

        with ZipFile(
            self.layout.archive,
            "w",
            compression=ZIP_DEFLATED,
            compresslevel=9,
        ) as archive:
            for source, archive_name in members:
                info = ZipInfo(archive_name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, source.read_bytes(), compresslevel=9)

        return format_file_size(self.layout.archive), perf_counter() - started

    def build(self) -> None:
        """Generate every language file and the final resource-pack archive."""
        outputs, generation_time = self.generate_language_files()
        print(f"\nLanguage file generation completed in {generation_time:.2f} s.")
        archive_size, archive_time = self.create_resource_pack(outputs)
        print(f"\nResource pack created ({archive_size}) in {archive_time:.2f} s.")

    def generate_correction_data(self) -> None:
        """Regenerate scheme-specific corrections from the manually segmented source."""
        converter = MandarinConverter(
            self.repository,
            auto_segment=False,
        )
        source = self.repository.corrections("source")
        tasks: tuple[tuple[str, TextTransform], ...] = (
            ("hanyu_pinyin", converter.to_hanyu_pinyin),
            (
                "mandarin_phonetic_symbols_ii",
                converter.to_mandarin_phonetic_symbols_ii,
            ),
            ("tongyong_pinyin", converter.to_tongyong_pinyin),
            ("yale_romanization", converter.to_yale_romanization),
            ("wade_giles", converter.to_wade_giles),
            ("gwoyeu_romatzyh", converter.to_gwoyeu_romatzyh),
            (
                "simplified_gwoyeu_romatzyh",
                converter.to_simplified_gwoyeu_romatzyh,
            ),
            ("cyrillic", converter.to_cyrillic),
            ("xiaoerjing", converter.to_xiaoerjing),
        )
        for scheme, transform in tasks:
            result = convert_language_entries(source, transform)
            path = self.repository.correction_path(scheme)
            write_json(path, result.data)
            print(f"Generated correction data {path.name} in {result.elapsed_seconds:.2f} s.")

    def _language_file_builds(self) -> tuple[LanguageFileBuild, ...]:
        english_source = self.repository.language_source("en_us")
        mandarin_source = self.repository.language_source("zh_cn")
        universal = self.repository.universal_corrections()
        english = EnglishConverter(self.repository)
        mandarin = MandarinConverter(self.repository)
        pronunciation = mandarin.apply_key_specific_pronunciation

        def mandarin_build(
            output_name: str,
            transform: TextTransform,
            correction_scheme: str | None = None,
        ) -> LanguageFileBuild:
            return LanguageFileBuild(
                output_name,
                mandarin_source,
                transform,
                self.repository.corrections(correction_scheme) if correction_scheme else None,
                universal,
                pronunciation,
            )

        return (
            LanguageFileBuild("en_i7h", english_source, english.to_numeronym),
            LanguageFileBuild("ja_kk", english_source, english.to_katakana),
            LanguageFileBuild("ja_my", english_source, english.to_manyogana),
            LanguageFileBuild(
                "zh_split",
                mandarin_source,
                mandarin.to_split,
                self.repository.corrections("source"),
                universal,
            ),
            mandarin_build("zh_py", mandarin.to_hanyu_pinyin, "hanyu_pinyin"),
            mandarin_build("zh_ipa", mandarin.to_ipa),
            mandarin_build("zh_bpmf", mandarin.to_bopomofo),
            mandarin_build("zh_wg", mandarin.to_wade_giles, "wade_giles"),
            mandarin_build(
                "zh_gr",
                mandarin.to_gwoyeu_romatzyh,
                "gwoyeu_romatzyh",
            ),
            mandarin_build(
                "zh_sgr",
                mandarin.to_simplified_gwoyeu_romatzyh,
                "simplified_gwoyeu_romatzyh",
            ),
            mandarin_build(
                "zh_mps2",
                mandarin.to_mandarin_phonetic_symbols_ii,
                "mandarin_phonetic_symbols_ii",
            ),
            mandarin_build(
                "zh_ty",
                mandarin.to_tongyong_pinyin,
                "tongyong_pinyin",
            ),
            mandarin_build(
                "zh_yale",
                mandarin.to_yale_romanization,
                "yale_romanization",
            ),
            mandarin_build("zh_kk", mandarin.to_katakana),
            mandarin_build("zh_cy", mandarin.to_cyrillic, "cyrillic"),
            mandarin_build("zh_xj", mandarin.to_xiaoerjing, "xiaoerjing"),
        )

    def _write_language_file(
        self,
        output_name: str,
        result: LanguageConversionResult,
    ) -> None:
        path = self.layout.output / f"{output_name}.json"
        write_json(path, result.data)
        print(
            f"Generated language file {path.name} ({format_file_size(path)}) "
            f"in {result.elapsed_seconds:.2f} s."
        )
