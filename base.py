# -*- encoding: utf-8 -*-
"""基础文件，提供通用功能和数据结构定义。"""

from pathlib import Path
from typing import TypeAlias, Dict, Set, Tuple, Final

import ujson

# 类型别名和常量定义
Ldata: TypeAlias = Dict[str, str]
P: Final[Path] = Path(__file__).resolve().parent
LANG_FILES: Final[Tuple[str, ...]] = ("en_us", "zh_cn")


def load_json(file: str, folder: str = "data") -> Ldata:
    """加载JSON文件。

    Args:
        file (str): 需要加载的文件名，不含后缀名
        folder (str, optional): JSON文件所在文件夹路径，默认为"data"

    Returns:
        Dict[str, str]: 加载的JSON内容
    """
    path = P / folder / f"{file}.json"
    with path.open("r", encoding="utf-8", newline="\n") as f:
        return ujson.load(f)


def save_to_json(
    input_data: Tuple[Ldata, float],
    output_file: str,
    output_folder: str = "output",
) -> None:
    """
    将生成的语言文件保存至JSON。

    Args:
        input_data (Tuple[Ldata, float]): 输入的数据
        output_file (str): 保存的文件名，无格式后缀
        output_folder (str, optional): 保存的文件夹，默认为“output”

    Raises:
        OSError: 文件保存失败
    """
    try:
        input_dict, elapsed_time = input_data
        (P / output_folder).mkdir(exist_ok=True)
        file_path = P / output_folder / f"{output_file}.json"
        with open(file_path, "w", encoding="utf-8", newline="\n") as j:
            ujson.dump(input_dict, j, indent=2, ensure_ascii=False)
        size = file_size(file_path)
        print(
            f"已生成语言文件“{output_file}.json”，大小{size}，耗时{elapsed_time:.2f} s。"
        )
    except Exception as e:
        raise OSError(f"保存至JSON失败：{str(e)}") from e


def file_size(p: Path) -> str:
    """计算文件大小并返回可读的字符串表示。

    Args:
        p (pathlib.Path): 待计算文件的路径对象

    Returns:
        str: 格式化的文件大小字符串
    """
    size_in_bytes = p.stat().st_size
    size = (
        f"{round(size_in_bytes / 1048576, 2)} MB"
        if size_in_bytes > 1048576
        else f"{round(size_in_bytes / 1024, 2)} KB"
    )
    return size


# 语言文件数据
DATA: Final[Dict[str, Ldata]] = {
    lang_name: load_json(lang_name, "mc_lang/full") for lang_name in LANG_FILES
}

# 转换映射表
PINYIN_TO: Final[Dict[str, Ldata]] = {
    "wadegiles": load_json("py2wg"),
    "romatzyh": load_json("py2gr"),
    "simp_romatzyh": load_json("py2sgr"),
    "mps2": load_json("py2mps2"),
    "tongyong": load_json("py2ty"),
    "yale": load_json("py2yale"),
    "ipa": load_json("py2ipa"),
    "katakana": load_json("py2kk"),
    "cyrillic": load_json("py2cy"),
    "xiaojing": load_json("py2xj"),
}

# 修正数据
fixed_zh: Dict[str, Ldata] = {
    f"zh_{scheme}": load_json(f"fixed_zh_{scheme}", "data/fixed")
    for scheme in [
        "py",  # 汉语拼音修正
        "wg",  # 威妥玛拼音修正
        "gr",  # 国语罗马字修正
        "sgr",  # 简化国语罗马字修正
        "mps2",  # 注音二式修正
        "ty",  # 通用拼音修正
        "yale",  # 耶鲁拼音修正
        "cy",  # 西里尔转写修正
        "xj",  # 小儿经转写修正
    ]
}

# 汉语拼音手动修正
fixed_zh["zh_py"].update(load_json("fixed_zh_py_manual", "data/fixed"))

gr_values: Set[str] = set(PINYIN_TO["romatzyh"].values())  # 国语罗马字的有效拼写
cy_values: Set[str] = set(PINYIN_TO["cyrillic"].values())  # 西里尔转写的有效拼写
TONE_TO_IPA: Final[Ldata] = {
    "1": "˥",
    "2": "˧˥",
    "3": "˨˩˦",
    "4": "˥˩",
    "5": "",
}  # IPA声调

rep_zh: Ldata = load_json("rep_zh", "data/rep")  # 连写的中文转写方案替换修正
PINYIN_FINALS: Final[Tuple[str, ...]] = tuple("aāááàoōóǒòeēéěè")  # 可能的零声母开头

rep_ja_kk: Ldata = load_json("rep_ja_kk", "data/rep")  # 片假名替换修正
