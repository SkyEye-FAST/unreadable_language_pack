from unreadable_language_pack.converters import MandarinConverter
from unreadable_language_pack.repository import LanguageDataRepository


def transcribe_language_entry(
    repository: LanguageDataRepository,
    converter: MandarinConverter,
    key: str,
    method: str = "to_hanyu_pinyin",
) -> str:
    source = repository.language_source("zh_cn")[key]
    prepared = converter.apply_key_specific_pronunciation(key, source)
    return getattr(converter, method)(prepared)


def test_minecraft_placeholders_are_preserved(
    repository: LanguageDataRepository,
    mandarin_converter: MandarinConverter,
) -> None:
    key = "argument.block.property.invalid"
    result = transcribe_language_entry(
        repository,
        mandarin_converter,
        key,
    )

    assert result == "%1$s de %3$s shǔxìng bù néng bèi shèwéi “%2$s”"
    assert "% 1 $ s" not in result

    for method in (
        "to_ipa",
        "to_bopomofo",
        "to_wade_giles",
        "to_gwoyeu_romatzyh",
        "to_simplified_gwoyeu_romatzyh",
        "to_mandarin_phonetic_symbols_ii",
        "to_tongyong_pinyin",
        "to_yale_romanization",
        "to_katakana",
        "to_cyrillic",
        "to_xiaoerjing",
    ):
        converted = transcribe_language_entry(repository, mandarin_converter, key, method)
        assert all(token in converted for token in ("%1$s", "%3$s", "%2$s"))
        assert "% 1 $ s" not in converted

        syntax = transcribe_language_entry(
            repository,
            mandarin_converter,
            "argument.block.property.unclosed",
            method,
        )
        assert " ] " in syntax

    assert (
        transcribe_language_entry(
            repository,
            mandarin_converter,
            "argument.block.property.unclosed",
        )
        == "Fāngkuài shǔxìng yīng yǐ ] jiéshù"
    )

    ordinal = transcribe_language_entry(
        repository,
        mandarin_converter,
        "narrator.position.object_list",
    )
    assert "dì-%s xiàng" in ordinal


def test_minecraft_multiline_tooltip_keeps_line_breaks(
    repository: LanguageDataRepository,
    mandarin_converter: MandarinConverter,
) -> None:
    result = transcribe_language_entry(
        repository,
        mandarin_converter,
        "options.graphics.fancy.tooltip",
    )

    assert result.count("\n") == 1
    assert result.splitlines()[1].startswith("Tiānqì")


def test_key_specific_pronunciation_corrections_are_applied(
    repository: LanguageDataRepository,
    mandarin_converter: MandarinConverter,
) -> None:
    meadows = transcribe_language_entry(
        repository,
        mandarin_converter,
        "advancements.adventure.play_jukebox_in_meadows.description",
    )

    assert "wèi cǎodiàn" in meadows

    attached_stem = "block.minecraft.attached_melon_stem"
    expected_prefixes = {
        "to_hanyu_pinyin": "Jiēguǒ de",
        "to_ipa": "t͡ɕjɛ˥ kwo˨˩˦ tɤ",
        "to_bopomofo": "ㄐㄧㄝ ㄍㄨㄛˇ ˙ㄉㄜ",
        "to_wade_giles": "Chieh¹-kuo³ te⁵",
        "to_gwoyeu_romatzyh": "Jieguoo .de",
        "to_simplified_gwoyeu_romatzyh": "Jieguoo 'de",
        "to_mandarin_phonetic_symbols_ii": "Jiē-guǒ de",
        "to_tongyong_pinyin": "Jie-guǒ de̊",
        "to_yale_romanization": "Jyē-gwǒ de",
    }
    for method, prefix in expected_prefixes.items():
        converted = transcribe_language_entry(repository, mandarin_converter, attached_stem, method)
        assert converted.startswith(prefix)

    negation = "advancements.adventure.brush_armadillo.title"
    expected_negation = {
        "to_hanyu_pinyin": "bù shì",
        "to_ipa": "pu˥˩ ʂɻ̍˥˩",
        "to_bopomofo": "ㄅㄨˋ ㄕˋ",
        "to_wade_giles": "pu⁴ shih⁴",
        "to_gwoyeu_romatzyh": "buh shyh",
        "to_simplified_gwoyeu_romatzyh": "buh shyh",
        "to_mandarin_phonetic_symbols_ii": "bù shr̀",
        "to_tongyong_pinyin": "bù shìh",
        "to_yale_romanization": "bù shr̀",
        "to_katakana": "ブー シー",
        "to_cyrillic": "бу ши",
        "to_xiaoerjing": "بُ شِ",
    }
    for method, fragment in expected_negation.items():
        converted = transcribe_language_entry(repository, mandarin_converter, negation, method)
        assert fragment in converted


def test_gb_t_16159_orthography_on_minecraft_entries(
    repository: LanguageDataRepository,
    mandarin_converter: MandarinConverter,
) -> None:
    expected_fragments = {
        "advancements.adventure.arbalistic.description": "wǔ zhǒng shēngwù",
        "advancements.adventure.heart_transplanter.description": "liǎng gè",
        "advancements.husbandry.root.description": "Zhège shìjiè",
        "tutorial.find_tree.title": "yī kē shù",
        "gui.banned.reason.hate_terrorism_notorious_figure": ("qúntǐ, kǒngbù zǔzhī huò bùfǎ fènzǐ"),
        "options.inactivityFpsLimit.afk.tooltip": "30. 9 fēnzhōng",
        "advancements.adventure.read_power_from_chiseled_bookshelf.title": "jiù shì",
        "advancements.adventure.brush_armadillo.title": "bù shì",
        "selectWorld.backupWarning.customized": "bǎochí yuánzhuàng",
        "demo.day.2": "Dì-èr tiān",
        "optimizeWorld.stage.failed": "Shībài le! :(",
        "selectWorld.allowCommands.info": "Lìrú /gamemode, /experience děng mìnglìng",
        "debug.copy_location.help": "wéi /tp mìnglìng, huò cháng'àn 10 miǎo",
        "mco.account.privacy.info.button": "《Tōngyòng shùjùbǎohù tiáolì》",
    }

    for key, fragment in expected_fragments.items():
        assert fragment in transcribe_language_entry(repository, mandarin_converter, key)
