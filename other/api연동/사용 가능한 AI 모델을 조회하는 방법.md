# 모델 목록

<TenantName /> Gateway에서 사용 가능한 AI 모델을 조회하는 방법을 안내합니다.

조직에 활성화된 모든 모델을 API로 확인할 수 있으며, 반환된 모델 `id`를 API 요청의 `model` 파라미터로 사용하시면 됩니다.

<Indent mt={12} />

어떤 모델을 사용할 수 있는지 먼저 확인해보세요. 조직의 구독 플랜에 따라 사용 가능한 모델이 다를 수 있습니다.

### 모델 조회

<ParameterText badge="/v1/gateway/models/">GET</ParameterText>

조직에서 사용 가능한 모델 목록을 반환합니다. 채팅/LLM 모델뿐 아니라 오디오, 이미지, 비디오 모델도 함께 내려옵니다.

---

### 요청 헤더

```http
GET https://factchat-cloud.mindlogic.ai/v1/gateway/models/
Authorization: Bearer YOUR_API_KEY
```

---

### 쿼리 파라미터

<ParameterText badge="string">type</ParameterText>
모델 종류로 목록을 거릅니다. `llm`, `audio`, `image`, `video` 중 하나를 넣거나 쉼표로 여러 개를 나열합니다. 생략하면 모든 종류가 반환됩니다.

```http
GET /v1/gateway/models/?type=audio
GET /v1/gateway/models/?type=image,video
```

---

### 모델 종류

각 항목에는 어느 엔드포인트에 속하는 모델인지 알려주는 `type` 필드가 붙습니다.

| `type` | 모델 | 엔드포인트 |
| --- | --- | --- |
| `llm` | 채팅 · 추론 모델 | `/v1/gateway/chat/completions/` |
| `audio` | TTS 모델 | `/v1/gateway/audio/speech/` |
| `image` | 이미지 생성 모델 | `/v1/gateway/images/generate/` |
| `video` | 비디오 생성 모델 | `/v1/gateway/video/generation/` |

```json
{
  "object": "list",
  "data": [
    {
      "id": "claude-opus-5",
      "object": "model",
      "created": 1776614400,
      "owned_by": "claude",
      "type": "llm"
    },
    {
      "id": "gemini-3.1-flash-tts-preview",
      "object": "model",
      "created": 1777075200,
      "owned_by": "gemini",
      "type": "audio"
    }
  ]
}
```

---

### 응답

```json
{
  "object": "list",
  "data": [
    {
      "id": "gpt-5.6-terra",
      "object": "model",
      "created": 1783694656,
      "owned_by": "openai",
      "profile_image_url": "https://factchat-public.s3.ap-northeast-2.amazonaws.com/public/svg/openai-icon-logo.svg",
      "type": "llm"
    },
    {
      "id": "claude-opus-5",
      "object": "model",
      "created": 1785151540,
      "owned_by": "claude",
      "profile_image_url": "https://factchat-public.s3.ap-northeast-2.amazonaws.com/public/png/claude_logo.png",
      "type": "llm"
    },
    {
      "id": "gemini-3.6-flash",
      "object": "model",
      "created": 1784730547,
      "owned_by": "gemini",
      "profile_image_url": "https://factchat-public.s3.ap-northeast-2.amazonaws.com/public/png/gemini_logo.png",
      "type": "llm"
    },
    {
      "id": "kimi-k3",
      "object": "model",
      "created": 1785325593,
      "owned_by": "moonshot-ai",
      "profile_image_url": "https://factchat-public.s3.ap-northeast-2.amazonaws.com/public/svg/kimi-logo.svg",
      "type": "llm"
    }
  ]
}
```

---

### 사용 가능 모델 (2026-08-13 기준)

사용 가능한 모델은 조직(테넌트) 설정과 사용자가 속한 그룹의 권한에 따라 달라집니다. 아래 표는 2026년 8월 13일 기준 게이트웨이로 호출 가능한 전체 LLM 목록이며, 모델은 수시로 추가됩니다. 내 계정에서 실제로 쓸 수 있는 목록은 위 `/models` API로 확인하세요.

#### Anthropic
| 모델 ID | 표시 이름 | 사고 모드 | 웹 검색 |
| --- | --- | --- | --- |
| `claude-sonnet-5` | Claude Sonnet 5 | ✓ | — |
| `claude-opus-5` | Claude Opus 5 | ✓ | — |
| `claude-fable-5` | Claude Fable 5 | ✓ | — |
| `claude-sonnet-4-6` | Claude 4.6 Sonnet | ✓ | — |
| `claude-sonnet-4-5-20250929` | Claude 4.5 Sonnet | ✓ | — |
| `claude-opus-4-8` | Claude 4.8 Opus | ✓ | — |
| `claude-opus-4-7` | Claude 4.7 Opus | ✓ | — |
| `claude-haiku-4-5-20251001` | Claude 4.5 Haiku | ✓ | — |

#### OpenAI
| 모델 ID | 표시 이름 | 사고 모드 | 웹 검색 |
| --- | --- | --- | --- |
| `gpt-5.6-luna` | GPT-5.6 Luna | ✓ | — |
| `gpt-5.6-terra` | GPT-5.6 Terra | ✓ | — |
| `gpt-5.6-sol` | GPT-5.6 Sol | ✓ | — |
| `gpt-5.5` | GPT-5.5 | ✓ | — |
| `gpt-5.4` | GPT-5.4 | ✓ | — |
| `gpt-5.4-mini` | GPT-5.4 mini | ✓ | — |
| `gpt-5.4-nano` | GPT-5.4 nano | ✓ | — |

