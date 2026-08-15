"""온통청년 Open API — 군산 대시보드 finfit_youth 클라이언트를 Vercel용으로 옮긴 버전.

참고 코드
  other/GunSan-youth-dashboard-KOSIS-main/.../finfit_youth/client.py
  other/GunSan-youth-dashboard-KOSIS-main/.../finfit_youth/service.py
  other/GunSan-youth-dashboard-KOSIS-main/.../finfit_youth/benefits_matcher.py

엔드포인트 / 인증 (client.py)
  GET https://www.youthcenter.go.kr/go/ythip/getPlcy     apiKeyNm=YOUTH_API_KEY
  GET https://www.youthcenter.go.kr/go/ythip/getContent  apiKeyNm=YOUTH_CONTENT_API_KEY
  GET https://www.youthcenter.go.kr/go/ythip/getSpace    apiKeyNm=YOUTH_CENTER_API_KEY
  http 는 https 로, :8080 은 제거. 403/5xx 는 재시도.

목록/상세 (service.py)
  목록  pageType=1, pageNum, pageSize, rtnType=json
  상세  pageType=2, plcyNo, rtnType=json
"""

from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from xml.etree import ElementTree
import json
import os
import re
import time
from pathlib import Path

BASE_URL = "https://www.youthcenter.go.kr"
POLICY_URL = BASE_URL + "/go/ythip/getPlcy"
CONTENT_URL = BASE_URL + "/go/ythip/getContent"
SPACE_URL = BASE_URL + "/go/ythip/getSpace"

TIMEOUT = 8.0
MAX_RETRIES = 3
BACKOFF = 0.7
PAGE_SIZE = 100
MAX_TEXT_LEN = 2000

GUNSAN_HINTS = ("군산", "Gunsan", "GUNSAN")
JEONBUK_HINTS = ("전북", "전라북", "전북특별", "전북자치")
JEONBUK_ZIP_PREFIXES = ("52", "45")
GUNSAN_ZIP_CODES = ("52130", "45130")  # 전북특별자치도 군산시 / 개편 전

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


def _load_dotenv():
    """config.py 와 같이 KEY=VALUE 를 프로세스 환경에 채운다. 이미 있는 값은 덮지 않는다."""
    here = Path(__file__).resolve()
    candidates = [
        here.parents[1] / ".env",
        here.parents[1] / ".env.local",
        Path.cwd() / ".env",
    ]
    seen = set()
    for path in candidates:
        try:
            path = path.resolve()
        except OSError:
            continue
        if path in seen or not path.is_file():
            continue
        seen.add(path)
        for raw in path.read_text(encoding="utf-8-sig").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            if line.lower().startswith("export "):
                line = line[7:].strip()
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip().strip("'").strip('"')
            if key and not os.environ.get(key, "").strip():
                os.environ[key] = val


_load_dotenv()


def _secret(name, default=""):
    return (os.environ.get(name) or default).strip()


def _safe_url(url):
    url = (url or "").strip()
    if url.startswith("http://"):
        url = "https://" + url[len("http://"):]
    return url.replace(":8080", "").rstrip("/")


class YouthApiError(Exception):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def _xml_to_dict(element):
    children = list(element)
    if not children:
        return element.text or ""
    result = {}
    for child in children:
        value = _xml_to_dict(child)
        if child.tag in result:
            existing = result[child.tag]
            if isinstance(existing, list):
                existing.append(value)
            else:
                result[child.tag] = [existing, value]
        else:
            result[child.tag] = value
    return result


def _parse_body(text, content_type=""):
    text = (text or "").strip()
    if not text:
        return {}
    if "json" in (content_type or "") or text[:1] in "{[":
        return json.loads(text)
    root = ElementTree.fromstring(text)
    return _xml_to_dict(root)


def youth_get(url, params, key_name):
    """client.YouthApiClient.get 과 같은 인증·재시도."""
    endpoint = _safe_url(url)
    key = _secret(key_name)
    if not key:
        raise YouthApiError("missing_key", key_name + " is not set")

    query = dict(params or {})
    if any(path in endpoint for path in ("/go/ythip/getPlcy", "/go/ythip/getContent", "/go/ythip/getSpace")):
        query["apiKeyNm"] = key
        query.pop("openApiVlak", None)
    else:
        query["openApiVlak"] = key

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = Request(
                endpoint + "?" + urlencode(query),
                headers={"User-Agent": "doenayo/1.0", "Accept": "application/json"},
            )
            with urlopen(req, timeout=TIMEOUT) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                ctype = resp.headers.get("Content-Type", "")
            return _parse_body(raw, ctype)
        except HTTPError as exc:
            last_error = YouthApiError("http_%s" % exc.code, str(exc))
            if exc.code < 500 and exc.code != 403:
                raise last_error
        except URLError as exc:
            last_error = YouthApiError("network", str(exc.reason if hasattr(exc, "reason") else exc))
        except Exception as exc:
            last_error = YouthApiError("parse", str(exc))
        if attempt < MAX_RETRIES:
            time.sleep(BACKOFF * attempt)
    raise last_error or YouthApiError("unknown", "unknown API error")


