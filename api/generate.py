from http.server import BaseHTTPRequestHandler
import json
import os
import re

from google import genai

# ── 설정 ──────────────────────────────────────────────
# 환경변수 GEMINI_MODEL 이 있으면 그걸 먼저 쓰고, 실패하면 아래 순서로 내린다.
MODEL_CANDIDATES = [
    os.environ.get("GEMINI_MODEL") or "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-flash-latest",
]
MIN_INPUT_LEN = 10
MAX_INPUT_LEN = 2000

SYSTEM_PROMPT = """당신은 청년 정책 공고문을 쉬운 말로 풀어주는 해설자입니다.
사용자가 붙여넣은 공고문 텍스트를 읽고, 아래 규칙에 따라 JSON만 출력하세요.

# 절대 규칙
1. 입력된 텍스트에 실제로 적혀 있는 내용만 사용합니다.
2. 원문에 없는 정보는 절대 만들어내지 마세요. 일반 상식이나 다른 정책 지식으로
   빈칸을 채우지 마세요.
3. 원문에서 확인할 수 없는 항목은 "공고문에 명시되지 않음" 이라고 적으세요.
4. 지원 자격을 최종 판정하지 마세요. "대상입니다" / "해당됩니다" 같은 단정 표현을
   쓰지 말고, 사용자가 스스로 확인할 수 있도록 조건을 항목으로 분해만 하세요.
5. 입력이 정책·지원사업 공고문이 아니면 is_policy 를 false 로 하고
   나머지 필드는 빈 배열 또는 빈 문자열로 두세요.
6. 입력에 "첨부 공고문 참조", "세부 사항은 별도 안내" 같은 표현이 있으면,
   해당 항목은 반드시 "공고문에 명시되지 않음" 으로 처리합니다.
   다른 유사 정책의 일반적인 기준을 가져오는 것을 금지합니다.

# 문체
- 존댓말, 행정 용어 대신 일상어를 사용합니다.
- 각 요약 문장은 45자 이내로 씁니다.
- 어려운 용어가 나오면 terms 에 풀이를 넣습니다. 최대 4개.

# 출력 형식
아래 구조의 JSON 객체 하나만 출력합니다.
설명 문장, 인사말, 마크다운 코드펜스(```) 를 절대 붙이지 마세요.

{
  "is_policy": true 또는 false,
  "title": "공고문에서 파악한 사업명 (없으면 빈 문자열)",
  "summary": ["무슨 사업인지", "무엇을 얼마나 지원하는지", "누가 어떻게 신청하는지"],
  "eligibility": [
    {"item": "조건을 한 문장으로", "note": "판단 기준일이나 예외. 없으면 빈 문자열"}
  ],
  "documents": ["필요한 서류명"],
  "deadline": "신청 기한. 원문에 없으면 공고문에 명시되지 않음",
  "terms": [
    {"word": "용어", "meaning": "한 문장 풀이"}
  ]
}

# 항목별 지침
- summary: 정확히 3개.
- eligibility: 원문의 자격 조건을 하나씩 분해합니다. 최대 8개.
  "만 19~34세", "군산시 거주", "기준 중위소득 150% 이하" 처럼
  사용자가 O/X 로 답할 수 있는 단위로 쪼개세요.
- documents: 본문과 별첨에 흩어진 서류를 모두 모읍니다. 원문에 없으면 빈 배열.
- deadline: 날짜와 시각까지 원문 그대로 옮깁니다.
"""

# ── 유틸 ──────────────────────────────────────────────
def _generate_with_model(client, model, text):
    """한 모델에 대해 Interactions → generate_content 순으로 시도한다."""
    try:
        create = getattr(getattr(client, "interactions", None), "create", None)
        if create:
            interaction = create(
                model=model,
                system_instruction=SYSTEM_PROMPT,
                input=text,
            )
            output = getattr(interaction, "output_text", None)
            if output:
                return output
            print("INTERACTIONS_EMPTY:", model)
    except Exception as e:
        print("INTERACTIONS_FALLBACK:", model, repr(e))

    response = client.models.generate_content(
        model=model,
        contents=text,
        config={
            "system_instruction": SYSTEM_PROMPT,
            "response_mime_type": "application/json",
        },
    )
    output = getattr(response, "text", None)
    if not output:
        raise RuntimeError("Gemini 응답이 비어 있습니다.")
    return output


