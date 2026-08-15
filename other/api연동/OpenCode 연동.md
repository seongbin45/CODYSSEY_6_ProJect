# OpenCode 연동

OpenCode에서 <TenantName /> Gateway의 AI 모델을 사용하는 방법을 안내합니다.

`opencode.json` 설정 파일 하나만 수정하면 모든 Gateway 모델에 바로 접근할 수 있습니다.

<Indent mt={12} />

- 공식 레퍼런스: [OpenCode Providers](https://opencode.ai/docs/providers/)

<Banner variant="info">
  시작하기 전에 <TenantName /> API 키가 필요합니다. [인증 가이드](/docs/gateway/getting-started/authentication)에서 발급 방법을 확인해주세요.
</Banner>

## 설정

프로젝트 루트에 `opencode.json`을 생성하거나 업데이트합니다:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "factchat": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "FactChat",
      "options": {
        "baseURL": "https://factchat-cloud.mindlogic.ai/v1/gateway",
        "apiKey": "{env:FACTCHAT_API_KEY}"
      },
      "models": {
        "claude-sonnet-4-6": {
          "name": "Claude Sonnet 4.6",
          "limit": { "context": 200000, "output": 16000 }
        },
        "claude-opus-4-6": {
          "name": "Claude Opus 4.6",
          "limit": { "context": 200000, "output": 32000 }
        },
        "gpt-5.2": {
          "name": "GPT 5.2",
          "limit": { "context": 400000, "output": 32768 }
        },
        "gemini-3.1-pro-preview": {
          "name": "Gemini 3.1 Pro Preview",
          "limit": { "context": 1000000, "output": 65536 }
        },
        "gemini-3-flash-preview": {
          "name": "Gemini 3 Flash Preview",
          "limit": { "context": 1000000, "output": 65536 }
        }
      }
    },
    "factchat-codex": {
      "npm": "@ai-sdk/openai",
      "name": "FactChat Codex",
      "options": {
        "baseURL": "https://factchat-cloud.mindlogic.ai/v1/gateway",
        "apiKey": "{env:FACTCHAT_API_KEY}"
      },
      "models": {
        "gpt-5.2-codex": {
          "name": "GPT 5.2 Codex",
          "limit": { "context": 400000, "output": 32768 }
        },
        "gpt-5.1-codex-max": {
          "name": "GPT 5.1 Codex Max",
          "limit": { "context": 400000, "output": 32768 }
        }
      }
    }
  }
}
```

API 키를 설정합니다:

```bash
export FACTCHAT_API_KEY=YOUR_API_KEY
```

---

## 주요 형식 세부사항

| 필드 | 값 |
| --- | --- |
| `npm` | `"@ai-sdk/openai-compatible"` (일반 모델) 또는 `"@ai-sdk/openai"` (Codex 모델) |
| `options.baseURL` | Gateway Base URL (후행 슬래시 없음) |
| `options.apiKey` | API 키, 또는 환경 변수용 `"{env:VAR_NAME}"` |
| `models.*.limit.context` | 최대 입력 토큰 |
| `models.*.limit.output` | 최대 출력 토큰 |

<Banner variant="info">
  Codex 모델(`gpt-5.2-codex`, `gpt-5.1-codex-max`)은 Responses API를 사용하므로 별도의 `factchat-codex` provider로 분리해야 합니다. `npm` 패키지는 `@ai-sdk/openai`를 사용합니다.
</Banner>

---

## 모델 선택

OpenCode 내에서 `/model`로 모델을 전환합니다:

```
/model factchat/claude-sonnet-4-6
/model factchat/gpt-5.2
/model factchat/gemini-3.1-pro-preview
/model factchat-codex/gpt-5.2-codex
/model factchat-codex/gpt-5.1-codex-max
```

---

## 참고

- OpenCode는 OpenAI 호환 `/chat/completions/` 엔드포인트를 사용합니다
- 모델 ID는 `GET /v1/gateway/models/`에서 반환되는 것과 정확히 일치해야 합니다
- `limit` 값은 컨텍스트 관리를 위한 힌트이며, 하드 리밋이 아닙니다