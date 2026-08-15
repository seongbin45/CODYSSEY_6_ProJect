# Anthropic Messages API

Anthropic Claude 모델의 모든 기능을 100% 활용할 수 있는 네이티브 엔드포인트입니다.

확장 사고(Extended Thinking), 프롬프트 캐싱, 비전, PDF 문서 분석 등 Anthropic 전용 기능이 필요한 경우 이 엔드포인트를 사용해주세요. 요청이 변환 없이 원시 바이트로 전달되어 모든 기능이 완벽하게 작동합니다.

<Indent mt={12} />

- 공식 레퍼런스: [Anthropic Messages API](https://docs.anthropic.com/en/api/messages) · [Streaming](https://docs.anthropic.com/en/api/messages-streaming)
- Anthropic SDK용 Base URL: `https://factchat-cloud.mindlogic.ai/v1/gateway/claude`

---

### 메시지 생성

<ParameterText badge="/v1/gateway/claude/v1/messages/">POST</ParameterText>

Anthropic 네이티브 API 형식으로 메시지를 생성합니다.

---

### 요청 헤더

```http
POST https://factchat-cloud.mindlogic.ai/v1/gateway/claude/v1/messages/
x-api-key: YOUR_API_KEY
anthropic-version: 2023-06-01
Content-Type: application/json
```

#### `anthropic-beta` 헤더

| 기능 | 헤더 값 |
| --- | --- |
| 프롬프트 캐싱 | `prompt-caching-2024-07-31` |
| 인터리브 사고 (수동 모드, Sonnet 4.6 전용) | `interleaved-thinking-2025-05-14` |
| 토큰 카운팅 | `token-counting-2024-11-01` |

<Banner variant="info">
  적응형 사고 (`thinking.type: "adaptive"`)는 베타 헤더가 필요 없으며 인터리브 사고가 자동으로 활성화됩니다.
</Banner>

---

### 파라미터

<ParameterText badge="string" required>model</ParameterText>
Anthropic 모델 이름 (`claude-opus-4-6`, `claude-sonnet-4-6`, `claude-haiku-4-5-20251001`).

<ParameterText badge="array" required>messages</ParameterText>
대화 기록. 각 메시지는 `role` (`"user"` 또는 `"assistant"`)과 `content` (문자열 또는 `ContentBlock[]`)로 구성됩니다.

<ParameterText badge="integer" required>max_tokens</ParameterText>
최대 출력 토큰.

<ParameterText badge="string | array">system</ParameterText>
시스템 프롬프트 (문자열 또는 캐싱용 `ContentBlock[]`).

<ParameterText badge="boolean">stream</ParameterText>
SSE 스트리밍 활성화.

<ParameterText badge="array">tools</ParameterText>
도구 정의.

<ParameterText badge="object">thinking</ParameterText>
사고 설정. 적응형 (Opus 4.6 / Sonnet 4.6 권장): `{"type": "adaptive"}`. 수동 (전체 모델): `{"type": "enabled", "budget_tokens": 10000}`.

<ParameterText badge="object">output_config</ParameterText>
적응형 사고의 노력 수준: `{"effort": "low" | "medium" | "high" | "max"}`. `"max"`는 Opus 4.6 전용.

<ParameterText badge="float">temperature</ParameterText>
샘플링 온도 0–1.

---

### 응답 (비스트리밍)

```json
{
  "id": "msg_abc123",
  "type": "message",
  "role": "assistant",
  "content": [
    {"type": "text", "text": "2+2 equals 4."}
  ],
  "model": "claude-sonnet-4-6",
  "stop_reason": "end_turn",
  "usage": {
    "input_tokens": 15,
    "output_tokens": 12,
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 0
  }
}
```

---

### Claude Code 빠른 시작

```bash
export ANTHROPIC_BASE_URL=https://factchat-cloud.mindlogic.ai/v1/gateway/claude
export ANTHROPIC_AUTH_TOKEN=YOUR_API_KEY
claude "What model are you?"
```

<Banner variant="warning">
  커스텀 Base URL을 설정할 때는 반드시 `ANTHROPIC_API_KEY`가 아닌 `ANTHROPIC_AUTH_TOKEN`을 사용하세요. 잘못 설정하면 401 인증 오류가 발생합니다.
</Banner>

---

### 적응형 사고 (권장)

적응형 사고를 사용하면 Claude가 요청의 복잡성에 따라 사고의 필요 여부와 깊이를 동적으로 결정합니다. 베타 헤더가 필요 없습니다.

```python
import anthropic

client = anthropic.Anthropic(
    api_key="YOUR_API_KEY",
    base_url="https://factchat-cloud.mindlogic.ai/v1/gateway/claude",
)

# 적응형 사고 — Claude가 사고 여부를 자동 결정
message = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=16000,
    thinking={"type": "adaptive"},
    messages=[{"role": "user", "content": "Solve this step by step: what is 127 * 389?"}],
)

for block in message.content:
    if block.type == "thinking":
        print("Thinking:", block.thinking[:200], "...")
    elif block.type == "text":
        print("Answer:", block.text)
```

effort 파라미터로 사고 깊이를 조절할 수 있습니다:

```python
# 낮은 effort — 빠른 응답, 간단한 사고
message = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=16000,
    thinking={"type": "adaptive"},
    output_config={"effort": "medium"},
    messages=[{"role": "user", "content": "What is the capital of France?"}],
)
```

| Effort | 동작 |
| --- | --- |
| `max` | 항상 사고, 깊이 제한 없음 (Opus 4.6 전용) |
| `high` (기본값) | 항상 사고, 심층 추론 |
| `medium` | 적절한 사고, 간단한 질문은 사고 생략 가능 |
| `low` | 최소한의 사고, 속도 우선 |

---

### 프롬프트 캐싱

```python
message = client.beta.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1000,
    system=[{
        "type": "text",
        "text": "You are an expert. Here is context:\n\n" + large_text,
        "cache_control": {"type": "ephemeral"},
    }],
    messages=[{"role": "user", "content": "Summarize the context."}],
    betas=["prompt-caching-2024-07-31"],
)
print(f"Cache created: {message.usage.cache_creation_input_tokens}")
print(f"Cache read:    {message.usage.cache_read_input_tokens}")
```

---

### 기능 호환성

Gateway를 통해 Anthropic의 모든 주요 기능을 제한 없이 사용할 수 있습니다. 아래 표에서 지원되는 기능을 확인해보세요.

| 기능 | 지원 | 비고 |
| --- | --- | --- |
| 스트리밍 | 지원 | 전체 SSE 패스스루 |
| 도구 사용 | 지원 | 변경 없이 전달 |
| 비전 (이미지) | 지원 | 변경 없이 전달 |
| PDF 문서 | 지원 | 변경 없이 전달 |
| 적응형 사고 | 지원 | Opus/Sonnet 4.6 권장. 베타 헤더 불필요 |
| 확장 사고 (수동) | 지원 | 전체 모델. Sonnet 4.6 인터리브 모드는 `anthropic-beta` 헤더 필요 |
| 프롬프트 캐싱 | 지원 | 캐시 토큰이 사용량에 추적됨 |
| 토큰 카운팅 | 지원 | `POST .../count_tokens/` 엔드포인트 |

---

### 제한 사항

- Anthropic 모델만 허용됩니다
- 비Anthropic 모델은 `/v1/gateway/chat/completions/`를 사용하세요