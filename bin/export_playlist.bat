@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
cd /d "%~dp0"

set "OUTDIR=%~dp0"
set "OUTDIR_NOTRAIL=%OUTDIR:~0,-1%"
set "LINKFILE=%OUTDIR%playlist_link.txt"

if not exist "%LINKFILE%" (
echo Creating playlist_link.txt ...
(
echo # Paste NetEase or QQ Music playlist URL below
echo # NetEase: https://music.163.com/#/playlist?id=931794508
echo # QQ: https://y.qq.com/n/yqq/playlist/7177076625.html
echo # Save and run this bat again to export CSV
) > "%LINKFILE%"
start notepad "%LINKFILE%"
echo.
echo Paste your link in the file, save, then run this bat again.
pause
exit /b 0
)

findstr /i "y.qq.com" "%LINKFILE%" >nul
if errorlevel 1 goto netease

echo QQ Music detected.
set QQ_API_BASE=http://127.0.0.1:3300
python "%~dp0qq_playlist_scraper.py" "%LINKFILE%" -t "%OUTDIR_NOTRAIL%"
goto done

:netease
echo NetEase detected.
set NETEASE_API_BASE=http://127.0.0.1:3000
python "%~dp0netease_playlist_scraper.py" "%LINKFILE%" -t "%OUTDIR_NOTRAIL%"

:done
echo.
if exist "%OUTDIR%last_export_path.txt" (
set /p CSVPATH=<"%OUTDIR%last_export_path.txt"
del "%OUTDIR%last_export_path.txt" 2>nul
if exist "!CSVPATH!" (
echo Exported: !CSVPATH!
start "" "!CSVPATH!"
) else (
echo CSV not found.
)
) else (
echo No CSV. Run API bat first, or check playlist_link.txt has valid URL.
)
echo.
pause
