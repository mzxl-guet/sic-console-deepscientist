# -*- coding: utf-8 -*-
"""一键还原：把 DeepScientist 前端恢复成官方原版"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BACKUP = os.path.join(HERE, "_backup")
DEFAULT_DIST = os.path.join(
    "D:", os.sep, "DeepScientist", "npm-global", "node_modules",
    "@researai", "deepscientist", "src", "ui", "dist",
)


def find_dist():
    env = os.environ.get("SIC_DIST")
    if env and os.path.isdir(env):
        return env
    if os.path.isdir(DEFAULT_DIST):
        return DEFAULT_DIST
    sys.exit("找不到前端目录，请设置环境变量 SIC_DIST")


def main():
    dist = find_dist()
    if not os.path.isdir(BACKUP):
        sys.exit("没有找到备份目录，无法还原：%s" % BACKUP)

    n = 0
    for base, _dirs, files in os.walk(BACKUP):
        for f in files:
            src = os.path.join(base, f)
            rel = os.path.relpath(src, BACKUP)
            dst = os.path.join(dist, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            n += 1

    brand_dir = os.path.join(dist, "brand")
    if os.path.isdir(brand_dir):
        shutil.rmtree(brand_dir)

    print("已还原 %d 个文件，并移除了 dist/brand/。请 Ctrl+F5 强制刷新。" % n)


if __name__ == "__main__":
    main()
