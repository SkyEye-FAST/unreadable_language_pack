# -*- encoding: utf-8 -*-
"""基础文件，提供通用功能和数据结构定义。"""
from pathlib import Path
from typing import TypeAlias, Dict, Set, Tuple, Final

import ujson

# 类型别名和常量定义
Ldata: TypeAlias = Dict[str, str]
P: Final[Path] = Path(__file__).resolve().parent
LANG_FILES: Final[Tuple[str, ...]] = ("en_us", "zh_cn")


def load_json(file: str, folder: str = "data") -> Ldata:
    """加载JSON文件。

    Args:
        file (str): 需要加载的文件名，不含后缀名
        folder (str, optional): JSON文件所在文件夹路径，默认为"data"

    Returns:
        Dict[str, str]: 加载的JSON内容
    """
    path = P / folder / f"{file}.json"
    with path.open("r", encoding="utf-8", newline="\n") as f:
        return ujson.load(f)


def file_size(p: Path) -> str:
    """计算文件大小并返回可读的字符串表示。

    Args:
        p (pathlib.Path): 待计算文件的路径对象

    Returns:
        str: 格式化的文件大小字符串
    """
    size_in_bytes = p.stat().st_size
    size = (
        f"{round(size_in_bytes / 1048576, 2)} MB"
        if size_in_bytes > 1048576
        else f"{round(size_in_bytes / 1024, 2)} KB"
    )
    return size


# 语言文件数据
DATA: Final[Dict[str, Ldata]] = {
    lang_name: load_json(lang_name, "mc_lang/full") for lang_name in LANG_FILES
}

# 转换映射表
PINYIN_TO: Final[Dict[str, Ldata]] = {
    "wadegiles": load_json("py2wg"),
    "romatzyh": load_json("py2gr"),
    "simp_romatzyh": load_json("py2sgr"),
    "mps2": load_json("py2mps2"),
    "tongyong": load_json("py2ty"),
    "yale": load_json("py2yale"),
    "ipa": load_json("py2ipa"),
    "katakana": load_json("py2kk"),
    "cyrillic": load_json("py2cy"),
    "xiaojing": load_json("py2xj"),
}

fixed_zh: Dict[str, Ldata] = {}
fixed_zh["source"] = load_json("fixed_zh_source")  # 来源修正
fixed_zh["zh_py"] = load_json("fixed_zh_py")  # 汉语拼音修正
fixed_zh["zh_py"].update(load_json("fixed_zh_py_manual"))  # 汉语拼音手动修正
fixed_zh["zh_wg"] = load_json("fixed_zh_wg")  # 威妥玛拼音修正
fixed_zh["zh_gr"] = load_json("fixed_zh_gr")  # 国语罗马字修正
fixed_zh["zh_sgr"] = load_json("fixed_zh_sgr")  # 简化国语罗马字修正
fixed_zh["zh_mps2"] = load_json("fixed_zh_mps2")  # 注音二式修正
fixed_zh["zh_ty"] = load_json("fixed_zh_ty")  # 通用拼音修正
fixed_zh["zh_yale"] = load_json("fixed_zh_yale")  # 耶鲁拼音修正
fixed_zh["zh_cy"] = load_json("fixed_zh_cy")  # 西里尔转写修正
fixed_zh["zh_xj"] = load_json("fixed_zh_xj")  # 小儿经转写修正

gr_values: Set[str] = set(PINYIN_TO["romatzyh"].values())  # 国语罗马字的有效拼写
cy_values: Set[str] = set(PINYIN_TO["cyrillic"].values())  # 西里尔转写的有效拼写
TONE_TO_IPA: Final[Ldata] = {
    "1": "˥",
    "2": "˧˥",
    "3": "˨˩˦",
    "4": "˥˩",
    "5": "",
}  # IPA声调

rep_zh: Ldata = load_json("rep_zh")  # 连写的中文转写方案替换修正
PINYIN_FINALS: Final[Tuple[str, ...]] = tuple("aāááàoōóǒòeēéěè")  # 可能的零声母开头

rep_ja_kk: Ldata = load_json("rep_ja_kk")  # 片假名替换修正
