# curl 예제

SDK 없이 터미널에서 바로 테스트해보고 싶으신가요?

아래 curl 예제를 사용하면 <TenantName /> API Gateway의 모든 엔드포인트를 빠르게 확인할 수 있습니다. API 연동 구축 시 참고 자료로도 활용해보세요.

<Indent mt={12} />

<Banner variant="info">
  아래 예제에서 `YOUR_API_KEY`를 실제 API 키로 대체해주세요. API 키가 아직 없다면 [인증 가이드](/docs/gateway/getting-started/authentication)를 참고해주세요.
</Banner>

## 변수

```bash
BASE="https://factchat-cloud.mindlogic.ai/v1/gateway"
KEY="YOUR_API_KEY"
```

---

## 모델 조회

```bash
curl "$BASE/models/" \
  -H "Authorization: Bearer $KEY"
```

---

## Chat Completions

### 비스트리밍

```bash
curl "$BASE/chat/completions/" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-6",
    "messages": [{"role": "user", "content": "What is 2+2?"}]
  }'
```

### 스트리밍

```bash
curl -N "$BASE/chat/completions/" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-6",
    "messages": [{"role": "user", "content": "Count to 5."}],
    "stream": true
  }'
```

### 도구 사용

```bash
curl "$BASE/chat/completions/" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-6",
    "messages": [{"role": "user", "content": "What is the weather in Seoul?"}],
    "tools": [{
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get current weather",
        "parameters": {
          "type": "object",
          "properties": {"location": {"type": "string"}},
          "required": ["location"]
        }
      }
    }]
  }'
```

---

## Anthropic Messages API

### x-api-key 헤더 사용

```bash
curl "$BASE/claude/v1/messages/" \
  -H "x-api-key: $KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-6",
    "max_tokens": 200,
    "messages": [{"role": "user", "content": "Say hello in Korean."}]
  }'
```

### 적응형 사고 (권장)

```bash
curl "$BASE/claude/v1/messages/" \
  -H "x-api-key: $KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-6",
    "max_tokens": 16000,
    "thinking": {"type": "adaptive"},
    "messages": [{"role": "user", "content": "Solve: what is 127 * 389?"}]
  }'
```

effort 파라미터로 사고 깊이 조절:

```bash
curl "$BASE/claude/v1/messages/" \
  -H "x-api-key: $KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-opus-4-6",
    "max_tokens": 16000,
    "thinking": {"type": "adaptive"},
    "output_config": {"effort": "medium"},
    "messages": [{"role": "user", "content": "What is the capital of France?"}]
  }'
```

---

## OpenAI Responses API

```bash
curl "$BASE/responses/" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5",
    "input": [{"role": "user", "content": "What is the 10th prime number?"}],
    "max_output_tokens": 200
  }'
```

---

## 인증 — 두 가지 헤더 방식

```bash
# 방식 1: Authorization Bearer (OpenAI 스타일)
curl "$BASE/chat/completions/" \
  -H "Authorization: Bearer $KEY" \
  -d '...'

# 방식 2: x-api-key (Anthropic 스타일)
curl "$BASE/chat/completions/" \
  -H "x-api-key: $KEY" \
  -d '...'
```