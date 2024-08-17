# -*- encoding: utf-8 -*-
"""基础文件"""

import json
from pathlib import Path
from typing import TypeAlias, Dict, Set, Tuple

# 当前绝对路径
P = Path(__file__).resolve().parent

# 类型别名
Ldata: TypeAlias = Dict[str, str]


def load_json(file: str, folder: str = "data") -> Ldata:
    """
    加载JSON文件。

    Args:
        file (str): 需要加载的文件，无格式后缀“.json”
        folder (str, optional): 存放的文件夹，默认为“data”

    Returns:
        Ldata: 加载结果，字典
    """

    with open(P / folder / f"{file}.json", "r", encoding="utf-8") as f:
        return json.load(f)


# 读取语言文件
data: Dict[str, Ldata] = {
    lang_name: load_json(lang_name, "mc_lang/full") for lang_name in ["en_us", "zh_cn"]
}

# 初始化其他自定义数据
pinyin_to: Dict[str, Ldata] = {}
pinyin_to["ipa"] = load_json("py2ipa")  # 汉语拼音至IPA
pinyin_to["wadegiles"] = load_json("py2wg")  # 汉语拼音至威妥玛拼音
pinyin_to["romatzyh"] = load_json("py2gr")  # 汉语拼音至国语罗马字
pinyin_to["cyrillic"] = load_json("py2cy")  # 汉语拼音至西里尔转写
pinyin_to["xiaojing"] = load_json("py2xj")  # 汉语拼音至小儿经

fixed_zh: Dict[str, Ldata] = {}
fixed_zh["zh_py"] = load_json("fixed_zh_py")  # 汉语拼音修正
fixed_zh["zh_wg"] = load_json("fixed_zh_wg")  # 威妥玛拼音修正
fixed_zh["zh_gr"] = load_json("fixed_zh_gr")  # 国语罗马字修正
fixed_zh["zh_cy"] = load_json("fixed_zh_cy")  # 西里尔转写修正
fixed_zh["zh_xj"] = load_json("fixed_zh_xj")  # 小儿经转写修正

gr_values: Set[str] = set(pinyin_to["romatzyh"].values())  # 国语罗马字的有效拼写
cy_values: Set[str] = set(pinyin_to["cyrillic"].values())  # 西里尔转写的有效拼写

rep_zh: Ldata = load_json("rep_zh")  # 连写的中文转写方案替换修正
finals: Tuple[str, ...] = tuple("aāááàoōóǒòeēéěè")  # 可能的零声母开头

rep_ja_kk: Ldata = load_json("rep_ja_kk")  # 片假名替换修正