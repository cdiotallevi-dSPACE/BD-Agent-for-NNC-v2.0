@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\bda.exe" (
  echo BDA virtual environment is missing. Run Run-BDA.cmd once to install it.
  pause
  exit /b 1
)
echo Starting BDA fast-iteration profile...
set "BDA_RECEIPT=%TEMP%\bda-verified-%RANDOM%-%RANDOM%-%RANDOM%.txt"
if exist "%BDA_RECEIPT%" exit /b 1
".venv\Scripts\python.exe" "verify_cycle_launch.py" "%~dp0." "%BDA_RECEIPT%" fast_iteration
set EXITCODE=%ERRORLEVEL%
if not exist "%BDA_RECEIPT%" (
  echo ERROR: No verified cycle receipt. Review logs and security alerts.
  set EXITCODE=1
)
if exist "%BDA_RECEIPT%" del "%BDA_RECEIPT%"
echo.
if not "%EXITCODE%"=="0" echo BDA fast iteration failed with exit code %EXITCODE%.
pause
exit /b %EXITCODE%
