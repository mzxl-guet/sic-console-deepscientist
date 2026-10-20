# -*- coding: utf-8 -*-
"""重写 start.cmd：守护进程在前台运行，窗口开着服务就活着。"""
import io

START = r"""@echo off
title DeepScientist 服务（关闭本窗口即停止服务）
setlocal
set "PATH=D:\DeepScientist\node;D:\DeepScientist\npm-global;%SystemRoot%\system32;%SystemRoot%;%SystemRoot%\System32\Wbem"
set "CONDA_PREFIX=D:\conda"
set "UV_CACHE_DIR=D:\DeepScientist\cache\uv"
set "DEEPSCIENTIST_HOME=D:\DeepScientist\home"
set "NODE_OPTIONS="
set "PYEXE=D:\DeepScientist\home\runtime\python-env\Scripts\python.exe"
cd /d "D:\DeepScientist\npm-global\node_modules\@researai\deepscientist"

curl -s -f -o NUL -m 2 http://127.0.0.1:20999/ >NUL 2>&1
if not errorlevel 1 goto ALREADY

echo.
echo   ==========================================================
echo    DeepScientist 正在启动...
echo.
echo    启动完成后浏览器会自动打开 http://127.0.0.1:20999
echo    这个黑窗口就是服务本体，用的时候请留着别关。
echo    要停止服务：直接关掉这个窗口，或双击「DeepScientist 停止」。
echo   ==========================================================
echo.

start "" /b cmd /c "ping -n 12 127.0.0.1 >NUL & start "" http://127.0.0.1:20999"

"%PYEXE%" -m deepscientist.cli --home "D:\DeepScientist\home" daemon --host 127.0.0.1 --port 20999 --auth false

echo.
echo   服务已退出。按任意键关闭窗口。
pause >NUL
exit /b 0

:ALREADY
echo.
echo   服务已经在运行： http://127.0.0.1:20999
echo   浏览器马上打开。这个窗口可以关掉。
echo.
start "" http://127.0.0.1:20999
ping -n 4 127.0.0.1 >NUL
exit /b 0
"""

io.open(r"D:\DeepScientist\start.cmd", "w", encoding="gbk", newline="\r\n").write(START)
print("start.cmd 已重写（前台模式，GBK）")
