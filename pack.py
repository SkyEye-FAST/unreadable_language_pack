"""Minecraft难视语言资源包生成器"""

import time
import zipfile as zf
from typing import Final

from base import DATA, P, file_size, fixed_zh, save_to_json
from converter import ChineseConverter, EnglishConverter

# 语言文件配置
LANG_CONVERSIONS: Final[list[tuple[str, str, dict]]] = [
    # (转换方法, 输出文件名, 修正字典)
    ("to_i7h", "en_i7h", None),
    ("to_katakana", "ja_kk", None),
    ("to_manyogana", "ja_my", None),
    ("to_split", "zh_split", fixed_zh["zh_source"]),
    ("to_harmonic", "zh_hm", None),
    ("to_pinyin", "zh_py", fixed_zh["zh_py"]),
    ("to_ipa", "zh_ipa", None),
    ("to_bopomofo", "zh_bpmf", None),
    ("to_wadegiles", "zh_wg", fixed_zh["zh_wg"]),
    ("to_romatzyh", "zh_gr", fixed_zh["zh_gr"]),
    ("to_simp_romatzyh", "zh_sgr", fixed_zh["zh_sgr"]),
    ("to_mps2", "zh_mps2", fixed_zh["zh_mps2"]),
    ("to_tongyong", "zh_ty", fixed_zh["zh_ty"]),
    ("to_yale", "zh_yale", fixed_zh["zh_yale"]),
    ("to_katakana", "zh_kk", None),
    ("to_cyrillic", "zh_cy", fixed_zh["zh_cy"]),
    ("to_xiaojing", "zh_xj", fixed_zh["zh_xj"]),
]


def generate_language_files() -> float:
    """生成所有语言文件。

    Returns:
        float: 生成耗时（秒）
    """
    start_time = time.time()
    en_conv = EnglishConverter(DATA["en_us"])
    zh_conv = ChineseConverter(DATA["zh_cn"])

    for method, output, fix_dict in LANG_CONVERSIONS:
        if output.startswith(("en_", "ja_")):
            conv = en_conv
        else:
            conv = zh_conv
        save_to_json(conv.convert(getattr(conv, method), fix_dict), output)

    return time.time() - start_time


def create_resource_pack() -> tuple[str, float]:
    """将生成的语言文件和必要的资源打包为Minecraft资源包。

    Returns:
        tuple[str, float]: (资源包大小，打包耗时)
    """
    start_time = time.time()
    pack_path = P / "unreadable_language_pack.zip"

    with zf.ZipFile(pack_path, "w", compression=zf.ZIP_DEFLATED, compresslevel=9) as z:
        z.write(P / "pack.mcmeta", arcname="pack.mcmeta")
        z.write(P / "pack.png", arcname="pack.png")
        for lang_file in P.glob("output/*.json"):
            if lang_file != "zh_split.json":
                z.write(lang_file, arcname=f"assets/minecraft/lang/{lang_file.name}")

    return file_size(pack_path), time.time() - start_time


if __name__ == "__main__":
    gen_time = generate_language_files()
    print(f"\n语言文件生成完毕，共耗时{gen_time:.2f} s。")

    pack_size, zip_time = create_resource_pack()
    print(f"\n资源包打包完毕，大小{pack_size}，打包耗时{zip_time:.2f} s。")
