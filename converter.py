# -*- encoding: utf-8 -*-
"""难视语言转换器"""

import re
import time
import inspect
from typing import List, Set, Tuple, Callable, Optional

import ujson
from romajitable import to_kana as tk
from pypinyin import Style, lazy_pinyin, load_phrases_dict
from pypinyin_dict.phrase_pinyin_data import cc_cedict, di
import jieba
from opencc import OpenCC

from base import (
    P,
    Ldata,
    load_json,
    file_size,
    pinyin_to,
    gr_values,
    cy_values,
    tone_to_ipa,
    finals,
    rep_zh,
)

# 初始化OpenCC
opencc_s2c = OpenCC(str(P / "GujiCC" / "opencc" / "s2c.json"))

# 初始化pypinyin
cc_cedict.load()
di.load()
phrases = load_json("phrases")
load_phrases_dict({k: [[_] for _ in v.split()] for k, v in phrases.items()})

# 初始化jieba
jieba.load_userdict(str(P / "data" / "dict.txt"))

# 初始化其他自定义数据
fixed_zh_u = load_json("fixed_zh_universal")
manyoganas_dict: Ldata = load_json("manyogana")  # 万叶假名


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


def capitalize_titles(text: str) -> str:
    """
    将字符串中书名号（《》）中的单词全部作首字母大写处理。

    Args:
        text (str): 需要转换的字符串

    Returns:
        str: 转换结果
    """

    return re.sub(
        r"《(.*?)》",
        lambda match: f"《{' '.join(word.capitalize() for word in match.group(1).split())}》",
        text,
    )


def add_apostrophes(input_list: List[str], values: Set[str]) -> List[str]:
    """
    处理隔音符号。

    Args:
        input_list (List[str]): 需要转换的字符串
        values (Set[str]): 有效的拼写

    Returns:
        List[str]: 处理结果
    """

    for i in range(1, len(input_list)):
        for j in range(len(input_list[i - 1])):
            prefix = input_list[i - 1][: -j - 1]
            suffix = input_list[i - 1][-j:]
            if (suffix + input_list[i] in values) and (prefix in values):
                input_list[i] = f"'{input_list[i]}"
                break

    return input_list


def segment_str(text: str, auto_cut: bool = True) -> List[str]:
    """
    将字符串分词。

    Args:
        text (str): 需要转换的字符串
        auto_cut (bool, optional): 是否自动分词，默认为True

    Returns:
        str: 转换结果
    """

    return jieba.lcut(text) if auto_cut else text.split()


def to_i7h(text: str) -> str:
    """
    将字符串中的所有单词缩写。
    保留单词的首尾字符，中间用字符数替代。
    长度为2或以下的单词保持不变。

    Args:
        text (str): 需要转换的字符串

    Returns:
        str: 转换结果
    """

    words = re.findall(r"\w+", text)
    results = []

    for word in words:
        if len(word) > 2:
            result = f"{word[0]}{len(word) - 2}{word[-1]}"
        else:
            result = word
        results.append(result)

    for word, result in zip(words, results):
        text = text.replace(word, result, 1)

    return text


def to_katakana(text: str, rep: Ldata) -> str:
    """
    将字符串中的英文转写为片假名。

    Args:
        text (str): 需要转换的字符串
        rep (Ldata): 需要替换格式的内容

    Returns:
        str: 转换结果
    """

    return replace_multiple(tk(text).katakana, rep)


def to_manyogana(text: str, rep: Ldata) -> str:
    """
    将字符串中的片假名转写为万叶假名。

    Args:
        text (str): 需要转换的字符串
        rep (Ldata): 需要替换格式的内容

    Returns:
        str: 转换结果
    """

    return "".join(manyoganas_dict.get(char, char) for char in to_katakana(text, rep))


def to_harmonic(text: str) -> str:
    """
    将字符串中的汉字按GB/Z 40637-2021和《通用规范汉字表》转换。

    Args:
        text (str): 需要转换的字符串

    Returns:
        str: 转换结果
    """

    return opencc_s2c.convert(text)


