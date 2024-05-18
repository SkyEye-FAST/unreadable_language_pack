# -*- encoding: utf-8 -*-
"""Minecraft难视语言资源包生成器"""

import json
import zipfile as zf
from pathlib import Path
from typing import Callable, TypeAlias, Optional, Dict, List, Set

from romajitable import to_kana as tk
from pypinyin import Style, lazy_pinyin, load_phrases_dict
from pypinyin_dict.phrase_pinyin_data import cc_cedict, di
import jieba

# 当前绝对路径
P = Path(__file__).resolve().parent

# 类型别名
Ldata: TypeAlias = Dict[str, str]


def load_json(file: str, folder: str = "data") -> Ldata:
    """
    加载JSON文件。

    Args:
        file (str): 需要加载的文件
        folder (str, optional): 存放的文件夹，默认为“data”

    Returns:
        Ldata: 加载结果，字典
    """

    with open(P / folder / f"{file}.json", "r", encoding="utf-8") as f:
        return json.load(f)


# 初始化pypinyin
cc_cedict.load()
di.load()
phrases = load_json("phrases")
load_phrases_dict({k: [[_] for _ in v.split()] for k, v in phrases.items()})

# 初始化jieba
jieba.load_userdict(str(P / "data" / "dict.txt"))

# 初始化其他自定义数据
finals = tuple("aāááàoōóǒòeēéěè")  # 可能的零声母开头
pinyin_to_ipa = load_json("py2ipa")  # 汉语拼音至IPA
tone_to_ipa: Ldata = {"1": "˥", "2": "˧˥", "3": "˨˩˦", "4": "˥˩", "5": ""}  # IPA声调
pinyin_to_wadegiles = load_json("py2wg")  # 汉语拼音至威妥玛拼音
pinyin_to_romatzyh = load_json("py2gr")  # 汉语拼音至国语罗马字
gr_values = set(pinyin_to_romatzyh.values())  # 国语罗马字的有效拼写
pinyin_to_cyrillic = load_json("py2cy")  # 汉语拼音至西里尔转写
cy_values = set(pinyin_to_cyrillic.values())  # 西里尔转写的有效拼写

rep_zh = load_json("rep_zh")  # 连写的中文转写方案替换修正
fixed_zh_py = load_json("fixed_zh_py")  # 汉语拼音修正
fixed_zh_gr = load_json("fixed_zh_gr")  # 国语罗马字修正
fixed_zh_wg = load_json("fixed_zh_wg")  # 威妥玛拼音修正

rep_ja_kk = load_json("rep_ja_kk")  # 片假名替换修正
manyoganas_dict = load_json("manyogana")  # 万叶假名

# 读取语言文件
data: Dict[str, Ldata] = {
    lang_name: load_json(lang_name, "source") for lang_name in ["en_us", "zh_cn"]
}


def replace_multiple(text: str, replacements: Ldata) -> str:
    """
    对字符串进行多次替换。

    Args:
        text (str): 需要替换的字符串
        replacements (Ldata): 替换的内容

    Returns:
        str: 替换结果
    """

    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def capitalize_lines(text: str) -> str:
    """
    处理句首大写，字符串中带换行符的单独处理。

    Args:
        text (str): 需要转换的字符串

    Returns:
        str: 转换结果
    """

    if "\n" in text:
        lines = text.splitlines()
        capitalized_lines = [line[:1].upper() + line[1:] for line in lines]
        return "\n".join(capitalized_lines)
    return text[:1].upper() + text[1:]


def add_apostrophes(input_list: List[str], values: Set[str]) -> List[str]:
    """
    处理隔音符号。

    Args:
        input_list (List[str]): 需要转换的字符串
        values (Set[str]): 有效的拼写

    Returns:
        list: 处理结果
    """

    for i in range(1, len(input_list)):
        for j in range(len(input_list[i - 1])):
            prefix = input_list[i - 1][: -j - 1]
            suffix = input_list[i - 1][-j:]
            if (suffix + input_list[i] in values) and (prefix in values):
                input_list[i] = f"'{input_list[i]}"
                break

    return input_list


def to_katakana(text: str) -> str:
    """
    将字符串中的英文转写为片假名。

    Args:
        text (str): 需要转换的字符串

    Returns:
        str: 转换结果
    """

    return replace_multiple(tk(text).katakana, rep_ja_kk)


def to_manyogana(text: str) -> str:
    """
    将字符串中的片假名转写为万叶假名。

    Args:
        text (str): 需要转换的字符串

    Returns:
        str: 转换结果
    """

    text = to_katakana(text)
    return "".join([manyoganas_dict.get(char, char) for char in text])


def to_pinyin(text: str) -> str:
    """
    将字符串中的汉字转写为拼音，尝试遵循GB/T 16159-2012分词，词之间使用空格分开。

    Args:
        text (str): 需要转换的字符串

    Returns:
        str: 转换结果
    """

    seg_list: List[str] = jieba.lcut(text)
    output_list: List[str] = []

    for seg in seg_list:
        pinyin_list = lazy_pinyin(seg, style=Style.TONE)
        # 处理隔音符号
        for i, py in enumerate(pinyin_list[1:], 1):
            if py.startswith(finals):
                pinyin_list[i] = f"'{py}"
        output_list.append("".join(pinyin_list))

    # 调整格式
    result = replace_multiple(" ".join(output_list), rep_zh)

    return capitalize_lines(result)


