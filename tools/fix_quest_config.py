# -*- coding: utf-8 -*-
"""把 codex config.toml 里 command/args 行的 Windows 路径转义成合法 TOML。"""
import io
import re
import shutil
import sys

path = sys.argv[1] if len(sys.argv) > 1 else r"D:\DeepScientist\home\quests\002\.ds\codex-home\config.toml"
shutil.copy2(path, path + ".bak-manual")

src = io.open(path, encoding="utf-8").read()
out, fixed = [], 0
for line in src.splitlines():
    m = re.match(r'^(\s*(?:command|args)\s*=\s*)(.*)$', line)
    if m and "\\" in m.group(2):
        body = m.group(2)
        # 只把「单个反斜杠」变成「双反斜杠」，已转义的不动
        body_fixed = re.sub(r'(?<!\\)\\(?!\\)', r'\\\\', body)
        if body_fixed != body:
            fixed += 1
            line = m.group(1) + body_fixed
    out.append(line)

io.open(path, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
print("已转义 %d 行 -> %s" % (fixed, path))
for line in out:
    if line.strip().startswith("command"):
        print("   ", line.strip())
