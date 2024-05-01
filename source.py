# -*- encoding: utf-8 -*-
"""Minecraft语言文件更新器"""

import sys
from zipfile import ZipFile
from pathlib import Path
import requests as r


def get_json(url: str):
    """获取JSON"""
    try:
        resp = r.get(url, timeout=60)
        resp.raise_for_status()
        return resp.json()
    except r.exceptions.RequestException as ex:
        print(f"请求发生错误: {ex}")
        sys.exit()


# 文件夹
P = Path(__file__).resolve().parent
LANG_DIR = P / "source"
LANG_DIR.mkdir(exist_ok=True)

# 获取version_manifest_v2.json
version_manifest_path = P / "version_manifest_v2.json"
try:
    print("正在获取版本清单“version_manifest_v2.json”……\n")
    version_manifest = r.get(
        "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json",
        timeout=60,
    )
    version_manifest.raise_for_status()
    version_manifest_json = version_manifest.json()
except r.exceptions.RequestException as e:
    print("无法获取版本清单，请检查网络连接。")
    sys.exit()
V = version_manifest_json["latest"]["snapshot"]
with open(P / "version.txt", "w", encoding="utf-8") as f:
    f.write(V)

# 获取client.json
client_manifest_url = next(
    (i["url"] for i in version_manifest_json["versions"] if i["id"] == V), None
)

print(f"正在获取客户端索引文件“{client_manifest_url.rsplit('/', 1)[-1]}”……")
client_manifest = get_json(client_manifest_url)

# 获取客户端JAR
client_url = client_manifest["downloads"]["client"]["url"]
client_path = P / "client.jar"
print("正在下载客户端Java归档（client.jar）……")
try:
    response = r.get(client_url, timeout=120)
    response.raise_for_status()
    with open(client_path, "wb") as f:
        f.write(response.content)
except r.exceptions.RequestException as e:
    print(f"请求发生错误: {e}")
    client_path.unlink()
    sys.exit()

# 解压English (US)语言文件
with ZipFile(client_path) as client:
    with client.open("assets/minecraft/lang/en_us.json") as content:
        with open(LANG_DIR / "en_us.json", "wb") as f:
            print("正在从client.jar解压语言文件“en_us.json”……")
            f.write(content.read())

# 删除客户端JAR
print("正在删除client.jar……\n")
client_path.unlink()

print("已完成。")
