@echo off
setlocal

cd /d "%~dp0"

set "PYTHONUTF8=1"
set "QT_QPA_PLATFORM=offscreen"

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=%CD%\.venv\Scripts\python.exe"
) else (
    where python >nul 2>nul
    if errorlevel 1 (
        echo [CodeParser] Python was not found. Install Python 3.12+ or create .venv first.
        exit /b 1
    )
    set "PYTHON_EXE=python"
)

echo [CodeParser] Using Python: %PYTHON_EXE%
echo [CodeParser] Installing build dependencies...
call "%PYTHON_EXE%" -m pip install --upgrade pip
if errorlevel 1 goto :error

call "%PYTHON_EXE%" -m pip install -r requirements.txt pyinstaller pytest pytest-qt
if errorlevel 1 goto :error

if /I "%CODEPARSER_INSTALL_OPTIONAL%"=="1" (
    echo [CodeParser] Installing optional Tree-sitter dependencies...
    call "%PYTHON_EXE%" -m pip install -r requirements-optional.txt
    if errorlevel 1 goto :error

    call "%PYTHON_EXE%" -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('tree_sitter') and importlib.util.find_spec('tree_sitter_languages') else 1)"
    if errorlevel 1 (
        echo [CodeParser] Optional Tree-sitter packages are unavailable for this Python version. Continuing with graceful fallback compression support.
    ) else (
        echo [CodeParser] Optional Tree-sitter packages detected. Advanced compression support will be bundled into the EXE when available at runtime.
    )
)

echo [CodeParser] Running tests...
call "%PYTHON_EXE%" -m pytest tests
if errorlevel 1 goto :error

echo [CodeParser] Building CodeParser.exe...
call "%PYTHON_EXE%" -m PyInstaller --clean --noconfirm CodeParser.spec
if errorlevel 1 goto :error

echo.
echo [CodeParser] Build complete:
echo [CodeParser] %CD%\dist\CodeParser.exe
exit /b 0

:error
echo.
echo [CodeParser] Build failed.
exit /b 1
