#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""轮询 GitHub 设备授权结果；成功后写入 gh 配置与 token.txt，并打印账号名。

用法：python gh_device_poll.py [等待秒数，默认 600]
"""
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

CLIENT_ID = "178c6fc778ccc68e1d6a"
DEVICE = r"D:\DeepScientist\tools\device.json"
TOKEN_OUT = r"D:\DeepScientist\tools\token.txt"
GH = r"D:\DeepScientist\tools\gh\bin\gh.exe"
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def post(url, data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Accept", "application/json")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("User-Agent", "sic-console-uploader")
    try:
        with OPENER.open(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        return json.loads(exc.read().decode("utf-8", "replace") or "{}")


def get_me(token):
    req = urllib.request.Request("https://api.github.com/user")
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "sic-console-uploader")
    with OPENER.open(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def main():
    wait = int(sys.argv[1]) if len(sys.argv) > 1 else 600
    dev = json.load(open(DEVICE, encoding="utf-8"))
    deadline = time.time() + wait
    interval = dev.get("interval", 5)
    last = ""
    while time.time() < deadline:
        r = post("https://github.com/login/oauth/access_token", {
            "client_id": CLIENT_ID,
            "device_code": dev["device_code"],
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        })
        err = r.get("error")
        if r.get("access_token"):
            tok = r["access_token"]
            me = get_me(tok)
            with open(TOKEN_OUT, "w", encoding="utf-8") as fh:
                fh.write(tok)
            try:
                p = subprocess.run([GH, "auth", "login", "--hostname", "github.com",
                                    "--git-protocol", "https", "--with-token"],
                                   input=tok, text=True, capture_output=True, timeout=60,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                print("gh 配置写入:", "成功" if p.returncode == 0 else p.stderr.strip()[:120])
            except Exception as exc:
                print("gh 配置写入失败:", exc)
            print("AUTH_OK")
            print("账号:", me.get("login"))
            print("token 已保存到", TOKEN_OUT)
            return 0
        if err == "authorization_pending":
            if last != err:
                print("等待你在网页上点 Authorize ...", flush=True)
                last = err
        elif err == "slow_down":
            interval = int(r.get("interval", interval + 5))
        elif err in ("expired_token", "access_denied"):
            print("授权失败:", err, r.get("error_description", ""))
            return 2
        else:
            print("未知返回:", json.dumps(r, ensure_ascii=False)[:200])
            return 2
        time.sleep(interval)
    print("等待超时，未完成授权")
    return 3


if __name__ == "__main__":
    sys.exit(main())
