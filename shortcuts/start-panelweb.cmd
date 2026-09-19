@echo off
set ROOT=C:\dev\adafruit-pannel
cd /d "%ROOT%"
if not exist "%ROOT%\bin\panelweb.exe" (
  echo Building panelweb.exe
  go build -o bin\panelweb.exe ./web
)
echo Starting http://127.0.0.1:8787
start "panelweb" "%ROOT%\bin\panelweb.exe"
timeout /t 1 /nobreak >nul
start "" "http://127.0.0.1:8787/"