def to_ipa(text: str) -> str:
    """
    将字符串中的汉字转写为IPA，单字之间使用空格分开。
    IPA数据来自@UntPhesoca，宽式标音。

    Args:
        text (str): 需要转换的字符串

    Returns:
        str: 转换结果
    """

    pinyin_list = lazy_pinyin(text, style=Style.TONE3, neutral_tone_with_five=True)
    ipa_list = [
        f"{pinyin_to_ipa.get(p[:-1], p[:-1])}{tone_to_ipa.get(p[-1], p[-1])}"
        for p in pinyin_list
    ]
    return " ".join(ipa_list)


def to_bopomofo(text: str) -> str:
    """
    将字符串中的汉字转写为注音符号，单字之间使用空格分开。

    Args:
        text (str): 需要转换的字符串

    Returns:
        str: 转换结果
    """

    return " ".join(lazy_pinyin(text, style=Style.BOPOMOFO))


def to_wadegiles(text: str) -> str:
    """
    将字符串中的汉字转写为威妥玛拼音，单字之间使用连字符分开，词之间使用空格分开。

    Args:
        text (str): 需要转换的字符串

    Returns:
        str: 转换结果
    """

    seg_list: List[str] = jieba.lcut(text)
    output_list: List[str] = []

    for seg in seg_list:
        pinyin_list = lazy_pinyin(seg, style=Style.TONE3, neutral_tone_with_five=True)
        gr_list = [pinyin_to_wadegiles.get(p, p) for p in pinyin_list]
        output_list.append("-".join(gr_list))

    # 调整格式
    result = replace_multiple(" ".join(output_list), rep_zh)

    return capitalize_lines(result)


def to_romatzyh(text: str) -> str:
    """
    将字符串中的汉字转写为国语罗马字，词之间使用空格分开。

    Args:
        text (str): 需要转换的字符串

    Returns:
        str: 转换结果
    """

    seg_list: List[str] = jieba.lcut(text)
    output_list: List[str] = []

    for seg in seg_list:
        seg = seg.replace("不", "bu")
        pinyin_list = lazy_pinyin(seg, style=Style.TONE3, neutral_tone_with_five=True)
        gr_list = [pinyin_to_romatzyh.get(p, p) for p in pinyin_list]
        output_list.append("".join(add_apostrophes(gr_list, gr_values)))

    result = replace_multiple(" ".join(output_list), rep_zh)  # 调整格式

    return capitalize_lines(result)


def to_cyrillic(text: str) -> str:
    """
    将字符串中的汉字转写为西里尔字母，使用帕拉季音标体系，词之间使用空格分开。

    Args:
        text (str): 需要转换的字符串

    Returns:
        str: 转换结果
    """

    seg_list: List[str] = jieba.lcut(text)
    output_list: List[str] = []

    for seg in seg_list:
        pinyin_list = lazy_pinyin(seg)
        cy_list = [pinyin_to_cyrillic.get(p, p) for p in pinyin_list]
        output_list.append("".join(add_apostrophes(cy_list, cy_values)))

    result = replace_multiple(" ".join(output_list), rep_zh)  # 调整格式

    return capitalize_lines(result)


def save_to_json(
    input_lang: str,
    output_file: str,
    func: Callable[[str], str],
    fix_dict: Optional[Ldata] = None,
) -> None:
    """
    将生成的语言文件保存至JSON。

    Args:
        input_lang (str): 源语言名
        output_file (str): 保存的文件名，无格式后缀
        func (Callable[[str], str]): 生成语言文件所用的函数
        fix_dict (Optional[Ldata], optional): 语言文件中需要修复的内容. 默认为None
    """

    output_dict = {k: func(v) for k, v in data[input_lang].items()}
    if fix_dict:
        output_dict.update(fix_dict)
    with open(P / "output" / f"{output_file}.json", "w", encoding="utf-8") as j:
        json.dump(output_dict, j, indent=2, ensure_ascii=False)


def main() -> None:
    """
    主函数，生成语言文件并打包成资源包。
    """

    # 生成语言文件
    save_to_json("en_us", "ja_kk", to_katakana)
    save_to_json("en_us", "ja_my", to_manyogana)
    save_to_json("zh_cn", "zh_py", to_pinyin, fixed_zh_py)
    save_to_json("zh_cn", "zh_ipa", to_ipa)
    save_to_json("zh_cn", "zh_bpmf", to_bopomofo)
    save_to_json("zh_cn", "zh_wg", to_wadegiles, fixed_zh_wg)
    save_to_json("zh_cn", "zh_gr", to_romatzyh, fixed_zh_gr)
    save_to_json("zh_cn", "zh_cy", to_cyrillic)

    # 生成资源包
    pack_dir = P / "unreadable_language_pack.zip"
    with zf.ZipFile(pack_dir, "w", compression=zf.ZIP_DEFLATED, compresslevel=9) as z:
        z.write(P / "pack.mcmeta", arcname="pack.mcmeta")
        for lang_file in P.glob("output/*.json"):
            z.write(lang_file, arcname=f"assets/minecraft/lang/{lang_file.name}")


if __name__ == "__main__":
    main()
