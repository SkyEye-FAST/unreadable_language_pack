# -*- encoding: utf-8 -*-
"""Minecraft难视语言资源包生成器"""

import time
import zipfile as zf

from base import P, data, fixed_zh
from converter import (
    save_to_json,
    to_bopomofo,
    to_cyrillic,
    to_ipa,
    to_katakana,
    to_manyogana,
    to_pinyin,
    to_romatzyh,
    to_wadegiles,
    to_xiaojing,
)


def main() -> None:
    """
    主函数，生成语言文件并打包成资源包。
    """

    # 生成语言文件
    main_start_time = time.time()
    save_to_json(data["en_us"], "ja_kk", to_katakana)
    save_to_json(data["en_us"], "ja_my", to_manyogana)
    save_to_json(data["zh_cn"], "zh_py", to_pinyin, fixed_zh["zh_py"])
    save_to_json(data["zh_cn"], "zh_ipa", to_ipa)
    save_to_json(data["zh_cn"], "zh_bpmf", to_bopomofo)
    save_to_json(data["zh_cn"], "zh_wg", to_wadegiles, fixed_zh["zh_wg"])
    save_to_json(data["zh_cn"], "zh_gr", to_romatzyh, fixed_zh["zh_gr"])
    save_to_json(data["zh_cn"], "zh_cy", to_cyrillic, fixed_zh["zh_cy"])
    save_to_json(data["zh_cn"], "zh_xj", to_xiaojing, fixed_zh["zh_xj"])
    main_elapsed_time = time.time() - main_start_time
    print(f"\n语言文件生成完毕，共耗时{main_elapsed_time:.2f} s。")

    # 生成资源包
    zip_start_time = time.time()
    pack_path = P / "unreadable_language_pack.zip"
    with zf.ZipFile(pack_path, "w", compression=zf.ZIP_DEFLATED, compresslevel=9) as z:
        z.write(P / "pack.mcmeta", arcname="pack.mcmeta")
        z.write(P / "pack.png", arcname="pack.png")
        for lang_file in P.glob("output/*.json"):
            z.write(lang_file, arcname=f"assets/minecraft/lang/{lang_file.name}")
    zip_elapsed_time = time.time() - zip_start_time
    pack_size = f"{round(pack_path.stat().st_size / 1024, 2)} KB"
    print(
        f"\n资源包“{pack_path.name}”打包完毕，大小{pack_size}，打包耗时{zip_elapsed_time:.2f} s。"
    )


if __name__ == "__main__":
    main()
