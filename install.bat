@echo off
title PHANTOM SYNC INSTALLER [v2.0]
color 0a
cls

echo.
echo [ INITIALIZING SYSTEM ]
echo.
timeout /t 1 >nul
echo  [*] Checking Python version...      [OK]
timeout /t 1 >nul
echo  [*] Verifying pip package manager... [OK]
timeout /t 1 >nul
echo  [*] Allocating memory...            [OK]
timeout /t 1 >nul
echo.
echo [ SYSTEM READY. STARTING INSTALLATION ]
echo.
echo ---------------------------------------------------
echo.

set /p="Loading modules: [>" <nul
timeout /t 1 >nul
set /p="==>" <nul
timeout /t 1 >nul
set /p="====>" <nul
timeout /t 1 >nul
set /p="======>]  100%%" <nul
echo.
echo.


echo [ EXECUTING PIP INSTALL ]
echo.
pip install -r requirements.txt


if %errorlevel% neq 0 (
    color 0c
    echo.
    echo [!] ERROR: Installation failed!
    echo Check if Python is installed and added to PATH.
    pause
    exit /b
)

cls
color 0b
echo.
echo.
echo      SUCCESSFULLY INSTALLED!
echo.
echo      Now you can run the software.
echo.
echo ---------------------------------------------------
echo    Type: python main.py
echo    OR run start.bat
echo ---------------------------------------------------
echo.
pause