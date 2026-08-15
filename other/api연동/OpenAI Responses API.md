# OpenAI Responses API

OpenAI의 최신 Responses API를 지원하는 엔드포인트입니다.

o-시리즈 추론 모델, Codex 코드 생성 모델(`gpt-5.3-codex`, `gpt-5.2-codex`, `gpt-5.1-codex-max`) 등 Responses API 전용 모델을 사용하려면 이 엔드포인트를 이용해주세요. `reasoning_effort`와 `tools`를 동시에 사용해야 하는 경우에도 이 엔드포인트가 권장됩니다. 백그라운드 실행과 폴링을 통한 장시간 작업도 지원합니다.

<Indent mt={12} />

- 공식 레퍼런스: [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses)

<Banner variant="info">
  Responses API는 `messages` 대신 `input`을, `max_tokens` 대신 `max_output_tokens`를 사용합니다. OpenAI 모델만 지원됩니다.
</Banner>

---

### 응답 생성

<ParameterText badge="/v1/gateway/responses/">POST</ParameterText>

OpenAI Responses API 형식으로 응답을 생성합니다.

---

### 추가 엔드포인트

| Method | Path | 설명 |
| --- | --- | --- |
| GET | `/v1/gateway/responses/{id}/` | 백그라운드 응답 폴링 |
| POST | `/v1/gateway/responses/{id}/cancel/` | 백그라운드 응답 취소 |

---

### 파라미터

<ParameterText badge="string" required>model</ParameterText>
OpenAI 모델 이름.

<ParameterText badge="array" required>input</ParameterText>
입력 메시지 (`role` + `content`).

<ParameterText badge="string">instructions</ParameterText>
시스템 프롬프트 대체. `input` 전에 적용됩니다.

<ParameterText badge="integer">max_output_tokens</ParameterText>
최대 출력 토큰 (기본값: 4096).

<ParameterText badge="boolean">stream</ParameterText>
SSE 스트리밍 활성화.

<ParameterText badge="object">reasoning</ParameterText>
추론 설정: `{"effort": "low" | "medium" | "high", "summary": "auto" | "none"}`.

<ParameterText badge="object">text</ParameterText>
구조화된 출력을 위한 출력 형식 설정.

<ParameterText badge="boolean">background</ParameterText>
백그라운드 작업으로 실행 — 즉시 반환 후 폴링.

<ParameterText badge="string">previous_response_id</ParameterText>
다중 턴 대화를 위한 응답 체이닝.

---

### 응답 형식

```json
{
  "id": "resp_abc123",
  "object": "response",
  "created_at": 1720000000,
  "status": "completed",
  "model": "gpt-5.2",
  "output": [
    {
      "type": "message",
      "id": "msg_abc",
      "role": "assistant",
      "content": [
        {"type": "output_text", "text": "The answer is 42."}
      ]
    }
  ],
  "usage": {
    "input_tokens": 25,
    "output_tokens": 30,
    "output_tokens_details": {
      "reasoning_tokens": 512
    }
  }
}
```

---

### 사용 예제

```python
import httpx

BASE = "https://factchat-cloud.mindlogic.ai/v1/gateway"
HEADERS = {"Authorization": "Bearer YOUR_API_KEY", "Content-Type": "application/json"}

# 응답 생성
r = httpx.post(f"{BASE}/responses/", json={
    "model": "gpt-5.2-codex",
    "input": [{"role": "user", "content": "Analyze this dataset..."}],
}, headers=HEADERS, timeout=120.0)
data = r.json()

if data["status"] == "completed":
    print(data["output"][-1]["content"][0]["text"])
```

---

### 지원 모델

| 패밀리 | 예시 | 비고 |
| --- | --- | --- |
| Codex 시리즈 | `gpt-5.3-codex`, `gpt-5.2-codex`, `gpt-5.1-codex-max` | Responses API 전용 — Chat Completions에서 사용 시 404 반환 |
| GPT-5.4 시리즈 | `gpt-5.4`, `gpt-5.4-mini`, `gpt-5.4-nano` | Chat Completions로도 사용 가능. `reasoning_effort` + `tools` 동시 사용 시 이 엔드포인트 권장 |
| Standard | `gpt-5.2`, `gpt-5.1`, `gpt-5` | Chat Completions로도 사용 가능 |

---

### 제한 사항

- OpenAI 모델만 지원됩니다
- Anthropic 모델은 [Messages API](/docs/gateway/api-reference/messages-api)를 사용하세요
- Codex 모델(`gpt-5.2-codex`, `gpt-5.1-codex-max`)은 이 엔드포인트에서만 지원됩니다 — `/chat/completions/`에서 사용하면 404가 반환됩니다