def extract_items(payload):
    """service.YouthDataService._extract_list 와 동일 키 순서."""
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("youthPolicyList", "youthContentList", "youthCenterList", "result", "data", "list", "items"):
        value = payload.get(key)
        if isinstance(value, list):
            return [x for x in value if isinstance(x, dict)]
        if isinstance(value, dict):
            nested = extract_items(value)
            if nested:
                return nested
    if payload.get("plcyNo") or payload.get("plcyNm") or payload.get("pstSn"):
        return [payload]
    return []


def policy_list_params(page_num=1):
    return {
        "pageNum": page_num,
        "pageSize": PAGE_SIZE,
        "pageType": "1",
        "rtnType": "json",
    }


def policy_detail_params(plcy_no):
    return {
        "pageType": "2",
        "plcyNo": plcy_no,
        "rtnType": "json",
    }


def _blob(item):
    parts = [
        item.get("plcyNm"),
        item.get("plcyExplnCn"),
        item.get("plcySprtCn"),
        item.get("plcyKywdNm"),
        item.get("sprvsnInstCdNm"),
        item.get("operInstCdNm"),
        item.get("rgtrInstCdNm"),
        item.get("ptcpPrpTrgtCn"),
        item.get("zipCd"),
        item.get("lclsfNm"),
        item.get("mclsfNm"),
    ]
    return " ".join(str(p) for p in parts if p)


def region_score(item):
    """benefits_matcher._region_score 와 같은 군산/전북 가점."""
    blob = _blob(item)
    inst = str(item.get("sprvsnInstCdNm") or "") + str(item.get("rgtrInstCdNm") or "")
    zip_cd = str(item.get("zipCd") or "")
    if any(h in blob for h in GUNSAN_HINTS) or "군산" in inst:
        return 50, "군산"
    if any(h in blob or h in inst for h in JEONBUK_HINTS):
        return 35, "전북"
    codes = re.findall(r"\d{5}", zip_cd)
    if any(c in GUNSAN_ZIP_CODES for c in codes):
        return 50, "군산"
    if codes and any(c.startswith(JEONBUK_ZIP_PREFIXES) for c in codes):
        return 30, "전북"
    if not zip_cd.strip():
        return 15, "전국"
    return 5, "기타"


def summarize(item, region_label):
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


def flatten(item):
    lines = ["[출처] 온통청년 getPlcy"]
    age_min, age_max = item.get("sprtTrgtMinAge"), item.get("sprtTrgtMaxAge")
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
    blob = _blob(item).lower()
    return all(token in blob for token in query.lower().split() if len(token) >= 2)


def fetch_policy_page(page_num=1):
    payload = youth_get(POLICY_URL, policy_list_params(page_num), "YOUTH_API_KEY")
    return extract_items(payload)


def list_policies(query, scope):
    # 참고 서비스는 전 페이지를 캐시한다. Vercel 한도 안에서는 1페이지.
    # getPlcy 는 zipCd 5자리만 받는다. 52130 = 군산시 (실측).
    params = policy_list_params(1)
    if scope in {"gunsan", "jeonbuk"}:
        params["zipCd"] = "52130"
    items = extract_items(youth_get(POLICY_URL, params, "YOUTH_API_KEY"))
    rows = []
    for item in items:
        if not _matches_query(item, query):
            continue
        score, label = region_score(item)
        if scope == "gunsan" and score < 50:
            continue
        if scope != "all" and score < 30:
            continue
        card = summarize(item, label)
        if not card["id"]:
            continue
        card["_score"] = score
        rows.append(card)
    rows.sort(key=lambda r: (-r["_score"], r["title"]))
    for row in rows:
        row.pop("_score", None)
    return rows[:30]


def policy_detail(plcy_no):
    payload = youth_get(POLICY_URL, policy_detail_params(plcy_no), "YOUTH_API_KEY")
    items = extract_items(payload)
    if not items:
        raise YouthApiError("not_found", "policy not found")
    item = items[0]
    _, label = region_score(item)
    card = summarize(item, label)
    card["text"] = flatten(item)
    return card


def _send(handler, status, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


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
        except YouthApiError as exc:
            if exc.code == "missing_key":
                _send(self, 500, {
                    "error": "온통청년 연결이 준비되지 않았습니다. Vercel에 YOUTH_API_KEY 를 넣거나 공고문을 붙여넣어 주세요.",
                })
            elif exc.code == "not_found":
                _send(self, 404, {"error": "해당 정책을 찾지 못했습니다."})
            else:
                print("YOUTH_API_ERROR:", exc.code, str(exc))
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
