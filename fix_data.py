# -*- encoding: utf-8 -*-
"""数据修复脚本"""

from base import load_json
from converter import (
    save_to_json,
    ChineseConverter
)

rep = {"！:(": "! :(", "，": ", ", "-!": "!"}

fixed_zh_source = load_json("fixed_zh_source")
conv = ChineseConverter(fixed_zh_source, rep, False)

save_to_json(
    conv.convert(conv.to_pinyin),
    "fixed_zh_py",
    "data",
)
save_to_json(
    conv.convert(conv.to_mps2),
    "fixed_zh_mps2",
    "data",
)
save_to_json(
    conv.convert(conv.to_tongyong),
    "fixed_zh_ty",
    "data",
)
save_to_json(
    conv.convert(conv.to_yale),
    "fixed_zh_yale",
    "data",
)
save_to_json(
    conv.convert(conv.to_wadegiles),
    "fixed_zh_wg",
    "data",
)
save_to_json(
    conv.convert(conv.to_romatzyh),
    "fixed_zh_gr",
    "data",
)
save_to_json(
    conv.convert(conv.to_cyrillic),
    "fixed_zh_cy",
    "data",
)
save_to_json(
    conv.convert(conv.to_xiaojing),
    "fixed_zh_xj",
    "data",
)
