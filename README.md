# 되나요 (Doenayo)

> 청년 정책 공고문을 붙여넣으면, **대상 여부부터** 확인해 주는 웹 서비스

🔗 **배포 URL:** `https://<배포후-기입>.vercel.app`  
🔗 **GitHub:** https://github.com/seongbin45/CODYSSEY_6_ProJect

<!-- TODO: images/screenshot.png 추가 후 아래 주석 해제 -->
<!-- ![되나요 메인 화면](images/screenshot.png) -->

---

## 1. 서비스 소개

### 왜 만들었나

청년 정책 공고문은 정보가 없어서가 아니라 **읽히지 않아서** 신청으로 이어지지 않습니다.

- 지원 자격이 `~에 해당하는 자로서, 다만 ~인 경우는 제외한다` 형태의 중첩 조건문으로 서술됩니다
- 정작 사용자가 알고 싶은 **"내가 대상인가"** 는 공고문 어디에도 한 줄로 적혀 있지 않습니다
- 제출 서류는 본문과 별첨에 흩어져 있어, 마감 직전에야 누락을 발견합니다
- 실제 군산·전북 청년정책 공고를 조사한 결과, **상세 내용이 HWP 첨부파일에만 있고 웹 본문은 요약뿐인 경우**가 많았습니다

결과적으로 **"읽다가 포기"** 가 발생하고, 자격이 되는데도 신청하지 않는 사람이 생깁니다.

### 무엇을 하나

공고문 텍스트를 붙여넣으면 AI가 **4가지 블록**으로 정리합니다.

| 블록 | 내용 |
|---|---|
| ① 한눈에 보기 | 3줄 요약 |
| ② 내가 대상인지 확인하기 | 자격 조건을 O/X 단위로 분해한 **체크리스트** |
| ③ 준비할 서류 | 본문·별첨에 흩어진 서류를 한 목록으로 |
| ④ 신청 기한 | 기한 + 어려운 용어 풀이 |

### 하지 않는 것

- **자격 여부를 판정하지 않습니다.** AI는 사용자의 나이·소득·거주지를 모릅니다. 조건을 분해해 줄 뿐, 최종 판단은 사용자가 합니다
- **원문에 없는 내용을 만들지 않습니다.** 확인할 수 없는 항목은 "공고문에 명시되지 않음"으로 표시합니다
- **정책을 검색해 주지 않습니다.** 이미 찾은 공고문을 *읽어주는* 서비스입니다

### 타겟 사용자

정책 지원을 받아본 적 없는 **20대 초·중반 대학생 / 사회초년생 / 구직자**

---

## 2. 주요 기능

| 섹션 | 기능 |
|---|---|
| 홈 (`#home`) | 문제 제기, 3단계 사용법, 확인하기로 바로 이동 |
| **확인하기 (`#check`)** | 공고문 입력 → AI 변환 → 4블록 결과 · 샘플 공고문 체험 · 글자수 카운터 |
| 이용 안내 (`#guide`) | 사용법, **AI 요약의 한계 고지**, 자주 나오는 용어 풀이, 공식 출처 링크 |

---

## 3. 기술 스택

| 구분 | 기술 | 비고 |
|---|---|---|
| 프론트엔드 | HTML5, CSS3, Vanilla JavaScript | **프레임워크 미사용** |
| 백엔드 | Vercel Serverless Functions (Python) | `http.server.BaseHTTPRequestHandler` |
| AI | Google Gemini | `google-genai` SDK |
| 배포 | Vercel | GitHub 연동 자동 배포 |
| 형상 관리 | Git / GitHub | |

---

## 4. 프로젝트 구조

```
doenayo/
├── index.html          # 3개 섹션 전체 (홈 / 확인하기 / 이용 안내)
├── css/style.css       # CSS 변수 기반 스타일, 모바일 우선
├── js/app.js           # 입력 검증, fetch, 상태 전환, 결과 렌더링
├── api/generate.py     # 서버리스 함수 → POST /api/generate
├── images/             # 로고, 스크린샷
├── 증빙자료/            # 스크린샷·대화 로그
├── requirements.txt    # google-genai 한 줄만
├── env.example         # 변수명만 (값 없음). 로컬에서는 .env 로 복사
├── vercel.json         # framework preset 오인 방지
├── .gitignore          # .env 포함
└── README.md
```

---

## 5. 동작 흐름

