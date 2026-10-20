#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""以 stdio 方式唤醒 deepscientist 的 MCP 服务，列出它暴露的工具。"""
import json
import os
import subprocess
import sys
import threading
import time

PY = r"D:\DeepScientist\home\runtime\python-env\Scripts\python.exe"
CWD = r"D:\DeepScientist\home\quests\001"


def probe(namespace):
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    env.pop("NODE_OPTIONS", None)
    env["QUEST_ROOT"] = CWD
    env["DEEPSCIENTIST_HOME"] = r"D:\DeepScientist\home"
    proc = subprocess.Popen(
        [PY, "-m", "deepscientist.mcp.server", "--namespace", namespace],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        cwd=CWD, env=env, text=True, encoding="utf-8", errors="replace",
    )

    out_lines = []
    err_lines = []

    def reader(stream, bucket):
        for line in stream:
            bucket.append(line.rstrip())

    threading.Thread(target=reader, args=(proc.stdout, out_lines), daemon=True).start()
    threading.Thread(target=reader, args=(proc.stderr, err_lines), daemon=True).start()

    def send(obj):
        proc.stdin.write(json.dumps(obj) + "\n")
        proc.stdin.flush()

    send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
          "params": {"protocolVersion": "2024-11-05",
                     "capabilities": {},
                     "clientInfo": {"name": "probe", "version": "1.0"}}})
    time.sleep(1.5)
    send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
    send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    time.sleep(3.0)

    try:
        proc.terminate()
    except Exception:
        pass

    tools = []
    for line in out_lines:
        try:
            msg = json.loads(line)
        except Exception:
            continue
        if msg.get("id") == 2:
            for t in (msg.get("result") or {}).get("tools", []):
                tools.append(t.get("name"))
    print("=== 命名空间 %s ===" % namespace)
    print("返回工具:", tools if tools else "（无）")
    if not tools:
        bad = [l for l in out_lines if "error" in l.lower()][:3]
        print("输出片段:", out_lines[:3])
        print("错误片段:", (err_lines[:6] or bad))
    else:
        print("备注:", [t for t in tools][:10])
    return tools


if __name__ == "__main__":
    for ns in sys.argv[1:] or ["bash_exec", "memory", "artifact"]:
        probe(ns)
        print()
