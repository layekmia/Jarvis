@echo off
echo Initializing MSVC Environment...
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" x64

echo.
echo Installing Python dependencies...
cd /d "%~dp0.."
backend\.venv\Scripts\pip.exe install -r backend\requirements.txt
