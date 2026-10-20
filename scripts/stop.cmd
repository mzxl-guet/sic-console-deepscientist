@echo off
title DeepScientist 停止
setlocal
set "PATH=D:\DeepScientist\node;D:\DeepScientist\npm-global;%SystemRoot%\system32;%SystemRoot%;%SystemRoot%\System32\Wbem"
set "CONDA_PREFIX=D:\conda"
set "UV_CACHE_DIR=D:\DeepScientist\cache\uv"
set "DEEPSCIENTIST_HOME=D:\DeepScientist\home"
cd /d D:\DeepScientist\workspace

echo.
echo   正在停止 DeepScientist ...
echo.

ds --home "D:\DeepScientist\home" --stop

echo.
echo   已停止，窗口 6 秒后自动关闭。
echo.
timeout /t 6 >NUL
exit /b 0
