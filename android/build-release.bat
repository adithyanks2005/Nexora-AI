@echo off
REM ============================================================
REM  Nexora AI — Build Signed Release APK
REM  (Use build-aab.bat for Play Store; use this for direct install)
REM ============================================================

setlocal

echo.
echo ================================================
echo   Nexora AI — Build Release APK
echo ================================================
echo.

if not exist "%~dp0local.properties" (
    echo [ERROR] local.properties not found.
    echo Run generate-keystore.bat first.
    pause
    exit /b 1
)

echo Building signed release APK...
echo.

call "%~dp0gradlew.bat" assembleRelease --stacktrace

if errorlevel 1 (
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

echo.
echo ================================================
echo   BUILD SUCCESSFUL!
echo ================================================
echo.
echo Signed APK:
echo   app\build\outputs\apk\release\app-release.apk
echo.
echo Install on a connected device:
echo   adb install app\build\outputs\apk\release\app-release.apk
echo.
pause