#### Google Gemini
| 모델 ID | 표시 이름 | 사고 모드 | 웹 검색 |
| --- | --- | --- | --- |
| `gemini-3.6-flash` | Gemini 3.6 Flash | ✓ | ✓ |
| `gemini-3.5-flash` | Gemini 3.5 Flash | ✓ | ✓ |
| `gemini-3.5-flash-lite` | Gemini 3.5 Flash-Lite | ✓ | ✓ |
| `gemini-3.1-pro-preview` | Gemini 3.1 Pro | ✓ | ✓ |
| `gemini-3.1-flash-lite` | Gemini 3.1 Flash Lite | ✓ | ✓ |
| `gemini-3-flash-preview` | Gemini 3 Flash | ✓ | ✓ |
| `gemini-2.5-flash` | Gemini 2.5 Flash | — | ✓ |
| `gemini-2.5-pro` | Gemini 2.5 Pro | — | ✓ |

#### xAI
| 모델 ID | 표시 이름 | 사고 모드 | 웹 검색 |
| --- | --- | --- | --- |
| `grok-4.5` | Grok 4.5 | — | — |
| `grok-4-1-fast` | Grok 4.1 Fast | — | — |
| `grok-3-mini` | Grok 3 Mini | — | — |
| `grok-4` | Grok 4 | — | — |

#### 국내 모델
| 모델 ID | 표시 이름 | 사고 모드 | 웹 검색 |
| --- | --- | --- | --- |
| `solar-pro3` | Solar Pro 3 | ✓ | — |
| `solar-pro2` | Solar Pro 2 | ✓ | — |
| `LGAI-EXAONE/K-EXAONE-236B-A23B` | K-EXAONE | — | — |

#### 기타 제공업체
| 모델 ID | 표시 이름 | 사고 모드 | 웹 검색 |
| --- | --- | --- | --- |
| `google/gemma-4-31B-it` | Gemma 4 | — | — |
| `qwen3.7-plus` | Qwen 3.7 Plus | ✓ | — |
| `qwen3.7-max` | Qwen 3.7 Max | ✓ | — |
| `glm-5.2` | GLM-5.2 | ✓ | — |
| `kimi-k3` | Kimi K3 | ✓ | — |
| `kimi-k2.6` | Kimi K2.6 | ✓ | — |
| `seed-2-0-pro-260328` | Seed 2.0 Pro | ✓ | — |
| `seed-2-0-lite-260428` | Seed 2.0 Lite | ✓ | — |
| `sonar-pro` | Sonar Pro | — | ✓ |
| `sonar-reasoning-pro` | Sonar Reasoning Pro | — | ✓ |

<Banner variant="warning">
  **게이트웨이 API로 호출할 수 없는 모델이 있습니다.** 아래 모델은 앱 화면에서만 제공되며, 정책상 API로는 제공되지 않습니다. `model` 파라미터로 호출하면 사용할 수 없다는 오류(403)가 반환됩니다.

  - **Super Agent** (`mindlogic-super-agent`): 앱 전용 기능입니다. 영상·음악·음성 등 내장 도구는 게이트웨이 API로 호출할 수 없습니다.
  - **무료 모델** (`gpt-5-nano`, `gpt-4.1-nano`, SAIT 등): 무료 모델은 게이트웨이 API 대상에서 제외됩니다. API에서는 `gpt-5.4-nano`, `gpt-5.4`, `claude-sonnet-4-6` 등 일반 모델을 사용하세요.
</Banner>

<Banner variant="info">
  위 표는 채팅/LLM 모델 목록입니다. 오디오, 이미지, 비디오 모델도 같은 엔드포인트에서 내려오며 `?type=audio`, `?type=image`, `?type=video`로 걸러낼 수 있습니다. 파라미터와 과금은 각 API 레퍼런스 페이지를 참조하세요.
</Banner>

---

### 코드 예제

```python
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_API_KEY",
    base_url="https://factchat-cloud.mindlogic.ai/v1/gateway",
)

models = client.models.list()
for model in models.data:
    print(model.id)
```

---

### 모델별 권장 엔드포인트

| 모델 제공업체 | 권장 엔드포인트 |
| --- | --- |
| Anthropic | `/v1/gateway/chat/completions/` 또는 `/v1/gateway/claude/v1/messages/` |
| OpenAI (채팅) | `/v1/gateway/chat/completions/` |
| OpenAI (o-시리즈 추론) | `/v1/gateway/responses/` |
| Google Gemini | `/v1/gateway/chat/completions/` |
| OpenAI (Codex) | `/v1/gateway/responses/` |
| 기타 제공업체 | `/v1/gateway/chat/completions/` |

---

### 참고

- 조직에 활성화된 모델만 이 목록에 표시됩니다
- 모델 가용성은 구독 플랜에 따라 다릅니다
- API 요청에서 `id` 필드를 `model` 파라미터로 사용하세요
- `type` 필드로 해당 모델의 엔드포인트를 확인하거나, 조회 단계에서 `?type=`으로 미리 걸러내세요

<Banner variant="info">
  어떤 엔드포인트를 사용해야 할지 모르겠다면, `/v1/gateway/chat/completions/`를 사용해보세요. 대부분의 모델이 이 엔드포인트를 통해 사용 가능합니다.
</Banner>