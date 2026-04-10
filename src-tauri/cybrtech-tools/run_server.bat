@echo off
REM Run CybrTech AI Server with the Python virtual environment
cd /d "%~dp0"
call cybrtech-env\Scripts\activate.bat
python cybrtech_server.py %*
