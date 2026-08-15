# Audio — 텍스트 음성 변환

텍스트를 자연스러운 음성으로 변환하는 TTS(Text-to-Speech) 엔드포인트입니다.

Google Gemini TTS 모델을 활용하여 단일 화자 및 다중 화자 합성을 지원합니다. 팟캐스트, 오디오북, 안내 음성 등 다양한 용도로 활용해보세요.

<Indent mt={12} />

- 공식 레퍼런스: [Google Gemini TTS](https://ai.google.dev/gemini-api/docs/speech-generation)

---

### 텍스트 음성 변환

<ParameterText badge="/v1/gateway/audio/speech/">POST</ParameterText>

텍스트를 오디오로 변환합니다. 응답은 원시 PCM 바이트입니다.

---

### 파라미터

<ParameterText badge="string" required>model</ParameterText>
TTS 모델 이름 (예: `gemini-3.1-flash-tts-preview`).

<ParameterText badge="string" required>input</ParameterText>
합성할 텍스트. 다중 화자의 경우 대화 형식을 사용합니다.

<ParameterText badge="string">voice</ParameterText>
음성 이름 (기본값: `"Aoede"`). 옵션: `Aoede`, `Charon`, `Fenrir`, `Kore`, `Puck` 등.

<ParameterText badge="object">speakers</ParameterText>
다중 화자 매핑 `{speaker_name: voice_name}`.

---

<Banner variant="info">
  응답은 원시 PCM 오디오(24kHz 모노, 16비트 LE)로 반환됩니다. MP3나 WAV로 변환하려면 아래 ffmpeg 예제를 참고해주세요.
</Banner>

### 응답

원시 PCM 오디오 바이트 (`audio/pcm`), 24kHz 모노, 16비트 리틀 엔디안.

| 헤더 | 설명 |
| --- | --- |
| `X-Input-Tokens` | 입력 텍스트에 소비된 토큰 |
| `X-Output-Tokens` | 오디오 출력에 소비된 토큰 |
| `Content-Type` | `audio/pcm` |

---

### 예제

#### curl

```bash
curl -X POST https://factchat-cloud.mindlogic.ai/v1/gateway/audio/speech/ \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-3.1-flash-tts-preview",
    "input": "Hello! This is a test of the TTS gateway.",
    "voice": "Aoede"
  }' \
  --output speech.pcm
```

#### Python

```python
import httpx

response = httpx.post(
    "https://factchat-cloud.mindlogic.ai/v1/gateway/audio/speech/",
    headers={"Authorization": "Bearer YOUR_API_KEY"},
    json={
        "model": "gemini-3.1-flash-tts-preview",
        "input": "Hello! This is a test of the TTS gateway.",
        "voice": "Aoede",
    },
)
response.raise_for_status()

with open("speech.pcm", "wb") as f:
    f.write(response.content)

print(f"Input tokens:  {response.headers.get('X-Input-Tokens')}")
print(f"Output tokens: {response.headers.get('X-Output-Tokens')}")
```

#### PCM을 MP3로 변환

```bash
ffmpeg -f s16le -ar 24000 -ac 1 -i speech.pcm speech.mp3
```

---

### 다중 화자 TTS

```json
{
  "model": "gemini-3.1-flash-tts-preview",
  "input": "TTS the following:\nAlice: Hello Bob, how are you?\nBob: I'm doing great, thanks!",
  "speakers": {
    "Alice": "Aoede",
    "Bob": "Puck"
  }
}
```

---

### 오디오 형식

| 속성 | 값 |
| --- | --- |
| 형식 | Raw PCM (WAV/MP3 헤더 없음) |
| 샘플 레이트 | 24,000 Hz |
| 채널 | 모노 (1 ch) |
| 비트 깊이 | 16비트 부호 있음, 리틀 엔디안 |

---

### 사용 가능한 모델

| 모델 | 표시 이름 | 10k 입력 토큰당 크레딧 | 10k 출력 토큰당 크레딧 |
| --- | --- | --- | --- |
| `gemini-3.1-flash-tts-preview` | Gemini 3.1 Flash TTS | 10 | 200 |
| `gemini-2.5-flash-preview-tts` | Gemini 2.5 Flash TTS | 5 | 100 |
| `gemini-2.5-pro-preview-tts` | Gemini 2.5 Pro TTS | 10 | 200 |

`gemini-3.1-flash-tts-preview`가 최신 모델이며, 새로 연동한다면 이 모델을 권장합니다. Gemini 2.5 모델도 계속 지원합니다.

---

### 사용 가능한 음성

**여성:**
`Aoede` (산뜻함), `Achernar` (부드러움), `Autonoe` (밝음), `Callirrhoe` (편안함), `Despina` (매끄러움), `Erinome` (선명함), `Gacrux` (성숙함), `Kore` (단단함), `Laomedeia` (경쾌함), `Leda` (젊음), `Pulcherrima` (적극적), `Sulafat` (따뜻함), `Vindemiatrix` (온화함), `Zephyr` (밝음)

**남성:**
`Achird` (친근함), `Algenib` (거친), `Algieba` (매끄러움), `Alnilam` (단단함), `Charon` (정보적), `Enceladus` (숨결), `Fenrir` (활기찬), `Iapetus` (선명함), `Orus` (단단함), `Puck` (경쾌함), `Rasalgethi` (정보적), `Sadachbia` (활발함), `Sadaltager` (박식함), `Schedar` (차분함), `Umbriel` (편안함), `Zubenelgenubi` (캐주얼)

---

### 참고

- 조직에 따라 일부 모델이 활성화되지 않을 수 있습니다. 활성화되지 않은 모델을 사용하면 `403` 에러가 반환됩니다 — 관리자에게 문의하세요.