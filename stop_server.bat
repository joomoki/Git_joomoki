@echo off
echo Stopping Joomoki Web Server...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Joomoki Web Server*" >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1
echo Server stopped.
pause
