# -*- encoding: utf-8 -*-
"""数据修复脚本"""
from typing import Final

from base import load_json, Ldata
from converter import save_to_json, ChineseConverter

# 定义替换规则
REPLACEMENTS: Final[Ldata] = {"！:(": "! :(", "，": ", ", "-!": "!"}


if __name__ == "__main__":
    fixed_zh_source = load_json("fixed_zh_source")
    conv = ChineseConverter(fixed_zh_source, REPLACEMENTS, False)

    # 生成各种转换格式
    conversions = [
        ("to_pinyin", "fixed_zh_py"),
        ("to_mps2", "fixed_zh_mps2"),
        ("to_tongyong", "fixed_zh_ty"),
        ("to_yale", "fixed_zh_yale"),
        ("to_wadegiles", "fixed_zh_wg"),
        ("to_romatzyh", "fixed_zh_gr"),
        ("to_simp_romatzyh", "fixed_zh_sgr"),
        ("to_cyrillic", "fixed_zh_cy"),
        ("to_xiaojing", "fixed_zh_xj"),
    ]

    for method, output in conversions:
        save_to_json(conv.convert(getattr(conv, method)), output, "data")
