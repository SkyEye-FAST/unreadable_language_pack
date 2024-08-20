# -*- encoding: utf-8 -*-
"""Minecraft难视语言资源包生成器"""

import time
import zipfile as zf

from base import P, data, fixed_zh, rep_ja_kk, file_size
from converter import (
    save_to_json,
    convert,
    to_bopomofo,
    to_cyrillic,
    to_harmonic,
    to_i7h,
    to_ipa,
    to_katakana,
    to_manyogana,
    to_mps2,
    to_pinyin,
    to_romatzyh,
    to_tongyong,
    to_wadegiles,
    to_xiaojing,
    to_yale,
)


def main() -> None:
    """
    主函数，生成语言文件并打包成资源包。
    """

    # 生成语言文件
    main_start_time = time.time()
    save_to_json(convert(data["en_us"], to_i7h), "en_i7h")
    save_to_json(convert(data["en_us"], to_katakana, rep=rep_ja_kk), "ja_kk")
    save_to_json(convert(data["en_us"], to_manyogana, rep=rep_ja_kk), "ja_my")
    save_to_json(convert(data["zh_cn"], to_harmonic), "zh_hm")
    save_to_json(convert(data["zh_cn"], to_pinyin, fixed_zh["zh_py"]), "zh_py")
    save_to_json(convert(data["zh_cn"], to_mps2, fixed_zh["zh_mps2"]), "zh_mps2")
    save_to_json(convert(data["zh_cn"], to_tongyong, fixed_zh["zh_ty"]), "zh_ty")
    save_to_json(convert(data["zh_cn"], to_yale, fixed_zh["zh_yale"]), "zh_yale")
    save_to_json(convert(data["zh_cn"], to_ipa), "zh_ipa")
    save_to_json(convert(data["zh_cn"], to_bopomofo), "zh_bpmf")
    save_to_json(convert(data["zh_cn"], to_wadegiles, fixed_zh["zh_wg"]), "zh_wg")
    save_to_json(convert(data["zh_cn"], to_romatzyh, fixed_zh["zh_gr"]), "zh_gr")
    save_to_json(convert(data["zh_cn"], to_cyrillic, fixed_zh["zh_cy"]), "zh_cy")
    save_to_json(convert(data["zh_cn"], to_xiaojing, fixed_zh["zh_xj"]), "zh_xj")
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
    pack_size = file_size(pack_path)
    print(
        f"\n资源包“{pack_path.name}”打包完毕，大小{pack_size}，打包耗时{zip_elapsed_time:.2f} s。"
    )


if __name__ == "__main__":
    main()
