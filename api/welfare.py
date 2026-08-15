"""공공데이터포털 — 전 연령 복지·공공서비스.

한국사회보장정보원 중앙부처/지자체, 행정안전부 정부24 공공서비스.
인증 파라미터 serviceKey = DATA_GO_KR_SERVICE_KEY
"""

from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from xml.etree import ElementTree
import json
import os
import re
import threading
import time
from pathlib import Path

TIMEOUT = 7.0
MAX_RETRIES = 2
BACKOFF = 0.35
MAX_BODY = 180000
SOURCE_DEADLINE = 7.0

GOV24_LIST = "https://api.odcloud.kr/api/gov24/v3/serviceList"
GOV24_DETAIL = "https://api.odcloud.kr/api/gov24/v3/serviceDetail"
NAT_LIST = "https://apis.data.go.kr/B554287/NationalWelfareInformationsV001/NationalWelfarelistV001"
NAT_DETAIL = "https://apis.data.go.kr/B554287/NationalWelfareInformationsV001/NationalWelfaredetailedV001"
LOCAL_LIST = "https://apis.data.go.kr/B554287/LocalGovernmentWelfareInformations/LcgvWelfarelist"
LOCAL_DETAIL = "https://apis.data.go.kr/B554287/LocalGovernmentWelfareInformations/LcgvWelfaredetailed"

# 지자체복지서비스_코드표(v1.0)
LIFE_BY_AGE = (
    (18, "001"),  # 영유아 — 보호자 답일 때도 육아 가구에서 따로 넣음
    (12, "002"),
    (18, "003"),
    (39, "004"),
    (64, "005"),
    (200, "006"),
)
LIFE_PREGNANT = "007"

HOUSEHOLD_CODE = {
    "onefam": "060",
}
DISABILITY_CODE = "040"
LOW_INCOME_CODE = "050"

INTEREST_CODE = {
    "주거": "040",
    "일자리": "050",
    "교육": "100",
    "돌봄": "120",
    "건강": "010",
    "창업": "050",
    "금융": "130",
    "문화": "060",
}
GOV24_FIELD = {
    "주거": "주거",
    "일자리": "고용",
    "교육": "교육",
    "돌봄": "보육",
    "건강": "보건",
    "창업": "산업",
    "금융": "생활",
    "문화": "문화",
}
CTPV_NM = {
    "서울": "서울특별시",
    "부산": "부산광역시",
    "대구": "대구광역시",
    "인천": "인천광역시",
    "광주": "광주광역시",
    "대전": "대전광역시",
    "울산": "울산광역시",
    "세종": "세종특별자치시",
    "경기": "경기도",
    "강원": "강원특별자치도",
    "충북": "충청북도",
    "충남": "충청남도",
    "전북": "전북특별자치도",
    "전남": "전라남도",
    "경북": "경상북도",
    "경남": "경상남도",
    "제주": "제주특별자치도",
}


def _load_dotenv():
    here = Path(__file__).resolve()
    for path in (here.parents[1] / ".env", Path.cwd() / ".env"):
        if not path.is_file():
            continue
        for raw in path.read_text(encoding="utf-8-sig").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip().strip("'").strip('"')
            if key and not os.environ.get(key, "").strip():
                os.environ[key] = val


_load_dotenv()


def _secret():
    return (
        os.environ.get("DATA_GO_KR_SERVICE_KEY")
        or os.environ.get("WELFARE_API_KEY")
        or os.environ.get("GOV_BENEFIT_API_KEY")
        or ""
    ).strip()


def _log(trace, *parts):
    line = "GOV_TRACE " + " | ".join("" if p is None else str(p) for p in parts)
    print(line)
    if trace is not None:
        trace.append(line)


class WelfareError(Exception):
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


def _parse(raw, ctype=""):
    text = (raw or "").strip()
    if not text:
        return {}
    if "json" in (ctype or "") or text[:1] in "{[":
        return json.loads(text)
    return _xml_to_dict(ElementTree.fromstring(text))


