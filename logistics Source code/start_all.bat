@echo off
title TradeSentinel Automation Copilot - Local Launcher
echo ======================================================================
echo   TradeSentinel - AI Business Automation Copilot (PS4)
echo ======================================================================
echo.
echo Launching Backend and Frontend in separate windows...
echo.

start "TradeSentinel Backend (8001)" cmd /k "cd /d %~dp0backend && python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload"

timeout /t 3 /nobreak > nul

start "TradeSentinel Frontend (3000)" cmd /k "cd /d %~dp0frontend && set PORT=3000 && npm start"

echo.
echo ======================================================================
echo Services started:
echo   - Backend API:       http://localhost:8001/docs
echo   - Frontend App:      http://localhost:3000
echo   - Automation Copilot: http://localhost:3000/app/copilot
echo.
echo Default Demo Logins:
echo   - Admin:   admin@tradesentinel.demo   / Admin@123
echo   - Manager: manager@tradesentinel.demo / Manager@123
echo   - Viewer:  viewer@tradesentinel.demo  / Viewer@123
echo ======================================================================
echo.
pause