```
[브라우저]  공고문 붙여넣기 → [결과 확인하기]
    │  ① 클라이언트 검증 (빈 값 / 10자 미만 / 2,000자 초과)
    │  ② loading 상태 전환, 버튼 비활성화 (연타 방지)
    │  ③ fetch('/api/generate', POST) + AbortController 25초
    ▼
[Vercel Serverless Function]  api/generate.py
    │  ④ 요청 파싱 및 서버 재검증
    │  ⑤ os.environ["GEMINI_API_KEY"] 확인   ← 키는 서버에만 존재
    │  ⑥ Gemini 호출 (system_instruction으로 JSON 출력 지시)
    │  ⑦ 응답 JSON 파싱 + 필드 정규화
    ▼
[Gemini API]
    │
    ▼ (역방향)
[브라우저]  ⑧ success / error 상태 전환 → ⑨ 4블록 렌더링
```

### 왜 프론트에서 AI를 직접 호출하지 않는가

프론트엔드 코드는 브라우저에 전부 내려갑니다. API 키를 JavaScript에 두면 개발자도구의 소스 탭이나 Network 탭에서 그대로 노출되어, 제3자가 내 쿼터를 소진시킬 수 있습니다.

서버리스 함수를 경유하면 키는 **서버 환경변수에만** 존재하고, 브라우저는 `/api/generate` 라는 내 도메인 경로만 알게 됩니다. 같은 오리진이므로 CORS 설정도 필요 없습니다.

---

## 6. 로컬 실행 방법

```bash
git clone https://github.com/<사용자명>/doenayo.git
cd doenayo

# Vercel CLI 설치 (api/ 함수를 로컬에서 실행하기 위해 필요)
npm i -g vercel
vercel login

# 환경변수 설정 (7번 참고)
copy env.example .env
# .env 를 열어 GEMINI_API_KEY 값을 채웁니다

vercel dev
# → http://localhost:3000
```

> ⚠️ `python -m http.server` 나 VS Code Live Server 로는 **`api/` 함수가 동작하지 않습니다.**
> 정적 파일만 서빙되어 `/api/generate` 요청이 404가 납니다. 반드시 `vercel dev` 를 사용하세요.

---

## 7. 환경 변수 설정

| 변수명 | 설명 | 발급처 |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini API 인증 키 | https://aistudio.google.com/apikey |
| `GEMINI_MODEL` | (선택) 사용할 모델명. 없으면 `gemini-2.5-flash` 부터 자동으로 내림 | AI Studio |

### 로컬

프로젝트 루트에 `.env` 파일을 만듭니다.

```
GEMINI_API_KEY=your_key_here
```

### 배포 (Vercel)

1. Vercel 프로젝트 > **Settings** > **Environment Variables**
2. Name `GEMINI_API_KEY`, Value 에 발급받은 키 입력
3. **Production / Preview / Development 를 모두 체크**
4. 저장 후 **Deployments 탭에서 Redeploy** (환경변수는 재배포해야 반영됩니다)

### 보안 주의사항

- `.env` 는 `.gitignore` 에 포함되어 저장소에 커밋되지 않습니다
- 키를 코드에 하드코딩하면 브라우저와 저장소 양쪽에 노출됩니다. 절대 금지입니다
- **키가 커밋된 경우**: ①먼저 AI Studio에서 해당 키를 폐기하고 재발급 → Vercel 환경변수 교체 → Redeploy ②그 다음 커밋 이력 정리 (`git rm --cached` 로는 히스토리가 지워지지 않습니다)

커밋 이력 점검:
```bash
git log -p | grep -iE "AIza|api[_-]?key\s*=\s*['\"][A-Za-z0-9_-]{20,}"
```

---

## 8. 배포 방법

