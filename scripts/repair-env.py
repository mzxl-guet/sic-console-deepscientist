#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""DeepScientist 原生 Windows 环境修复工具（幂等，可重复运行）。

解决两个都会伪装成 `[WinError 2] 系统找不到指定的文件。` 的问题：

  1) 服务进程 PATH 里没有 git        -> 任务快照阶段失败
  2) runners.yaml 的 binary 是裸名   -> 拉起 runner 阶段失败

用法：
    python scripts/repair-env.py                # 自动探测并修复
    python scripts/repair-env.py --dry-run      # 只报告，不改文件
    python scripts/repair-env.py --start-cmd "D:\\DeepScientist\\start.cmd"

文件为 GBK + CRLF，按原编码写回，避免中文乱码。
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

GIT_CANDIDATES = [
    r"C:\Program Files\Git\cmd",
    r"C:\Program Files\Git\mingw64\bin",
    r"C:\Program Files (x86)\Git\cmd",
    r"D:\aiagent\WorkBuddy\resources\vendor\PortableGit\mingw64\bin",
    r"D:\aiagent\WorkBuddy\resources\vendor\PortableGit\cmd",
]

CODEX_CANDIDATES = [
    Path(os.environ.get("APPDATA", "")) / "npm" / "codex.CMD",
    Path(os.environ.get("APPDATA", "")) / "npm" / "codex.cmd",
]


def find_git_dirs() -> list[str]:
    """返回所有存在的 Git 目录（用于拼 PATH）。"""
    dirs = [d for d in GIT_CANDIDATES if Path(d).is_dir()]
    # 系统 PATH 里如果已经有 git，也把它所在目录带上
    found = shutil.which("git")
    if found:
        parent = str(Path(found).parent)
        if parent not in dirs:
            dirs.insert(0, parent)
    return dirs


def find_codex() -> Path | None:
    for p in CODEX_CANDIDATES:
        if p.is_file():
            return p
    found = shutil.which("codex")
    if found:
        return Path(found)
    return None


def verify(exe: str) -> str:
    """验证某个命令能否真的被 subprocess 调用起来。"""
    try:
        r = subprocess.run([exe, "--version"], capture_output=True, timeout=25, text=True)
        return (r.stdout or r.stderr).strip().splitlines()[0][:60]
    except Exception as exc:  # noqa: BLE001
        return f"FAIL: {type(exc).__name__}: {exc}"


def patch_start_cmd(path: Path, git_dirs: list[str], codex: Path | None, dry: bool) -> None:
    if not path.is_file():
        print(f"  [跳过] 找不到 {path}")
        return
    raw = path.read_bytes()
    text = raw.decode("gbk", errors="replace")
    original = text

    # 1) 补 git 与 npm 目录
    if "%APPDATA%\\npm" not in text:
        for line in text.split("\r\n"):
            if line.startswith('set "PATH=') and "%SystemRoot%" in line:
                head = line[len('set "PATH='):-1]
                extra = "%APPDATA%\\npm;%USERPROFILE%\\AppData\\Roaming\\npm;"
                extra += "".join(d + ";" for d in git_dirs)
                text = text.replace(line, 'set "PATH=' + extra + head + '"', 1)
                print("  [改] PATH 已补 %APPDATA%\\npm 与 git 目录")
                break

    # 2) 显式指定 codex 绝对路径
    if codex and "DEEPSCIENTIST_CODEX_BINARY" not in text:
        anchor = 'set "NODE_OPTIONS="'
        if anchor in text:
            text = text.replace(
                anchor,
                anchor + '\r\nset "DEEPSCIENTIST_CODEX_BINARY=' + str(codex) + '"',
                1,
            )
            print("  [改] 已插入 DEEPSCIENTIST_CODEX_BINARY")

    text = text.replace("\r\n", "\n").replace("\n", "\r\n")

    if text == original:
        print("  [OK] 无需修改")
        return
    if dry:
        print("  [dry-run] 将修改，未写入")
        return
    path.with_suffix(path.suffix + ".bak").write_bytes(raw)
    path.write_bytes(text.encode("gbk"))
    print(f"  [写] {path}（备份 {path.name}.bak）")


def patch_runners_yaml(path: Path, codex: Path | None, dry: bool) -> None:
    if not path.is_file():
        print(f"  [跳过] 找不到 {path}")
        return
    if not codex:
        print("  [跳过] 没找到 codex，无法写绝对路径")
        return
    text = path.read_text(encoding="utf-8")
    if str(codex).replace("\\", "/") in text:
        print("  [OK] binary 已是绝对路径")
        return
    out = []
    changed = False
    for line in text.splitlines():
        if line.strip().startswith("binary:") and "codex" in line and not changed:
            indent = line[: len(line) - len(line.lstrip())]
            out.append(f"{indent}binary: {str(codex).replace(chr(92), '/')}")
            changed = True
        else:
            out.append(line)
    if not changed:
        print("  [警告] 没找到 binary 行")
        return
    if dry:
        print("  [dry-run] 将修改 runners.yaml，未写入")
        return
    path.with_suffix(".yaml.bak").write_text(text, encoding="utf-8")
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"  [写] {path}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--home", default=r"D:\DeepScientist\home")
    ap.add_argument("--start-cmd", default=r"D:\DeepScientist\start.cmd")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    home = Path(args.home)
    git_dirs = find_git_dirs()
    codex = find_codex()

    print("=== 探测结果 ===")
    print("git 目录:", git_dirs or "未找到")
    print("codex   :", codex or "未找到")

    print("\n=== 修复 start.cmd ===")
    patch_start_cmd(Path(args.start_cmd), git_dirs, codex, args.dry_run)

    print("\n=== 修复 runners.yaml ===")
    patch_runners_yaml(home / "config" / "runners.yaml", codex, args.dry_run)

    print("\n=== 验证（用 subprocess 真实调用）===")
    for exe in ("git", "codex"):
        loc = shutil.which(exe)
        print(f"{exe:6s} which={loc}")
        if loc:
            print(f"       -> {verify(loc)}")
        elif codex and exe == "codex":
            print(f"       -> 绝对路径 {codex}: {verify(str(codex))}")

    print("\n提示：codex 必须用绝对路径调用；裸名在任何 PATH 下都会 WinError 2。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
