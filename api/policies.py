"""온통청년 정책 목록·상세.

참고: other/GunSan-youth-dashboard-KOSIS-main
  - GET https://www.youthcenter.go.kr/go/ythip/getPlcy
  - 인증 파라미터 apiKeyNm
  - 군산/전북 가점은 zipCd·기관명·본문 휴리스틱 (finfit_youth/benefits_matcher.py)
"""

from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import json
import os
import re

POLICY_URL = "https://www.youthcenter.go.kr/go/ythip/getPlcy"
TIMEOUT = 8
PAGE_SIZE = 50

GUNSAN_HINTS = ("군산", "Gunsan", "GUNSAN")
JEONBUK_HINTS = ("전북", "전라북", "전북특별", "전북자치")
JEONBUK_ZIP_PREFIXES = ("52", "45")  # 전북특별자치도 / 개편 전 전북

# 상세를 공고문 텍스트로 펼칠 때 쓰는 필드 (있는 것만)
TEXT_FIELDS = (
    ("plcyNm", "사업명"),
    ("plcyKywdNm", "키워드"),
    ("lclsfNm", "대분류"),
    ("mclsfNm", "중분류"),
    ("plcyExplnCn", "정책 설명"),
    ("plcySprtCn", "지원 내용"),
    ("ptcpPrpTrgtCn", "참여 대상"),
    ("addAplyQlfcCndCn", "추가 자격"),
    ("earnEtcCn", "소득 조건"),
    ("aplyYmd", "신청 기간"),
    ("sbmsnDcmntCn", "제출 서류"),
    ("aplyMthdCn", "신청 방법"),
    ("srngMthdCn", "심사 방법"),
    ("sprvsnInstCdNm", "주관 기관"),
    ("operInstCdNm", "운영 기관"),
    ("inqplCtpcNm", "문의처"),
    ("aplyUrlAddr", "신청 주소"),
    ("refUrlAddr1", "참고 주소"),
)

MAX_TEXT_LEN = 2000