def portal_get(url, params, trace=None):
    key = _secret()
    if not key:
        raise WelfareError("missing_key", "DATA_GO_KR_SERVICE_KEY is not set")
    query = dict(params or {})
    query["serviceKey"] = key
    last = None
    for attempt in range(1, MAX_RETRIES + 1):
        started = time.time()
        shown = dict(query)
        shown["serviceKey"] = "set(len=%s)" % len(key)
        _log(trace, "get.start", url, "attempt", attempt, shown)
        try:
            req = Request(
                url + "?" + urlencode(query, safe=""),
                headers={"User-Agent": "doenayo/1.0", "Accept": "application/json, application/xml"},
            )
            with urlopen(req, timeout=TIMEOUT) as resp:
                blob = resp.read(MAX_BODY + 1)
                if len(blob) > MAX_BODY:
                    raise WelfareError("too_large", "response too large")
                ctype = resp.headers.get("Content-Type", "")
                parsed = _parse(blob.decode("utf-8", errors="replace"), ctype)
            _log(trace, "get.ok", url, "ms", int((time.time() - started) * 1000), "bytes", len(blob), "ctype", ctype)
            return parsed
        except HTTPError as exc:
            last = WelfareError("http_%s" % exc.code, str(exc))
            _log(trace, "get.http", url, exc.code, int((time.time() - started) * 1000))
            if exc.code < 500 and exc.code not in {400, 403}:
                raise last
        except URLError as exc:
            last = WelfareError("network", str(getattr(exc, "reason", exc)))
            _log(trace, "get.net", url, last)
        except Exception as exc:
            last = WelfareError("parse", str(exc))
            _log(trace, "get.parse", url, type(exc).__name__, exc)
        if attempt < MAX_RETRIES:
            time.sleep(BACKOFF * attempt)
    raise last or WelfareError("unknown", "unknown")


def _as_list(value, key):
    if isinstance(value, list):
        return [x for x in value if isinstance(x, dict)]
    if not isinstance(value, dict):
        return []
    node = value.get(key)
    if isinstance(node, list):
        return [x for x in node if isinstance(x, dict)]
    if isinstance(node, dict):
        return [node]
    for wrap in ("wantedList", "response", "body", "items"):
        inner = value.get(wrap)
        if isinstance(inner, dict):
            found = _as_list(inner, key)
            if found:
                return found
    if value.get("servId") or value.get("서비스ID"):
        return [value]
    return []


def life_codes(age, marital, household):
    codes = []
    if age is not None:
        if age < 6:
            codes.append("001")
        elif age < 13:
            codes.append("002")
        elif age < 19:
            codes.append("003")
        elif age <= 39:
            codes.append("004")
        elif age <= 64:
            codes.append("005")
        else:
            codes.append("006")
    if marital == "pregnant" or household == "kids":
        if "007" not in codes:
            codes.append("007")
        if household == "kids" and "002" not in codes:
            codes.append("002")
    return codes


def household_codes(household, marital, disability, income):
    codes = []
    if household == "onefam" or marital == "onefam":
        codes.append(HOUSEHOLD_CODE["onefam"])
    if disability in {"self", "family"}:
        codes.append(DISABILITY_CODE)
    if income is not None and income <= 50:
        codes.append(LOW_INCOME_CODE)
    return codes


def interest_codes(interests):
    out = []
    for name in interests or []:
        code = INTEREST_CODE.get(name)
        if code and code not in out:
            out.append(code)
    return out


def ctpv_name(city):
    city = (city or "").strip()
    if not city:
        return ""
    if city in CTPV_NM:
        return CTPV_NM[city]
    for short, full in CTPV_NM.items():
        if short in city or city in full:
            return full
    return city


def _clip(text, n=160):
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(text) > n:
        return text[: n - 1] + "…"
    return text


