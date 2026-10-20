#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
只走 api.github.com 的仓库上传器（不需要 git，不需要能访问 github.com 主站）。

用法：
    python gh_push_api.py --token ghp_xxx --repo sic-console-deepscientist
    python gh_push_api.py --token ghp_xxx --repo xxx --private 0     # 建公开仓库
    python gh_push_api.py --token ghp_xxx --repo xxx --dry-run       # 只列出要传的文件

原理：
  1) GET  /user                                  确认 token 是谁的
  2) POST /user/repos                            建仓库（已存在则复用）
  3) POST /repos/{o}/{r}/git/blobs               每个文件转成 blob
  4) POST /repos/{o}/{r}/git/trees               一次提交整棵目录树
  5) POST /repos/{o}/{r}/git/commits             生成 commit
  6) POST /repos/{o}/{r}/git/refs                把 main 指过去

依赖：只用 Python 标准库。
"""
import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.github.com"
SKIP_DIRS = {".git", "__pycache__", "_edgeprofile", ".pytest_cache", "node_modules"}
SKIP_SUFFIX = (".pyc", ".pyo", ".bak", ".zip", ".tmp")


def make_opener():
    """强制直连，绕开 https_proxy —— api.github.com 直连是通的。"""
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))


OPENER = make_opener()


def call(method, path, token, payload=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(API + path, data=data, method=method)
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "sic-console-uploader")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with OPENER.open(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, (json.loads(raw) if raw.strip() else {})
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            body = json.loads(raw)
        except Exception:
            body = {"message": raw[:300]}
        return exc.code, body
    except Exception as exc:  # 网络层
        return 0, {"message": "%s: %s" % (type(exc).__name__, exc)}


def collect(root):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if name.endswith(SKIP_SUFFIX):
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            out.append((rel, full))
    out.sort(key=lambda x: x[0])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", default="")
    ap.add_argument("--token-file", default="", help="从文本文件读取 token（避免在聊天里粘贴）")
    ap.add_argument("--repo", default="sic-console-deepscientist")
    ap.add_argument("--source", default=r"D:\DeepScientist\sic-console-repo")
    ap.add_argument("--private", default="1", help="1=私有，0=公开")
    ap.add_argument("--desc", default="信通智研台：DeepScientist 前端改造、采样定理实验与可行性验证")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.token_file:
        with open(args.token_file, "r", encoding="utf-8-sig") as fh:
            args.token = fh.read().strip()
    if not args.token:
        print("[错误] 没有拿到 token。用 --token 或 --token-file 提供。")
        return 2

    files = collect(args.source)
    total = sum(os.path.getsize(f) for _, f in files)
    print("[1/5] 待上传 %d 个文件，共 %.1f MB" % (len(files), total / 1048576.0))

    if args.dry_run:
        for rel, full in files:
            print("   %8.1f KB  %s" % (os.path.getsize(full) / 1024.0, rel))
        return 0

    st, me = call("GET", "/user", args.token)
    if st != 200:
        print("[错误] token 校验失败（HTTP %s）：%s" % (st, me.get("message")))
        print("       常见原因：token 复制不全、已过期、或没勾选 repo 权限。")
        return 2
    owner = me["login"]
    print("[2/5] token 属于：%s" % owner)

    is_private = str(args.private).lower() not in ("0", "false", "no")
    st, repo = call("POST", "/user/repos", args.token, {
        "name": args.repo,
        "description": args.desc,
        "private": is_private,
        "auto_init": False,
        "has_issues": True,
    })
    if st == 201:
        print("[3/5] 仓库已创建：%s" % repo["html_url"])
    elif st == 422:
        st2, repo = call("GET", "/repos/%s/%s" % (owner, args.repo), args.token)
        if st2 != 200:
            print("[错误] 仓库已存在但读不到（HTTP %s）：%s" % (st2, repo.get("message")))
            return 2
        print("[3/5] 仓库已存在，复用：%s" % repo["html_url"])
    else:
        print("[错误] 建仓库失败（HTTP %s）：%s" % (st, repo.get("message")))
        return 2

    tree = []
    # 空仓库不能直接创建 blob，先放一个初始提交
    st_ref, _ref = call("GET", "/repos/%s/%s/git/ref/heads/main" % (owner, args.repo), args.token)
    if st_ref != 200:
        st_b, boot = call("PUT", "/repos/%s/%s/contents/README.md" % (owner, args.repo),
                          args.token, {
                              "message": "chore: 初始化仓库",
                              "content": base64.b64encode("# 信通智研台\n".encode("utf-8")).decode("ascii"),
                          })
        if st_b in (200, 201):
            print("       （已为空仓库创建初始提交）")
        else:
            print("[警告] 初始化空仓库失败（HTTP %s）：%s" % (st_b, boot.get("message")))

    for i, (rel, full) in enumerate(files, 1):
        with open(full, "rb") as fh:
            content = base64.b64encode(fh.read()).decode("ascii")
        st, blob = call("POST", "/repos/%s/%s/git/blobs" % (owner, args.repo),
                        args.token, {"content": content, "encoding": "base64"})
        if st != 201:
            print("[错误] 上传 %s 失败（HTTP %s）：%s" % (rel, st, blob.get("message")))
            return 2
        tree.append({"path": rel, "mode": "100644", "type": "blob", "sha": blob["sha"]})
        print("   (%d/%d) %s" % (i, len(files), rel))

    print("[4/5] 生成目录树与提交 ...")
    st, tr = call("POST", "/repos/%s/%s/git/trees" % (owner, args.repo),
                  args.token, {"tree": tree})
    if st != 201:
        print("[错误] 建树失败（HTTP %s）：%s" % (st, tr.get("message")))
        return 2

    st, parents = call("GET", "/repos/%s/%s/git/ref/heads/main" % (owner, args.repo), args.token)
    parent_list = [parents["object"]["sha"]] if st == 200 else []

    st, cm = call("POST", "/repos/%s/%s/git/commits" % (owner, args.repo), args.token, {
        "message": "信通智研台：DeepScientist 前端改造 + 采样定理实验 + 可行性验证",
        "tree": tr["sha"],
        "parents": parent_list,
    })
    if st != 201:
        print("[错误] 建提交失败（HTTP %s）：%s" % (st, cm.get("message")))
        return 2

    if parent_list:
        st, _ = call("PATCH", "/repos/%s/%s/git/refs/heads/main" % (owner, args.repo),
                     args.token, {"sha": cm["sha"], "force": False})
        ok = st == 200
    else:
        st, _ = call("POST", "/repos/%s/%s/git/refs" % (owner, args.repo),
                     args.token, {"ref": "refs/heads/main", "sha": cm["sha"]})
        ok = st == 201
    if not ok:
        print("[错误] 更新 main 分支失败（HTTP %s）" % st)
        return 2

    print("[5/5] 完成")
    print("仓库地址：%s" % repo["html_url"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
