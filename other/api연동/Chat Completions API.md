# Chat Completions API

가장 범용적인 텍스트 생성 엔드포인트입니다.

OpenAI, Anthropic, Google Gemini, xAI 등 대부분의 모델을 이 하나의 엔드포인트로 사용할 수 있으며, OpenAI SDK와 100% 호환됩니다. 기존 OpenAI 코드의 Base URL만 변경하면 바로 시작할 수 있습니다.

<Indent mt={12} />

- 공식 레퍼런스: [OpenAI Chat Completions API](https://platform.openai.com/docs/api-reference/chat)

---

### Chat Completions

<ParameterText badge="/v1/gateway/chat/completions/">POST</ParameterText>

채팅 완성을 생성합니다. 게이트웨이는 OpenAI Chat API와 동일한 요청/응답 스키마를 구현합니다.

---

### 요청 헤더

```http
POST https://factchat-cloud.mindlogic.ai/v1/gateway/chat/completions/
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

---

### 파라미터

#### 핵심

<ParameterText badge="string" required>model</ParameterText>
`GET /v1/gateway/models/`에서 확인 가능한 모델 이름.

<ParameterText badge="array" required>messages</ParameterText>
대화 기록 (role + content).

<ChildAttributes>

<ParameterText badge="object">System / Developer message</ParameterText>
모델이 따라야 하는 지침.
<Indent>
  <ParameterText badge="string" required>role</ParameterText>
  `"system"` 또는 `"developer"`

  <ParameterText badge="string | array" required>content</ParameterText>
  지침 내용
</Indent>

<ParameterText badge="object">User message</ParameterText>
사용자 입력.
<Indent>
  <ParameterText badge="string" required>role</ParameterText>
  `"user"`

  <ParameterText badge="string | array" required>content</ParameterText>
  사용자 입력 내용
</Indent>

<ParameterText badge="object">Assistant message</ParameterText>
모델이 생성한 응답.
<Indent>
  <ParameterText badge="string" required>role</ParameterText>
  `"assistant"`

  <ParameterText badge="string | array" required>content</ParameterText>
  생성된 응답
</Indent>

</ChildAttributes>

<ParameterText badge="boolean">stream</ParameterText>
SSE 스트리밍 활성화 (기본값: `false`).

<ParameterText badge="object">stream_options</ParameterText>
`{"include_usage": true}` — 마지막 스트림 청크에 사용량 포함.

---

#### 샘플링

<ParameterText badge="float">temperature</ParameterText>
무작위성 0–2. 낮을수록 더 결정적. 기본값: `1.0`.

<Banner variant="info">
  일부 OpenAI 모델(`gpt-5`, `gpt-5-mini`, `gpt-5.1-chat-latest`, `gpt-5.2-chat-latest`)은 `temperature: 1`만 지원합니다. 다른 값을 설정하면 400 에러가 반환됩니다.
</Banner>

<ParameterText badge="float">top_p</ParameterText>
핵 샘플링 임계값. 기본값: `1.0`.

<ParameterText badge="integer">top_k</ParameterText>
Top-k 샘플링 (Anthropic OpenAI 호환 전용).

---

#### 출력 제한

<ParameterText badge="integer">max_tokens</ParameterText>
최대 출력 토큰. 최신 모델에서는 `max_completion_tokens`로 자동 변환됩니다.

<Banner variant="info">
  추론 모델(GPT-5 시리즈, Gemini 2.5 Pro)은 내부 추론 토큰이 `max_tokens` 예산에 포함됩니다. 너무 낮게 설정하면(예: 4096 미만) 빈 응답이 반환될 수 있습니다. 추론이 필요한 작업에는 최소 `16000` 이상 사용하세요.
</Banner>

<ParameterText badge="integer">max_completion_tokens</ParameterText>
직접 별칭; o-시리즈 / gpt-5+ 모델에 사용.

<ParameterText badge="string | array">stop</ParameterText>
최대 4개의 중단 시퀀스.

---

#### 도구 호출

<ParameterText badge="array">tools</ParameterText>
도구 정의 목록 (`type: "function"`).

<ParameterText badge="string | object">tool_choice</ParameterText>
`"auto"`, `"none"`, `"required"`, 또는 `{"type":"function","function":{"name":"..."}}`.

---

#### 구조화된 출력

<ParameterText badge="object">response_format</ParameterText>
`{"type": "json_schema", "json_schema": {"name": "...", "strict": true, "schema": {...}}}`. `strict: true`와 `additionalProperties: false`가 포함된 유효한 JSON Schema가 필요합니다.

---

#### 추론 / 사고

<ParameterText badge="string">reasoning_effort</ParameterText>
`"low"` / `"medium"` / `"high"` — OpenAI o-시리즈 및 gpt-5+.

<ParameterText badge="integer">thinking_budget</ParameterText>
최대 사고 토큰 (0–8192, 또는 동적의 경우 `-1`). Gemini 2.5 시리즈 전용.

<ParameterText badge="string">thinking_level</ParameterText>
Gemini 3.0 시리즈 전용. Flash: `"minimal"`/`"low"`/`"medium"`/`"high"`. Pro: `"low"`/`"high"`.

<Banner variant="warning">
  `thinking_budget`과 `thinking_level`은 상호 배타적입니다. 두 파라미터를 동시에 사용하면 에러가 발생할 수 있으니 주의해주세요.
</Banner>

<Banner variant="info">
  일부 모델에서 `reasoning_effort`와 `tools`를 동시에 사용하면 400 에러가 발생할 수 있습니다 (GPT-5.4 시리즈, chat 모델, Grok 4 등). 게이트웨이는 이 경우 자동으로 `reasoning_effort`를 제거하고 재시도하므로, 별도 처리 없이 안정적으로 사용할 수 있습니다.
</Banner>

---

### 지원 제공업체

| 제공업체 | 예시 모델 |
| --- | --- |
| OpenAI | `gpt-5.4`, `gpt-5.4-mini`, `gpt-5.4-nano`, `gpt-5.2`, `gpt-5.1` |
| Anthropic | `claude-opus-4-6`, `claude-sonnet-4-6`, `claude-haiku-4-5-20251001` |
| Google Gemini | `gemini-3.1-pro-preview`, `gemini-3-flash-preview`, `gemini-2.5-pro` |
| xAI | `grok-4`, `grok-3` |
| Perplexity | `sonar-pro`, `sonar-reasoning-pro` |
| Meta / 오픈소스 | `meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8` |

<Banner variant="info">
  Anthropic 네이티브 기능(확장 사고, 프롬프트 캐싱, 비전)이 필요하신가요? [Messages API](/docs/gateway/api-reference/messages-api)를 사용하시면 모든 Anthropic 전용 기능을 그대로 사용할 수 있습니다.
</Banner>

<Banner variant="warning">
 Codex 모델(`gpt-5.2-codex`, `gpt-5.1-codex-max`)은 이 엔드포인트에서 지원되지 않습니다. [Responses API](/docs/gateway/api-reference/responses-api)를 사용하세요.
</Banner>

---

### 코드 예제

#### 기본 채팅 (Python)

```python
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_API_KEY",
    base_url="https://factchat-cloud.mindlogic.ai/v1/gateway",
)

response = client.chat.completions.create(
    model="claude-sonnet-4-6",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.choices[0].message.content)
```

#### 스트리밍 (JavaScript)

```javascript
import OpenAI from "openai";

const client = new OpenAI({
  apiKey: "YOUR_API_KEY",
  baseURL: "https://factchat-cloud.mindlogic.ai/v1/gateway",
});

const stream = await client.chat.completions.create({
  model: "gemini-3-flash-preview",
  messages: [{ role: "user", content: "Tell me a joke." }],
  stream: true,
});

for await (const chunk of stream) {
  process.stdout.write(chunk.choices[0]?.delta?.content ?? "");
}
```

---

### 다음 단계

- [OpenAI SDK 연동](/docs/gateway/integrations/openai-sdk) — Python/JavaScript에서 바로 사용해보세요
- [curl 예제](/docs/gateway/integrations/curl) — 터미널에서 빠르게 테스트
- [에러 가이드](/docs/gateway/reference/errors) — 문제 발생 시 참고