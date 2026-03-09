@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title QQ Music API - Port 3300

cd /d "%~dp0"
set "QQDIR=%~dp0bin\QQMusicApi"

echo ========================================
echo   QQ Music API (Port 3300)
echo ========================================
echo.

if not exist "!QQDIR!" (
    echo [1/3] Cloning QQMusicApi...
    git clone --depth 1 https://github.com/jsososo/QQMusicApi.git "!QQDIR!"
    if errorlevel 1 (
        echo.
        echo Clone failed. Install Git and check network, then run again.
        echo Git: https://git-scm.com/
        echo.
        pause
        exit /b 1
    )
    echo Done.
    echo.
)

if not exist "!QQDIR!\package.json" (
    if exist "!QQDIR!" (
        echo Incomplete folder, re-cloning...
        rd /s /q "!QQDIR!" 2>nul
    )
    echo [1/3] Cloning QQMusicApi...
    git clone --depth 1 https://github.com/jsososo/QQMusicApi.git "!QQDIR!"
    if errorlevel 1 (
        echo Clone failed.
        pause
        exit /b 1
    )
    echo.
)

if not exist "!QQDIR!\node_modules" (
    echo [2/3] Dependencies not installed. Please run manually:
    echo.
    echo   1. Open CMD or PowerShell
    echo   2. cd "!QQDIR!"
    echo   3. npm install
    echo   4. Then run this bat again
    echo.
    echo Or: open QQMusicApi folder, type cmd in address bar, run npm install
    echo.
    start "" "!QQDIR!"
    echo Opened QQMusicApi folder.
    echo.
    pause
    exit /b 0
)

echo [3/3] Starting QQ Music API on port 3300...
echo.
echo When you see "Listening" or "running", run "Export playlist" bat to export.
echo Close this window to stop the server.
echo ----------------------------------------
cd /d "!QQDIR!"
npm start
if errorlevel 1 (
    echo.
    echo Trying node app.js ...
    node app.js
)

echo.
echo Server stopped. Press any key to close...
pause >nul
