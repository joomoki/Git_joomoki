@echo off
cd /d %~dp0
call venv\Scripts\activate.bat
echo Starting Joomoki Web Server in background...
start "" pythonw src/web/main.py
echo Server started. You can close this window.
echo Access at http://localhost:8000
pause
