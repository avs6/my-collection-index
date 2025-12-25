@echo off
setlocal enabledelayedexpansion

REM -----------------------------
REM Awesome-Abi Star Updater (Windows)
REM Double-click to run
REM -----------------------------

REM 1) CONFIG: set your repo folder (absolute path)
set "REPO_DIR=C:\Users\Abi\Desktop\github\my-collection-index"

REM 2) CONFIG: set your GitHub username
set "GITHUB_USER=YOUR_GITHUB_USERNAME"

REM 3) OPTIONAL: token handling
REM If GITHUB_TOKEN is already set in your environment, do nothing.
REM Otherwise, uncomment and paste your token here (NOT recommended for shared machines).
REM set "GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

echo.
echo ============================================================
echo   Awesome-Abi: Stars -> README Auto Update (Windows)
echo ============================================================
echo Repo:  %REPO_DIR%
echo User:  %GITHUB_USER%
echo.

if not exist "%REPO_DIR%" (
  echo ERROR: Repo folder not found: "%REPO_DIR%"
  echo Fix REPO_DIR in this .bat file.
  pause
  exit /b 1
)

cd /d "%REPO_DIR%"

REM 4) Ensure script exists
if not exist "scripts\update_from_stars.py" (
  echo ERROR: scripts\update_from_stars.py not found in:
  echo   %REPO_DIR%
  echo Fix REPO_DIR or repo structure.
  pause
  exit /b 1
)

REM 5) Use python launcher if available, else python
where py >nul 2>nul
if %ERRORLEVEL%==0 (
  set "PY=py"
) else (
  set "PY=python"
)

echo --- Step 1: Dry run (safe preview) ---
%PY% scripts\update_from_stars.py --user %GITHUB_USER% --dry-run
if %ERRORLEVEL% neq 0 (
  echo.
  echo ERROR: Dry run failed. Fix the error above and rerun.
  pause
  exit /b %ERRORLEVEL%
)

echo.
echo --- Step 2: Write README (updates AUTO-MANAGED block) ---
%PY% scripts\update_from_stars.py --user %GITHUB_USER% --write
if %ERRORLEVEL% neq 0 (
  echo.
  echo ERROR: Write step failed. Fix the error above and rerun.
  pause
  exit /b %ERRORLEVEL%
)

echo.
echo ✅ Done! README.md updated.
echo Next:
echo   git diff
echo   git add README.md
echo   git commit -m "Auto-update curated index from stars"
echo   git push
echo.
pause
endlocal
