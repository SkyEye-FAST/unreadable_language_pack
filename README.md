# Minecraft难视语言资源包

- **[English](README_en.md) | [中文](README.md)**

----

此项目用于提供将Minecraft Java版语言文件的源字符串转写为片假名和万叶假名，并将简体中文转写为汉语拼音、注音符号及IPA的资源包。

请使用模组[Modern UI](https://modrinth.com/mod/modern-ui)让游戏支持现代字体特性来保证所有字符正常显示。

推荐与模组[Language Reload](https://modrinth.com/mod/language-reload)和[Untranslated Items](https://www.curseforge.com/minecraft/mc-mods/untranslated-items)一同使用。

## 说明

### 依赖项

请使用下面的命令安装依赖项：

``` shell
pip install -r requirements.txt
```

### 获取语言文件

本仓库会在每天🕧00:30（UTC+8，即🕟UTC 16:30）自动检查Minecraft Java版语言文件（`en_us.json`、`zh_cn.json`）更新并更新资源包。使用脚本为[`source.py`](source.py)。获取到的语言文件存储在与脚本同级的`source`文件夹下。

### 资源包

资源包使用[`pack.py`](pack.py)生成。脚本生成的语言文件为[`ja_kk.json`](ja_kk.json)、[`ja_my.json`](ja_my.json)、[`zh_py.json`](zh_py.json)、[`zh_pyw.json`](zh_pyw.json)和[`zh_ipa.json`](zh_ipa.json)，同[`pack.mcmeta`](pack.mcmeta)一同打包为`unreadable_language_pack.zip`。

资源包向游戏内添加了6种语言：

- **“エングリスホ (カタカナ)”**
  - 即“English (Katakana)”。
  - 选择之后，所有字符串会变为英文转写而来的片假名。
- **“依尓愚煎須百 (万葉仮名)”**
  - 即“English (Man'yōgana)”。
  - 选择之后，所有字符串会变为英文转写而来的万叶假名。为保证生成结果不偏差过大，仅选择万叶假名多种可能中的某一种。
  > [!WARNING]
  > 英文转写至片假名使用了[KotRikD/romajitable](https://github.com/KotRikD/romajitable)的映射，这不是正确的音译方式，**可能和英文的真实读音相差甚大**。**请不要将转写结果用于娱乐场景外的地方。**
  >
  > 转写结果中修复了“Lena Raine”和“Samuel Åberg”的转写，并保留了“C418”。
- **“pīn yīn jiǎn tǐ zhōng wén (zhōng guó dà lù)”**
  - 即“拼音简体中文 (中国大陆)”。
  - 选择之后，所有字符串会变为简体中文转写而来的汉语拼音，以字为单位。
  > [!NOTE]
  > 汉字标音使用了库`pypinyin`和`pypinyin_dict`，补充了[cc_cedict.org](https://cc-cedict.org/)的数据，并手动添加了某些词语的读音。
  >
  > 原则上，读音以普通话音系为准。
- **“Pīnyīn jiǎntǐ zhōngwén (Zhōngguó dàlù)”**
  - 即“拼音简体中文 (中国大陆)”。
  - 选择之后，所有字符串会变为简体中文转写而来的汉语拼音，以词为单位，尝试遵循了GB/T 16159-2012。
  > [!IMPORTANT]
  > 中文分词使用了库`jieba`，配置了词库并进行了替换修正。
  >
  > 虽然经过处理，但结果仍然无法保证完全符合GB/T 16159-2012的要求。应加连接号的地方尚未有合适的方法满足要求。
  >
  > “一”“不”等变调按照GB/T 16159-2012要求不标出。
  >
  > **由于没有经过完整的人工审核，不能保证长文本的分词准确性。**
- **“IPA t͡ɕjɛn˨˩˦ tʰi˨˩˦ t͡ʂʊŋ˥ wən˧ (t͡ʂʊŋ˥ kwo˧˥ ta˥˩ lu˥˩)”**
  - 即“IPA简体中文 (中国大陆)”。
  - 选择之后，所有字符串会变为简体中文转写而来的IPA。
  > [!NOTE]
  > IPA转写方案来自[@UntPhesoca](https://www.zhihu.com/people/UntW)所写文章[新老派普通话的宽严式记音（含儿化韵）](https://zhuanlan.zhihu.com/p/38258415)中的宽式标音。轻声作不标出处理。
- **“ㄓㄨˋ ㄧㄣ ㄐㄧㄢˇ ㄊㄧˇ ㄓㄨㄥ ㄨㄣˊ (ㄓㄨㄥ ㄍㄨㄛˊ ㄉㄚˋ ㄌㄨˋ)”**
  - 即“注音简体中文 (中国大陆)”。
  - 选择之后，所有字符串会变为简体中文转写而来的注音符号。

![Sample](sample/sample_ja_kk.png)
![Sample](sample/sample_ja_my.png)
![Sample](sample/sample_zh_py.png)
![Sample](sample/sample_zh_pyw.png)
![Sample](sample/sample_zh_ipa.png)
![Sample](sample/sample_zh_bpmf.png)

## 反馈

遇到的问题和功能建议等可以提出议题（Issue）。

欢迎创建拉取请求（Pull request）。
