@echo off
setlocal
title BDA for NNC v2.0

set "BDA_ROOT=%~dp0"
set "BDA_EXE=%BDA_ROOT%.venv\Scripts\bda.exe"
set "BDA_WORKBOOK=%BDA_ROOT%data\Companies.xlsx"

cd /d "%BDA_ROOT%"

echo.
echo ============================================================
echo  BDA for NNC v2.0 - Companies.xlsx processing cycle
echo ============================================================
echo.

if not exist "%BDA_EXE%" (
    echo ERROR: The BDA virtual environment is not installed.
    echo Expected command:
    echo   %BDA_EXE%
    echo.
    echo Create and install it with:
    echo   py -3.11 -m venv .venv
    echo   .venv\Scripts\python.exe -m pip install -e ".[dev,vector]"
    goto :failure
)

if not exist "%BDA_WORKBOOK%" (
    echo ERROR: Input workbook not found.
    echo Expected file:
    echo   %BDA_WORKBOOK%
    goto :failure
)

echo [1/9] Validating installation...
"%BDA_EXE%" validate-installation
if errorlevel 1 goto :failure

echo.
echo [2/9] Validating application configuration...
"%BDA_EXE%" validate-config
if errorlevel 1 goto :failure

echo.
echo [3/9] Validating fixed production models...
"%BDA_EXE%" validate-models
if errorlevel 1 goto :failure

echo.
echo [4/9] Validating the dSPACE portfolio index...
"%BDA_EXE%" validate-portfolio-index
if errorlevel 1 goto :failure

echo.
echo [5/9] Validating target-company search providers...
"%BDA_EXE%" validate-search-providers
if errorlevel 1 goto :failure

echo.
echo [6/9] Validating zero-cost search policy and quota ledger...
"%BDA_EXE%" validate-free-search-config
if errorlevel 1 goto :failure

echo.
echo [7/9] Validating Companies.xlsx...
"%BDA_EXE%" validate-registry --workbook "data\Companies.xlsx"
if errorlevel 1 goto :failure

echo.
echo [8/9] Rows selected for this processing cycle:
"%BDA_EXE%" list-registry-selection --workbook "data\Companies.xlsx"
if errorlevel 1 goto :failure

echo.
echo [9/9] Starting the sequential BDA processing cycle...
set "BDA_RECEIPT=%TEMP%\bda-verified-%RANDOM%-%RANDOM%-%RANDOM%.txt"
if exist "%BDA_RECEIPT%" goto :failure
"%BDA_ROOT%.venv\Scripts\python.exe" "%BDA_ROOT%verify_cycle_launch.py" "%BDA_ROOT%." "%BDA_RECEIPT%" standard
if errorlevel 1 goto :failure
if not exist "%BDA_RECEIPT%" (
    echo ERROR: No verified cycle receipt. A process may have been blocked.
    goto :failure
)
del "%BDA_RECEIPT%"

echo.
echo ============================================================
echo  BDA processing cycle completed successfully.
echo  Results are available under:
echo    %BDA_ROOT%output
echo ============================================================
echo.
pause
exit /b 0

:failure
echo.
echo ============================================================
echo  BDA stopped because an error occurred.
echo  Cycle completion was not verified. Review logs and security alerts.
echo  Partial results or workbook updates may already exist.
echo ============================================================
echo.
pause
exit /b 1
