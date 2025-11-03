@echo off

set PYTHON_VERSION=3.14

py -%PYTHON_VERSION% -m pip install --upgrade pip
py -%PYTHON_VERSION% -m pip install -r requirements.txt
if errorlevel 1 (
    echo( 
    echo -------------------------------------------
    echo(
    echo ====! Must have python %PYTHON_VERSION% installed !=====    
    echo(
    pause
    exit
)
py -%PYTHON_VERSION% utilities\update_checker.py --check-only
py -%PYTHON_VERSION% main.py
pause
