@echo off
setlocal

cd /d "%~dp0"

echo [CodeParser] Advanced build requested. Optional Tree-sitter dependencies will be installed when supported by the current Python version.
set "CODEPARSER_INSTALL_OPTIONAL=1"

call "%~dp0build_exe.bat"
exit /b %errorlevel%
