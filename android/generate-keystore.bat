@echo off
REM ============================================================
REM  Nexora AI — Release Keystore Generator
REM  Run this ONCE to create your signing keystore.
REM  The generated .jks file stays in android/app/.
REM  NEVER commit nexora-release.jks or local.properties to git.
REM ============================================================

setlocal

set KEYSTORE=app\nexora-release.jks
set ALIAS=nexora

echo.
echo ================================================
echo   Nexora AI — Keystore Generator
echo ================================================
echo.
echo This will create a signing keystore at:
echo   %~dp0%KEYSTORE%
echo.
echo You will be prompted for:
echo   - A keystore password (remember this!)
echo   - Your name / organisation / city / country
echo.
pause

keytool -genkey -v ^
  -keystore "%~dp0%KEYSTORE%" ^
  -alias %ALIAS% ^
  -keyalg RSA ^
  -keysize 2048 ^
  -validity 10000

if errorlevel 1 (
    echo.
    echo [ERROR] Keystore generation failed.
    echo Make sure Java is installed and on your PATH.
    pause
    exit /b 1
)

echo.
echo ================================================
echo  Keystore created: %KEYSTORE%
echo ================================================
echo.
echo Extracting SHA-256 fingerprint...
echo (You will need to enter your keystore password again)
echo.

keytool -list -v -keystore "%~dp0%KEYSTORE%" -alias %ALIAS% | findstr "SHA256"

echo.
echo ================================================
echo  NEXT STEPS:
echo ================================================
echo.
echo 1. Copy the SHA-256 fingerprint shown above.
echo.
echo 2. Open: frontend\.well-known\assetlinks.json
echo    Replace REPLACE_WITH_YOUR_SHA256_CERT_FINGERPRINT
echo    with your actual fingerprint (keep colon-separated format).
echo.
echo 3. Create android\local.properties with these lines:
echo      STORE_FILE=app/nexora-release.jks
echo      STORE_PASSWORD=your_keystore_password
echo      KEY_ALIAS=nexora
echo      KEY_PASSWORD=your_key_password
echo.
echo 4. Push the updated assetlinks.json to Vercel (git push).
echo.
echo 5. Run build-aab.bat to build the Play Store bundle.
echo ================================================
echo.
pause
