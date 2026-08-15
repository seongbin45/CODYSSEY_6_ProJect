# OpenAI SDK 연동

이미 OpenAI SDK를 사용하고 계신가요? 🙌

`base_url`과 `api_key` 두 줄만 변경하면 <TenantName /> Gateway의 모든 모델을 바로 사용할 수 있습니다. Python과 JavaScript/TypeScript 모두 지원됩니다.

<Indent mt={12} />

- 공식 레퍼런스: [OpenAI Python SDK](https://github.com/openai/openai-python) · [OpenAI Node SDK](https://github.com/openai/openai-node)

<Banner variant="info">
  시작하기 전에 <TenantName /> API 키가 필요합니다. [인증 가이드](/docs/gateway/getting-started/authentication)에서 발급 방법을 확인해주세요.
</Banner>

## Python

### 설치

```bash
pip install openai
```

### 기본 사용법

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

### 스트리밍

```python
stream = client.chat.completions.create(
    model="claude-sonnet-4-6",
    messages=[{"role": "user", "content": "Write a haiku about coding."}],
    stream=True,
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### 환경 변수

```bash
export OPENAI_API_KEY=YOUR_API_KEY
export OPENAI_BASE_URL=https://factchat-cloud.mindlogic.ai/v1/gateway
```

<Banner variant="warning">
  환경 변수에 API 키를 저장할 때, 소스 코드에 직접 키를 포함하지 않도록 주의해주세요.
</Banner>

### 도구 사용

```python
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name"},
            },
            "required": ["location"],
        },
    },
}]

response = client.chat.completions.create(
    model="claude-sonnet-4-6",
    messages=[{"role": "user", "content": "What's the weather in Seoul?"}],
    tools=tools,
    tool_choice="auto",
)
```

### 모델 목록

```python
models = client.models.list()
for model in models.data:
    print(model.id)
```

---

## JavaScript / TypeScript

### 설치

```bash
npm install openai
```

### 기본 사용법

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  apiKey: "YOUR_API_KEY",
  baseURL: "https://factchat-cloud.mindlogic.ai/v1/gateway",
});

const response = await client.chat.completions.create({
  model: "claude-sonnet-4-6",
  messages: [{ role: "user", content: "Hello!" }],
});
console.log(response.choices[0].message.content);
```

### 스트리밍

```typescript
const stream = await client.chat.completions.create({
  model: "claude-sonnet-4-6",
  messages: [{ role: "user", content: "Write a haiku about coding." }],
  stream: true,
});

for await (const chunk of stream) {
  process.stdout.write(chunk.choices[0]?.delta?.content ?? "");
}
```

### Next.js API 라우트

```typescript
// app/api/chat/route.ts
import OpenAI from "openai";
import { NextRequest, NextResponse } from "next/server";

const client = new OpenAI({
  apiKey: process.env.FACTCHAT_API_KEY!,
  baseURL: "https://factchat-cloud.mindlogic.ai/v1/gateway",
});

export async function POST(req: NextRequest) {
  const { messages } = await req.json();
  const response = await client.chat.completions.create({
    model: "claude-sonnet-4-6",
    messages,
  });
  return NextResponse.json(response);
}
```

---

## 다음 단계

- [Chat Completions API](/docs/gateway/api-reference/chat-completions) — 파라미터와 응답 형식 상세 참고
- [사용 가능한 모델 조회](/docs/gateway/getting-started/models) — 어떤 모델을 사용할 수 있는지 확인
- [에러 가이드](/docs/gateway/reference/errors) — 문제 발생 시 참고