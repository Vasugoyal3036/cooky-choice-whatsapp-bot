@echo off
title Push Cooky Choice WhatsApp Bot to GitHub
echo ==============================================================
echo    Pushing Cooky Choice Rice WhatsApp Bot to GitHub
echo    Repository: Vasugoyal3036/cooky-choice-whatsapp-bot
echo ==============================================================
echo.

set PATH=C:\Users\h\git\cmd;%PATH%
cd /d "%~dp0"

echo Step 1: Checking status...
git status
echo.

echo Step 2: Pushing to GitHub (main branch)...
echo If a GitHub browser window opens, click 'Sign in with your browser'.
echo.

git push -u origin main

echo.
echo ==============================================================
echo Finished! Check your repository:
echo https://github.com/Vasugoyal3036/cooky-choice-whatsapp-bot
echo ==============================================================
echo.
pause

