# AI 코딩 도구 사용 과정

작업일: 2026-03-26  
도구: Cursor 대화형 코딩 도구  
목적: 과제 목표 6번 — 코드를 생성하더라도 오류 원인을 파악하고 수정 방향을 설명할 수 있는지 남긴다.

---

## 1. 초기 판단

과제 원문과 기존 기획 문서를 대조했다.

- 제출 패키지 5종: 배포 URL / GitHub / README / 기획서 / 증빙
- 개발 환경: 순수 HTML/CSS/JS + Vercel `api/` Python
- 기존 zip·저장소는 Streamlit/React/Flutter라 재사용 불가
- 코드가 없고 문서만 있는 상태였으므로, 화면을 예쁘게 만들기 전에 `index.html` + `api/generate.py` 골격을 먼저 만들었다

## 2. AI 제안을 거부한 지점

### Flask / FastAPI를 넣지 않은 이유

파이썬 백엔드를 만들면 흔히 Flask를 권한다. 이 프로젝트에서는 거부했다.

Vercel은 `requirements.txt`에서 Flask/FastAPI를 감지하면 framework preset으로 전환한다. 그 순간 `api/` 파일 기반 함수가 무효화되고 `index.html`이 404가 된다.

그래서 `requirements.txt`는 `google-genai` 한 줄만 유지했다. `vercel.json`의 `"framework": null`은 같은 오인을 한 번 더 막는 장치다.

### 구버전 Gemini SDK를 쓰지 않은 이유

학습 데이터에는 아래 코드가 많이 남아 있다.

- `google-generativeai`
- `genai.configure()`
- `GenerativeModel("gemini-pro")`
- `response.text`

현재 패키지는 `google-genai`이고, 키는 `GEMINI_API_KEY` 환경변수로 `genai.Client()`가 읽는다. 키를 JS에 넣지 않은 이유도 같다. 프론트 코드는 브라우저에 내려가므로 키가 그대로 노출된다.

다만 배포 런타임의 SDK 버전이 Interactions API를 아직 안 가질 수 있다. 그래서 `interactions.create()`를 우선 시도하고, 실패하면 `models.generate_content()`로 내리도록 바꿨다. 가이드를 따르되, 버전 차이 하나로 서비스 전체가 502가 나면 안 되기 때문이다.

## 3. 교차검증에서 고친 것

| 증상 | 원인 | 수정 |
|---|---|---|
| 데스크톱 메뉴가 테마 버튼 오른쪽에 붙음 | HTML에서 버튼이 링크보다 앞에 있음 | 로고 → 메뉴 → 버튼 순서로 바꿈 |
| 빈 입력 후에도 이전 결과가 남음 | 검증 실패 시 `result`를 비우지 않음 | `showError()`에서 결과 영역을 같이 지움 |
| 공고문 아님 판정 후에도 이전 4블록이 보임 | `is_policy: false`일 때 결과 HTML을 안 지움 | 렌더 시작 시 결과 영역을 비움 |
| AI가 배열을 빼먹으면 화면이 멈춤 | `r.summary.map` 등을 그대로 호출 | 배열이 아니면 빈 배열로 보고 그림 |
| `.env.example`을 만들 수 없음 | 도구가 비밀 파일로 차단 | 값이 없는 `env.example`로 대체 |

## 4. 아직 사람이 해야 하는 것

코드만으로는 배포 URL이 생기지 않는다.

1. 프로젝트 루트 `.env`에 `GEMINI_API_KEY` 넣기
2. GitHub `main`에 푸시
3. Vercel Import, Framework Preset `Other`, 환경변수 등록 후 Deploy
4. 배포 URL에서 샘플 공고문 / 빈 입력 / 무관한 텍스트를 확인
5. 주소창이 보이게 스크린샷 촬영

로컬에서 `python -m http.server`만 켜면 `/api/generate`는 404다. `api/`는 Vercel 함수이므로 `vercel dev` 또는 실제 배포 URL에서만 동작한다.
