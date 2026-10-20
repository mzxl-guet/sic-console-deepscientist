@echo off
title DeepScientist 启动中
setlocal
rem 固定运行环境：避免受系统里多个 Python 影响
set "PATH=D:\DeepScientist\node;D:\DeepScientist\npm-global;%SystemRoot%\system32;%SystemRoot%;%SystemRoot%\System32\Wbem"
set "CONDA_PREFIX=D:\conda"
set "UV_CACHE_DIR=D:\DeepScientist\cache\uv"
set "DEEPSCIENTIST_HOME=D:\DeepScientist\home"
cd /d D:\DeepScientist\workspace

echo.
echo   DeepScientist 正在启动，请稍等（第一次可能要几分钟）...
echo.

ds --home "D:\DeepScientist\home"

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
echo    启动成功，网页地址： http://127.0.0.1:20999
echo    浏览器已经自动打开；如果没有弹出，请手动输入上面的网址。
echo.
echo    要停止服务：双击桌面上的「DeepScientist 停止」
echo    这个黑窗口 10 秒后自动关闭，关掉不影响后台运行。
echo   ==========================================================
echo.
timeout /t 10 >NUL
exit /b 0

:FAILED
echo.
echo   ==========================================================
echo    启动失败：等了 2 分钟，网页端口 20999 一直没有响应。
echo.
echo    请把这个日志文件发给帮你安装的人：
echo      D:\DeepScientist\home\logs\daemon.log
echo   ==========================================================
echo.
pause
exit /b 1