def card_from_welfare(item, source):
    if source == "benefit":
        uid = str(item.get("서비스ID") or "")
        title = str(item.get("서비스명") or "제목 없음")
        summary = item.get("서비스목적요약") or item.get("지원대상") or item.get("지원내용") or ""
        org = str(item.get("소관기관명") or "정부24")
        link = str(item.get("상세조회URL") or "https://www.gov.kr/")
        deadline = str(item.get("신청기한") or "")
        field = str(item.get("서비스분야") or "")
        return {
            "id": "gov-benefit-" + uid,
            "remoteId": uid,
            "remoteSource": "benefit",
            "source": "benefit",
            "title": title,
            "summary": _clip(summary),
            "org": org,
            "region": org,
            "inst": org,
            "cat": [field] if field else ["공공서비스"],
            "docs": [],
            "deadline": deadline or "공고 원문에서 확인",
            "link": link,
            "linkLabel": "정부24",
            "age_check": "공공서비스 목록",
            "region_check": org,
        }
    uid = str(item.get("servId") or "")
    title = str(item.get("servNm") or "제목 없음")
    summary = item.get("servDgst") or ""
    if source == "local":
        org = " ".join(x for x in (item.get("ctpvNm"), item.get("sggNm"), item.get("bizChrDeptNm")) if x)
        link = str(item.get("servDtlLink") or "https://www.bokjiro.go.kr/")
        region = str(item.get("ctpvNm") or "")
        label = "지자체 복지"
    else:
        org = str(item.get("jurMnofNm") or item.get("jurOrgNm") or "중앙부처")
        link = str(item.get("servDtlLink") or "https://www.bokjiro.go.kr/")
        region = "전국"
        label = "중앙부처 복지"
    thema = str(item.get("intrsThemaArray") or item.get("intrsThemaNmArray") or "")
    return {
        "id": "gov-%s-%s" % (source, uid),
        "remoteId": uid,
        "remoteSource": source,
        "source": source,
        "title": title,
        "summary": _clip(summary),
        "org": org or label,
        "region": region,
        "inst": org,
        "cat": [p.strip() for p in thema.split(",") if p.strip()][:3] or [label],
        "docs": [],
        "deadline": "복지로에서 확인",
        "link": link.replace("&amp;", "&"),
        "linkLabel": "복지로",
        "age_check": str(item.get("lifeArray") or item.get("lifeNmArray") or ""),
        "region_check": region or "전국",
    }


def fetch_benefit(interests, city, trace):
    params = {"page": 1, "perPage": 8, "returnType": "JSON"}
    field = ""
    for name in interests or []:
        if name in GOV24_FIELD:
            field = GOV24_FIELD[name]
            break
    if field:
        params["cond[서비스분야::LIKE]"] = field
    payload = portal_get(GOV24_LIST, params, trace)
    rows = payload.get("data") if isinstance(payload, dict) else []
    if not isinstance(rows, list):
        rows = []
    city = (city or "").strip()
    kept = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        org = str(item.get("소관기관명") or "")
        kind = str(item.get("소관기관유형") or "")
        if city and city not in org and "중앙" not in kind and "교육청" not in kind and "공공" not in kind:
            _log(trace, "filter.drop", "benefit", city, org, item.get("서비스명"))
            continue
        card = card_from_welfare(item, "benefit")
        if card["remoteId"]:
            kept.append(card)
            _log(trace, "filter.keep", "benefit", card["title"][:40], org)
    return kept


def fetch_national(life, household, interests, trace):
    params = {"pageNo": 1, "numOfRows": 8, "callTp": "L", "srchKeyCode": "001"}
    if life:
        params["lifeArray"] = ",".join(life)
    if household:
        params["trgterIndvdlArray"] = ",".join(household)
    if interests:
        params["intrsThemaArray"] = ",".join(interests)
    payload = portal_get(NAT_LIST, params, trace)
    raw = _as_list(payload, "servList")
    _log(trace, "national.raw", len(raw), "life", params.get("lifeArray"), "hh", params.get("trgterIndvdlArray"))
    return [card_from_welfare(item, "welfare") for item in raw if item.get("servId")]


