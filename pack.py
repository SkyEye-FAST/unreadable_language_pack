# -*- encoding: utf-8 -*-
"""Minecraft Katakana Language Resource Pack Generator"""

import json
import zipfile as z
from pathlib import Path
from romajitable import to_kana as tk

# 当前绝对路径
P = Path(__file__).resolve().parent

# 读取语言文件
with open(P / "source" / "en_us.json", "rb") as s:
    source = json.load(s)

# 生成语言文件
with open(P / "ja_kk.json", "w", encoding="utf-8") as f:
    json.dump(
        {
            k: tk(v)
            .katakana.replace("%ス", r"%s")
            .replace("%ド", r"%d")
            .replace("。。。", r"...")
            for k, v in source.items()
        },
        f,
        indent=2,
    )

# 生成资源包
pack_dir = P / "katakana_language_pack.zip"
with z.ZipFile(pack_dir, "w", compression=z.ZIP_DEFLATED, compresslevel=9) as f:
    f.write(P / "pack.mcmeta", arcname="pack.mcmeta")
    f.write(P / "ja_kk.json", arcname="assets/minecraft/lang/ja_kk.json")
