@echo off
title Push to GitHub - VITHostelBot
echo ========================================================
echo       Checking in code to GitHub: VITHostelBot
echo ========================================================
echo.
cd /d "%~dp0"

echo [1/5] Initializing Git repository...
git init

echo [2/5] Adding remote origin...
git remote remove origin 2>nul
git remote add origin https://github.com/ananya290208/VITHostelBot.git

echo [3/5] Staging files...
git add .

echo [4/5] Committing changes...
git commit -m "Initial commit: VIT Hostel Information & Complaint Management AI ChatBot"

echo [5/5] Pushing to main branch...
git branch -M main
git push -u origin main

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ------------------------------------------------------------------------
    echo If the remote repository already contains a README or commits, run:
    echo git pull origin main --rebase
    echo git push -u origin main
    echo ------------------------------------------------------------------------
)

echo.
echo Done!
pause
