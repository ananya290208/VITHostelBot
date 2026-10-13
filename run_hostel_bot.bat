@echo off
title Campus Hostel AI ChatBot
echo ========================================================
echo       Starting Campus Hostel AI ChatBot System
echo ========================================================
echo.
cd /d "%~dp0\backend"
echo [1/2] Checking dependencies...
pip install -r requirements.txt
echo.
echo [2/2] Starting server at http://localhost:8000 ...
start http://localhost:8000
python main.py
pause
