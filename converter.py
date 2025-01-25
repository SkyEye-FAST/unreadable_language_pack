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
    PINYIN_TO,
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


class ConverterError(Exception):
    """转换器基础异常类"""


class ConversionError(ConverterError):
    """转换过程中的异常"""


class BaseConverter:
    """基础转换器，提供通用文本操作方法。

    Attributes:
        data (Ldata): 输入的语言数据字典
        rep (Ldata): 需要替换的格式内容字典
    """

    def __init__(self, data: Ldata, rep: Ldata) -> None:
        self.data = data
        self.rep = rep

    def replace_multiple(self, text: str, replacement: Optional[Ldata] = None) -> str:
        """对字符串进行多次替换。

        Args:
            text (str): 需要替换的字符串
            replacement (Optional[Dict[str, str]], optional): 替换格式字典

        Returns:
            str: 替换后的字符串
        """
        if not replacement:
            replacement = self.rep
        for old, new in replacement.items():
            text = text.replace(old, new)
        return text

    def capitalize_lines(self, text: str) -> str:
        """处理句首大写，字符串中带换行符和省略号的单独处理。

        Args:
            text (str): 需要转换的字符串

        Returns:
            str: 转换结果
        """

        def _capitalize_with_ellipsis(segment: str) -> str:
            """处理带省略号的文本段落，确保每个省略号后的文本都大写。"""
            if not segment:
                return segment

            parts = segment.split("...")
            capitalized_parts = []

            for part in parts:
                if not part:
                    capitalized_parts.append(part)
                    continue

                if part[0] == " ":
                    capitalized_parts.append(
                        " " + part[1].upper() + part[2:] if len(part) > 1 else part
                    )
                else:
                    capitalized_parts.append(part[0].upper() + part[1:])

            return "...".join(capitalized_parts)

        if not text:
            return text

        if "\n" not in text:
            if "..." not in text:
                return text[0].upper() + text[1:]
            return _capitalize_with_ellipsis(text)

        lines = text.splitlines()
        capitalized_lines = []

        for line in lines:
            if not line:
                capitalized_lines.append(line)
                continue

            capitalized_lines.append(_capitalize_with_ellipsis(line))

        return "\n".join(capitalized_lines)

    def capitalize_titles(self, text: str) -> str:
        """将书名号《》中的单词首字母大写。

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
        """处理隔音符号。

        Args:
            input_list (List[str]): 需要转换的字符串
            values (Set[str]: 有效的拼写

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
        """转换语言数据。

        Args:
            func (Callable[[str], str): 字符串转换函数
            fix_dict (Optional[Dict[str, str]], optional): 修复内容字典
            rep (Optional[Dict[str, str]], optional): 替换格式字典

        Returns:
            Tuple[Dict[str, str], float): (转换结果字典，耗时秒数)

        Raises:
            ConversionError: 转换过程出错
        """
        try:
            if not rep:
                rep = self.rep
            input_dict = self.data
            start_time = time.time()

            output_dict: Ldata = {}
            for k, v in input_dict.items():
                try:
                    output_dict[k] = func(v)
                except Exception as e:
                    raise ConversionError(f"转换{k}时出现错误：{str(e)}") from e

            if self.rep is rep_zh:
                output_dict.update(fixed_zh_u)

            if fix_dict:
                output_dict.update(fix_dict)

            return output_dict, time.time() - start_time

        except Exception as e:
            raise ConversionError(f"转换失败：{str(e)}") from e


class EnglishConverter(BaseConverter):
    """
    英文转换器。处理英文文本到其他格式的转换。

    Attributes:
        data (Ldata): 输入的英文语言数据
        rep (Ldata, optional): 英文转写替换规则
    """

    def __init__(self, data: Ldata, rep: Ldata = rep_ja_kk) -> None:
        super().__init__(data, rep)

    def to_i7h(self, text: str) -> str:
        """将字符串中的所有单词缩写。
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
        """将字符串转写为片假名。

        Args:
            text (str): 输入的文本

        Returns:
            str: 转换后的片假名字符串
        """
        self.rep = rep_ja_kk
        return self.replace_multiple(tk(text).katakana)

    def to_manyogana(self, text: str) -> str:
        """将字符串转写为万叶假名。

        Args:
            text (str): 输入的文本

        Returns:
            str: 转换后的万叶假名字符串
        """
        kk_dict = self.to_katakana(text)
        return "".join(manyoganas_dict.get(char, char) for char in kk_dict)


class ChineseConverter(BaseConverter):
    """中文转换器。

    Attributes:
        data (Ldata): 输入的中文语言数据
        rep (Ldata, optional): 中文转写替换规则
        auto_cut (bool, optional): 是否使用自动分词
    """

    def __init__(self, data: Ldata, rep: Ldata = rep_zh, auto_cut: bool = True) -> None:
        super().__init__(data, rep)
        self.auto_cut = auto_cut

    def segment_str(self, text: str) -> List[str]:
        """根据设置分词或者直接拆分字符串。

        Args:
            text (str): 需要分割的字符串

        Returns:
            List[str): 分割后的字符串列表
        """
        return jieba.lcut(text) if self.auto_cut else text.split()

    def to_split(self, text: str) -> str:
        """输出拆分后的字符串结果。

        Args:
            text (str): 需要转换的字符串

        Returns:
            str: 转换结果
        """
        rep = self.rep.copy()
        rep.update(
            {
                "了.": " 了.",
                "了!": " 了!",
                "了?": " 了?",
                "了…": " 了…",
                "之物": "之 物",
            }
        )
        return self.replace_multiple(
            " ".join(self.segment_str(text)).replace(" 了", "了"), rep
        )

    def to_harmonic(self, text: str) -> str:
        """将字符串中的汉字按GB/Z 40637-2021和《通用规范汉字表》转换。

        Args:
            text (str): 需要转换的字符串

        Returns:
            str: 转换结果
        """
        return opencc_s2c.convert(text)

    def to_pinyin(self, text: str) -> str:
        """将汉字转写为拼音，尝试遵循GB/T 16159-2012分词，词之间使用空格分开。

        Args:
            text (str): 需要转换的字符串

        Returns:
            str: 转换结果
        """
        seg_list = self.segment_str(text)
        result = ""

        for i, seg in enumerate(seg_list):
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
            result += (
                ""
                if seg == "了"
                and i + 1 < len(seg_list)
                and seg_list[i + 1] not in {"。", "！", "？", "…"}
                else " "
            )
            result += "".join(pinyin_list)
        return self.capitalize_lines(
            self.capitalize_titles(self.replace_multiple(result[1:]))
        )

    def pinyin_to_other(
        self,
        correspondence: Ldata,
        text: str,
        delimiter: str = "-",
    ) -> str:
        """将汉字转写为其他拼音系统。

        Args:
            correspondence (Ldata): 对应的拼音系统映射
            text (str): 输入的文本
            delimiter (str, optional): 分隔符，默认为'-'

        Returns:
            str: 转换结果
        """
        seg_list = self.segment_str(text)
        result = ""

        for i, seg in enumerate(seg_list):
            pinyin_list = lazy_pinyin(
                seg, style=Style.TONE3, neutral_tone_with_five=True
            )
            result_list = [correspondence.get(p, p) for p in pinyin_list]
            result += (
                ""
                if seg == "了"
                and i + 1 < len(seg_list)
                and seg_list[i + 1] not in {"。", "！", "？", "…"}
                else " "
            )
            result += delimiter.join(result_list)
        return self.capitalize_lines(
            self.capitalize_titles(self.replace_multiple(result[1:]))
        )

    def to_ipa(self, text: str) -> str:
        """将字符串中的汉字转写为IPA，单字之间使用空格分开。
        IPA数据来自@UntPhesoca，宽式标音。

        Args:
            text (str): 需要转换的字符串

        Returns:
            str: 转换结果
        """
        pinyin_list = lazy_pinyin(text, style=Style.TONE3, neutral_tone_with_five=True)
        ipa_list = [
            f"{PINYIN_TO['ipa'].get(p[:-1], p[:-1])}{tone_to_ipa.get(p[-1], p[-1])}"
            for p in pinyin_list
        ]
        return " ".join(ipa_list)

    def to_bopomofo(self, text: str) -> str:
        """将字符串中的汉字转写为注音符号，单字之间使用空格分开。

        Args:
            text (str): 需要转换的字符串

        Returns:
            str: 转换结果
        """
        bpmf_list = lazy_pinyin(text, style=Style.BOPOMOFO)
        bpmf_list = [f"˙{i[:-1]}" if i.endswith("˙") else i for i in bpmf_list]
        return " ".join(bpmf_list)

    def to_wadegiles(self, text: str) -> str:
        """将字符串中的汉字转写为威妥玛拼音，单字之间使用连字符分开，词之间使用空格分开。

        Args:
            text (str): 需要转换的字符串

        Returns:
            str: 转换结果
        """
        return self.pinyin_to_other(PINYIN_TO["wadegiles"], text)

    def to_romatzyh(self, text: str) -> str:
        """将字符串中的汉字转写为国语罗马字，词之间使用空格分开。

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
            gr_list = [PINYIN_TO["romatzyh"].get(p, p) for p in pinyin_list]
            output_list.append("".join(self.add_apostrophes(gr_list, gr_values)))

        result = " ".join(output_list)

        return self.capitalize_lines(
            self.capitalize_titles(self.replace_multiple(result))
        )

    def to_simp_romatzyh(self, text: str) -> str:
        """将字符串中的汉字转写为简化国语罗马字，词之间使用空格分开。

        Args:
            text (str): 需要转换的字符串

        Returns:
            str: 转换结果
        """
        return self.pinyin_to_other(PINYIN_TO["simp_romatzyh"], text, delimiter="")

    def to_mps2(self, text: str) -> str:
        """将字符串中的汉字转写为注音符号第二式，单字之间使用连字符分开，词之间使用空格分开。

        Args:
            text (str): 需要转换的字符串

        Returns:
            str: 转换结果
        """
        return self.pinyin_to_other(PINYIN_TO["mps2"], text)

    def to_tongyong(self, text: str) -> str:
        """将字符串中的汉字转写为通用拼音，单字之间使用连字符分开，词之间使用空格分开。

        Args:
            text (str): 需要转换的字符串

        Returns:
            str: 转换结果
        """
        return self.pinyin_to_other(PINYIN_TO["tongyong"], text)

    def to_yale(self, text: str) -> str:
        """将字符串中的汉字转写为耶鲁拼音，单字之间使用连字符分开，词之间使用空格分开。

        Args:
            text (str): 需要转换的字符串

        Returns:
            str: 转换结果
        """
        return self.pinyin_to_other(PINYIN_TO["yale"], text)

    def to_katakana(self, text: str = "") -> str:
        """将字符串中的汉字转写为片假名。

        Args:
            text (str): 需要转换的字符串

        Returns:
            str: 转换结果
        """
        pinyin_list = lazy_pinyin(text)
        kana_list = [f"{PINYIN_TO['katakana'].get(p, p)}" for p in pinyin_list]
        return " ".join(kana_list)

    def to_cyrillic(self, text: str) -> str:
        """将字符串中的汉字转写为西里尔字母，使用巴拉第音标体系。

        Args:
            text (str): 需要转换的字符串

        Returns:
            str: 转换结果
        """
        seg_list = self.segment_str(text)
        output_list: List[str] = []

        for seg in seg_list:
            pinyin_list = lazy_pinyin(seg)
            cy_list = [PINYIN_TO["cyrillic"].get(p, p) for p in pinyin_list]
            output_list.append("".join(self.add_apostrophes(cy_list, cy_values)))

        result = " ".join(output_list)
        return self.capitalize_lines(
            self.capitalize_titles(self.replace_multiple(result))
        )

    def to_xiaojing(self, text: str) -> str:
        """将字符串中的汉字转写为小儿经，使用零宽不连字（U+200C）分开。

        Args:
            text (str): 需要转换的字符串

        Returns:
            str: 转换结果
        """
        seg_list = self.segment_str(text)
        output_list = []

        for seg in seg_list:
            pinyin_list = lazy_pinyin(seg)
            xj_list = [PINYIN_TO["xiaojing"].get(p, p) for p in pinyin_list]
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

    Raises:
        OSError: 文件保存失败
    """
    try:
        input_dict, elapsed_time = input_data
        file_path = P / output_folder / f"{output_file}.json"
        with open(file_path, "w", encoding="utf-8", newline="\n") as j:
            ujson.dump(input_dict, j, indent=2, ensure_ascii=False)
        size = file_size(file_path)
        print(
            f"已生成语言文件“{output_file}.json”，大小{size}，耗时{elapsed_time:.2f} s。"
        )
    except Exception as e:
        raise OSError(f"保存至JSON失败：{str(e)}") from e
