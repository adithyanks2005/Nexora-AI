@echo off
REM ============================================================
REM  Nexora AI — Build Android App Bundle (.aab)
REM  Required for new Google Play Store submissions.
REM  Run from the android\ directory.
REM ============================================================

setlocal

echo.
echo ================================================
echo   Nexora AI — Build Release AAB
echo ================================================
echo.

REM Check local.properties exists
if not exist "%~dp0local.properties" (
    echo [ERROR] local.properties not found.
    echo.
    echo Please create android\local.properties with:
    echo   STORE_FILE=app/nexora-release.jks
    echo   STORE_PASSWORD=your_keystore_password
    echo   KEY_ALIAS=nexora
    echo   KEY_PASSWORD=your_key_password
    echo.
    echo Run generate-keystore.bat first if you haven't yet.
    pause
    exit /b 1
)

echo Building release AAB (this takes 1-3 minutes)...
echo.

call "%~dp0gradlew.bat" bundleRelease --stacktrace

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed. Check the output above for details.
    pause
    exit /b 1
)

echo.
echo ================================================
echo   BUILD SUCCESSFUL!
echo ================================================
echo.
echo Your AAB is at:
echo   app\build\outputs\bundle\release\app-release.aab
echo.
echo Upload this file to Google Play Console:
echo   https://play.google.com/console
echo.
echo Steps:
echo   1. Open Play Console ^> Your App ^> Production
echo   2. Create new release
echo   3. Upload app-release.aab
echo   4. Fill in release notes
echo   5. Submit for review (~1-3 days)
echo.
pause
