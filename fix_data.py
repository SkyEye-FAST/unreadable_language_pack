# -*- encoding: utf-8 -*-
"""数据修复脚本"""

from typing import List
from pypinyin import Style, lazy_pinyin

from base import (
    load_json,
    pinyin_to,
    gr_values,
    cy_values,
)
from converter import (
    save_to_json,
    capitalize_lines,
    capitalize_titles,
    replace_multiple,
    add_apostrophes,
)

rep_zh = {"！:(": "! :(", "，": ", "}


def to_pinyin(text: str) -> str:
    """
    将字符串中的汉字转写为拼音，尝试遵循GB/T 16159-2012分词，词之间使用空格分开。

    Args:
        text (str): 需要转换的字符串

    Returns:
        str: 转换结果
    """

    seg_list: List[str] = text.split()
    output_list: List[str] = []

    for seg in seg_list:
        pinyin_list = lazy_pinyin(seg, style=Style.TONE)
        output_list.append("".join(pinyin_list))

    # 调整格式
    result = replace_multiple(" ".join(output_list), rep_zh)

    return capitalize_lines(capitalize_titles(result))


def to_wadegiles(text: str) -> str:
    """
    将字符串中的汉字转写为威妥玛拼音，单字之间使用连字符分开，词之间使用空格分开。

    Args:
        text (str): 需要转换的字符串

    Returns:
        str: 转换结果
    """

    seg_list: List[str] = text.split()
    output_list: List[str] = []

    for seg in seg_list:
        pinyin_list = lazy_pinyin(seg, style=Style.TONE3, neutral_tone_with_five=True)
        gr_list = [pinyin_to["wadegiles"].get(p, p) for p in pinyin_list]
        output_list.append("-".join(gr_list))

    # 调整格式
    result = replace_multiple(" ".join(output_list), rep_zh)

    return capitalize_lines(capitalize_titles(result))


def to_romatzyh(text: str) -> str:
    """
    将字符串中的汉字转写为国语罗马字，词之间使用空格分开。

    Args:
        text (str): 需要转换的字符串

    Returns:
        str: 转换结果
    """

    seg_list: List[str] = text.split()
    output_list: List[str] = []

    for seg in seg_list:
        seg = seg.replace("不", "bu")
        pinyin_list = lazy_pinyin(seg, style=Style.TONE3, neutral_tone_with_five=True)
        gr_list = [pinyin_to["romatzyh"].get(p, p) for p in pinyin_list]
        output_list.append("".join(add_apostrophes(gr_list, gr_values)))

    result = replace_multiple(" ".join(output_list), rep_zh)  # 调整格式

    return capitalize_lines(capitalize_titles(result))


def to_cyrillic(text: str) -> str:
    """
    将字符串中的汉字转写为西里尔字母，使用帕拉季音标体系，词之间使用空格分开。

    Args:
        text (str): 需要转换的字符串

    Returns:
        str: 转换结果
    """

    seg_list: List[str] = text.split()
    output_list: List[str] = []

    for seg in seg_list:
        pinyin_list = lazy_pinyin(seg)
        cy_list = [pinyin_to["cyrillic"].get(p, p) for p in pinyin_list]
        output_list.append("".join(add_apostrophes(cy_list, cy_values)))

    result = replace_multiple(" ".join(output_list), rep_zh)  # 调整格式

    return capitalize_lines(capitalize_titles(result))


def to_xiaojing(text: str) -> str:
    """
    将字符串中的汉字转写为小儿经，单字之间使用零宽不连字（U+200C）分开，词之间使用空格分开。

    Args:
        text (str): 需要转换的字符串

    Returns:
        str: 转换结果
    """

    seg_list: List[str] = text.split()
    output_list: List[str] = []

    for seg in seg_list:
        pinyin_list = lazy_pinyin(seg)
        xj_list = [pinyin_to["xiaojing"].get(p, p) for p in pinyin_list]
        output_list.append("\u200c".join(xj_list))

    return replace_multiple(" ".join(output_list), rep_zh)


fixed_zh_source = load_json("fixed_zh_source")
save_to_json(fixed_zh_source, "fixed_zh_py", to_pinyin, output_folder="data")
save_to_json(fixed_zh_source, "fixed_zh_wg", to_wadegiles, output_folder="data")
save_to_json(fixed_zh_source, "fixed_zh_gr", to_romatzyh, output_folder="data")
save_to_json(fixed_zh_source, "fixed_zh_cy", to_cyrillic, output_folder="data")
save_to_json(fixed_zh_source, "fixed_zh_xj", to_xiaojing, output_folder="data")