def _send(handler, status, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _youth_get(params):
    key = (os.environ.get("YOUTH_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("missing_key")

    query = dict(params)
    query["apiKeyNm"] = key
    query.setdefault("rtnType", "json")
    url = POLICY_URL + "?" + urlencode(query)
    req = Request(url, headers={"User-Agent": "doenayo/1.0"})
    try:
        with urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        raise RuntimeError("http_%s" % exc.code) from exc
    except URLError as exc:
        raise RuntimeError("network") from exc

    text = (raw or "").strip()
    if not text:
        return {}
    if text.startswith("{") or text.startswith("["):
        return json.loads(text)
    raise RuntimeError("bad_payload")


def _extract_items(payload):
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("youthPolicyList", "result", "data", "list", "items"):
        value = payload.get(key)
        if isinstance(value, list):
            return [x for x in value if isinstance(x, dict)]
        if isinstance(value, dict):
            nested = _extract_items(value)
            if nested:
                return nested
    if payload.get("plcyNo") or payload.get("plcyNm"):
        return [payload]
    return []


def _blob(item):
    parts = [
        item.get("plcyNm"),
        item.get("plcyExplnCn"),
        item.get("plcySprtCn"),
        item.get("plcyKywdNm"),
        item.get("sprvsnInstCdNm"),
        item.get("operInstCdNm"),
        item.get("ptcpPrpTrgtCn"),
        item.get("zipCd"),
        item.get("rgtrInstCdNm"),
    ]
    return " ".join(str(p) for p in parts if p)


def _region_score(item):
    blob = _blob(item)
    inst = str(item.get("sprvsnInstCdNm") or "") + str(item.get("rgtrInstCdNm") or "")
    zip_cd = str(item.get("zipCd") or "")
    if any(h in blob for h in GUNSAN_HINTS) or "군산" in inst:
        return 50, "군산"
    if any(h in blob or h in inst for h in JEONBUK_HINTS):
        return 35, "전북"
    codes = re.findall(r"\d{5}", zip_cd)
    if codes and any(c.startswith(JEONBUK_ZIP_PREFIXES) for c in codes):
        return 30, "전북"
    if not zip_cd.strip():
        return 15, "전국"
    return 5, "기타"


def _summarize(item, region_label):
    expl = str(item.get("plcyExplnCn") or item.get("plcySprtCn") or "").strip()
    if len(expl) > 140:
        expl = expl[:140] + "…"
    return {
        "id": str(item.get("plcyNo") or ""),
        "title": str(item.get("plcyNm") or "제목 없음"),
        "summary": expl,
        "region": region_label,
        "inst": str(item.get("sprvsnInstCdNm") or ""),
    }


def _flatten(item):
    lines = ["[출처] 온통청년 정책 API"]
    age_min = item.get("sprtTrgtMinAge")
    age_max = item.get("sprtTrgtMaxAge")
    if age_min or age_max:
        lines.append("연령: %s~%s" % (age_min or "?", age_max or "?"))
    for key, label in TEXT_FIELDS:
        value = str(item.get(key) or "").strip()
        if value:
            lines.append("%s: %s" % (label, value))
    text = "\n".join(lines).strip()
    if len(text) > MAX_TEXT_LEN:
        text = text[: MAX_TEXT_LEN - 1] + "…"
    return text


def _matches_query(item, query):
    if not query:
        return True
    blob = (_blob(item) + " " + str(item.get("title") or "")).lower()
    return all(token in blob for token in query.lower().split() if len(token) >= 2)


def list_policies(query, scope):
    keywords = []
    if query:
        keywords.append(query)
    elif scope == "gunsan":
        keywords.append("군산")
    else:
        keywords.extend(["군산", "전북"])

    seen = {}
    last_error = None
    for keyword in keywords[:2]:
        try:
            payload = _youth_get({
                "pageNum": 1,
                "pageSize": PAGE_SIZE,
                "pageType": "1",
                "keyword": keyword,
            })
        except Exception as exc:
            last_error = exc
            continue
        for item in _extract_items(payload):
            pid = str(item.get("plcyNo") or "")
            if pid:
                seen[pid] = item

    if not seen and last_error:
        raise last_error

    if not seen:
        payload = _youth_get({
            "pageNum": 1,
            "pageSize": PAGE_SIZE,
            "pageType": "1",
        })
        for item in _extract_items(payload):
            pid = str(item.get("plcyNo") or "")
            if pid:
                seen[pid] = item

    rows = []
    for item in seen.values():
        if not _matches_query(item, query):
            continue
        score, label = _region_score(item)
        if scope == "gunsan" and score < 50:
            continue
        if scope != "all" and score < 30:
            continue
        card = _summarize(item, label)
        card["_score"] = score
        rows.append(card)

    rows.sort(key=lambda r: (-r["_score"], r["title"]))
    for row in rows:
        row.pop("_score", None)
    return rows[:30]


def policy_detail(plcy_no):
    payload = _youth_get({
        "pageType": "2",
        "plcyNo": plcy_no,
    })
    items = _extract_items(payload)
    if not items:
        raise RuntimeError("not_found")
    item = items[0]
    score, label = _region_score(item)
    card = _summarize(item, label)
    card["text"] = _flatten(item)
    card["_score"] = score
    card.pop("_score", None)
    return card


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        qs = parse_qs(urlparse(self.path).query)
        plcy_no = (qs.get("id") or [""])[0].strip()
        query = (qs.get("q") or [""])[0].strip()
        scope = (qs.get("scope") or ["jeonbuk"])[0].strip().lower()
        if scope not in {"gunsan", "jeonbuk", "all"}:
            scope = "jeonbuk"

        try:
            if plcy_no:
                _send(self, 200, {"item": policy_detail(plcy_no)})
            else:
                items = list_policies(query, scope)
                _send(self, 200, {"items": items, "count": len(items)})
        except RuntimeError as exc:
            code = str(exc)
            if code == "missing_key":
                _send(self, 500, {
                    "error": "온통청년 연결이 준비되지 않았습니다. 공고문을 직접 붙여넣어 주세요.",
                })
                return
            if code == "not_found":
                _send(self, 404, {"error": "해당 정책을 찾지 못했습니다."})
                return
            print("YOUTH_API_ERROR:", repr(exc))
            _send(self, 502, {
                "error": "온통청년에서 목록을 가져오지 못했습니다. 잠시 후 다시 시도하거나 직접 붙여넣어 주세요.",
            })
        except Exception as exc:
            print("YOUTH_API_ERROR:", repr(exc))
            _send(self, 502, {
                "error": "온통청년에서 목록을 가져오지 못했습니다. 잠시 후 다시 시도하거나 직접 붙여넣어 주세요.",
            })

    def do_POST(self):
        _send(self, 405, {"error": "GET /api/policies 만 지원합니다."})

    def log_message(self, format, *args):
        print("%s - %s" % (self.address_string(), format % args))
