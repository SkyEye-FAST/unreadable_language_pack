# -*- encoding: utf-8 -*-
"""数据修复脚本"""

from base import load_json
from converter import (
    save_to_json,
    to_pinyin,
    to_wadegiles,
    to_romatzyh,
    to_cyrillic,
    to_xiaojing,
)

rep = {"！:(": "! :(", "，": ", "}

fixed_zh_source = load_json("fixed_zh_source")
save_to_json(
    fixed_zh_source,
    {
        "output_file": "fixed_zh_py",
        "func": to_pinyin,
        "output_folder": "data",
        "auto_cut": False,
        "rep": rep,
    },
)
save_to_json(
    fixed_zh_source,
    {
        "output_file": "fixed_zh_wg",
        "func": to_wadegiles,
        "output_folder": "data",
        "auto_cut": False,
        "rep": rep,
    },
)
save_to_json(
    fixed_zh_source,
    {
        "output_file": "fixed_zh_gr",
        "func": to_romatzyh,
        "output_folder": "data",
        "auto_cut": False,
        "rep": rep,
    },
)
save_to_json(
    fixed_zh_source,
    {
        "output_file": "fixed_zh_cy",
        "func": to_cyrillic,
        "output_folder": "data",
        "auto_cut": False,
        "rep": rep,
    },
)
save_to_json(
    fixed_zh_source,
    {
        "output_file": "fixed_zh_xj",
        "func": to_xiaojing,
        "output_folder": "data",
        "auto_cut": False,
        "rep": rep,
    },
)
