# 전 연령 정책 데이터 API — 발급 방법과 엔드포인트

현재 연결: 온통청년 `getPlcy`, 정부24 공공서비스(혜택), 복지로 중앙부처·지자체.
**고용24와 워크넷은 연결하지 않았습니다.** 아래 3절에만 남겨 둡니다.

핵심: 정부24·복지로·고용24는 사이트에서 직접 API를 열지 않습니다. 대신 각 소관 기관이
**공공데이터포털(data.go.kr)** 에 오픈API로 올려둔 것을 신청해서 씁니다.

---

## 0. 무엇을 먼저 붙일지

| 우선순위 | API | 커버 범위 | 키 발급처 |
|---|---|---|---|
| ★1 | 행정안전부_대한민국 공공서비스(혜택) 정보 (보조금24 계열) | 전 부처·지자체·공공기관·교육청 수혜서비스 = **전 연령** | data.go.kr |
| ★2 | 한국사회보장정보원_중앙부처복지서비스 | 전국민 대상 중앙부처 복지사업 | data.go.kr |
| ★3 | 한국사회보장정보원_지자체복지서비스 | 시·도/시·군·구 복지서비스 | data.go.kr |
| 4 | 온통청년 `getPlcy` (기존) | 19~39 청년정책 | 온통청년 마이페이지 |
| — | 고용24 · 워크넷 채용정보 | **미연결.** 구현하지 않음. 기록만 남김 | data.go.kr / 고용24 자체 인증 |

1~3만 붙이면 청소년·중장년·노년·임신출산·장애·소상공인이 모두 채워집니다. 청년(4)은 이미 동작하니 그대로 두고 소스만 추가하면 됩니다.

---

## 1. 공공데이터포털 인증키 발급 (1~3, 5 공통)

1. https://www.data.go.kr 회원가입 후 로그인
2. 아래 데이터 상세 페이지로 이동 → 우측 상단 **활용신청**
3. 활용목적(학습·개인 프로젝트) 입력, 이용허락범위 **동의** 체크 → 활용신청
4. 마이페이지 → 데이터활용 → **Open API → 활용신청 현황 / 인증키 발급 현황** 에서 상태 확인
5. 발급된 `serviceKey`(일반 인증키)를 `.env` 및 Vercel 환경변수에 저장

<!-- 참고: 자동승인 API는 신청 직후, 심사 대상은 승인 후 키가 활성화됩니다. 활성화까지 1~2시간 걸리는 경우가 있습니다. -->

### 신청할 데이터 페이지

| 이름 | 신청 URL |
|---|---|
| 행정안전부_대한민국 공공서비스(혜택) 정보 | https://www.data.go.kr/data/15113968/openapi.do |
| 한국사회보장정보원_중앙부처복지서비스 | https://www.data.go.kr/data/15090532/openapi.do |
| 한국사회보장정보원_지자체복지서비스 | https://www.data.go.kr/data/15108347/openapi.do |
| 한국고용정보원_온통청년_청년정책API (포털 경유용) | https://www.data.go.kr/data/15143273/openapi.do |
| 한국고용정보원_워크넷 채용정보 | https://www.data.go.kr/data/3038225/openapi.do |

각 페이지에 **Swagger 문서와 활용가이드·코드표**가 첨부되어 있습니다. 요청 파라미터명과 코드값은
반드시 그 문서를 기준으로 맞추세요(포털 API는 오퍼레이션별로 파라미터가 다릅니다).

- 복지서비스 계열은 오퍼레이션이 **목록조회 / 상세조회 2개**입니다. 목록으로 카드용 데이터를 받고,
  상세에서 지원대상·선정기준·신청방법을 받아 판정에 씁니다. 지금 `policies.py`의 `list` / `detail` 구조와 같습니다.
- 호출 형식은 `?serviceKey=<발급키>&…&type=json` 형태의 REST GET, 응답은 JSON 또는 XML입니다.

### 키 없이 먼저 개발하고 싶다면

