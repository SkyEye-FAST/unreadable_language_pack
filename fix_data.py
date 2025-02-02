# -*- encoding: utf-8 -*-
"""数据修复脚本"""

from base import load_json, save_to_json
from converter import ChineseConverter

if __name__ == "__main__":
    conv = ChineseConverter(
        load_json("fixed_zh_source"), {"！:(": "! :(", "，": ", ", "-!": "!"}, False
    )

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
        save_to_json(conv.convert(getattr(conv, method)), output, "data/fixed")
