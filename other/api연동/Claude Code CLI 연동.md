# Claude Code CLI 연동

Anthropic의 공식 AI 코딩 도우미 Claude Code를 <TenantName /> Gateway와 함께 사용해보세요!

환경 변수 2개만 설정하면 Claude Code의 모든 기능을 Gateway를 통해 사용할 수 있습니다. 스트리밍, 도구 사용, 확장 사고 등 모든 Anthropic 기능이 완벽하게 지원됩니다.

<Indent mt={12} />

- 공식 문서: [Claude Code](https://code.claude.com/docs/ko)
- VS Code 확장 사용법: [VS Code에서 Claude Code 사용하기](https://code.claude.com/docs/ko/vs-code)
- 모델 선택 설정: [모델 구성](https://code.claude.com/docs/ko/model-config)

<Banner variant="info">
  시작하기 전에 <TenantName /> API 키가 필요합니다. [인증 가이드](/docs/gateway/getting-started/authentication)에서 발급 방법을 확인해주세요.
</Banner>

## 설정

```bash
# 1단계: Anthropic 호환 게이트웨이 접두사로 Base URL 설정
export ANTHROPIC_BASE_URL=https://factchat-cloud.mindlogic.ai/v1/gateway/claude

# 2단계: API 키 설정
# 참고: 커스텀 Base URL에서는 ANTHROPIC_API_KEY가 아닌 ANTHROPIC_AUTH_TOKEN을 사용
export ANTHROPIC_AUTH_TOKEN=YOUR_API_KEY

# 3단계: 연결 확인
claude "Say hello"
```

<Accordion>
  <AccordionButton>
    왜 ANTHROPIC_API_KEY가 아닌 ANTHROPIC_AUTH_TOKEN인가요?
  </AccordionButton>
  <AccordionPanel>
    `ANTHROPIC_BASE_URL`이 설정되면 Claude Code는 `ANTHROPIC_AUTH_TOKEN`의 토큰을 `x-api-key` 헤더로 전송합니다. Gateway는 `Authorization: Bearer`와 `x-api-key` 헤더를 모두 지원하므로 원활하게 작동합니다. 실수로 `ANTHROPIC_API_KEY`를 사용하면 Claude Code가 커스텀 엔드포인트에 접근하기 전에 Anthropic 직접 검증을 시도하여 401 오류가 발생할 수 있습니다. 반드시 `ANTHROPIC_AUTH_TOKEN`을 사용해주세요.
  </AccordionPanel>
</Accordion>

---

## 영구 설정

`~/.zshrc` 또는 `~/.bashrc`에 추가:

```bash
export ANTHROPIC_BASE_URL=https://factchat-cloud.mindlogic.ai/v1/gateway/claude
export ANTHROPIC_AUTH_TOKEN=YOUR_API_KEY
```

또는 프로젝트에 `.env` 파일 생성:

```env
ANTHROPIC_BASE_URL=https://factchat-cloud.mindlogic.ai/v1/gateway/claude
ANTHROPIC_AUTH_TOKEN=YOUR_API_KEY
```

---

## 모델 지정

```bash
# 특정 모델 사용
claude --model claude-fable-5 "Explain async/await"

# ANTHROPIC_MODEL 환경 변수로 사용
export ANTHROPIC_MODEL=claude-fable-5
claude "Explain async/await"
```

호출 가능한 모델 목록은 Gateway에서 직접 확인합니다.

```bash
curl -s https://factchat-cloud.mindlogic.ai/v1/gateway/claude/v1/models \
  -H "x-api-key: YOUR_API_KEY" | jq '.data[].id'
```

<Banner variant="info">
  이 목록은 기관 설정과 멤버 그룹 권한에 따라 계정마다 다릅니다. 여기에 보이는 모델 ID는
  그대로 `--model`이나 `ANTHROPIC_MODEL`에 넣어 쓸 수 있습니다.
</Banner>

---

## VS Code 확장에서 사용하기

VS Code의 Claude Code 확장도 같은 환경 변수를 씁니다. 프로젝트의 `.vscode/settings.json`
대신 Claude Code 설정 파일(`~/.claude/settings.json` 또는 프로젝트의 `.claude/settings.json`)의
`env` 항목에 넣으면 확장과 CLI가 같은 설정을 공유합니다.

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://factchat-cloud.mindlogic.ai/v1/gateway/claude",
    "ANTHROPIC_AUTH_TOKEN": "YOUR_API_KEY",
    "ANTHROPIC_MODEL": "claude-fable-5"
  }
}
```

설정을 바꾼 뒤에는 VS Code 창을 다시 로드해야 확장이 새 값을 읽습니다
(명령 팔레트 → `Developer: Reload Window`).

**모델 선택 화면에 원하는 모델이 안 보일 때**

모델 선택 목록(`/model`)에는 Claude Code가 서버로부터 "사용 가능"을 확인한 모델만 올라옵니다.
Gateway를 통해 연결하면 그 확인 절차를 거치지 않는 모델이 있어, 호출은 되는데 목록에는 안 보이는
경우가 생깁니다. Claude Fable 5가 대표적입니다.

목록에 없어도 아래 방법으로 선택하면 그대로 호출됩니다.

- 채팅창에서 `/model fable` 입력 — 목록에 없어도 선택됩니다
- 위 설정처럼 `ANTHROPIC_MODEL`에 모델 ID를 직접 지정
- `fable` 별칭이 가리키는 모델을 바꾸려면 `ANTHROPIC_DEFAULT_FABLE_MODEL`을 `claude-fable-5`로 지정

실제로 어떤 모델이 응답했는지는 응답의 `model` 필드로 확인하실 수 있습니다.

<Banner variant="warning">
  Claude Fable 5는 Claude Code v2.1.170 이상에서만 선택할 수 있습니다. 그 이전 버전은 목록에
  표시되지 않고 선택도 되지 않습니다. PC마다 동작이 다르다면 VS Code 확장 탭에서 Claude Code
  확장을 최신으로 업데이트해 주십시오.
</Banner>

**확장 자체 사용법**

확장 설치, 단축키, `@` 파일 참조, 플러그인 관리 등은 Anthropic 공식 문서에 정리돼 있습니다.
한국어판이 제공됩니다.

- VS Code에서 Claude Code 사용하기: https://code.claude.com/docs/ko/vs-code
- 모델 구성(`/model`, 모델 별칭, 환경 변수): https://code.claude.com/docs/ko/model-config
- 설정 파일(`settings.json`, `env` 블록): https://code.claude.com/docs/ko/settings

확장은 CLI 복사본을 자체적으로 포함하고 있어, 터미널의 `claude` 버전과 확장이 쓰는 버전이 다를 수
있습니다.

---

## 지원 기능

| 기능 | 지원 여부 |
| --- | --- |
| 스트리밍 응답 | 지원 |
| 도구 사용 (function calling) | 지원 |
| 비전 (이미지 입력) | 지원 |
| 확장 사고 | 지원 |
| 프롬프트 캐싱 | 지원 |
| 다중 턴 대화 | 지원 |

---

## 트러블슈팅

**401 Unauthorized**
- `ANTHROPIC_API_KEY`가 아닌 `ANTHROPIC_AUTH_TOKEN`이 설정되어 있는지 확인
- API 키가 유효한지 확인

**모델을 찾을 수 없음 / 404**
- `ANTHROPIC_BASE_URL`이 `/v1/gateway/claude`로 끝나는지 확인
- SDK가 Base URL에 `/v1/messages`를 자동으로 추가합니다

---

## Gateway 해제 (Anthropic 직접 연결로 복원)

```bash
unset ANTHROPIC_BASE_URL
unset ANTHROPIC_AUTH_TOKEN
export ANTHROPIC_API_KEY=YOUR_REAL_ANTHROPIC_KEY
```