@echo off
title 推送到 GitHub
setlocal
set "GH=D:/DeepScientist/tools/gh/bin/gh.exe"
set "REPO=D:/DeepScientist/sic-console-repo"
set "NAME=sic-console-deepscientist"

echo.
echo   [1/3] 检查 GitHub 登录状态...
"%GH%" auth status >nul 2>&1
if errorlevel 1 (
  echo   未登录，正在打开浏览器登录，请按提示输入一次性代码...
  "%GH%" auth login --hostname github.com --git-protocol https --web
)

echo.
echo   [2/3] 创建仓库并推送...
cd /d "%REPO%"
"%GH%" repo create %NAME% --private --source . --remote origin --push
if errorlevel 1 (
  echo   创建失败，尝试直接推送到已有仓库...
  git push -u origin main
)

echo.
echo   [3/3] 完成。仓库地址：https://github.com/你的用户名/%NAME%
echo.
pause
