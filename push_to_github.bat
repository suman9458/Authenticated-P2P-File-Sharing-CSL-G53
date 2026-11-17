@echo off
echo ======================================================================
echo    DEPLOY AUTHENTICATED P2P FILE SHARING (CSL-G53) TO GITHUB
echo    Student: Suman Kumar (Roll No: 23ESKCS822)
echo ======================================================================
echo.
echo Step 1: Make sure you have created an empty repository on GitHub:
echo         https://github.com/new
echo         Repository name: Authenticated-P2P-File-Sharing-CSL-G53
echo         (Do NOT initialize with README, .gitignore, or license)
echo.
echo Step 2: Attempting to push repository to GitHub...
git push -u origin main
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ======================================================================
    echo [+] SUCCESS! Project successfully deployed to your GitHub:
    echo     https://github.com/suman9458/Authenticated-P2P-File-Sharing-CSL-G53
    echo ======================================================================
) else (
    echo.
    echo [!] Push encountered an authentication prompt or the repository does not exist yet.
    echo     1. Visit: https://github.com/new
    echo     2. Create the repository named: Authenticated-P2P-File-Sharing-CSL-G53
    echo     3. Run this script again or open GitHub Desktop to publish with 1-click!
)
pause
