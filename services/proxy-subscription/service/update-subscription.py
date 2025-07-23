#!/usr/bin/env python3

"""
使用Python3实现订阅文件的更新逻辑
"""

import os
import sys
import base64
import shutil
import subprocess
from datetime import datetime
from dotenv import load_dotenv
from router.target import constants, logger, proxy

# 加载环境变量
if os.path.exists("/etc/profile.d/50-environment.sh"):
    print("Loading environment variables")
    with open("/etc/profile.d/50-environment.sh", "r") as f:
       load_dotenv(stream=f)
    PROXY = os.environ.get("PROXY",None)
    print(f"PROXY='{PROXY}'")

INPUT_FILE = os.environ.get("INPUT_FILE", "${ROUTER_DATA_PATH}/proxy/subscription.txt")
STATE_DIRECTORY = os.environ.get("STATE_DIRECTORY", "/var/lib/proxy")

print(f"STATE_DIRECTORY='{STATE_DIRECTORY}'")
os.makedirs(STATE_DIRECTORY, exist_ok=True)
os.chdir(STATE_DIRECTORY)

def die(msg, code=1):
    """
    输出错误信息并退出
    """
    print(msg, file=sys.stderr)
    sys.exit(code)

def _wget(*args, env={}):
    """
    使用wget下载文件
    """
    cmds = ["--quiet", "--timeout=5", *args]
    print(f"  >> wget {' '.join(cmds)}", file=sys.stderr)
    return subprocess.run(["wget", *cmds], check=False)

def with_proxy(cmd: list):
    """
    使用代理执行命令
    """
    PROXY = os.environ.get("PROXY",None)
    https_proxy = os.environ.get("https_proxy",None)
    if https_proxy:
        print(f"[proxy] execute using environment: {https_proxy}")
        return _wget(*cmd)
    elif PROXY:
        print(f"[proxy] execute using proxy: {PROXY}")
        env = os.environ.copy()
        for k in ["https_proxy", "http_proxy", "all_proxy", "HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY"]:
            env[k] = PROXY
        return _wget(*cmd, env=env)
    else:
        print("[proxy] execute with proxy: no proxy setting")
        return subprocess.CompletedProcess(cmd, 1)

def without_proxy(cmd: list):
    """
    不使用代理执行命令
    """
    print("[proxy] execute without proxy:")
    env = os.environ.copy()
    for k in ["https_proxy", "http_proxy", "all_proxy", "HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY"]:
        env[k] = ""

    return _wget(*cmd, env=env)

def write_if_change(fname, data):
    """
    仅当内容变化时写入文件
    """
    global SOME_CHANGED
    old_data = None
    if os.path.exists(fname):
        with open(fname, "rb") as f:
            old_data = f.read()
        if old_data == data:
            print(f"{fname} unchanged")
            return
    print(f"emit file {fname}")
    with open(fname, "wb") as f:
        f.write(data)
    SOME_CHANGED = 1

if not os.path.exists(INPUT_FILE):
    die(f"missing input file at {INPUT_FILE}", 66)

os.makedirs("subscriptions", exist_ok=True)
os.chdir("subscriptions")

print(f"reading from {INPUT_FILE}")

# 检查输入文件格式
with open(INPUT_FILE, "r") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if " " not in line:
            die(f"\tinvalid line: {line}\n\texpected format: NAME https://xxxx", 66)

ALLOW_NAMES = []
SOME_CHANGED = 0

with open(INPUT_FILE, "r") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
            
        fname, url = line.split(" ", 1)
        fname = fname.strip()
        url = url.strip()
        ALLOW_NAMES.append(f"{fname}.txt")
        print(f"[{fname}] Downloading from: {url}")

        # 先尝试不使用代理
        result = without_proxy([url, "-O", f"{fname}.downloading"])
        if result.returncode == 0:
            print("complete without proxy")
        else:
            print("failed without proxy")
            # 再尝试使用代理
            result = with_proxy([url, "-O", f"{fname}.downloading"])
            if result.returncode == 0:
                print("complete with proxy")
            elif os.path.exists(f"{fname}.txt"):
                print(f"[{fname}] Failed to download. use old one.")
                continue
            else:
                die(f"[{fname}] Error: failed to download, and no old one.")

        proxy.tools.fix_base64_padding(f"{fname}.downloading")
        try:
            with open(f"{fname}.downloading", "rb") as fdown:
                raw = fdown.read()
                try:
                    data = base64.b64decode(raw, validate=True)
                    print("file is valid base64 encoded")
                    os.remove(f"{fname}.downloading")
                except Exception:
                    print("file is NOT valid base64 encoded")
                    data = raw
        except Exception as e:
            die(f"[{fname}] Error reading downloaded file: {e}")

        write_if_change(f"{fname}.txt", data)

# 处理未订阅的文件
for fname in [f for f in os.listdir(".") if f.endswith(".txt")]:
    if fname not in ALLOW_NAMES:
        print(f"[{fname}] unsubscribed")
        shutil.move(fname, f"{fname}.old")
        SOME_CHANGED = 1

if SOME_CHANGED or not os.path.exists("../subscription-updated"):
    print("[***] subscription updated")
    with open("../subscription-updated", "w") as f:
        f.write(datetime.now().strftime("%Y%m%d-%H%M%S"))
else:
    print("[***] subscription not changed")
