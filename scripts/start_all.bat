@echo off
echo ============================================================
echo   AI Employee - Full Workflow Startup (Windows)
echo ============================================================
echo.

cd /d "%~dp0\.."

:: Activate virtual environment
call venv-win\Scripts\activate.bat

:: Start the workflow
echo Starting all watchers...
python src\workflow\start_workflow.py %*

pause
