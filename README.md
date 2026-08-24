# Minecraft难视语言资源包

[![Update resource pack](https://github.com/SkyEye-FAST/unreadable_language_pack/actions/workflows/update.yml/badge.svg)](https://github.com/SkyEye-FAST/unreadable_language_pack/actions/workflows/update.yml) [![Checks](https://github.com/SkyEye-FAST/unreadable_language_pack/actions/workflows/checks.yml/badge.svg)](https://github.com/SkyEye-FAST/unreadable_language_pack/actions/workflows/checks.yml)

- **[English](README_en.md) | [中文](README.md)**

---

此项目提供由现有语言转换而来的新增非常规“语言”Minecraft Java版资源包。详见[#资源包](#资源包)一节。

请使用模组[Modern UI](https://modrinth.com/mod/modern-ui)让游戏支持现代字体特性来保证所有字符正常显示。

推荐与模组[Language Reload](https://modrinth.com/mod/language-reload)和[Untranslated Items](https://www.curseforge.com/minecraft/mc-mods/untranslated-items)一同使用。

## 下载

- [**下载最新版本资源包**](https://github.com/SkyEye-FAST/unreadable_language_pack/releases/latest/download/unreadable_language_pack.zip)
- [查看历史版本](https://github.com/SkyEye-FAST/unreadable_language_pack/releases/)

> [!TIP]
> 由于1.19.2之后所有版本的语言文件都可以通用，不一定需要选择对应版本的标签，选择最新版本即可。

## 说明

### 依赖项

项目使用 Python 3.12+ 和 [uv](https://docs.astral.sh/uv/) 管理依赖。克隆仓库（含子模块）后执行：

```shell
uv sync --locked --dev
uv run language-pack build
```

运行测试与代码检查：

```shell
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

### 获取语言文件

本仓库会在每天🕧00:30（UTC+8，即🕟UTC 16:30）自动检查Minecraft Java版语言文件（`en_us.json`、`zh_cn.json`）更新并更新资源包。

### 资源包

资源包使用 `uv run language-pack build` 生成。语言文件存储在 `output` 文件夹下，并同 [`pack.mcmeta`](pack.mcmeta) 和 [`pack.png`](pack.png) 一起打包为 `unreadable_language_pack.zip`。ZIP 的成员顺序和时间戳固定，相同输入会得到相同归档。

资源包向游戏内添加了15种语言。

> [!TIP]
> 本项目使用的中文转写对照表参见下两表：
>
> [`comparison_table_1.tsv`](table/comparison_table_1.tsv)（带声调，注音方案）
>
> [`comparison_table_2.tsv`](table/comparison_table_2.tsv)（不带声调，外文转写）
>
> 表中可能含有普通话中不存在的音节，如lüan等，仅供参考。
>
> 表中省略了ㆭ（ng，/ŋ̍/）、ㆬ（m，/m̩/）、ㄯ（n，/n̩/）、ㄏㆬ（hm，/xm̩/）、ㄏㆭ（hng，/xŋ̍/）的转写。大部分方案中都没有说明它们应如何拼写，本项目实际上也没有用到这些音节。

#### i18nglish (i7h)（[`en_i7h.json`](output/en_i7h.json)）

- 选择之后，所有字符串会变为保留英文单词的首尾字符，中间用字符数替代的缩写。长度为2或以下的单词保持不变。

#### エングリスホ (カタカナ)（[`ja_kk.json`](output/ja_kk.json)）

- 即“English (Katakana)”。
- 选择之后，所有字符串会变为英文转写而来的片假名。

> [!WARNING]
> 英文转写至片假名使用了[KotRikD/romajitable](https://github.com/KotRikD/romajitable)的映射，这不是正确的音译方式，**可能和英文的真实读音相差甚大**。**请不要将转写结果用于娱乐场景外的地方。**
>
> 转写结果中修复了“Lena Raine”和“Samuel Åberg”的转写，并保留了“C418”。

#### 江尓具利須保 (万葉仮名)（[`ja_my.json`](output/ja_my.json)）

- 即“English (Man'yōgana)”。
- 选择之后，所有字符串会变为英文转写而来的万叶假名。为保证生成结果不偏差过大，仅选择万叶假名多种可能中的某一种。

#### Hànyǔ Pīnyīn (Zhōngguó Dàlù)（[`zh_py.json`](output/zh_py.json)）

- 即“汉语拼音 (中国大陆)”。
- 选择之后，所有字符串会变为简体中文转写而来的汉语拼音，以词为单位。
  - 按现行推荐性国家标准 [GB/T 16159-2012《汉语拼音正词法基本规则》](https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=5645BD8DB9D8D73053AD3A2397E15E74)审校；[教育部公开的标准全文](https://www.moe.gov.cn/ewebeditor/uploadfile/2015/01/13/20150113091717604.pdf)可用于核对具体条款。

> [!IMPORTANT]
> 汉字标音使用 `pypinyin` 和 `pypinyin-dict`，补充 [CC-CEDICT](https://cc-cedict.org/) 数据，并由 `data/mandarin_phrase_pronunciations.json` 提供项目级词组读音。词典按“基础词典 → CC-CEDICT/di → 项目人工校订”的优先级加载。词组键中的空格表示只在相邻分词完全匹配时采用该上下文读音，例如 `结果 的`。所有根据普通话发音转写的方案都使用这份读音数据。
>
> 中文分词使用 `jieba` 和 `data/mandarin_segmentation_dictionary.txt`；Minecraft 语料的人工词边界修正在 `data/mandarin_word_boundary_corrections.json` 中维护。所有中文派生方案共享读音判定、词边界和 Minecraft 技术单元保护，但不共享汉语拼音的标点、大小写和标调规则。其他方案保留源标点，并分别使用自己的拼写、声调和分隔规则。
>
> 汉语拼音输出以词为单位分写，按语法和词汇化程度处理常见结构，并处理序数连接号、隔音符号、句首及标题首词大写、轻声不标调和“一”“不”标本调。比如“不是”写作 `bù shì`，而不是记录口语变调的 `bú shì`。Minecraft 格式码、占位符、命令和程序语法会先作为技术单元保护；完整的阅读结论与项目取舍见 [`docs/hanyu-pinyin-orthography.md`](docs/hanyu-pinyin-orthography.md)。
>
> 这里的“按国标审校”不等同于形式化合规认证。自动分词无法仅靠上下文可靠判断所有语法关系、专名、成语结构和多音词；项目只维护 Minecraft 实际语言条目需要的词语和修正。发现问题时应优先补充 `data/mandarin_phrase_pronunciations.json`、`data/mandarin_segmentation_dictionary.txt`、`data/mandarin_word_boundary_corrections.json` 或对应语言键的修正数据，而不是加入无关通用词汇或在代码中硬编码语言键。

#### Chinese in IPA (t͡ʂʊŋ˥ kwo˧˥ ta˥˩ lu˥˩)（[`zh_ipa.json`](output/zh_ipa.json)）

- 即“国际音标转写 (中国大陆)”。
- 选择之后，所有字符串会变为简体中文转写而来的IPA。

> [!NOTE]
> IPA转写方案来自[@UntPhesoca](https://www.zhihu.com/people/UntW)所写文章[新老派普通话的宽严式记音（含儿化韵）](https://zhuanlan.zhihu.com/p/38258415)中的宽式标音。轻声作不标出处理。

#### ㄓㄨˋ ㄧㄣ ㄈㄨˊ ㄏㄠˋ (ㄓㄨㄥ ㄍㄨㄛˊ ㄉㄚˋ ㄌㄨˋ)（[`zh_bpmf.json`](output/zh_bpmf.json)）

- 即“注音符号 (中国大陆)”。
- 选择之后，所有字符串会变为简体中文转写而来的注音符号。

#### Wade–Giles (Chung¹-Kuo² Ta⁴-Lu⁴)（[`zh_wg.json`](output/zh_wg.json)）

- 即“威妥玛拼音 (中国大陆)”。
- 选择之后，所有字符串会变为简体中文转写而来的威妥玛拼音。

#### Gwoyeu Romatzyh (Jonggwo Dahluh)（[`zh_gr.json`](output/zh_gr.json)）

- 即“国语罗马字 (中国大陆)”。
- 选择之后，所有字符串会变为简体中文转写而来的国语罗马字。

#### Jiaanhuah Guoryuu Romatzyh (JJungguor Dahluh)（[`zh_sgr.json`](output/zh_sgr.json)）

- 即“简化国语罗马字 (中国大陆)”。
- 选择之后，所有字符串会变为简体中文转写而来的简化国语罗马字。

#### Jù-yīn Fú-hàu Dì-èr Shr̀ (Jūng-guó Dà-lù)（[`zh_mps2.json`](output/zh_mps2.json)）

- 即“注音符号第二式 (中国大陆)”。
- 选择之后，所有字符串会变为简体中文转写而来的注音符号第二式。

#### Tong-yòng Pin-yin (Jhong-guó Dà-lù)（[`zh_ty.json`](output/zh_ty.json)）

- 即“通用拼音 (中国大陆)”。
- 选择之后，所有字符串会变为简体中文转写而来的通用拼音。

#### Yale romanization (Jūng-gwó Dà-lù)（[`zh_yale.json`](output/zh_yale.json)）

- 即“耶鲁拼音 (中国大陆)”。
- 选择之后，所有字符串会变为简体中文转写而来的耶鲁拼音。

#### カタカナ (ジョン グオ ダー ルー)（[`zh_kk.json`](output/zh_kk.json)）

- 即“片假名 (中国大陆)”。
- 选择之后，所有字符串会变为简体中文转写而来的片假名。

#### Палладицу (Чжунго далу)（[`zh_cy.json`](output/zh_cy.json)）

- 即“西里尔化中文 (中国大陆)”。
- 选择之后，所有字符串会变为使用巴拉第音标体系西里尔化的简体中文。

#### ثِیَوْعَرݣ‌ٍْ (جْو‌قُوَ دَا‌لُ)（[`zh_xj.json`](output/zh_xj.json)）

- 即“小儿经 (中国大陆)”。
- 选择之后，所有字符串会变为简体中文转写而来的小儿经。

![Sample](sample/sample_en_i7h.png)
![Sample](sample/sample_ja_kk.png)
![Sample](sample/sample_ja_my.png)
![Sample](sample/sample_zh_py.png)
![Sample](sample/sample_zh_ipa.png)
![Sample](sample/sample_zh_bpmf.png)
![Sample](sample/sample_zh_wg.png)
![Sample](sample/sample_zh_gr.png)
![Sample](sample/sample_zh_sgr.png)
![Sample](sample/sample_zh_mps2.png)
![Sample](sample/sample_zh_ty.png)
![Sample](sample/sample_zh_yale.png)
![Sample](sample/sample_zh_kk.png)
![Sample](sample/sample_zh_cy.png)
![Sample](sample/sample_zh_xj.png)

## 协议

资源包在[Apache 2.0协议](LICENSE)下发布。

```text
  Copyright 2024-2025 SkyEye_FAST

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
```

## 反馈

遇到的问题和功能建议等可以提出议题（Issue）。

欢迎创建拉取请求（Pull request）。
