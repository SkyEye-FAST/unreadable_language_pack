# -*- encoding: utf-8 -*-
"""Minecraft Unreadable Language Resource Pack Generator"""

import json
import zipfile as zf
from pathlib import Path

from romajitable import to_kana as tk
from pypinyin import Style, lazy_pinyin
from pypinyin_dict.phrase_pinyin_data import cc_cedict

# 当前绝对路径
P = Path(__file__).resolve().parent

# 初始化
cc_cedict.load()
with open(P / "data" / "ipa.json", "r", encoding="utf-8") as ipa_dict:
    pinyin_to_ipa = json.load(ipa_dict)
tone_to_ipa = {
    "1": "˥",
    "2": "˧˥",
    "3": "˨˩˦",
    "4": "˥˩",
    "5": "",
}


def replace_multiple(s: str, rep: dict) -> str:
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
            "ク418": "C418",
            "サムエル・åベルグ": "サミュエル・オーバーグ",
            "レナ・ライネ": "レナ・レイン",
        },
    )


def to_pinyin(s: str) -> str:
    """转写为拼音"""
    pinyin_list = lazy_pinyin(s, style=Style.TONE)
    return " ".join(pinyin_list)


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
for lang_name in ["en_us", "zh_cn", "ja_jp"]:
    with open(P / "source" / f"{lang_name}.json", "r", encoding="utf-8") as l:
        data[lang_name] = json.load(l)


# 生成语言文件
def save_to_json(input_data, output_file, func):
    """保存至JSON"""
    output_dict = {k: func(v) for k, v in input_data.items()}
    with open(P / "output" / output_file, "w", encoding="utf-8") as f:
        json.dump(output_dict, f, indent=2, ensure_ascii=False)


save_to_json(data["en_us"], "ja_kk.json", to_katakana)
save_to_json(data["zh_cn"], "zh_py.json", to_pinyin)
save_to_json(data["zh_cn"], "zh_ipa.json", to_ipa)


# 生成资源包
pack_dir = P / "unreadable_language_pack.zip"
with zf.ZipFile(pack_dir, "w", compression=zf.ZIP_DEFLATED, compresslevel=9) as z:
    z.write(P / "pack.mcmeta", arcname="pack.mcmeta")
    z.write(P / "output" / "ja_kk.json", arcname="assets/minecraft/lang/ja_kk.json")
    z.write(P / "output" / "zh_py.json", arcname="assets/minecraft/lang/zh_py.json")
    z.write(P / "output" / "zh_ipa.json", arcname="assets/minecraft/lang/zh_ipa.json")
