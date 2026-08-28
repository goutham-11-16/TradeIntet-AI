@echo off
title TradeSentinel Backend (Port 8001)
echo ====================================================
echo Starting TradeSentinel Backend API on port 8001...
echo ====================================================
cd /d "%~dp0backend"
python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload
pause
