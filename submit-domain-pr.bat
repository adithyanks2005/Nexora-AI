@echo off
echo ============================================
echo  MediCura AI - Domain Registration Script
echo ============================================
echo.
echo This script will open 2 browser tabs:
echo.
echo 1. Create domain file in your fork
echo 2. Create Pull Request to is-a-dev
echo.
echo Press any key to continue...
pause > nul

echo.
echo Opening Step 1: Create domain file...
echo.
start "" "https://github.com/adithyanks2005/is-a-dev-register/new/main?filename=domains/medicura-ai.json"

echo Waiting 3 seconds...
timeout /t 3 /nobreak > nul

echo.
echo ============================================
echo  STEP 1 INSTRUCTIONS
echo ============================================
echo.
echo The browser opened. Now:
echo.
echo 1. Paste this JSON content:
echo.
type "%~dp0domain-config-to-paste.txt"
echo.
echo 2. Commit message: Add medicura-ai.is-a.dev domain
echo 3. Click "Commit new file"
echo.
echo After committing, press any key to continue to Step 2...
pause > nul

echo.
echo Opening Step 2: Create Pull Request...
echo.
start "" "https://github.com/is-a-dev/register/compare/main...adithyanks2005:is-a-dev-register:main"

echo.
echo ============================================
echo  STEP 2 INSTRUCTIONS
echo ============================================
echo.
echo The browser opened. Now:
echo.
echo 1. Click "Create pull request"
echo 2. Title: Add medicura-ai.is-a.dev
echo 3. Paste the description from: pr-description.txt
echo 4. Click "Create pull request" again
echo.
echo ============================================
echo  DONE!
echo ============================================
echo.
echo After submitting:
echo - Check your email: ksadithyan2021@gmail.com
echo - Approval typically takes 1-3 days
echo - You'll get notified when domain is live
echo.
echo Press any key to close...
pause > nul
