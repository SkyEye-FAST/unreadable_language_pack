from unreadable_language_pack.converters import ChineseConverter
from unreadable_language_pack.repository import DataRepository


def transcribe_entry(
    repository: DataRepository,
    converter: ChineseConverter,
    key: str,
) -> str:
    source = repository.language("zh_cn")[key]
    prepared = converter.preprocess_pronunciation(key, source)
    return converter.to_pinyin(prepared)


def test_minecraft_placeholders_are_preserved(
    repository: DataRepository,
    chinese_converter: ChineseConverter,
) -> None:
    result = transcribe_entry(
        repository,
        chinese_converter,
        "argument.block.property.invalid",
    )

    assert result == "%1$s de %3$s shǔxìng bù néng bèi shèwéi “%2$s”"
    assert "% 1 $ s" not in result

    ordinal = transcribe_entry(repository, chinese_converter, "narrator.position.object_list")
    assert "dì-%s xiàng" in ordinal


def test_minecraft_multiline_tooltip_keeps_line_breaks(
    repository: DataRepository,
    chinese_converter: ChineseConverter,
) -> None:
    result = transcribe_entry(
        repository,
        chinese_converter,
        "options.graphics.fancy.tooltip",
    )

    assert result.count("\n") == 1
    assert result.splitlines()[1].startswith("Tiānqì")


def test_key_specific_pronunciation_corrections_are_applied(
    repository: DataRepository,
    chinese_converter: ChineseConverter,
) -> None:
    meadows = transcribe_entry(
        repository,
        chinese_converter,
        "advancements.adventure.play_jukebox_in_meadows.description",
    )

    assert "wèi cǎodiàn" in meadows


def test_gb_t_16159_orthography_on_minecraft_entries(
    repository: DataRepository,
    chinese_converter: ChineseConverter,
) -> None:
    expected_fragments = {
        "advancements.adventure.arbalistic.description": "wǔ zhǒng shēngwù",
        "advancements.adventure.heart_transplanter.description": "liǎng gè",
        "advancements.husbandry.root.description": "Zhège shìjiè",
        "tutorial.find_tree.title": "yī kē shù",
        "gui.banned.reason.hate_terrorism_notorious_figure": ("qúntǐ, kǒngbù zǔzhī huò bùfǎ fènzǐ"),
        "options.inactivityFpsLimit.afk.tooltip": "30. 9 fēnzhōng",
        "advancements.adventure.read_power_from_chiseled_bookshelf.title": "jiù shì",
        "selectWorld.backupWarning.customized": "bǎochí yuánzhuàng",
    }

    for key, fragment in expected_fragments.items():
        assert fragment in transcribe_entry(repository, chinese_converter, key)
