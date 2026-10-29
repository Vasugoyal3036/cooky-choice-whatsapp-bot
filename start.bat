@echo off
title Cooky Choice Rice - WhatsApp Automation Server
echo ==============================================================
echo    Cooky Choice Rice - WhatsApp Automation Server
echo    Official Meta Cloud API • Simulator • Admin Console
echo ==============================================================
echo.

set PYTHON_EXE=C:\Users\h\AppData\Local\Programs\Python\Python312\python.exe

if not exist "%PYTHON_EXE%" (
    set PYTHON_EXE=python
)

echo Starting Server on http://localhost:8000 ...
echo - WhatsApp Chat Simulator: http://localhost:8000
echo - Brand Owner Admin Panel: http://localhost:8000/admin
echo.

"%PYTHON_EXE%" main.py
pause
