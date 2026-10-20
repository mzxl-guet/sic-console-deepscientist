@echo off
title DeepScientist Í£Ö¹
setlocal
echo.
echo   ÕýÔÚÍ£Ö¹ DeepScientist ...

for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":20999" ^| findstr "LISTENING"') do (
    taskkill /PID %%P /F >NUL 2>&1
)

echo   ÒÑÍ£Ö¹¡£
echo.
timeout /t 3 >NUL
exit /b 0