def to_pinyin(text: str, rep: Ldata, auto_cut: bool = True) -> str:
    """
    将字符串中的汉字转写为拼音，尝试遵循GB/T 16159-2012分词，词之间使用空格分开。

    Args:
        text (str): 需要转换的字符串
        rep (Ldata): 需要替换格式的内容
        auto_cut (bool, optional): 是否自动分词，默认为True

    Returns:
        str: 转换结果
    """

    seg_list = segment_str(text, auto_cut)
    output_list: List[str] = []

    for seg in seg_list:
        pinyin_list = lazy_pinyin(seg, style=Style.TONE)
        pinyin_list = [
            (
                f"'{py}"
                if i > 0 and py.startswith(finals) and pinyin_list[i - 1][-1].isalpha()
                else py
            )
            for i, py in enumerate(pinyin_list)
        ]
        output_list.append("".join(pinyin_list))

    result = " ".join(output_list)
    return capitalize_lines(capitalize_titles(replace_multiple(result, rep)))


def pinyin_to_other(
    correspondence: Ldata,
    text: str,
    rep: Ldata,
    auto_cut: bool = True,
    delimiter: str = "-",
) -> str:
    """
    将字符串中的汉字转写，单字之间使用delimiter定义的符号分开，词之间使用空格分开。

    Args:
        correspondence (Ldata): 对应关系
        text (str): 需要转换的字符串
        rep (Ldata): 需要替换格式的内容
        auto_cut (bool, optional): 是否自动分词，默认为True
        delimiter (str, optional): 分隔符，默认为'-'

    Returns:
        str: 转换结果
    """

    seg_list = segment_str(text, auto_cut)
    output_list: List[str] = []

    for seg in seg_list:
        pinyin_list = lazy_pinyin(seg, style=Style.TONE3, neutral_tone_with_five=True)
        result_list = [correspondence.get(p, p) for p in pinyin_list]
        output_list.append(delimiter.join(result_list))

    result = " ".join(output_list)
    return capitalize_lines(capitalize_titles(replace_multiple(result, rep)))


def to_mps2(text: str, rep: Ldata, auto_cut: bool = True) -> str:
    """
    将字符串中的汉字转写为注音符号第二式，单字之间使用连字符分开，词之间使用空格分开。

    Args:
        text (str): 需要转换的字符串
        rep (Ldata): 需要替换格式的内容
        auto_cut (bool, optional): 是否自动分词，默认为True

    Returns:
        str: 转换结果
    """

    return pinyin_to_other(pinyin_to["mps2"], text, rep, auto_cut)


def to_tongyong(text: str, rep: Ldata, auto_cut: bool = True) -> str:
    """
    将字符串中的汉字转写为通用拼音，单字之间使用连字符分开，词之间使用空格分开。

    Args:
        text (str): 需要转换的字符串
        rep (Ldata): 需要替换格式的内容
        auto_cut (bool, optional): 是否自动分词，默认为True

    Returns:
        str: 转换结果
    """

    return pinyin_to_other(pinyin_to["tongyong"], text, rep, auto_cut)


def to_yale(text: str, rep: Ldata, auto_cut: bool = True) -> str:
    """
    将字符串中的汉字转写为耶鲁拼音，单字之间使用连字符分开，词之间使用空格分开。

    Args:
        text (str): 需要转换的字符串
        rep (Ldata): 需要替换格式的内容
        auto_cut (bool, optional): 是否自动分词，默认为True

    Returns:
        str: 转换结果
    """

    return pinyin_to_other(pinyin_to["yale"], text, rep, auto_cut)


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
        f"{pinyin_to['ipa'].get(p[:-1], p[:-1])}{tone_to_ipa.get(p[-1], p[-1])}"
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

    bpmf_list = lazy_pinyin(text, style=Style.BOPOMOFO)
    bpmf_list = [f"˙{i[:-1]}" if i.endswith("˙") else i for i in bpmf_list]
    return " ".join(bpmf_list)


def to_wadegiles(text: str, rep: Ldata, auto_cut: bool = True) -> str:
    """
    将字符串中的汉字转写为威妥玛拼音，单字之间使用连字符分开，词之间使用空格分开。

    Args:
        text (str): 需要转换的字符串
        rep (Ldata): 需要替换格式的内容
        auto_cut (bool, optional): 是否自动分词，默认为True

    Returns:
        str: 转换结果
    """

    return pinyin_to_other(pinyin_to["wadegiles"], text, rep, auto_cut)


def to_romatzyh(text: str, rep: Ldata, auto_cut: bool = True) -> str:
    """
    将字符串中的汉字转写为国语罗马字，词之间使用空格分开。

    Args:
        text (str): 需要转换的字符串
        rep (Ldata): 需要替换格式的内容
        auto_cut (bool, optional): 是否自动分词，默认为True

    Returns:
        str: 转换结果
    """

    seg_list = segment_str(text, auto_cut)
    output_list = []

    for seg in seg_list:
        seg = seg.replace("不", "bu")
        pinyin_list = lazy_pinyin(seg, style=Style.TONE3, neutral_tone_with_five=True)
        gr_list = [pinyin_to["romatzyh"].get(p, p) for p in pinyin_list]
        output_list.append("".join(add_apostrophes(gr_list, gr_values)))

    result = " ".join(output_list)

    return capitalize_lines(capitalize_titles(replace_multiple(result, rep)))


