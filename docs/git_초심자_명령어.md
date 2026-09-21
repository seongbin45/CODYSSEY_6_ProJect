# Git 초심자 명령어 — 커밋하고 푸시하기

더블클릭으로 실행하려면 `scripts\git_commit_push.bat` 을 쓰면 됩니다.
이 문서는 **한 번도 Git을 안 써본 사람**이
`되나요` 프로젝트를 GitHub에 올리기 위해 그대로 복사해 쓰는 용도입니다.

- Windows + PowerShell 또는 CMD 기준입니다.
- `<>` 안에 있는 값만 본인 것으로 바꿉니다.
- 아래에 적힌 `seongbin45` / `sungbin45@office365.kunsan.ac.kr` 은
  **이 프로젝트 작성자의 실제 설정**입니다. 다른 사람은 자기 값으로 바꿉니다.

---

## 0. 한 번만 하는 준비

### 0-1. Git이 설치되어 있는지 확인

```powershell
git --version
```

`git version 2.xx.x` 처럼 나오면 됩니다.
안 나오면 https://git-scm.com/download/win 에서 설치합니다.

### 0-2. 내 이름과 이메일을 Git에 등록

커밋마다 “누가 만들었는지”가 이 값으로 찍힙니다.

**이 프로젝트 작성자(최성빈)는 이렇게 되어 있습니다.**

```powershell
git config --global user.name "seongbin45"
git config --global user.email "sungbin45@office365.kunsan.ac.kr"
```

**다른 초심자는 자기 값으로 바꿉니다.**

```powershell
git config --global user.name "<깃허브아이디>"
git config --global user.email "<깃허브에등록한이메일>"
```

확인:

```powershell
git config --global --get user.name
git config --global --get user.email
```

이 프로젝트에서 나와야 하는 값:

```
seongbin45
sungbin45@office365.kunsan.ac.kr
```

> 이메일은 GitHub 계정에 등록된 주소여야 커밋이 내 프로필에 연결됩니다.
> 학교 메일을 쓰기 싫으면 GitHub이 주는 비공개 주소도 됩니다.
> 예: `272260321+seongbin45@users.noreply.github.com`

---

## 1. 프로젝트 폴더로 이동

```powershell
cd C:\Users\seong\Downloads\CODYSSEY_6_ProJect
```

다른 사람 PC라면 자기 폴더 경로로 바꿉니다.

```powershell
cd <프로젝트폴더경로>
```

맞는지 확인:

```powershell
git status
```

`On branch main` 이 보이면 이 저장소가 맞습니다.

---

## 2. GitHub 저장소가 연결되어 있는지 확인

이 프로젝트의 원격 저장소:

```
https://github.com/seongbin45/CODYSSEY_6_ProJect.git
```

확인:

```powershell
git remote -v
```

이렇게 나와야 합니다.

```
origin  https://github.com/seongbin45/CODYSSEY_6_ProJect.git (fetch)
origin  https://github.com/seongbin45/CODYSSEY_6_ProJect.git (push)
```

안 연결되어 있으면:

```powershell
git remote add origin https://github.com/seongbin45/CODYSSEY_6_ProJect.git
```

이미 있는데 주소를 고쳐야 하면:

```powershell
git remote set-url origin https://github.com/seongbin45/CODYSSEY_6_ProJect.git
```

다른 사람 저장소라면:

```powershell
git remote add origin https://github.com/<깃허브아이디>/<저장소이름>.git
```

---

## 3. 비밀 파일이 커밋에 안 들어가는지 확인 ★ 필수

API 키가 들어 있는 `.env` 는 **절대 올리면 안 됩니다.**

```powershell
git check-ignore -v .env
```

정상:

```
.gitignore:5:.env	.env
```

그다음:

```powershell
git status --porcelain
```

여기 `.env` 가 **보이면 즉시 중단**합니다.
보이면 아래를 실행하고 다시 확인합니다.

```powershell
git rm --cached .env
```

`other/` 폴더도 올리면 안 됩니다. `.gitignore` 에 이미 넣어 두었습니다.

---

## 4. 올릴 파일만 고르기

전체를 `git add .` 하지 않습니다.
키가 섞일 위험이 있어서, 필요한 파일만 집어 넣습니다.

```powershell
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
```

확인:

```powershell
git status
```

`Changes to be committed` 아래에 위 파일들이 있어야 합니다.
`.env` 와 `other/` 는 없어야 합니다.

---

## 5. 커밋하기

커밋 = “이 시점의 스냅샷을 기록한다”는 뜻입니다.
아직 GitHub에는 안 올라갑니다.

```powershell
git commit -m "feat: add Doenayo web service with Gemini serverless API"
```

이미 같은 메시지 커밋이 있다면, 그다음 변경은 새 메시지로 남깁니다.

```powershell
git commit -m "docs: add beginner git commit and push commands"
```

`nothing to commit` 이면 새로 커밋할 내용이 없는 것입니다.
그때는 6번으로 가면 됩니다.

누가 커밋했는지 확인:

```powershell
git log -1 --format=full
```

이 프로젝트에서 정상 예:

```
Author: seongbin45 <sungbin45@office365.kunsan.ac.kr>
```

---

## 6. GitHub에 푸시하기

푸시 = 내 PC 기록을 GitHub에 올리는 것입니다.

처음 한 번:

```powershell
git push -u origin main
```

이후부터는:

```powershell
git push
```

브라우저에서 확인:

https://github.com/seongbin45/CODYSSEY_6_ProJect

`index.html`, `api/generate.py`, `js/app.js` 가 보여야 합니다.
`.env` 가 보이면 실패한 것입니다. 즉시 키를 폐기하고 재발급합니다.

---

## 7. 막히면 보는 곳

| 메시지 | 의미 | 할 일 |
|---|---|---|
| `git: command not found` | Git 미설치 | Git 설치 후 터미널 다시 열기 |
| `Please tell me who you are` | 이름/이메일 없음 | 0-2번 다시 실행 |
| `failed to push some refs` | GitHub에 다른 커밋이 있음 | 아래 `git pull` 참고 |
| `Authentication failed` | GitHub 로그인 실패 | GitHub 로그인, 또는 Personal Access Token 사용 |
| `.env` 가 status에 보임 | 키가 커밋될 위험 | 3번으로 돌아가 중단 |

GitHub에 이미 다른 커밋이 있어서 푸시가 거절되면:

```powershell
git pull --rebase origin main
git push
```

---

## 8. 이 프로젝트에서 그대로 쓰는 최소 복사본

작성자 PC 기준, 위에서 필요한 줄만 모았습니다.

```powershell
git config --global user.name "seongbin45"
git config --global user.email "sungbin45@office365.kunsan.ac.kr"

cd C:\Users\seong\Downloads\CODYSSEY_6_ProJect

git check-ignore -v .env
git status --porcelain

git add .gitignore index.html css/style.css js/app.js api/generate.py requirements.txt env.example vercel.json README.md "기획서_되나요.md" "증빙자료" images/.gitkeep docs/git_초심자_명령어.md

git status
git commit -m "docs: add beginner git commit and push commands"
git push -u origin main
```

다른 초심자 최소 복사본:

```powershell
git config --global user.name "<깃허브아이디>"
git config --global user.email "<깃허브에등록한이메일>"

cd <프로젝트폴더경로>

git check-ignore -v .env
git status --porcelain

git add .gitignore index.html css/style.css js/app.js api/generate.py requirements.txt env.example vercel.json README.md

git status
git commit -m "feat: add my first working version"
git push -u origin main
```
