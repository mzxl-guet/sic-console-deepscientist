# -*- coding: utf-8 -*-
import io

BS = chr(92)
OLD_START = 'ds --home "D:' + BS + 'DeepScientist' + BS + 'home"'
OLD_STOP = OLD_START + " --stop"


def fix(path, pairs):
    raw = io.open(path, encoding="gbk").read()
    lines = raw.splitlines()
    changed = 0
    out = []
    for ln in lines:
        cur = ln
        for old, new in pairs:
            if cur.strip() == old:
                cur = new
                changed += 1
        out.append(cur)
    io.open(path, "w", encoding="gbk", newline="\r\n").write("\n".join(out) + "\n")
    print("%-30s 替换 %d 行" % (path, changed))


fix(r"D:\DeepScientist\start.cmd", [(OLD_START, "ds")])
fix(r"D:\DeepScientist\stop.cmd", [(OLD_STOP, "ds --stop")])

for f in ("start.cmd", "stop.cmd"):
    s = io.open(r"D:\DeepScientist" + BS + f, encoding="gbk").read()
    hits = [l.strip() for l in s.splitlines() if l.strip().startswith("ds")]
    print(f, "->", hits)
