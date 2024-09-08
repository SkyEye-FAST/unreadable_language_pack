# -*- encoding: utf-8 -*-
"""难视语言转换器"""

import re
import time
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
    rep_ja_kk,
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


class BaseConverter:
    """
    基础转换器类，提供通用的文本操作方法。
    """

    def __init__(self, data: Ldata, rep: Ldata) -> None:
        """
        初始化基础转换器。

        Args:
            data (Ldata): 输入的语言数据
            rep (Ldata): 需要替换的格式内容
        """

        self.data = data
        self.rep = rep

    def replace_multiple(self, text: str) -> str:
        """
        对字符串进行多次替换。

        Args:
            text (str): 需要替换的字符串

        Returns:
            str: 替换后的字符串
        """

        for old, new in self.rep.items():
            text = text.replace(old, new)
        return text

    def capitalize_lines(self, text: str) -> str:
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

    def capitalize_titles(self, text: str) -> str:
        """
        将书名号《》中的单词首字母大写。

        Args:
            text (str): 需要转换的字符串

        Returns:
            str: 转换结果
        """

        return re.sub(
            r"《(.*?)》",
            lambda m: f"《{' '.join(w.capitalize() for w in m.group(1).split())}》",
            text,
        )

    def add_apostrophes(self, input_list: List[str], values: Set[str]) -> List[str]:
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

    def convert(
        self,
        func: Callable[[str], str],
        fix_dict: Optional[Ldata] = None,
        rep: Optional[Ldata] = None,
    ) -> Tuple[Ldata, float]:
        """
        转换语言数据。

        Args:
            func (Callable[[str], str]): 生成语言文件所用的函数
            fix_dict (Optional[Ldata], optional): 语言文件中需要修复的内容，默认为None
            rep (Optional[Ldata], optional): 需要替换格式的内容

        Returns:
            (Ldata, float): 转换结果及耗时
        """
        if not rep:
            rep = self.rep
        input_dict = self.data
        start_time = time.time()

        output_dict: Ldata = {}
        for k, v in input_dict.items():
            output_dict[k] = func(v)

        if self.rep is rep_zh:
            output_dict.update(fixed_zh_u)

        if fix_dict:
            output_dict.update(fix_dict)

        elapsed_time = time.time() - start_time

        return output_dict, elapsed_time


class EnglishConverter(BaseConverter):
    """
    英文转换器类。
    """

    def __init__(self, data: Ldata, rep: Ldata = rep_ja_kk) -> None:
        """
        初始化转换器。

        Args:
            data (Ldata): 输入的语言数据
            rep (Ldata, optional): 替换的格式内容
        """

        super().__init__(data, rep)
        self.data = data
        self.rep = rep

    def to_i7h(self, text: str) -> str:
        """
        将字符串中的所有单词缩写。
        保留单词的首尾字符，中间用字符数替代。
        长度为2或以下的单词保持不变。

        Args:
            text (str): 需要转换的字符串

        Returns:
            str: 转换结果
        """

        words = re.findall(r"[^\W_]+", text)
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

    def to_katakana(self, text: str) -> str:
        """
        将字符串转写为片假名。

        Args:
            text (str): 输入的文本

        Returns:
            str: 转换后的片假名字符串
        """

        self.rep = rep_ja_kk
        return self.replace_multiple(tk(text).katakana)

    def to_manyogana(self, text: str) -> str:
        """
        将字符串转写为万叶假名。

        Args:
            text (str): 输入的文本

        Returns:
            str: 转换后的万叶假名字符串
        """

        kk_dict = self.to_katakana(text)
        return "".join(manyoganas_dict.get(char, char) for char in kk_dict)


