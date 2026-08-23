from unreadable_language_pack.converters import ChineseConverter
from unreadable_language_pack.repository import DataRepository


def transcribe_entry(
    repository: DataRepository,
    converter: ChineseConverter,
    key: str,
    method: str = "to_pinyin",
) -> str:
    source = repository.language("zh_cn")[key]
    prepared = converter.preprocess_pronunciation(key, source)
    return getattr(converter, method)(prepared)


def test_minecraft_placeholders_are_preserved(
    repository: DataRepository,
    chinese_converter: ChineseConverter,
) -> None:
    key = "argument.block.property.invalid"
    result = transcribe_entry(
        repository,
        chinese_converter,
        key,
    )

    assert result == "%1$s de %3$s shǔxìng bù néng bèi shèwéi “%2$s”"
    assert "% 1 $ s" not in result

    for method in (
        "to_ipa",
        "to_bopomofo",
        "to_wadegiles",
        "to_romatzyh",
        "to_simp_romatzyh",
        "to_mps2",
        "to_tongyong",
        "to_yale",
        "to_katakana",
        "to_cyrillic",
        "to_xiaojing",
    ):
        converted = transcribe_entry(repository, chinese_converter, key, method)
        assert all(token in converted for token in ("%1$s", "%3$s", "%2$s"))
        assert "% 1 $ s" not in converted

        syntax = transcribe_entry(
            repository,
            chinese_converter,
            "argument.block.property.unclosed",
            method,
        )
        assert " ] " in syntax

    assert (
        transcribe_entry(
            repository,
            chinese_converter,
            "argument.block.property.unclosed",
        )
        == "Fāngkuài shǔxìng yīng yǐ ] jiéshù"
    )

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

    attached_stem = "block.minecraft.attached_melon_stem"
    expected_prefixes = {
        "to_pinyin": "Jiēguǒ de",
        "to_ipa": "t͡ɕjɛ˥ kwo˨˩˦ tɤ",
        "to_bopomofo": "ㄐㄧㄝ ㄍㄨㄛˇ ˙ㄉㄜ",
        "to_wadegiles": "Chieh¹-kuo³ te⁵",
        "to_romatzyh": "Jieguoo .de",
        "to_simp_romatzyh": "Jieguoo 'de",
        "to_mps2": "Jiē-guǒ de",
        "to_tongyong": "Jie-guǒ de̊",
        "to_yale": "Jyē-gwǒ de",
    }
    for method, prefix in expected_prefixes.items():
        converted = transcribe_entry(repository, chinese_converter, attached_stem, method)
        assert converted.startswith(prefix)

    negation = "advancements.adventure.brush_armadillo.title"
    expected_negation = {
        "to_pinyin": "bù shì",
        "to_ipa": "pu˥˩ ʂɻ̍˥˩",
        "to_bopomofo": "ㄅㄨˋ ㄕˋ",
        "to_wadegiles": "pu⁴ shih⁴",
        "to_romatzyh": "buh shyh",
        "to_simp_romatzyh": "buh shyh",
        "to_mps2": "bù shr̀",
        "to_tongyong": "bù shìh",
        "to_yale": "bù shr̀",
        "to_katakana": "ブー シー",
        "to_cyrillic": "бу ши",
        "to_xiaojing": "بُ شِ",
    }
    for method, fragment in expected_negation.items():
        converted = transcribe_entry(repository, chinese_converter, negation, method)
        assert fragment in converted


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
        "advancements.adventure.brush_armadillo.title": "bù shì",
        "selectWorld.backupWarning.customized": "bǎochí yuánzhuàng",
        "demo.day.2": "Dì-èr tiān",
        "optimizeWorld.stage.failed": "Shībài le! :(",
        "selectWorld.allowCommands.info": "Lìrú /gamemode, /experience děng mìnglìng",
        "debug.copy_location.help": "wéi /tp mìnglìng, huò cháng'àn 10 miǎo",
        "mco.account.privacy.info.button": "《Tōngyòng shùjùbǎohù tiáolì》",
    }

    for key, fragment in expected_fragments.items():
        assert fragment in transcribe_entry(repository, chinese_converter, key)
