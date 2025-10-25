@echo off

IF EXIST ".git" (
    echo Updating UltimatePyve via git pull
    git pull
) ELSE (
    echo Updating UltimatePyve via zip file download
    curl -L -o "%TMP%\UltimatePyve.zip" "https://github.com/jasonuithol/UltimatePyve/archive/refs/heads/master.zip"

    rmdir /S /Q "%TMP%\UltimatePyve" 2>nul
    mkdir "%TMP%\UltimatePyve" 2>nul

    tar -xf "%TMP%\UltimatePyve.zip" -C "%TMP%\UltimatePyve"
    xcopy "%TMP%\UltimatePyve\UltimatePyve-master" . /E /I /Y

    rem del "%TMP%\UltimatePyve.zip"
    rem rmdir /S /Q "%TMP%\UltimatePyve"
)

rem This actually updates log/last_commit.txt
py -3.13 utilities\update_checker.py --non-interactive --silent

echo "Update complete"

pause