def fetch_local(life, household, interests, city, trace):
    params = {"pageNo": 1, "numOfRows": 8, "callTp": "L", "srchKeyCode": "001"}
    ctpv = ctpv_name(city)
    if ctpv:
        params["ctpvNm"] = ctpv
    if life:
        params["lifeArray"] = ",".join(life)
    if household:
        params["trgterIndvdlArray"] = ",".join(household)
    if interests:
        params["intrsThemaArray"] = ",".join(interests)
    payload = portal_get(LOCAL_LIST, params, trace)
    raw = _as_list(payload, "servList")
    _log(trace, "local.raw", len(raw), "ctpvNm", ctpv)
    if not raw and city == "광주":
        params["ctpvNm"] = "전남광주통합특별시"
        payload = portal_get(LOCAL_LIST, params, trace)
        raw = _as_list(payload, "servList")
        _log(trace, "local.retry_gwangju", len(raw))
    return [card_from_welfare(item, "local") for item in raw if item.get("servId")]


def _run_deadline(fn, seconds, *args):
    box = {}

    def worker():
        try:
            box["value"] = fn(*args)
        except Exception as exc:
            box["error"] = exc

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(seconds)
    if thread.is_alive():
        raise WelfareError("timeout", "시간 초과")
    if "error" in box:
        raise box["error"]
    return box.get("value")


def list_welfare(age, city, interests, household, marital, disability, income, sources, trace):
    life = life_codes(age, marital, household)
    hh = household_codes(household, marital, disability, income)
    thema = interest_codes(interests)
    _log(trace, "list.begin", "age", age, "city", city, "life", life, "hh", hh, "thema", thema, "sources", sources)
    jobs = []
    if "benefit" in sources:
        jobs.append(("benefit", fetch_benefit, (interests, city, trace)))
    if "welfare" in sources:
        jobs.append(("welfare", fetch_national, (life, hh, thema, trace)))
    if "local" in sources:
        jobs.append(("local", fetch_local, (life, hh, thema, city, trace)))

    box = {}

    def run(name, fn, args):
        try:
            rows = _run_deadline(fn, SOURCE_DEADLINE, *args)
            box[name] = {"rows": rows, "fetched": len(rows), "kept": len(rows), "error": ""}
        except WelfareError as exc:
            _log(trace, "list.source_error", name, exc.code, exc)
            box[name] = {"rows": [], "fetched": 0, "kept": 0, "error": exc.code}
        except Exception as exc:
            _log(trace, "list.source_crash", name, repr(exc))
            box[name] = {"rows": [], "fetched": 0, "kept": 0, "error": "error"}

    threads = []
    for name, fn, args in jobs:
        thread = threading.Thread(target=run, args=(name, fn, args), daemon=True)
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join(SOURCE_DEADLINE + 0.5)

    items = []
    stats = {}
    for name, _, _ in jobs:
        row = box.get(name) or {"rows": [], "fetched": 0, "kept": 0, "error": "timeout"}
        items.extend(row["rows"][:6])
        stats[name] = {"fetched": row["fetched"], "kept": row["kept"], "error": row["error"]}
    _log(trace, "list.done", "shown", len(items), stats)
    return items, stats, {"life": life, "household": hh, "interest": thema, "ctpvNm": ctpv_name(city)}


