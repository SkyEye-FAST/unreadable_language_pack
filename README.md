# Minecraft难视语言资源包

- **[English](/README_en.md) | [中文](/README.md)**

----

此项目用于提供将Minecraft Java版语言文件的源字符串转写为片假名、简体中文转写为汉语拼音及IPA的资源包。

推荐与模组[Language Reload](https://modrinth.com/mod/language-reload)和[Untranslated Items](https://www.curseforge.com/minecraft/mc-mods/untranslated-items)一同使用。

## 说明

### 依赖项

请使用下面的命令安装依赖项：

``` shell
pip install -r requirements.txt
```

### 获取语言文件

本仓库会在每天🕧00:30（UTC+8，即🕟UTC 16:30）自动检查Minecraft Java版语言文件（`en_us.json`、`zh_cn.json`、`ja_jp.json`）更新并更新资源包。使用脚本为[`source.py`](/source.py)（需要库`requests`、`romajitable`、`pypinyin`、`pypinyin_dict`）。获取到的语言文件存储在与脚本同级的`source`文件夹下。

### 资源包

资源包使用[`pack.py`](/pack.py)生成。脚本生成的语言文件为[`ja_kk.json`](/ja_kk.json)、[`zh_py.json`](/zh_py.json)和[`zh_ipa.json`](/zh_ipa.json)，同[`pack.mcmeta`](/pack.mcmeta)一同打包为`unreadable_language_pack.zip`。

资源包向游戏内添加了3种语言：

- “エングリスホ (カタカナ)”（即“English (Katakana)”）。选择之后，所有字符串会变为英文转写而来的片假名。
- “pīn yīn (zhōng guó)”（即“拼音 (中国)”）。选择之后，所有字符串会变为简体中文转写而来的汉语拼音。
- “pʰin˥ jin˥ (t͡ʂʊŋ˥ kwo˧˥)”（即“拼音 (中国)”）。选择之后，所有字符串会变为简体中文转写而来的IPA。

## 反馈

遇到的问题和功能建议等可以提出议题（Issue）。

欢迎创建拉取请求（Pull request）。
