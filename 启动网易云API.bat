@echo off
chcp 65001 >nul
title NetEase API - Port 3000

echo Starting NetEase local API...
echo.
echo When you see "server running @ http://localhost:3000" then it is ready.
echo To export playlist, run export_playlist.bat
echo Close this window to stop the API.
echo.
npx NeteaseCloudMusicApi@latest

pause
