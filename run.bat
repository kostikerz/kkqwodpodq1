@echo off
cd /d "%~dp0"
if defined PYTHON_EXE (
  "%PYTHON_EXE%" -m src.cli %*
) else (
  python -m src.cli %*
)
