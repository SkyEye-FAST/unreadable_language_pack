# -*- encoding: utf-8 -*-
"""Minecraft Unreadable Language Resource Pack Generator"""

import json
import zipfile as z
from pathlib import Path

from romajitable import to_kana as tk
from pypinyin import Style, lazy_pinyin
from pypinyin_dict.phrase_pinyin_data import cc_cedict

# 当前绝对路径
P = Path(__file__).resolve().parent

# 初始化
cc_cedict.load()
with open(P / "data" / "ipa.json", "r", encoding="utf-8") as f:
    pinyin_to_ipa = json.load(f)
tone_to_ipa = {
    "1": "˥",
    "2": "˧˥",
    "3": "˨˩˦",
    "4": "˥˩",
    "5": "",
}


def to_katakana(s: str) -> str:
    """转写为片假名"""
    return (
        tk(s)
        .katakana.replace("%ス", r"%s")
        .replace("%ド", r"%d")
        .replace("。。。", "...")
        .replace(":\u30fb", "：")
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
    with open(P / "source" / f"{lang_name}.json", "r", encoding="utf-8") as f:
        data[lang_name] = json.load(f)

# 生成语言文件
with open(P / "output" / "ja_kk.json", "w", encoding="utf-8") as f:
    json.dump({k: to_katakana(v) for k, v in data["en_us"].items()}, f, indent=2)

with open(P / "output" / "zh_py.json", "w", encoding="utf-8") as f:
    json.dump({k: to_pinyin(v) for k, v in data["zh_cn"].items()}, f, indent=2)

with open(P / "output" / "zh_ipa.json", "w", encoding="utf-8") as f:
    json.dump({k: to_ipa(v) for k, v in data["zh_cn"].items()}, f, indent=2)

# 生成资源包
pack_dir = P / "unreadable_language_pack.zip"
with z.ZipFile(pack_dir, "w", compression=z.ZIP_DEFLATED, compresslevel=9) as f:
    f.write(P / "pack.mcmeta", arcname="pack.mcmeta")
    f.write(P / "output" / "ja_kk.json", arcname="assets/minecraft/lang/ja_kk.json")
    f.write(P / "output" / "zh_py.json", arcname="assets/minecraft/lang/zh_py.json")
    f.write(P / "output" / "zh_ipa.json", arcname="assets/minecraft/lang/zh_ipa.json")
