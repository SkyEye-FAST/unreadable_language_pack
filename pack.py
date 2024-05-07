# -*- encoding: utf-8 -*-
"""Minecraft难视语言资源包生成器"""

import json
import zipfile as zf
from pathlib import Path
from random import choice
from typing import Callable

from romajitable import to_kana as tk
from pypinyin import Style, lazy_pinyin, load_phrases_dict
from pypinyin_dict.phrase_pinyin_data import cc_cedict, di
import jieba

# 当前绝对路径
P = Path(__file__).resolve().parent

# 初始化pypinyin
cc_cedict.load()
di.load()
load_phrases_dict({"行商": [["xíng"], ["shāng"]]})
load_phrases_dict({"校频": [["jiào"], ["pín"]]})
load_phrases_dict({"藤蔓": [["téng"], ["wàn"]]})
load_phrases_dict({"方框": [["fāng"], ["kuàng"]]})
load_phrases_dict({"切制": [["qiē"], ["zhì"]]})
load_phrases_dict({"到了": [["dào"], ["le"]]})
load_phrases_dict({"子串": [["zǐ"], ["chuàn"]]})
load_phrases_dict({"结果": [["jié"], ["guǒ"]]})
load_phrases_dict({"力量": [["lì"], ["liàng"]]})
load_phrases_dict({"树荫": [["shù"], ["yīn"]]})
load_phrases_dict({"看来": [["kàn"], ["lái"]]})
load_phrases_dict({"困难": [["kùn"], ["nán"]]})
load_phrases_dict({"尺寸": [["chǐ"], ["cùn"]]})
load_phrases_dict({"转动": [["zhuàn"], ["dòng"]]})
load_phrases_dict({"中的": [["zhōng"], ["de"]]})
load_phrases_dict({"拍打": [["pāi"], ["dǎ"]]})
load_phrases_dict({"别人": [["bié"], ["rén"]]})
load_phrases_dict({"位置": [["wèi"], ["zhì"]]})
load_phrases_dict({"干海带": [["gān"], ["hǎi"], ["dài"]]})

# 初始化jieba
jieba.load_userdict(str(P / "data" / "dict.txt"))

# 初始化自定义数据
with open(P / "data" / "py2ipa.json", "r", encoding="utf-8") as ipa_dict:
    pinyin_to_ipa: dict[str, str] = json.load(ipa_dict)
tone_to_ipa: dict[str, str] = {
    "1": "˥",
    "2": "˧˥",
    "3": "˨˩˦",
    "4": "˥˩",
    "5": "",
}
with open(P / "data" / "symbols.json", "r", encoding="utf-8") as syb_dict:
    symbols_dict: dict[str, str] = json.load(syb_dict)
with open(P / "data" / "manyogana.json", "r", encoding="utf-8") as manyo_dict:
    manyoganas_dict: dict[str, str] = json.load(manyo_dict)


def replace_multiple(s: str, rep: dict[str, str]) -> str:
    """
    对字符串进行多次替换。

    :param s: 需要替换的字符串
    :type s: str

    :param rep: 替换的内容
    :type rep: dict[str, str]

    :return: 替换结果，字符串
    """

    for old, new in rep.items():
        s = s.replace(old, new)
    return s


def to_katakana(s: str) -> str:
    """
    将字符串中的英文转写为片假名。

    :param s: 需要转换的字符串
    :type s: str

    :return: 转换结果，字符串
    """

    return replace_multiple(
        tk(s).katakana,
        {
            "%ス": "%s",
            "%ド": "%d",
            "。。。": "...",
            ":・": "：",
            "・ー・": " ー ",
            "・&・": " & ",
            "ク418": "C418",
            "サムエル・åベルグ": "サミュエル・オーバーグ",
            "レナ・ライネ": "レナ・レイン",
        },
    )


def to_manyogana(s: str) -> str:
    """
    将字符串中的片假名转写为万叶假名。

    :param s: 需要转换的字符串
    :type s: str

    :return: 转换结果，字符串
    """

    s = to_katakana(s)
    result = ""
    for char in s:
        if char in manyoganas_dict:
            result += choice(manyoganas_dict[char])
        else:
            result += char
    return result