1. GitHub 저장소에 push
2. [vercel.com/new](https://vercel.com/new) → 저장소 Import
3. **Framework Preset: `Other`** 선택 ← 다른 값으로 잡히면 반드시 변경
4. Root Directory: `./`
5. Environment Variables 에 `GEMINI_API_KEY` 등록 (7번 참고)
6. Deploy
7. 이후 `main` 브랜치에 push 하면 자동 재배포

> ⚠️ `requirements.txt` 에 `flask` / `fastapi` 등을 추가하면 Vercel이 **Python framework preset** 으로 전환되어, `api/` 폴더의 파일 기반 함수가 전부 무효화되고 `index.html` 이 서빙되지 않습니다. 이 프로젝트의 `requirements.txt` 는 `google-genai` **한 줄만** 유지해야 합니다.

---

## 9. AI 기능 명세

### `POST /api/generate`

**요청**
```json
{ "input": "공고문 텍스트 (10자 이상 2,000자 이하)" }
```

**성공 응답 `200`**
```json
{
  "result": {
    "is_policy": true,
    "title": "2026 군산 청년 서포터즈 2기 참여자 모집",
    "summary": ["...", "...", "..."],
    "eligibility": [{ "item": "군산시에 주소를 둔 청년", "note": "18세 이상 39세 이하" }],
    "documents": ["참여신청서", "주민등록초본", "개인정보동의서"],
    "deadline": "2026. 6. 3.(수) ~ 6. 25.(목)",
    "terms": [{ "word": "기타소득", "meaning": "..." }]
  }
}
```

**실패 응답**

| 상황 | 코드 | 메시지 |
|---|---|---|
| 빈 입력 | `400` | 공고문 내용을 붙여넣어 주세요. |
| 10자 미만 | `400` | 내용이 너무 짧습니다. 지원 자격이나 서류 부분을 함께 붙여넣어 주세요. |
| 2,000자 초과 | `400` | 2,000자까지 입력할 수 있습니다. |
| 환경변수 누락 | `500` | 서비스 점검 중입니다. 잠시 후 다시 시도해 주세요. |
| AI 호출 실패 | `502` | 결과를 가져오지 못했습니다. 잠시 후 다시 시도해 주세요. |
| 응답 파싱 실패 | `502` | 결과를 정리하지 못했습니다. 내용을 조금 줄여서 다시 시도해 주세요. |

**클라이언트 측 처리**

| 상황 | 처리 | 메시지 |
|---|---|---|
| 25초 초과 | `AbortController` 로 중단 | 응답이 지연되고 있습니다. 잠시 후 다시 시도해 주세요. |
| 네트워크 단절 | `fetch` 의 `TypeError` 포착 | 네트워크 연결을 확인해 주세요. |
| 공고문 아님 | `is_policy: false` | 정책 공고문으로 보이지 않습니다. |

### 환각 방지 설계

정책 정보에서 없는 내용을 지어내면 사용자가 잘못된 서류를 준비하거나 마감을 놓칩니다. `SYSTEM_PROMPT` 에서 다음을 강제합니다.

1. 입력 텍스트에 실제로 적혀 있는 내용만 사용
2. 원문에 없으면 `"공고문에 명시되지 않음"` 으로 처리
3. 다른 정책 지식이나 일반 상식으로 빈칸을 메우지 않음
4. 자격 여부를 단정하지 않음

또한 AI 응답을 **신뢰할 수 없는 입력으로 취급**합니다.
- 서버: `normalize()` 로 필드 누락에 대비한 기본값 처리
- 클라이언트: `esc()` 로 HTML 이스케이프 (XSS 방어)

---

## 10. 트러블슈팅 기록

> 작업 중 실제로 겪은 문제를 여기에 기록합니다. (증상 / 원인 / 해결)

### 10-1. Flask를 넣으면 사이트가 통째로 안 뜬다

**증상**
배포 후 `index.html` 이 뜨지 않거나 `/api/generate` 가 함수로 안 잡힘

**원인**
`requirements.txt` 에 `flask` / `fastapi` 가 있으면 Vercel이 Python framework preset으로 전환한다. 이때 `api/` 파일 기반 함수는 전부 무효화된다.

**해결**
`requirements.txt` 는 `google-genai` 한 줄만 유지한다. `vercel.json` 에 `"framework": null` 을 두어 같은 오인을 한 번 더 막는다.

**배운 것**
이 과제의 백엔드는 “파이썬 웹 프레임워크”가 아니라 **파일 하나가 곧 엔드포인트인 서버리스 함수**다.

### 10-2. 구버전 Gemini SDK 코드는 그대로 쓰면 안 된다

**증상**
`genai.configure is not a function` 또는 `GenerativeModel` import 실패

**원인**
학습 데이터에 남은 `google-generativeai` 코드와 현재 `google-genai` API가 다르다.

**해결**
`from google import genai` → `client = genai.Client()` 를 쓴다. 키는 코드에 넣지 않고 `GEMINI_API_KEY` 환경변수만 읽는다. Interactions API가 없는 런타임을 대비해 `generate_content` 로 내린다.

### 10-3. 빈 입력 안내 뒤에 이전 결과가 남았다

**증상**
한 번 성공한 뒤 빈 값으로 다시 제출하면, 안내 문구와 이전 4블록이 같이 보임

**원인**
클라이언트 검증은 `notice` 만 바꾸고 `result` 를 비우지 않았다.

**해결**
`showError()` 에서 결과 영역을 함께 지운다. `is_policy: false` 일 때도 같다.

---

## 11. 참고 자료

- [Vercel — Python Functions in the /api Directory](https://vercel.com/docs/functions/runtimes/python/api-directory)
- [Vercel — Functions Limits](https://vercel.com/docs/functions/limitations)
- [Gemini API — Text Generation](https://ai.google.dev/gemini-api/docs/text-generation)
- [군산시 청년정책 포털](https://gsyouth.or.kr/main/m116/)

> 샘플 공고문은 군산시 청년정책 포털에 게시된 「2026 군산 청년 서포터즈 2기 참여자 모집」 공고를 발췌한 것입니다.

---

## 12. 만든 사람

최성빈 · 학습 목적 프로젝트 (AI 웹 개발 미션)
