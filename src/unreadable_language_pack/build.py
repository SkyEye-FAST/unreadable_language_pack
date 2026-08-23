"""Generate language files and assemble the Minecraft resource pack."""

from collections.abc import Mapping
from dataclasses import dataclass
from time import perf_counter
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from unreadable_language_pack.conversion import (
    ConversionResult,
    TextPreprocessor,
    TextTransform,
    convert_language,
)
from unreadable_language_pack.converters import ChineseConverter, EnglishConverter
from unreadable_language_pack.repository import (
    DataRepository,
    ProjectLayout,
    StringMap,
    format_file_size,
    write_json,
)


@dataclass(frozen=True, slots=True)
class BuildTask:
    """Configuration for generating one language file."""

    output_name: str
    source: Mapping[str, str]
    transform: TextTransform
    fixes: Mapping[str, str] | None = None
    universal_fixes: Mapping[str, str] | None = None
    preprocess: TextPreprocessor | None = None


class PackBuilder:
    """Orchestrate conversions and create a reproducible resource pack."""

    def __init__(self, layout: ProjectLayout) -> None:
        """Initialize the builder for a project layout."""
        self.layout = layout
        self.repository = DataRepository(layout)

    def generate_languages(self) -> tuple[list[str], float]:
        """Generate all language files and return their names and elapsed time."""
        started = perf_counter()
        outputs: list[str] = []

        for task in self._tasks():
            result = convert_language(
                task.source,
                task.transform,
                fixes=task.fixes,
                universal_fixes=task.universal_fixes,
                preprocess=task.preprocess,
            )
            self._save_result(task.output_name, result)
            outputs.append(task.output_name)

        return outputs, perf_counter() - started

    def create_archive(self, output_names: list[str]) -> tuple[str, float]:
        """Create a reproducible ZIP with stable member order and timestamps."""
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
        outputs, generation_time = self.generate_languages()
        print(f"\n语言文件生成完毕，共耗时 {generation_time:.2f} s。")
        archive_size, archive_time = self.create_archive(outputs)
        print(f"\n资源包打包完毕，大小 {archive_size}，耗时 {archive_time:.2f} s。")

    def generate_fix_data(self) -> None:
        """Regenerate scheme-specific fixes from the manually segmented source."""
        replacements: StringMap = {"！:(": "! :(", "，": ", ", "-!": "!"}
        converter = ChineseConverter(
            self.repository,
            auto_segment=False,
            replacements=replacements,
        )
        source = self.repository.fixes("source")
        tasks: tuple[tuple[str, TextTransform], ...] = (
            ("py", converter.to_pinyin),
            ("mps2", converter.to_mps2),
            ("ty", converter.to_tongyong),
            ("yale", converter.to_yale),
            ("wg", converter.to_wadegiles),
            ("gr", converter.to_romatzyh),
            ("sgr", converter.to_simp_romatzyh),
            ("cy", converter.to_cyrillic),
            ("xj", converter.to_xiaojing),
        )
        for scheme, transform in tasks:
            result = convert_language(source, transform)
            path = self.layout.data / "fixed" / f"fixed_zh_{scheme}.json"
            write_json(path, result.data)
            print(f"已生成修正数据 {path.name}，耗时 {result.elapsed_seconds:.2f} s。")

    def _tasks(self) -> tuple[BuildTask, ...]:
        english_source = self.repository.language("en_us")
        chinese_source = self.repository.language("zh_cn")
        universal = self.repository.universal_fixes()
        english = EnglishConverter(self.repository)
        chinese = ChineseConverter(self.repository)
        pronunciation = chinese.preprocess_pronunciation

        def chinese_task(
            output_name: str,
            transform: TextTransform,
            fix_scheme: str | None = None,
        ) -> BuildTask:
            return BuildTask(
                output_name,
                chinese_source,
                transform,
                self.repository.fixes(fix_scheme) if fix_scheme else None,
                universal,
                pronunciation,
            )

        return (
            BuildTask("en_i7h", english_source, english.to_i7h),
            BuildTask("ja_kk", english_source, english.to_katakana),
            BuildTask("ja_my", english_source, english.to_manyogana),
            BuildTask(
                "zh_split",
                chinese_source,
                chinese.to_split,
                self.repository.fixes("source"),
                universal,
            ),
            chinese_task("zh_py", chinese.to_pinyin, "py"),
            chinese_task("zh_ipa", chinese.to_ipa),
            chinese_task("zh_bpmf", chinese.to_bopomofo),
            chinese_task("zh_wg", chinese.to_wadegiles, "wg"),
            chinese_task("zh_gr", chinese.to_romatzyh, "gr"),
            chinese_task("zh_sgr", chinese.to_simp_romatzyh, "sgr"),
            chinese_task("zh_mps2", chinese.to_mps2, "mps2"),
            chinese_task("zh_ty", chinese.to_tongyong, "ty"),
            chinese_task("zh_yale", chinese.to_yale, "yale"),
            chinese_task("zh_kk", chinese.to_katakana),
            chinese_task("zh_cy", chinese.to_cyrillic, "cy"),
            chinese_task("zh_xj", chinese.to_xiaojing, "xj"),
        )

    def _save_result(self, output_name: str, result: ConversionResult) -> None:
        path = self.layout.output / f"{output_name}.json"
        write_json(path, result.data)
        print(
            f"已生成语言文件 {path.name}，大小 {format_file_size(path)}，"
            f"耗时 {result.elapsed_seconds:.2f} s。"
        )
