@echo off
title BHU LOKA (भूलोक) - Full-Stack Geospatial Workstation Launcher
setlocal
set ROOT=%~dp0
set TARGET_HTML=%ROOT%bhu_loka_cyber_dashboard.html
set PY_EXE=C:\Users\ljpri\AppData\Local\Programs\Python\Python313\python.exe

echo [1/2] Starting BHU LOKA FastAPI Live Telemetry + Hybrid RAG Server on http://127.0.0.1:8000 ...
start "BHU LOKA FastAPI Backend (:8000)" /min "%PY_EXE%" "%ROOT%Models\04_Hybrid_RAG\enterprise_rag_app\main.py"

timeout /t 2 /nobreak >nul

echo [2/2] Launching Chromium Sovereign Workstation...
if exist "%ROOT%BhuLoka_Chromium_App\node_modules\.bin\electron.cmd" (
    pushd "%ROOT%BhuLoka_Chromium_App"
    call node_modules\.bin\electron.cmd .
    popd
    goto :eof
)

if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --app="http://127.0.0.1:8000/" --window-size=1600,960
    goto :eof
)

if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
    start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --app="http://127.0.0.1:8000/" --window-size=1600,960
    goto :eof
)

start "" "%TARGET_HTML%"