`한국사회보장정보원_복지서비스정보` 파일데이터(https://www.data.go.kr/data/15083323/fileData.do)는
로그인·키 없이 CSV로 내려받을 수 있습니다. 중앙부처 복지사업 목록(서비스ID·서비스명·요약·소관부처·URL)이라
**시드 데이터/로컬 목업**으로 쓰기 좋습니다. 승인 대기 중 화면 개발은 이걸로 진행하세요.

---

## 2. 온통청년 (이미 쓰는 키)

- 발급: https://www.youthcenter.go.kr/myPage/openapi — 로그인 → 마이페이지 → OPEN API → 신청 → **담당자 심사 후 승인**
- 이용 안내: https://www.youthcenter.go.kr/cmnFooter/openapiIntro/oaiGuide
- 제공 목록: https://www.youthcenter.go.kr/cmnFooter/openapiIntro/oaiDoc
- 엔드포인트(현행 코드와 동일):
  - `GET https://www.youthcenter.go.kr/go/ythip/getPlcy` — 정책 (인증 파라미터 `apiKeyNm`)
  - `GET https://www.youthcenter.go.kr/go/ythip/getSpace` — 청년공간
  - `GET https://www.youthcenter.go.kr/go/ythip/getContent` — 콘텐츠 (응답이 커서 목록용으로는 비권장)
- 목록은 요청마다 1페이지를 치지 않습니다. 군산 대시보드와 같이 `pageSize=100`으로 끝까지 받아
  `data/youth_policy_snapshot.json`에 두고, `/api/policies`는 그 스냅샷을 나이·지역으로 거릅니다.
  갱신: `py -3 scripts/sync_youth.py` 또는 `/api/policies?sync=1` (로컬·배치용).
- 구 엔드포인트(`/opi/youthPlcyList.do`, 인증 파라미터 `openApiVlak`)는 문서에 남아 있으나 신규 개발은 `go/ythip` 계열을 쓰세요.

---

## 3. 고용24 · 워크넷 — 연결하지 않음

이 프로젝트는 고용24와 워크넷 API를 **붙이지 않습니다.** 화면의 고용24는 이동 링크만 있습니다.

나중에 보강할 때 참고할 위치만 적습니다.

- data.go.kr 경유: 한국고용정보원_워크넷 채용정보. 근무지역·직종·연령 우대조건으로 고령자·여성 일자리를 뽑을 수 있습니다.
  https://www.data.go.kr/data/3038225/openapi.do
- 기관 자체 인증: https://www.work24.go.kr/cm/e/a/0110/selectOpenApiIntro.do
- 훈련과정(내일배움카드)은 HRD-Net 계열을 따로 신청해야 합니다.

## 4. 정부24 · 복지로에 대한 정리

- 정부24는 자체 API 대신 https://www.gov.kr/openapi 에서 **"공공데이터포털에서 신청하라"** 고 안내합니다.
  포털에 올라온 정부24 데이터 상당수는 통계(발급건수 등)라 정책 목록으로는 쓸 수 없습니다.
  정책 목록용은 위 ★1 행정안전부 공공서비스(혜택) 정보입니다.
- 복지로 데이터는 **한국사회보장정보원** 이름으로 포털에 올라옵니다(★2, ★3). 복지로 사이트에는 개발자용 키 발급이 없습니다.

---

## 5. 서버 확장 제안 (`api/policies.py`)

지금 구조(`SOURCE_META` → `list_catalog` → `summarize` / `flatten`)를 그대로 확장할 수 있습니다.

```python
SOURCE_META = {
    "policy":  {"url": POLICY_URL,   "key": "YOUTH_API_KEY",       "label": "청년정책"},
    "benefit": {"url": BENEFIT_URL,  "key": "GOV_BENEFIT_API_KEY", "label": "공공서비스"},   # ★1
    "welfare": {"url": WELFARE_URL,  "key": "WELFARE_API_KEY",     "label": "중앙부처 복지"}, # ★2
    "local":   {"url": LOCAL_URL,    "key": "WELFARE_API_KEY",     "label": "지자체 복지"},   # ★3
    "space":   {"url": SPACE_URL,    "key": "YOUTH_CENTER_API_KEY","label": "청년공간"},
}
```

- 포털 API는 인증 파라미터가 `serviceKey`입니다. `youth_get()`의 인증 분기에
  `"apis.data.go.kr" in endpoint → params["serviceKey"] = key` 한 줄을 추가하면 됩니다.
- `summarize()`에 소스별 필드 매핑을 하나씩 더합니다(서비스명/지원대상/소관부처/신청URL).
- 화면의 8개 답변(나이·지역·가구·소득·상태·혼인자녀·장애·관심분야) → API 파라미터 대응은
  복지서비스 계열의 **생애주기·가구유형·관심주제 코드표**가 거의 1:1로 맞습니다. 첨부된 코드표를 그대로 상수로 옮기세요.
- 온통청년에서 확인된 것과 같은 문제(목록 API가 나이·지역 쿼리를 무시)를 대비해,
  현재의 **응답 기준 재필터**(`age_ok`, `region_ok`) 구조는 유지하는 편이 안전합니다.

### 환경변수 추가

```
GOV_BENEFIT_API_KEY=      # 행정안전부 공공서비스(혜택) 정보
WELFARE_API_KEY=          # 한국사회보장정보원 중앙부처/지자체 복지서비스
# WORKNET_API_KEY 는 쓰지 않음. 고용24·워크넷 미연결.
```

Vercel > Settings > Environment Variables 에 Production/Preview/Development 모두 체크 후 **Redeploy** 해야 반영됩니다.
