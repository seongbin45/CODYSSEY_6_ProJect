@echo off
chcp 65001 >nul
setlocal EnableExtensions

rem ============================================================
rem  되나요 — 초심자용 커밋/푸시
rem  사용법: 이 파일을 더블클릭하거나, 터미널에서 실행
rem
rem  다른 사람은 아래 4줄만 자기 값으로 바꾸면 됩니다.
rem ============================================================
set "GIT_USER_NAME=seongbin45"
set "GIT_USER_EMAIL=sungbin45@office365.kunsan.ac.kr"
set "REPO_DIR=C:\Users\seong\Downloads\CODYSSEY_6_ProJect"
set "REMOTE_URL=https://github.com/seongbin45/CODYSSEY_6_ProJect.git"
set "COMMIT_MSG=docs: add beginner git commit and push commands"

echo.
echo [1/8] 프로젝트 폴더로 이동
cd /d "%REPO_DIR%"
if errorlevel 1 (
  echo ERROR: 폴더를 찾지 못했습니다. REPO_DIR 을 확인하세요.
  echo 현재 값: %REPO_DIR%
  goto :fail
)
echo     %CD%

echo.
echo [2/8] Git 설치 확인
git --version
if errorlevel 1 (
  echo ERROR: Git 이 없습니다. https://git-scm.com/download/win 에서 설치하세요.
  goto :fail
)

echo.
echo [3/8] 커밋 작성자 등록
git config --global user.name "%GIT_USER_NAME%"
git config --global user.email "%GIT_USER_EMAIL%"
echo     name  = %GIT_USER_NAME%
echo     email = %GIT_USER_EMAIL%

echo.
echo [4/8] GitHub 원격 주소 확인
git remote get-url origin >nul 2>&1
if errorlevel 1 (
  echo     origin 이 없어서 추가합니다.
  git remote add origin "%REMOTE_URL%"
) else (
  git remote set-url origin "%REMOTE_URL%"
)
git remote -v

echo.
echo [5/8] .env 가 커밋에서 제외되는지 확인
git check-ignore -v .env
if errorlevel 1 (
  echo ERROR: .env 가 무시되지 않습니다. 푸시를 중단합니다.
  echo .gitignore 에 .env 가 있는지 확인하세요.
  goto :fail
)

echo.
echo [6/8] 올릴 파일만 추가
git add .gitignore
git add index.html
git add css/style.css
git add js/app.js
git add api/generate.py
git add requirements.txt
git add env.example
git add vercel.json
git add README.md
git add "기획서_되나요.md"
git add "증빙자료"
git add images/.gitkeep
git add docs/git_초심자_명령어.md
git add scripts/git_commit_push.bat

echo.
echo     --- git status ---
git status
findstr /C:".env" /C:"other/" "%TEMP%\doenayo-git-status.txt" >nul 2>&1

echo.
echo [7/8] 커밋
git diff --cached --quiet
if not errorlevel 1 (
  echo     새로 커밋할 내용이 없습니다. 푸시만 시도합니다.
) else (
  git commit -m "%COMMIT_MSG%"
  if errorlevel 1 (
    echo ERROR: 커밋에 실패했습니다.
    goto :fail
  )
)

echo.
echo [8/8] GitHub 로 푸시
git branch -M main
git push -u origin main
if errorlevel 1 (
  echo.
  echo 푸시가 거절되면 아래를 한 줄씩 실행해 보세요.
  echo     git pull --rebase origin main
  echo     git push
  goto :fail
)

echo.
echo 완료. 브라우저에서 확인하세요.
echo https://github.com/seongbin45/CODYSSEY_6_ProJect
echo.
echo 확인: .env 파일이 GitHub 에 보이면 실패한 것입니다. 키를 즉시 폐기하세요.
goto :end

:fail
echo.
echo 실패로 종료했습니다. 위 메시지를 읽고 다시 실행하세요.
pause
exit /b 1

:end
pause
endlocal