def call_gemini(text):
    """신형 SDK를 우선 쓰되, 모델명·메서드 차이로 배포가 통째로 502가 나지 않게 한다."""
    client = genai.Client()
    seen = []
    last_error = None

    for model in MODEL_CANDIDATES:
        if not model or model in seen:
            continue
        seen.append(model)
        try:
            return _generate_with_model(client, model, text)
        except Exception as e:
            last_error = e
            print("MODEL_FALLBACK:", model, repr(e))

    raise last_error or RuntimeError("사용 가능한 Gemini 모델이 없습니다.")


def extract_json(text):
    """모델 응답에서 JSON 객체만 뽑아낸다.
    프롬프트로 코드펜스를 막아도 가끔 붙으므로 2차 방어."""
    t = (text or "").strip()

    fenced = re.search(r"```(?:json)?\s*(.*?)```", t, re.S)
    if fenced:
        t = fenced.group(1).strip()

    start, end = t.find("{"), t.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("응답에서 JSON 객체를 찾지 못했습니다.")

    return json.loads(t[start:end + 1])


def normalize(data):
    """필드 누락에 대비해 기본값을 채운다. 프론트 렌더링이 터지지 않게."""
    if not isinstance(data, dict):
        raise ValueError("JSON 객체가 아닙니다.")

    return {
        "is_policy":   bool(data.get("is_policy", False)),
        "title":       str(data.get("title") or ""),
        "summary":     [str(s) for s in (data.get("summary") or [])][:3],
        "eligibility": [
            {"item": str(e.get("item", "")), "note": str(e.get("note", "") or "")}
            for e in (data.get("eligibility") or []) if isinstance(e, dict)
        ][:8],
        "documents":   [str(d) for d in (data.get("documents") or [])],
        "deadline":    str(data.get("deadline") or "공고문에 명시되지 않음"),
        "terms": [
            {"word": str(t.get("word", "")), "meaning": str(t.get("meaning", ""))}
            for t in (data.get("terms") or []) if isinstance(t, dict)
        ][:4],
    }


# ── 핸들러 ────────────────────────────────────────────
class handler(BaseHTTPRequestHandler):

    def _send(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        # ① 요청 파싱
        try:
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            data = json.loads(raw.decode("utf-8") or "{}")
        except (ValueError, UnicodeDecodeError):
            self._send(400, {"error": "요청 형식이 올바르지 않습니다."})
            return

        # ② 입력 검증 (기획서 §4-6 의 1·2·3번)
        text = (data.get("input") or "").strip()
        if not text:
            self._send(400, {"error": "공고문 내용을 붙여넣어 주세요."})
            return
        if len(text) < MIN_INPUT_LEN:
            self._send(400, {"error": "내용이 너무 짧습니다. 지원 자격이나 서류 부분을 함께 붙여넣어 주세요."})
            return
        if len(text) > MAX_INPUT_LEN:
            self._send(400, {"error": f"{MAX_INPUT_LEN:,}자까지 입력할 수 있습니다. 지원 자격·서류·기한 부분만 붙여넣어 보세요."})
            return

        # ③ 환경변수 확인 (6번)
        if not os.environ.get("GEMINI_API_KEY"):
            print("CONFIG_ERROR: GEMINI_API_KEY is missing")
            self._send(500, {"error": "서비스 점검 중입니다. 잠시 후 다시 시도해 주세요."})
            return

        # ④ AI 호출 (4번)
        try:
            output = call_gemini(text)
        except Exception as e:
            print("GEMINI_ERROR:", repr(e))
            self._send(502, {"error": "결과를 가져오지 못했습니다. 잠시 후 다시 시도해 주세요."})
            return

        # ⑤ 응답 파싱 (5번)
        try:
            result = normalize(extract_json(output))
        except (ValueError, json.JSONDecodeError) as e:
            print("PARSE_ERROR:", repr(e), "| RAW:", (output or "")[:300])
            self._send(502, {"error": "결과를 정리하지 못했습니다. 내용을 조금 줄여서 다시 시도해 주세요."})
            return

        self._send(200, {"result": result})

    def do_GET(self):
        self._send(405, {"error": "POST /api/generate 만 지원합니다."})

    def log_message(self, format, *args):
        # Vercel Runtime Logs에만 남기고, 기본 액세스 로그 소음을 줄인다.
        print("%s - %s" % (self.address_string(), format % args))
