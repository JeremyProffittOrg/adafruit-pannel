@echo off
setlocal EnableExtensions
title Login with Amazon — ap.jeremy.ninja
cd /d "%~dp0.."

echo.
echo ============================================================
echo  Login with Amazon  (LWA)  for  https://ap.jeremy.ninja
echo ============================================================
echo.
echo  This window is the ONLY place you type the Client ID and
echo  Client Secret. They go straight into GitHub secrets.
echo  They are never printed back, never logged, never pasted
echo  into chat.
echo.
echo  STEP 1 — open Amazon and create a Security Profile
echo  ------------------------------------------------------------
echo  Console (create / list profiles):
echo    https://developer.amazon.com/loginwithamazon/console/site/lwa/overview.html
echo.
echo  New security profile:
echo    https://developer.amazon.com/settings/console/securityprofile/new.html
echo.
echo  Web settings docs:
echo    https://developer.amazon.com/docs/login-with-amazon/register-web.html
echo.
echo  STEP 2 — Web Settings on that profile  (exact values)
echo  ------------------------------------------------------------
echo  Allowed Origins  (one per line):
echo    https://ap.jeremy.ninja
echo.
echo  Allowed Return URLs  (one per line):
echo    https://ap.jeremy.ninja/auth/amazon/callback
echo.
echo  Privacy Notice URL:
echo    https://ap.jeremy.ninja/privacy.html
echo.
echo  Consent Privacy Notice URL: same as Privacy Notice URL
echo.
echo  After Save, open Web Settings again and copy:
echo    Client ID
echo    Client Secret
echo.
pause

set "BASH="
if exist "%ProgramFiles%\Git\bin\bash.exe" set "BASH=%ProgramFiles%\Git\bin\bash.exe"
if not defined BASH if exist "%ProgramFiles(x86)%\Git\bin\bash.exe" set "BASH=%ProgramFiles(x86)%\Git\bin\bash.exe"
if not defined BASH (
  echo ERROR: Git Bash not found. Install Git for Windows, then re-run this script.
  pause
  exit /b 1
)

echo.
echo  STEP 3 — push Client ID to GitHub secret LWA_CLIENT_ID
echo  ------------------------------------------------------------
echo  Type the Client ID at the hidden prompt. Confirm it.
"%BASH%" "%~dp0set-secret.sh" LWA_CLIENT_ID
if errorlevel 1 (
  echo FAILED: LWA_CLIENT_ID was not set.
  pause
  exit /b 1
)

echo.
echo  STEP 4 — push Client Secret to GitHub secret LWA_CLIENT_SECRET
echo  ------------------------------------------------------------
echo  Type the Client Secret at the hidden prompt. Confirm it.
"%BASH%" "%~dp0set-secret.sh" LWA_CLIENT_SECRET
if errorlevel 1 (
  echo FAILED: LWA_CLIENT_SECRET was not set.
  pause
  exit /b 1
)

echo.
echo  STEP 5 — session HMAC  (generated, you do not type this)
echo  ------------------------------------------------------------
"%BASH%" "%~dp0set-secret.sh" SESSION_SECRET --generate
if errorlevel 1 (
  echo FAILED: SESSION_SECRET was not set.
  pause
  exit /b 1
)

echo.
echo  OK. GitHub secrets on JeremyProffittOrg/adafruit-pannel:
echo    LWA_CLIENT_ID
echo    LWA_CLIENT_SECRET
echo    SESSION_SECRET
echo.
echo  They reach Lambda on the next push to main.
echo  Leave this window open if you still need the URLs above.
echo.
pause
endlocal
