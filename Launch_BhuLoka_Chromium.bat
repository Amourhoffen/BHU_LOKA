@echo off
title BHU LOKA (भूलोक) - Chromium Sovereign Launcher
setlocal
set ROOT=%~dp0
set TARGET_HTML=%ROOT%bhu_loka_cyber_dashboard.html

if exist "%ROOT%BhuLoka_Chromium_App\node_modules\.bin\electron.cmd" (
    echo Launching BHU LOKA via Electron Chromium Runtime...
    pushd "%ROOT%BhuLoka_Chromium_App"
    call node_modules\.bin\electron.cmd .
    popd
    goto :eof
)

if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    echo Launching BHU LOKA via Google Chrome Chromium App Shell...
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --app="file:///%TARGET_HTML:\=/%" --window-size=1600,960
    goto :eof
)

if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
    echo Launching BHU LOKA via Microsoft Edge Chromium App Shell...
    start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --app="file:///%TARGET_HTML:\=/%" --window-size=1600,960
    goto :eof
)

start "" "%TARGET_HTML%"

