# -*- encoding: utf-8 -*-
"""Minecraft Unreadable Language Resource Pack Generator"""

import json
import zipfile as zf
from pathlib import Path
from random import choice
from typing import Callable

from romajitable import to_kana as tk
from pypinyin import Style, lazy_pinyin, load_phrases_dict
from pypinyin_dict.phrase_pinyin_data import cc_cedict
import jieba

# 当前绝对路径
P = Path(__file__).resolve().parent

# 初始化
cc_cedict.load()
load_phrases_dict({"行商": [["xíng"], ["shāng"]]})
load_phrases_dict({"校频": [["jiào"], ["pín"]]})
load_phrases_dict({"藤蔓": [["téng"], ["wàn"]]})

jieba.load_userdict(str(P / "data" / "dict.txt"))

with open(P / "data" / "py2ipa.json", "r", encoding="utf-8") as ipa_dict:
    pinyin_to_ipa = json.load(ipa_dict)
tone_to_ipa = {
    "1": "˥",
    "2": "˧˥",
    "3": "˨˩˦",
    "4": "˥˩",
    "5": "",
}
with open(P / "data" / "symbols.json", "r", encoding="utf-8") as syb_dict:
    symbols_dict = json.load(syb_dict)
with open(P / "data" / "manyogana.json", "r", encoding="utf-8") as manyo_dict:
    manyoganas_dict = json.load(manyo_dict)


def replace_multiple(s: str, rep: dict[str, str]) -> str:
    """对字符串进行多次替换"""
    for old, new in rep.items():
        s = s.replace(old, new)
    return s


def to_katakana(s: str) -> str:
    """转写为片假名"""
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
    """片假名转写为万叶假名"""
    s = to_katakana(s)
    result = ""
    for char in s:
        if char in manyoganas_dict:
            result += choice(manyoganas_dict[char])
        else:
            result += char
    return result


def to_pinyin(s: str) -> str:
    """转写为拼音，分字"""
    pinyin_list = lazy_pinyin(s, style=Style.TONE)
    return " ".join(pinyin_list)


def to_pinyin_word(s: str) -> str:
    """转写为拼音，分词"""
    seg_list = jieba.lcut(s)
    output_list = []

    for w in seg_list:
        pinyin_list = lazy_pinyin(w, style=Style.TONE)
        output_list.append("".join(pinyin_list))
    result = replace_multiple(" ".join(output_list), symbols_dict)

    return result[0].upper() + result[1:]


def to_bopomofo(s: str) -> str:
    """转写为注音符号"""
    bopomofo_list = lazy_pinyin(s, style=Style.BOPOMOFO)
    return " ".join(bopomofo_list)


def to_ipa(s: str) -> str:
    """转写为IPA"""
    pinyin_list = lazy_pinyin(s, style=Style.TONE3, neutral_tone_with_five=True)
    ipa_list = []
    for pinyin in pinyin_list:
        tone = pinyin[-1]
        pinyin = pinyin[:-1]

        ipa = pinyin_to_ipa.get(pinyin, pinyin)
        tone_ipa = tone_to_ipa.get(tone, tone)
        ipa_list.append(f"{ipa}{tone_ipa}")

    return " ".join(ipa_list)


# 读取语言文件
data = {}
for lang_name in ["en_us", "zh_cn", "zh_tw", "ja_jp"]:
    with open(P / "source" / f"{lang_name}.json", "r", encoding="utf-8") as l:
        data[lang_name] = json.load(l)


# 生成语言文件
def save_to_json(
    input_data: dict[str, str], output_file: str, func: Callable[[str], str]
):
    """保存至JSON"""
    output_dict = {k: func(v) for k, v in input_data.items()}
    with open(P / "output" / output_file, "w", encoding="utf-8") as f:
        json.dump(output_dict, f, indent=2, ensure_ascii=False)


save_to_json(data["en_us"], "ja_kk.json", to_katakana)
save_to_json(data["en_us"], "ja_my.json", to_manyogana)
save_to_json(data["zh_cn"], "zh_py.json", to_pinyin)
save_to_json(data["zh_cn"], "zh_pyw.json", to_pinyin_word)
save_to_json(data["zh_cn"], "zh_ipa.json", to_ipa)
save_to_json(data["zh_tw"], "zh_bpmf.json", to_bopomofo)


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