def detail_welfare(item_id, source, trace):
    _log(trace, "detail.begin", source, item_id)
    if source == "benefit":
        payload = portal_get(GOV24_DETAIL, {
            "page": 1, "perPage": 1, "returnType": "JSON",
            "cond[서비스ID::EQ]": item_id,
        }, trace)
        rows = payload.get("data") if isinstance(payload, dict) else []
        item = rows[0] if rows else {}
        card = card_from_welfare(item, "benefit")
        docs = [p.strip("- ").strip() for p in str(item.get("구비서류") or "").splitlines() if p.strip()]
        card["docs"] = docs[:8]
        card["deadline"] = str(item.get("신청기한") or card["deadline"])
        card["summary"] = _clip(item.get("지원대상") or item.get("서비스목적") or card["summary"], 400)
        card["text"] = "\n".join([
            "[출처] 정부24 공공서비스",
            "지원대상: %s" % (item.get("지원대상") or ""),
            "선정기준: %s" % (item.get("선정기준") or ""),
            "지원내용: %s" % (item.get("지원내용") or ""),
            "신청방법: %s" % (item.get("신청방법") or ""),
            "구비서류: %s" % (item.get("구비서류") or ""),
        ])
        return card

    url = NAT_DETAIL if source == "welfare" else LOCAL_DETAIL
    params = {"servId": item_id}
    if source == "welfare":
        params["callTp"] = "D"
    payload = portal_get(url, params, trace)
    item = payload if isinstance(payload, dict) else {}
    if item.get("wantedDtl") and isinstance(item["wantedDtl"], dict):
        item = item["wantedDtl"]
    card = card_from_welfare(item, source)
    card["summary"] = _clip(item.get("tgtrDtlCn") or item.get("sprtTrgtCn") or item.get("servDgst") or card["summary"], 400)
    card["deadline"] = str(item.get("enfcEndYmd") or card["deadline"])
    card["docs"] = [str(item.get("aplyMtdCn") or "복지로·주민센터에서 확인")]
    card["text"] = "\n".join([
        "[출처] 복지로 %s" % ("중앙부처" if source == "welfare" else "지자체"),
        "대상: %s" % (item.get("tgtrDtlCn") or item.get("sprtTrgtCn") or ""),
        "선정: %s" % (item.get("slctCritCn") or ""),
        "내용: %s" % (item.get("alwServCn") or ""),
        "방법: %s" % (item.get("aplyMtdCn") or ""),
    ])
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
        source = (qs.get("source") or ["all"])[0].strip().lower()
        if source not in {"benefit", "welfare", "local", "all"}:
            source = "all"
        item_id = (qs.get("id") or [""])[0].strip()
        debug = (qs.get("debug") or [""])[0] in {"1", "true", "yes"}
        try:
            age = int((qs.get("age") or [""])[0]) if (qs.get("age") or [""])[0] else None
        except ValueError:
            age = None
        city = re.sub(r"\s+", " ", (qs.get("region") or [""])[0]).strip()[:30]
        household = (qs.get("household") or [""])[0].strip()
        marital = (qs.get("marital") or [""])[0].strip()
        disability = (qs.get("disability") or [""])[0].strip()
        try:
            income = int((qs.get("income") or [""])[0]) if (qs.get("income") or [""])[0] else None
        except ValueError:
            income = None
        interests = [p for p in re.split(r"[,\s]+", (qs.get("interests") or [""])[0]) if p]
        sources = ("benefit", "welfare", "local") if source == "all" else (source,)
        trace = []
        _log(trace, "http.get", self.path)

        try:
            if item_id:
                detail_source = source if source in {"benefit", "welfare", "local"} else "welfare"
                item = detail_welfare(item_id, detail_source, trace)
                payload = {"item": item}
            else:
                items, stats, applied = list_welfare(
                    age, city, interests, household, marital, disability, income, sources, trace
                )
                payload = {"items": items, "count": len(items), "stats": stats, "applied": applied}
            if debug:
                payload["trace"] = trace
            _send(self, 200, payload)
        except WelfareError as exc:
            _log(trace, "http.error", exc.code, exc)
            if exc.code == "missing_key":
                _send(self, 500, {"error": "공공데이터포털 키가 없습니다. DATA_GO_KR_SERVICE_KEY 를 넣어 주세요."})
            else:
                _send(self, 502, {"error": "복지·공공서비스 목록을 가져오지 못했습니다."})
        except Exception as exc:
            print("GOV_ERROR", repr(exc))
            _send(self, 502, {"error": "복지·공공서비스 목록을 가져오지 못했습니다."})

    def do_POST(self):
        _send(self, 405, {"error": "GET /api/welfare 만 지원합니다."})

    def log_message(self, format, *args):
        print("%s - %s" % (self.address_string(), format % args))
