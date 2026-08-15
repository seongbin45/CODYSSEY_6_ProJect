# OpenClaw 연동

[OpenClaw](https://openclaw.ai)를 사용하여 AI 모델을 관리하고 계신가요?

<TenantName /> Gateway를 OpenClaw의 LLM 제공자로 설정하면, 단일 설정으로 모든 Gateway 모델에 접근할 수 있습니다. 아래 가이드를 따라 설정해보세요.

<Indent mt={12} />

- 공식 레퍼런스: [OpenClaw Model Providers](https://docs.openclaw.ai/concepts/model-providers)

## 사전 요구 사항

- OpenClaw 설치 (`npm install -g openclaw@latest`, Node >= 22 필요)
- <TenantName /> API 키 ([인증](/docs/gateway/getting-started/authentication) 참고)

---

## 설정

OpenClaw CLI를 사용하여 <TenantName /> Gateway를 커스텀 제공자로 추가합니다:

```bash
export FACTCHAT_API_KEY=YOUR_FACTCHAT_API_KEY

openclaw config set models '{
  "mode": "merge",
  "providers": {
    "factchat": {
      "baseUrl": "https://factchat-cloud.mindlogic.ai/v1/gateway",
      "apiKey": "'"$FACTCHAT_API_KEY"'",
      "api": "openai-completions",
      "models": [
        {
          "id": "claude-sonnet-4-6",
          "name": "Claude Sonnet 4.6",
          "contextWindow": 200000,
          "maxTokens": 16000
        },
        {
          "id": "claude-opus-4-6",
          "name": "Claude Opus 4.6",
          "contextWindow": 200000,
          "maxTokens": 32000
        },
        {
          "id": "gpt-5.2",
          "name": "GPT 5.2",
          "contextWindow": 400000,
          "maxTokens": 32768
        },
        {
          "id": "gemini-3-flash-preview",
          "name": "Gemini 3 Flash",
          "contextWindow": 1000000,
          "maxTokens": 65536
        },
        {
          "id": "gemini-3-pro-preview",
          "name": "Gemini 3 Pro",
          "contextWindow": 1000000,
          "maxTokens": 65536
        },
        {
          "id": "gemini-3.1-pro-preview",
          "name": "Gemini 3.1 Pro",
          "contextWindow": 1000000,
          "maxTokens": 65536
        },
        {
          "id": "gpt-5.2-codex",
          "name": "GPT 5.2 Codex",
          "contextWindow": 200000,
          "maxTokens": 32768
        },
        {
          "id": "gpt-5.1-codex-max",
          "name": "GPT 5.1 Codex Max",
          "contextWindow": 200000,
          "maxTokens": 32768
        }
      ]
    }
  }
}'
```

기본 모델을 설정합니다:

```bash
openclaw config set agents.defaults.model.primary "factchat/claude-sonnet-4-6"
```

---

## 주요 설정 필드

| 필드 | 설명 |
|------|------|
| `baseUrl` | Gateway 기본 URL (슬래시 없이) |
| `apiKey` | <TenantName /> API 키 (`${ENV_VAR}` 구문 지원) |
| `api` | `"openai-completions"` 필수 |
| `models[].id` | `GET /v1/gateway/models/`에서 반환된 ID와 일치해야 합니다 |
| `models[].contextWindow` | 최대 입력 토큰 수 (컨텍스트 관리 힌트) |
| `models[].maxTokens` | 최대 출력 토큰 수 |

---

## 모델 전환

`main` 에이전트의 기본 모델을 변경합니다:

```bash
openclaw config set agents.defaults.model.primary "factchat/gpt-5.2"
openclaw config set agents.defaults.model.primary "factchat/gemini-3-flash-preview"
openclaw config set agents.defaults.model.primary "factchat/claude-opus-4-6"
```

---

## 테스트

원샷 에이전트 명령을 실행하여 연동을 확인합니다:

```bash
openclaw agent --local --agent main --message "Hello, what model are you?" --json
```

응답에 `"provider": "factchat"`과 모델 이름이 포함되면 성공입니다.

---

## 로컬 개발

로컬 서버에 대해 테스트하려면:

```bash
openclaw config set models '{
  "mode": "merge",
  "providers": {
    "factchat-local": {
      "baseUrl": "http://localhost:8081/v1/gateway",
      "apiKey": "YOUR_LOCAL_API_KEY",
      "api": "openai-completions",
      "models": [
        {
          "id": "claude-sonnet-4-6",
          "name": "Claude Sonnet 4.6",
          "contextWindow": 200000,
          "maxTokens": 16000
        }
      ]
    }
  }
}'

openclaw config set agents.defaults.model.primary "factchat-local/claude-sonnet-4-6"
```

---

## 참고 사항

- OpenClaw는 `openai-completions` API 타입을 사용하며, 이는 Gateway의 `/chat/completions/` 엔드포인트에 매핑됩니다.
- Gateway는 모델 이름에 따라 각 제공자의 백엔드로 자동 라우팅합니다 — 모든 모델이 동일한 엔드포인트로 작동합니다.
- 모델 ID는 `GET /v1/gateway/models/`에서 반환되는 값과 정확히 일치해야 합니다.
- `contextWindow`와 `maxTokens` 값은 OpenClaw의 컨텍스트 관리를 위한 힌트이며, 하드 리밋을 적용하지 않습니다.
- OpenClaw는 기본적으로 `store: true`를 전송합니다. Gateway는 이를 지원하지 않는 제공자(예: Google Gemini)에 대해 자동으로 제거합니다.