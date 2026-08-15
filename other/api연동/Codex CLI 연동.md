# Codex CLI 연동

OpenAI의 터미널 코딩 에이전트 Codex CLI를 <TenantName /> Gateway와 함께 사용해보세요!

설정 파일에 프로바이더 하나만 등록하면 파일 생성·수정, 셸 명령 실행, 테스트 실행까지 Codex의 에이전트 루프 전체가 Gateway를 통해 동작합니다. 사용량은 <TenantName /> 계정의 크레딧으로 집계됩니다.

<Indent mt={12} />

- 공식 레퍼런스: [Codex CLI 문서](https://developers.openai.com/codex/cli)

<Banner variant="info">
  시작하기 전에 <TenantName /> API 키가 필요합니다. [인증 가이드](/docs/gateway/getting-started/authentication)에서 발급 방법을 확인해주세요.
</Banner>

## 설치

```bash
npm install -g @openai/codex

codex --version
# codex-cli 0.146.0
```

---

## 설정

Codex CLI는 ChatGPT 로그인 대신 **커스텀 프로바이더 + API 키** 방식으로 Gateway에 연결합니다. `~/.codex/config.toml`을 만들거나 아래 내용을 추가합니다.

```toml
model = "gpt-5.4"
model_provider = "factchat"

[model_providers.factchat]
name = "FactChat"
base_url = "https://factchat-cloud.mindlogic.ai/v1/gateway"
env_key = "FACTCHAT_API_KEY"
wire_api = "responses"
```

그리고 API 키를 환경 변수로 설정합니다.

```bash
export FACTCHAT_API_KEY=YOUR_API_KEY
```

<Accordion>
  <AccordionButton>
    base_url에 `/responses`를 붙이면 안 되나요?
  </AccordionButton>
  <AccordionPanel>
    붙이면 404가 발생합니다. Codex CLI가 `wire_api = "responses"` 설정에 따라 `base_url` 뒤에 `/responses`를 자동으로 붙이기 때문에, `base_url`은 반드시 `.../v1/gateway`까지만 지정해야 합니다.
  </AccordionPanel>
</Accordion>

---

## 연결 확인

```bash
codex exec "Reply with exactly: OK"
# OK
```

인터랙티브 모드는 `codex`만 입력하면 실행됩니다.

---

## 실제 사용 예시

셸 도구 호출을 포함한 에이전트 루프가 Gateway 경유로 그대로 동작합니다.

```bash
mkdir -p ~/codex-demo && cd ~/codex-demo

codex exec --skip-git-repo-check -s workspace-write \
  "Create fizzbuzz.py printing FizzBuzz for 1..15, run it, show output."
```

실행 결과 — 모델이 파일을 직접 생성하고, 셸로 실행한 뒤 출력까지 확인해 돌려줍니다.

```text
Created fizzbuzz.py and ran it successfully.

Output:
1
2
Fizz
4
Buzz
Fizz
7
8
Fizz
Buzz
11
Fizz
13
14
FizzBuzz

tokens used
13,749
```

```bash
ls
# fizzbuzz.py
```

<Banner variant="info">
  Codex는 기본적으로 `read-only` 샌드박스로 실행되므로 파일을 쓰지 못합니다. 파일을 생성·수정하려면 `-s workspace-write`를 지정하세요. Git 저장소가 아닌 디렉터리에서는 `--skip-git-repo-check`가 필요합니다.
</Banner>

---

## 모델 지정

```bash
# 실행 시 모델 지정
codex exec -m gpt-5.6-terra "Reply with exactly: OK"

# 인터랙티브 세션에서
codex -m gpt-5.6-terra
```

사용 가능한 모델 목록은 Gateway에서 조회할 수 있습니다.

```bash
curl "https://factchat-cloud.mindlogic.ai/v1/gateway/models/" \
  -H "Authorization: Bearer $FACTCHAT_API_KEY"
```

<Banner variant="warning">
  Codex 전용 튜닝 모델(`gpt-5.x-codex` 계열)은 기관 설정에 따라 노출되지 않을 수 있습니다. 목록에 없으면 기관 관리자에게 모델 사용 허용을 요청해주세요. 일반 `gpt-5.x` 모델은 Codex CLI에서 동일하게 동작합니다.
</Banner>

---

## 지원 기능

| 기능 | 지원 여부 |
| --- | --- |
| 셸 도구 호출 (명령 실행) | 지원 |
| 파일 생성·수정 (`-s workspace-write`) | 지원 |
| 스트리밍 응답 | 지원 |
| 추론(reasoning) 모델 | 지원 |
| 멀티 턴 세션 (`codex exec resume`) | 지원 |
| 이미지 첨부 (`-i`) | 모델별 지원 |
| 크레딧 사용량 집계 | 지원 (API 키 소유 계정에 차감) |

크레딧 잔액은 아래로 확인할 수 있습니다.

```bash
curl "https://factchat-cloud.mindlogic.ai/v1/gateway/credits/" \
  -H "Authorization: Bearer $FACTCHAT_API_KEY"
```

---

## 트러블슈팅

**401 Unauthorized**
- `FACTCHAT_API_KEY` 환경 변수가 현재 셸에 설정되어 있는지 확인
- `config.toml`의 `env_key` 값과 실제 환경 변수 이름이 일치하는지 확인

**404 Not Found**
- `base_url`이 `.../v1/gateway`로 끝나는지 확인 (`/responses`를 직접 붙이면 404)
- `wire_api = "responses"`가 설정되어 있는지 확인

**모델을 찾을 수 없음**
- Gateway `/models/` 목록에 해당 모델 ID가 있는지 확인
- 기관 관리자 설정에서 해당 모델이 허용돼 있는지 확인

**ChatGPT 로그인 화면으로 이동함**
- `model_provider = "factchat"`가 최상단에 설정돼 있는지 확인. 프로바이더가 지정되지 않으면 Codex는 기본 OpenAI 인증을 시도합니다.

**응답이 차단되거나 알 수 없는 형식으로 돌아옴**
- 기관 관리자 설정의 데이터 보안 > Gateway API 항목이 켜져 있으면 PII·금칙어 정책이 Gateway 트래픽에도 적용됩니다. 관리자에게 정책 적용 범위를 확인해주세요.

---

## Gateway 해제 (OpenAI 직접 연결로 복원)

`~/.codex/config.toml`에서 `model_provider` 줄을 제거하거나 아래처럼 실행 시점에만 우회합니다.

```bash
codex exec -c model_provider="openai" "..."
```