def to_pinyin(s: str) -> str:
    """
    将字符串中的汉字转写为拼音，单字之间使用空格分开。

    :param s: 需要转换的字符串
    :type s: 字符串

    :return: 转换结果，字符串
    """

    pinyin_list = lazy_pinyin(s, style=Style.TONE)
    return " ".join(pinyin_list)


def to_pinyin_word(s: str) -> str:
    """
    将字符串中的汉字转写为拼音，尝试遵循GB/T 16159-2012分词，词之间使用空格分开。

    :param s: 需要转换的字符串
    :type s: str

    :return: 转换结果，字符串
    """
    seg_list: list[str] = jieba.lcut(s)
    output_list: list[str] = []

    for w in seg_list:
        pinyin_list = lazy_pinyin(w, style=Style.TONE)
        output_list.append("".join(pinyin_list))
    result = replace_multiple(" ".join(output_list), symbols_dict)

    return result[0].upper() + result[1:]


def to_bopomofo(s: str) -> str:
    """
    将字符串中的汉字转写为注音符号，单字之间使用空格分开。

    :param s: 需要转换的字符串
    :type s: str

    :return: 转换结果，字符串
    """

    bopomofo_list = lazy_pinyin(s, style=Style.BOPOMOFO)
    return " ".join(bopomofo_list)


def to_ipa(s: str) -> str:
    """
    将字符串中的汉字转写为IPA，单字之间使用空格分开。
    IPA数据来自@UntPhesoca，宽式标音。

    :param s: 需要转换的字符串
    :type s: str

    :return: 转换结果，字符串
    """

    pinyin_list = lazy_pinyin(s, style=Style.TONE3, neutral_tone_with_five=True)
    ipa_list: list[str] = []
    for pinyin in pinyin_list:
        tone = pinyin[-1]
        pinyin = pinyin[:-1]

        ipa = pinyin_to_ipa.get(pinyin, pinyin)
        tone_ipa = tone_to_ipa.get(tone, tone)
        ipa_list.append(f"{ipa}{tone_ipa}")

    return " ".join(ipa_list)


# 读取语言文件
data: dict[str, dict[str, str]] = {}
for lang_name in ["en_us", "zh_cn"]:
    with open(P / "source" / f"{lang_name}.json", "r", encoding="utf-8") as l:
        data[lang_name] = json.load(l)


# 生成语言文件
def save_to_json(
    input_data: dict[str, str], output_file: str, func: Callable[[str], str]
):
    """
    将生成的语言文件保存至JSON。

    :param input_data: 需要保存的语言文件
    :type s: dict[str, str]

    :param output_file: 保存的文件名
    :type rep: str

    :param func: 生成语言文件所用的函数
    :type func: Callable[[str], str]
    """

    output_dict = {k: func(v) for k, v in input_data.items()}
    with open(P / "output" / output_file, "w", encoding="utf-8") as f:
        json.dump(output_dict, f, indent=2, ensure_ascii=False)


save_to_json(data["en_us"], "ja_kk.json", to_katakana)
save_to_json(data["en_us"], "ja_my.json", to_manyogana)
save_to_json(data["zh_cn"], "zh_py.json", to_pinyin)
save_to_json(data["zh_cn"], "zh_pyw.json", to_pinyin_word)
save_to_json(data["zh_cn"], "zh_ipa.json", to_ipa)
save_to_json(data["zh_cn"], "zh_bpmf.json", to_bopomofo)


# 生成资源包
pack_dir = P / "unreadable_language_pack.zip"
with zf.ZipFile(pack_dir, "w", compression=zf.ZIP_DEFLATED, compresslevel=9) as z:
    z.write(P / "pack.mcmeta", arcname="pack.mcmeta")
    z.write(P / "output" / "ja_kk.json", arcname="assets/minecraft/lang/ja_kk.json")
    z.write(P / "output" / "ja_my.json", arcname="assets/minecraft/lang/ja_my.json")
    z.write(P / "output" / "zh_py.json", arcname="assets/minecraft/lang/zh_py.json")
    z.write(P / "output" / "zh_pyw.json", arcname="assets/minecraft/lang/zh_pyw.json")
    z.write(P / "output" / "zh_ipa.json", arcname="assets/minecraft/lang/zh_ipa.json")
    z.write(P / "output" / "zh_bpmf.json", arcname="assets/minecraft/lang/zh_bpmf.json")
