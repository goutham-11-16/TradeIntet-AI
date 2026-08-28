@echo off
title TradeSentinel Frontend (Port 3000)
echo ====================================================
echo Starting TradeSentinel React Frontend on port 3000...
echo ====================================================
cd /d "%~dp0frontend"
set PORT=3000
set BROWSER=none
npm start
pause
