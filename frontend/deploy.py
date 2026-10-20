# -*- coding: utf-8 -*-
"""
把「信通智研台」皮肤部署到 DeepScientist 前端目录。

特点：
  * 首次运行会把原始文件备份到 my-ui/_backup/，之后重复运行不会污染备份
  * index.html 始终基于备份重新生成，所以可以反复部署
  * 只替换图片/样式/文案，不改任何 js 业务代码

用法：  python deploy.py
还原：  python restore.py
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
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
    # 退化方案：在 D:\DeepScientist 下按特征搜索
    root = os.path.join("D:" + os.sep, "DeepScientist", "npm-global")
    for base, dirs, files in os.walk(root):
        if base.replace("\\", "/").endswith("src/ui/dist") and "index.html" in files:
            return base
    sys.exit("找不到前端目录，请设置环境变量 SIC_DIST 指向 .../src/ui/dist")


def backup(dist, rel):
    """把原始文件备份一次（已备份过就跳过）"""
    src = os.path.join(dist, rel)
    dst = os.path.join(BACKUP, rel)
    if os.path.exists(dst) or not os.path.exists(src):
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)


IMAGE_MAP = {
    "logo.svg": "logo.svg",
    "logo.png": "logo.png",
    "logo-inverted.svg": "logo-inverted.svg",
    "logo-inverted.png": "logo-inverted.png",
    "logo-small.png": "logo-small.png",
    "logo-small-inverted.png": "logo-small-inverted.png",
    "hero/mountain.png": "hero-signal.png",
    "hero/watercolor.png": "fog-cool.png",
    "hero/subtle_watercolor.png": "fog-cool.png",
    "hero/seal.png": "seal-sic.png",
}

PAGE_TITLE = "信通智研台 · 桂电信息与通信学院"
PAGE_DESC = ("信通智研台 —— 桂林电子科技大学信息与通信学院 · "
             "电子信息方向的本地智能科研工作台")

BRAND_CSS = '<link rel="stylesheet" href="/ui/brand/brand.css" data-sic="1" />'
BRAND_JS = '<script src="/ui/brand/brand.js" data-sic="1" defer></script>'


def build_index(original_html):
    import re
    html = original_html

    # 标题
    html = re.sub(r"<title>.*?</title>",
                  "<title>%s</title>" % PAGE_TITLE, html, flags=re.S)

    # 描述
    html = re.sub(
        r'<meta\s+name="description"\s+content=".*?"\s*/>',
        '<meta name="description" content="%s" />' % PAGE_DESC,
        html, flags=re.S,
    )

    # 站点图标
    html = html.replace('/ui/logo-small.png', '/ui/brand/favicon-200.png')

    # 皮肤资源：插到 </head> 之前，保证优先级最高
    inject = "    " + BRAND_CSS + "\n    " + BRAND_JS + "\n  "
    html = html.replace("</head>", inject + "</head>", 1)
    return html


def main():
    dist = find_dist()
    print("前端目录:", dist)
    os.makedirs(BACKUP, exist_ok=True)

    # 1) 备份原始文件
    for rel in IMAGE_MAP:
        backup(dist, rel)
    backup(dist, "index.html")
    print("原始文件已备份到:", BACKUP)

    # 2) 部署皮肤资源
    brand_dir = os.path.join(dist, "brand")
    os.makedirs(brand_dir, exist_ok=True)
    for name in ("brand.css", "brand.js"):
        shutil.copy2(os.path.join(HERE, name), os.path.join(brand_dir, name))
    for f in ("favicon-200.png", "favicon-512.png"):
        shutil.copy2(os.path.join(ASSETS, f), os.path.join(brand_dir, f))
    print("皮肤资源 -> dist/brand/")

    # 3) 替换图片
    for rel, asset in IMAGE_MAP.items():
        src = os.path.join(ASSETS, asset)
        dst = os.path.join(dist, rel)
        if not os.path.exists(src):
            print("  ! 缺少素材:", asset)
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
    print("图片替换完成:", ", ".join(IMAGE_MAP))

    # 4) 重建 index.html（始终基于备份）
    base = os.path.join(BACKUP, "index.html")
    with open(base, "r", encoding="utf-8") as f:
        original = f.read()
    with open(os.path.join(dist, "index.html"), "w", encoding="utf-8") as f:
        f.write(build_index(original))
    print("index.html 已注入品牌资源")

    print("\n完成。刷新浏览器（Ctrl+F5 强制刷新）即可看到新界面。")
    print("如需还原：python restore.py")


if __name__ == "__main__":
    main()
