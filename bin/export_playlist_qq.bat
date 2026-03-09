@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
cd /d "%~dp0"

for %%I in ("%~dp0..") do set "ROOT=%%~fI\"
for %%I in ("%~dp0..") do set "OUTDIR_NOTRAIL=%%~fI"
set "LINKFILE=%ROOT%playlist_link_qq.txt"

if not exist "%LINKFILE%" (
echo Creating playlist_link_qq.txt in parent folder...
(
echo # Paste QQ Music playlist URL below, save and run this bat again
echo # Example: https://y.qq.com/n/ryqq_v2/playlist/1451828014
) > "%LINKFILE%"
start notepad "%LINKFILE%"
echo.
echo Paste your QQ playlist link in the file, save, then run this bat again.
pause
exit /b 0
)

echo QQ Music export.
set QQ_API_BASE=http://127.0.0.1:3300
python "%~dp0qq_playlist_scraper.py" "%LINKFILE%" -t "%OUTDIR_NOTRAIL%"

echo.
if exist "%ROOT%last_export_path.txt" (
set /p CSVPATH=<"%ROOT%last_export_path.txt"
del "%ROOT%last_export_path.txt" 2>nul
if exist "!CSVPATH!" (
echo Exported: !CSVPATH!
start "" "!CSVPATH!"
) else (
echo CSV not found.
)
) else (
echo No CSV. Run "Start QQ Music API.bat" first, or check playlist_link_qq.txt has valid URL.
)
echo.
pause
