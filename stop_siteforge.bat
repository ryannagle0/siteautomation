@echo off
setlocal enabledelayedexpansion
set FOUND=0
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":5000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%p >nul 2>&1
    set FOUND=1
)
if "!FOUND!"=="1" (
    echo SiteForge stopped.
) else (
    echo SiteForge was not running.
)
pause
