# -*- coding: utf-8 -*-
"""修复 codex MCP 配置里 Windows 路径未转义导致 TOML 解析失败的问题。

原始代码：f'command = "{sys.executable}"'
修复后：  f'command = {json.dumps(str(sys.executable))}'
"""
import io
import os

TARGETS = [
    r"D:\DeepScientist\home\runtime\python-env\Lib\site-packages\deepscientist\runners\codex.py",
    r"D:\DeepScientist\npm-global\node_modules\@researai\deepscientist\src\deepscientist\runners\codex.py",
]

OLD = """            f'command = "{sys.executable}"',"""
NEW = """            f'command = {json.dumps(str(sys.executable))}',"""

for path in TARGETS:
    if not os.path.exists(path):
        print("跳过（不存在）:", path)
        continue
    src = io.open(path, encoding="utf-8").read()
    if NEW in src:
        print("已修复过:", path)
        continue
    if OLD not in src:
        print("未找到目标行:", path)
        continue
    io.open(path, "w", encoding="utf-8", newline="\n").write(src.replace(OLD, NEW, 1))
    print("已修复:", path)
