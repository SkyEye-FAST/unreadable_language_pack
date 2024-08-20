# -*- encoding: utf-8 -*-
"""数据修复脚本"""

from base import load_json
from converter import (
    save_to_json,
    convert,
    to_pinyin,
    to_mps2,
    to_tongyong,
    to_yale,
    to_wadegiles,
    to_romatzyh,
    to_cyrillic,
    to_xiaojing,
)

rep = {"！:(": "! :(", "，": ", "}

fixed_zh_source = load_json("fixed_zh_source")
save_to_json(
    convert(fixed_zh_source, to_pinyin, auto_cut=False, rep=rep),
    "fixed_zh_py",
    "data",
)
save_to_json(
    convert(fixed_zh_source, to_mps2, auto_cut=False, rep=rep),
    "fixed_zh_mps2",
    "data",
)
save_to_json(
    convert(fixed_zh_source, to_tongyong, auto_cut=False, rep=rep),
    "fixed_zh_ty",
    "data",
)
save_to_json(
    convert(fixed_zh_source, to_yale, auto_cut=False, rep=rep),
    "fixed_zh_yale",
    "data",
)
save_to_json(
    convert(fixed_zh_source, to_wadegiles, auto_cut=False, rep=rep),
    "fixed_zh_wg",
    "data",
)
save_to_json(
    convert(fixed_zh_source, to_romatzyh, auto_cut=False, rep=rep),
    "fixed_zh_gr",
    "data",
)
save_to_json(
    convert(fixed_zh_source, to_cyrillic, auto_cut=False, rep=rep),
    "fixed_zh_cy",
    "data",
)
save_to_json(
    convert(fixed_zh_source, to_xiaojing, auto_cut=False, rep=rep),
    "fixed_zh_xj",
    "data",
)