class ChineseConverter(BaseConverter):
    """
    中文转换器类。
    """

    def __init__(self, data: Ldata, rep: Ldata = rep_zh, auto_cut: bool = True) -> None:
        """
        初始化转换器。

        Args:
            data (Ldata): 输入的语言数据
            rep (Ldata, optional): 替换的格式内容，默认为rep_zh
            auto_cut (bool, optional): 是否使用自动分词，默认为True
        """

        super().__init__(data, rep)
        self.data = data
        self.rep = rep
        self.auto_cut = auto_cut

    def segment_str(self, text: str) -> List[str]:
        """
        根据设置分词或者直接拆分字符串。

        Args:
            text (str): 需要分割的字符串

        Returns:
            List[str]: 分割后的字符串列表
        """

        return jieba.lcut(text) if self.auto_cut else text.split()

    def to_harmonic(self, text: str) -> str:
        """
        将字符串中的汉字按GB/Z 40637-2021和《通用规范汉字表》转换。

        Args:
            text (str): 需要转换的字符串

        Returns:
            str: 转换结果
        """

        return opencc_s2c.convert(text)

    def to_pinyin(self, text: str) -> str:
        """
        将汉字转写为拼音，尝试遵循GB/T 16159-2012分词，词之间使用空格分开。

        Args:
            text (str): 需要转换的字符串

        Returns:
            str: 转换结果
        """

        seg_list = self.segment_str(text)
        output_list: List[str] = []

        for seg in seg_list:
            pinyin_list = lazy_pinyin(seg, style=Style.TONE)
            pinyin_list = [
                (
                    f"'{py}"
                    if i > 0
                    and py.startswith(finals)
                    and pinyin_list[i - 1][-1].isalpha()
                    else py
                )
                for i, py in enumerate(pinyin_list)
            ]
            output_list.append("".join(pinyin_list))

        result = " ".join(output_list)
        return self.capitalize_lines(
            self.capitalize_titles(self.replace_multiple(result))
        )

    def pinyin_to_other(
        self,
        correspondence: Ldata,
        text: str,
        delimiter: str = "-",
    ) -> str:
        """
        将汉字转写为其他拼音系统。

        Args:
            correspondence (Ldata): 对应的拼音系统映射
            text (str): 输入的文本
            delimiter (str, optional): 分隔符，默认为'-'

        Returns:
            str: 转换结果
        """

        seg_list = self.segment_str(text)
        output_list: List[str] = []

        for seg in seg_list:
            pinyin_list = lazy_pinyin(
                seg, style=Style.TONE3, neutral_tone_with_five=True
            )
            result_list = [correspondence.get(p, p) for p in pinyin_list]
            output_list.append(delimiter.join(result_list))

        result = " ".join(output_list)
        return self.capitalize_lines(
            self.capitalize_titles(self.replace_multiple(result))
        )

    def to_mps2(self, text: str) -> str:
        """
        将字符串中的汉字转写为注音符号第二式，单字之间使用连字符分开，词之间使用空格分开。

        Args:
            text (str): 需要转换的字符串

        Returns:
            str: 转换结果
        """

        return self.pinyin_to_other(pinyin_to["mps2"], text)

    def to_tongyong(self, text: str) -> str:
        """
        将字符串中的汉字转写为通用拼音，单字之间使用连字符分开，词之间使用空格分开。

        Args:
            text (str): 需要转换的字符串

        Returns:
            str: 转换结果
        """

        return self.pinyin_to_other(pinyin_to["tongyong"], text)

    def to_yale(self, text: str) -> str:
        """
        将字符串中的汉字转写为耶鲁拼音，单字之间使用连字符分开，词之间使用空格分开。

        Args:
            text (str): 需要转换的字符串

        Returns:
            str: 转换结果
        """

        return self.pinyin_to_other(pinyin_to["yale"], text)

    def to_ipa(self, text: str) -> str:
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

    def to_bopomofo(self, text: str) -> str:
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

    def to_wadegiles(self, text: str) -> str:
        """
        将字符串中的汉字转写为威妥玛拼音，单字之间使用连字符分开，词之间使用空格分开。

        Args:
            text (str): 需要转换的字符串

        Returns:
            str: 转换结果
        """

        return self.pinyin_to_other(pinyin_to["wadegiles"], text)

    def to_romatzyh(self, text: str) -> str:
        """
        将字符串中的汉字转写为国语罗马字，词之间使用空格分开。

        Args:
            text (str): 需要转换的字符串

        Returns:
            str: 转换结果
        """

        seg_list = self.segment_str(text)
        output_list = []

        for seg in seg_list:
            seg = seg.replace("不", "bu")
            pinyin_list = lazy_pinyin(
                seg, style=Style.TONE3, neutral_tone_with_five=True
            )
            gr_list = [pinyin_to["romatzyh"].get(p, p) for p in pinyin_list]
            output_list.append("".join(self.add_apostrophes(gr_list, gr_values)))

        result = " ".join(output_list)

        return self.capitalize_lines(
            self.capitalize_titles(self.replace_multiple(result))
        )

    def pinyin_to_katakana(self, text: str = "") -> str:
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

    def to_cyrillic(self, text: str) -> str:
        """
        将字符串中的汉字转写为西里尔字母，使用帕拉季音标体系。

        Args:
            text (str): 需要转换的字符串

        Returns:
            str: 转换结果
        """

        seg_list = self.segment_str(text)
        output_list: List[str] = []

        for seg in seg_list:
            pinyin_list = lazy_pinyin(seg)
            cy_list = [pinyin_to["cyrillic"].get(p, p) for p in pinyin_list]
            output_list.append("".join(self.add_apostrophes(cy_list, cy_values)))

        result = " ".join(output_list)
        return self.capitalize_lines(
            self.capitalize_titles(self.replace_multiple(result))
        )

    def to_xiaojing(self, text: str) -> str:
        """
        将字符串中的汉字转写为小儿经，使用零宽不连字（U+200C）分开。

        Args:
            text (str): 需要转换的字符串

        Returns:
            str: 转换结果
        """

        seg_list = self.segment_str(text)
        output_list = []

        for seg in seg_list:
            pinyin_list = lazy_pinyin(seg)
            xj_list = [pinyin_to["xiaojing"].get(p, p) for p in pinyin_list]
            output_list.append("\u200c".join(xj_list))

        return self.replace_multiple(" ".join(output_list))


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
