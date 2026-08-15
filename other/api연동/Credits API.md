# Credits API

API 키에 연결된 계정의 크레딧 잔액을 조회합니다.

월별 할당 크레딧, 충전 크레딧, 전체 합계를 확인할 수 있어 외부 도구(Obsidian, OpenClaw 등)에서 사용량을 모니터링할 수 있습니다.

<Indent mt={12} />

---

### 크레딧 잔액 조회

<ParameterText badge="/v1/gateway/credits/">GET</ParameterText>

인증된 사용자의 크레딧 잔액 정보를 반환합니다. 별도의 파라미터 없이 API 키만으로 조회할 수 있습니다.

---

### 요청 헤더

```http
GET https://factchat-cloud.mindlogic.ai/v1/gateway/credits/
Authorization: Bearer YOUR_API_KEY
```

---

### 파라미터

파라미터 없음. API 키로 사용자를 자동 식별합니다.

---

### 응답

<ParameterText badge="string">object</ParameterText>
항상 `"credit_balance"`.

<ParameterText badge="object">monthly_allocated</ParameterText>
월별 할당 크레딧 정보.

<ChildAttributes>

<ParameterText badge="float">quota</ParameterText>
월별 할당량.

<ParameterText badge="float">used</ParameterText>
이번 달 사용량.

<ParameterText badge="float">remaining</ParameterText>
남은 크레딧 (`quota - used`).

<ParameterText badge="string | null">renewal_date</ParameterText>
다음 갱신일 (ISO 8601). 매월 1일에 리셋됩니다.

</ChildAttributes>

<ParameterText badge="object">purchased</ParameterText>
충전(구매) 크레딧 정보.

<ChildAttributes>

<ParameterText badge="float">quota</ParameterText>
총 충전 크레딧.

<ParameterText badge="float">used</ParameterText>
사용한 충전 크레딧.

<ParameterText badge="float">remaining</ParameterText>
남은 충전 크레딧.

</ChildAttributes>

<ParameterText badge="object">total</ParameterText>
전체 합계 (월별 + 충전).

<ChildAttributes>

<ParameterText badge="float">quota</ParameterText>
전체 할당량.

<ParameterText badge="float">used</ParameterText>
전체 사용량.

<ParameterText badge="float">remaining</ParameterText>
전체 남은 크레딧.

</ChildAttributes>

---

### 응답 예시

```json
{
  "object": "credit_balance",
  "monthly_allocated": {
    "quota": 20000,
    "used": 1523.45,
    "remaining": 18476.55,
    "renewal_date": "2026-05-01T00:00:00+09:00"
  },
  "purchased": {
    "quota": 5000,
    "used": 200.0,
    "remaining": 4800.0
  },
  "total": {
    "quota": 25000,
    "used": 1723.45,
    "remaining": 23276.55
  }
}
```

---

### 코드 예제

#### Python

```python
import requests

response = requests.get(
    "https://factchat-cloud.mindlogic.ai/v1/gateway/credits/",
    headers={"Authorization": "Bearer YOUR_API_KEY"},
)
balance = response.json()
print(f"남은 크레딧: {balance['total']['remaining']}")
```

#### curl

```bash
curl https://factchat-cloud.mindlogic.ai/v1/gateway/credits/ \
  -H "Authorization: Bearer YOUR_API_KEY"
```

---

### 다음 단계

- [인증 가이드](/docs/gateway/getting-started/authentication) — API 키 발급 방법
- [모델 목록](/docs/gateway/getting-started/models) — 사용 가능한 모델 확인
- [에러 가이드](/docs/gateway/reference/errors) — 문제 발생 시 참고