def pinyin_to_katakana(text: str) -> str:
    """
    将字符串中的汉字转写为片假名。

    Args:
        text (str): 需要转换的字符串

    Returns:
        str: 转换结果
    """

    pinyin_list = lazy_pinyin(text)
    kana_list = [f"{pinyin_to['katakana'].get(p, p)}" for p in pinyin_list]
    return " ".join(kana_list)


def to_cyrillic(text: str, rep: Ldata, auto_cut: bool = True) -> str:
    """
    将字符串中的汉字转写为西里尔字母，使用帕拉季音标体系。

    Args:
        text (str): 需要转换的字符串
        rep (Ldata): 需要替换格式的内容
        auto_cut (bool, optional): 是否自动分词，默认为True

    Returns:
        str: 转换结果
    """

    seg_list = segment_str(text, auto_cut)
    output_list: List[str] = []

    for seg in seg_list:
        pinyin_list = lazy_pinyin(seg)
        cy_list = [pinyin_to["cyrillic"].get(p, p) for p in pinyin_list]
        output_list.append("".join(add_apostrophes(cy_list, cy_values)))

    result = " ".join(output_list)
    return capitalize_lines(capitalize_titles(replace_multiple(result, rep)))


def to_xiaojing(text: str, rep: Ldata, auto_cut: bool = True) -> str:
    """
    将字符串中的汉字转写为小儿经，使用零宽不连字（U+200C）分开。

    Args:
        text (str): 需要转换的字符串
        rep (Ldata): 需要替换格式的内容
        auto_cut (bool, optional): 是否自动分词，默认为True

    Returns:
        str: 转换结果
    """

    seg_list = segment_str(text, auto_cut)
    output_list = []
    for seg in seg_list:
        pinyin_list = lazy_pinyin(seg)
        xj_list = [pinyin_to["xiaojing"].get(p, p) for p in pinyin_list]
        output_list.append("\u200c".join(xj_list))
    return replace_multiple(" ".join(output_list), rep)


def convert(
    input_dict: Ldata,
    func: Callable[[str], str],
    fix_dict: Optional[Ldata] = None,
    auto_cut: bool = True,
    rep: Ldata = rep_zh,
) -> Tuple[Ldata, float]:
    """
    转换语言数据。

    Args:
        input_dict (Ldata): 输入的数据
        func (Callable[[str], str]): 生成语言文件所用的函数
        fix_dict (Optional[Ldata], optional): 语言文件中需要修复的内容. 默认为None
        auto_cut (bool, optional): 是否自动分词，默认为True
        rep (Ldata, optional): 需要替换的内容，默认为rep_zh的内容

    Returns:
        (Ldata, float): 转换结果及耗时
    """

    start_time = time.time()

    output_dict: Ldata = {}
    for k, v in input_dict.items():
        func_signature = inspect.signature(func)
        kwargs = {}
        if "auto_cut" in func_signature.parameters and auto_cut is not None:
            kwargs["auto_cut"] = auto_cut
        if "rep" in func_signature.parameters and rep is not None:
            kwargs["rep"] = rep
        output_dict[k] = func(v, **kwargs)

    if rep is rep_zh:
        output_dict.update(fixed_zh_u)

    if fix_dict:
        output_dict.update(fix_dict)

    elapsed_time = time.time() - start_time

    return output_dict, elapsed_time


def save_to_json(
    input_data: Tuple[Ldata, float],
    output_file: str,
    output_folder: str = "output",
) -> None:
    """
    将生成的语言文件保存至JSON。

    Args:
        input_data (Tuple[Ldata, float]): 输入的数据
        output_file (str): 保存的文件名，无格式后缀
        output_folder (str, optional): 保存的文件夹，默认为“output”
    """

    input_dict, elapsed_time = input_data
    file_path = P / output_folder / f"{output_file}.json"
    with open(file_path, "w", encoding="utf-8") as j:
        ujson.dump(input_dict, j, indent=2, ensure_ascii=False)
    size = file_size(file_path)
    print(f"已生成语言文件“{output_file}.json”，大小{size}，耗时{elapsed_time:.2f} s。")
