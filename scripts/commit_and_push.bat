@echo off
setlocal
cd /d "%~dp0.."

echo === git status ===
git status --porcelain
echo.

git check-ignore -v .env >nul 2>&1
if errorlevel 1 (
  echo ERROR: .env is not ignored. abort.
  exit /b 1
)

git add .gitignore index.html css/style.css js/app.js api/generate.py requirements.txt env.example vercel.json README.md "기획서_되나요.md" "증빙자료" images/.gitkeep
git status
git commit -m "feat: add Doenayo web service with Gemini serverless API"
git push -u origin main

echo.
echo done.
endlocal
