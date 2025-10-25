@echo off
py -3.13 -m pip install -r requirements.txt
if errorlevel 1 (
    echo( 
    echo -------------------------------------------
    echo(
    echo ====! Must have python 3.13 installed !=====    
    echo(
    pause
    exit
)
py -3.13 main.py
pause