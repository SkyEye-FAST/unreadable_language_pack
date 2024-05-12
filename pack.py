# -*- encoding: utf-8 -*-
"""Minecraft难视语言资源包生成器"""

import json
import zipfile as zf
from pathlib import Path
from typing import Callable, TypeAlias

Ldata: TypeAlias = dict[str, str]

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
with open(P / "data" / "py2ipa.json", "r", encoding="utf-8") as f:
    pinyin_to_ipa: Ldata = json.load(f)
tone_to_ipa: Ldata = {
    "1": "˥",
    "2": "˧˥",
    "3": "˨˩˦",
    "4": "˥˩",
    "5": "",
}
with open(P / "data" / "py2wg.json", "r", encoding="utf-8") as f:
    pinyin_to_wadegiles: Ldata = json.load(f)
with open(P / "data" / "py2gr.json", "r", encoding="utf-8") as f:
    pinyin_to_romatzyh: Ldata = json.load(f)
with open(P / "data" / "rep_zh_pyw.json", "r", encoding="utf-8") as f:
    rep_zh_pyw: Ldata = json.load(f)
with open(P / "data" / "fixed_zh_pyw.json", "r", encoding="utf-8") as f:
    fixed_zh_pyw: Ldata = json.load(f)
with open(P / "data" / "rep_ja_kk.json", "r", encoding="utf-8") as f:
    rep_ja_kk: Ldata = json.load(f)
with open(P / "data" / "manyogana.json", "r", encoding="utf-8") as f:
    manyoganas_dict: Ldata = json.load(f)


def replace_multiple(s: str, rep: Ldata) -> str:
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

    return replace_multiple(tk(s).katakana, rep_ja_kk)


def to_manyogana(s: str) -> str:
    """
    将字符串中的片假名转写为万叶假名。
    为保证生成结果不偏差过大，仅选择万叶假名多种可能中的某一种。

    :param s: 需要转换的字符串
    :type s: str

    :return: 转换结果，字符串
    """

    s = to_katakana(s)
    return "".join([manyoganas_dict.get(char, char) for char in s])


def to_pinyin(s: str) -> str:
    """
    将字符串中的汉字转写为拼音，单字之间使用空格分开。

    :param s: 需要转换的字符串
    :type s: 字符串

    :return: 转换结果，字符串
    """

    return " ".join(lazy_pinyin(s, style=Style.TONE))


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
    result = replace_multiple(" ".join(output_list), rep_zh_pyw)
    if "\n" in result:
        lines = result.splitlines()
        capitalized_lines = [line[:1].upper() + line[1:] for line in lines]
        return "\n".join(capitalized_lines)
    return result[:1].upper() + result[1:]


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


def to_bopomofo(s: str) -> str:
    """
    将字符串中的汉字转写为注音符号，单字之间使用空格分开。

    :param s: 需要转换的字符串
    :type s: str

    :return: 转换结果，字符串
    """

    return " ".join(lazy_pinyin(s, style=Style.BOPOMOFO))


def to_wadegiles(s: str) -> str:
    """
    将字符串中的汉字转写为威妥玛拼音，单字之间使用空格分开。

    :param s: 需要转换的字符串
    :type s: 字符串

    :return: 转换结果，字符串
    """

    pinyin_list = lazy_pinyin(s, style=Style.TONE3, neutral_tone_with_five=True)
    return " ".join([pinyin_to_wadegiles.get(_, _) for _ in pinyin_list])


def to_romatzyh(s: str) -> str:
    """
    将字符串中的汉字转写为国语罗马字，单字之间使用空格分开。

    :param s: 需要转换的字符串
    :type s: 字符串

    :return: 转换结果，字符串
    """

    s = s.replace("不", "bu")
    pinyin_list = lazy_pinyin(s, style=Style.TONE3, neutral_tone_with_five=True)
    return " ".join([pinyin_to_romatzyh.get(_, _) for _ in pinyin_list])


# 读取语言文件
data: dict[str, Ldata] = {}
for lang_name in ["en_us", "zh_cn"]:
    with open(P / "source" / f"{lang_name}.json", "r", encoding="utf-8") as f:
        data[lang_name] = json.load(f)


# 生成语言文件
def save_to_json(
    input_data: Ldata,
    output_file: str,
    func: Callable[[str], str],
    fix_dict: Ldata = None,
):
    """
    将生成的语言文件保存至JSON。

    :param input_data: 需要保存的语言文件
    :type s: dict[str, str]

    :param output_file: 保存的文件名
    :type rep: str

    :param func: 生成语言文件所用的函数
    :type func: Callable[[str], str]

    :param fix_dict: 语言文件中需要修复的内容
    :type fix_dict: dict[str, str]
    """

    output_dict = {k: func(v) for k, v in input_data.items()}
    if fix_dict:
        output_dict.update(fix_dict)
    with open(P / "output" / output_file, "w", encoding="utf-8") as j:
        json.dump(output_dict, j, indent=2, ensure_ascii=False)


save_to_json(data["en_us"], "ja_kk.json", to_katakana)
save_to_json(data["en_us"], "ja_my.json", to_manyogana)
save_to_json(data["zh_cn"], "zh_py.json", to_pinyin)
save_to_json(data["zh_cn"], "zh_pyw.json", to_pinyin_word, fixed_zh_pyw)
save_to_json(data["zh_cn"], "zh_ipa.json", to_ipa)
save_to_json(data["zh_cn"], "zh_bpmf.json", to_bopomofo)
save_to_json(data["zh_cn"], "zh_wg.json", to_wadegiles)
save_to_json(data["zh_cn"], "zh_gr.json", to_romatzyh)


# 生成资源包
pack_dir = P / "unreadable_language_pack.zip"
with zf.ZipFile(pack_dir, "w", compression=zf.ZIP_DEFLATED, compresslevel=9) as z:
    z.write(P / "pack.mcmeta", arcname="pack.mcmeta")
    for l in list(P.glob("output/*.json")):
        z.write(l, arcname=f"assets/minecraft/lang/{l.parts[-1]}")
