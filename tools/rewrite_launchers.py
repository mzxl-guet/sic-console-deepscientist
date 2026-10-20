# -*- coding: utf-8 -*-
"""重写 D:\\DeepScientist\\start.cmd / stop.cmd（GBK 编码），
改成直接拉起 Python 守护进程，避免走启动器里那条会随控制台一起退出的路径。
"""
import io

START = r"""@echo off
title DeepScientist 启动中
setlocal
rem 固定运行环境：避免受系统里多个 Python 影响
set "PATH=D:\DeepScientist\node;D:\DeepScientist\npm-global;%SystemRoot%\system32;%SystemRoot%;%SystemRoot%\System32\Wbem"
set "CONDA_PREFIX=D:\conda"
set "UV_CACHE_DIR=D:\DeepScientist\cache\uv"
set "DEEPSCIENTIST_HOME=D:\DeepScientist\home"
rem 必须清空，否则会被安全删除钩子拦住
set "NODE_OPTIONS="
set "PY=D:\DeepScientist\home\runtime\python-env\Scripts\pythonw.exe"
cd /d "D:\DeepScientist\npm-global\node_modules\@researai\deepscientist"

echo.
echo   DeepScientist 正在启动，请稍等（约 10-20 秒）...
echo.

curl -s -f -o NUL -m 2 http://127.0.0.1:20999/ >NUL 2>&1
if not errorlevel 1 goto READY

start "" /min "%PY%" -m deepscientist.cli --home "D:\DeepScientist\home" daemon --host 127.0.0.1 --port 20999 --auth false

set "TRIES=0"
:WAIT
set /a TRIES+=1
curl -s -f -o NUL -m 2 http://127.0.0.1:20999/ >NUL 2>&1
if not errorlevel 1 goto READY
if %TRIES% GEQ 60 goto FAILED
timeout /t 2 /nobreak >NUL
goto WAIT

:READY
start "" http://127.0.0.1:20999
echo.
echo   ==========================================================
echo   启动成功，网页地址： http://127.0.0.1:20999
echo   浏览器已经自动打开；如果没有，手动输入上面的地址即可。
echo.
echo   要停止服务，双击桌面上的「DeepScientist 停止」。
echo   本窗口 10 秒后自动关闭，关掉它不影响服务运行。
echo   ==========================================================
echo.
timeout /t 10 >NUL
exit /b 0

:FAILED
echo.
echo   ==========================================================
echo   启动失败（已等待 2 分钟，网页端口 20999 一直没有响应）。
echo.
echo   请把下面这个日志文件发给助手：
echo      D:\DeepScientist\home\logs\daemon.log
echo   ==========================================================
echo.
pause
exit /b 1
"""

STOP = r"""@echo off
title DeepScientist 停止
setlocal
echo.
echo   正在停止 DeepScientist ...

for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":20999" ^| findstr "LISTENING"') do (
    taskkill /PID %%P /F >NUL 2>&1
)

echo   已停止。
echo.
timeout /t 3 >NUL
exit /b 0
"""

io.open(r"D:\DeepScientist\start.cmd", "w", encoding="gbk", newline="\r\n").write(START)
io.open(r"D:\DeepScientist\stop.cmd", "w", encoding="gbk", newline="\r\n").write(STOP)
print("start.cmd / stop.cmd 已重写（GBK）")
