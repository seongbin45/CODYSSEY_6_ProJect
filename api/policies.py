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
import socket
import threading
import time
from pathlib import Path

BASE_URL = "https://www.youthcenter.go.kr"
POLICY_URL = BASE_URL + "/go/ythip/getPlcy"
CONTENT_URL = BASE_URL + "/go/ythip/getContent"
SPACE_URL = BASE_URL + "/go/ythip/getSpace"

TIMEOUT = 3.0
MAX_RETRIES = 1
BACKOFF = 0.2
PAGE_SIZE = 12
SOURCE_PAGE_SIZE = {"policy": 12, "content": 2, "space": 10}
SOURCE_DEADLINE = 3.6
MAX_BODY_BYTES = 180000
MAX_TEXT_LEN = 2000

socket.setdefaulttimeout(TIMEOUT)

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
                blob = resp.read(MAX_BODY_BYTES + 1)
                if len(blob) > MAX_BODY_BYTES:
                    raise YouthApiError("too_large", "response too large")
                raw = blob.decode("utf-8", errors="replace")
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
        item.get("lclsfNm"),
        item.get("mclsfNm"),
    ]
    return " ".join(str(p) for p in parts if p)


def region_score(item):
    """표시용 지역. 우편번호 목록에 52130이 하나 들어 있다고 군산으로 부르지 않는다."""
    title = str(item.get("plcyNm") or "")
    inst = str(item.get("sprvsnInstCdNm") or "") + " " + str(item.get("rgtrInstCdNm") or "")
    primary = title + " " + inst
    zip_cd = str(item.get("zipCd") or "")
    codes = re.findall(r"\d{5}", zip_cd)

    if any(h in primary for h in GUNSAN_HINTS):
        return 50, "군산"
    if any(h in primary for h in JEONBUK_HINTS):
        return 35, "전북"
    if len(codes) >= 5:
        return 10, "전국"
    if len(codes) == 1:
        if codes[0] in GUNSAN_ZIP_CODES:
            return 50, "군산"
        if codes[0].startswith(JEONBUK_ZIP_PREFIXES):
            return 30, "전북"
        return 5, "지역"
    if not codes:
        return 15, "전국"
    return 5, "복수 지역"


# 시·군 이름 → 우편번호 접두. 요청 zipCd 가 아니라 응답 필터용.
CITY_ZIP_PREFIXES = {
    "서울": ("11",),
    "부산": ("26",),
    "대구": ("27",),
    "인천": ("28",),
    "광주": ("29",),
    "대전": ("30",),
    "울산": ("31",),
    "세종": ("36",),
    "수원": ("162", "441"),
    "고양": ("412",),
    "용인": ("168", "446"),
    "창원": ("511", "641"),
    "청주": ("361", "431"),
    "전주": ("5211", "5214", "4511"),
    "천안": ("310", "330"),
    "제주": ("50", "63"),
    "군산": ("52130", "45130"),
    "익산": ("52180", "45180"),
    "목포": ("586",),
    "포항": ("376", "790"),
    "김해": ("508", "621"),
}

SOURCE_META = {
    "policy": {"url": POLICY_URL, "key": "YOUTH_API_KEY", "label": "정책"},
    "content": {"url": CONTENT_URL, "key": "YOUTH_CONTENT_API_KEY", "label": "콘텐츠"},
    "space": {"url": SPACE_URL, "key": "YOUTH_CENTER_API_KEY", "label": "청년공간"},
}


def _safe_int(value, default=0):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def age_ok(item, age):
    """응답의 sprtTrgt* 필드로 나이를 검사. 목록 API는 나이 쿼리를 무시한다(실측)."""
    if age is None:
        return True, "나이 미적용"
    mn = _safe_int(item.get("sprtTrgtMinAge"), 0)
    mx = _safe_int(item.get("sprtTrgtMaxAge"), 0)
    if mn and age < mn:
        return False, "최소연령 %s" % mn
    if mx and mx < 99 and age > mx:
        return False, "최대연령 %s" % mx
    if mn or mx:
        return True, "연령 %s~%s" % (mn or "?", mx or "?")
    return True, "연령 제한 없음"


def city_prefixes(city):
    city = (city or "").strip()
    if not city:
        return ()
    if city in CITY_ZIP_PREFIXES:
        return CITY_ZIP_PREFIXES[city]
    for name, prefixes in CITY_ZIP_PREFIXES.items():
        if name in city or city in name:
            return prefixes
    return ()


def region_ok(item, city, source):
    """응답 필드로 거주 시·군을 검사. getPlcy zipCd·getSpace ctpvCd 요청은 거의 무시된다(실측)."""
    city = (city or "").strip()
    if not city:
        return True, "거주 미적용"

    if source == "policy":
        codes = re.findall(r"\d{5}", str(item.get("zipCd") or ""))
        prefixes = city_prefixes(city)
        text = _blob(item)
        if city in text:
            return True, "본문·제목에 시·군명"
        if len(codes) >= 8:
            return True, "전국(우편번호 다수)"
        if not codes:
            return True, "지역 미지정"
        if prefixes and any(code.startswith(prefixes) for code in codes):
            return True, "우편번호 일치"
        return False, "거주 시·군과 우편번호 불일치"

    text = " ".join(
        str(item.get(k) or "")
        for k in (
            "pstTtl",
            "pstWholCn",
            "pstSeNm",
            "cntrNm",
            "cntrAddr",
            "cntrDaddr",
            "stdgCtpvCdNm",
            "stdgSggCdNm",
        )
    )
    if city in text:
        return True, "주소·제목에 시·군명"
    return False, "주소·제목에 시·군 없음"


def summarize(item, source="policy"):
    if source == "content":
        title = str(item.get("pstTtl") or "제목 없음")
        expl = str(item.get("pstWholCn") or "").strip()
        inst = str(item.get("pstSeNm") or "")
        uid = str(item.get("pstSn") or "")
        label = "콘텐츠"
    elif source == "space":
        title = str(item.get("cntrNm") or "이름 없음")
        expl = (str(item.get("cntrAddr") or "") + " " + str(item.get("cntrDaddr") or "")).strip()
        inst = str(item.get("stdgSggCdNm") or item.get("stdgCtpvCdNm") or "")
        uid = str(item.get("cntrSn") or "")
        label = inst or "청년공간"
    else:
        title = str(item.get("plcyNm") or "제목 없음")
        expl = str(item.get("plcyExplnCn") or item.get("plcySprtCn") or "").strip()
        inst = str(item.get("sprvsnInstCdNm") or "")
        uid = str(item.get("plcyNo") or "")
        _, label = region_score(item)
    if len(expl) > 140:
        expl = expl[:140] + "…"
    return {
        "id": uid,
        "source": source,
        "title": title,
        "summary": expl,
        "region": label,
        "inst": inst,
    }


def flatten(item, source="policy"):
    if source == "content":
        lines = ["[출처] 온통청년 getContent", str(item.get("pstTtl") or ""), str(item.get("pstWholCn") or "")]
    elif source == "space":
        lines = [
            "[출처] 온통청년 getSpace",
            "시설명: %s" % (item.get("cntrNm") or ""),
            "주소: %s %s" % (item.get("cntrAddr") or "", item.get("cntrDaddr") or ""),
            "전화: %s" % (item.get("cntrTelno") or ""),
        ]
    else:
        lines = ["[출처] 온통청년 getPlcy"]
        age_min, age_max = item.get("sprtTrgtMinAge"), item.get("sprtTrgtMaxAge")
        if age_min or age_max:
            lines.append("연령: %s~%s" % (age_min or "?", age_max or "?"))
        for key, label in TEXT_FIELDS:
            value = str(item.get(key) or "").strip()
            if value:
                lines.append("%s: %s" % (label, value))
    text = "\n".join(line for line in lines if str(line).strip()).strip()
    if len(text) > MAX_TEXT_LEN:
        text = text[: MAX_TEXT_LEN - 1] + "…"
    return text


def _matches_query(item, query, source="policy"):
    if not query:
        return True
    if source == "policy":
        blob = _blob(item).lower()
    elif source == "content":
        blob = ("%s %s" % (item.get("pstTtl") or "", item.get("pstWholCn") or "")).lower()
    else:
        blob = ("%s %s %s" % (
            item.get("cntrNm") or "",
            item.get("cntrAddr") or "",
            item.get("stdgSggCdNm") or "",
        )).lower()
    return all(token in blob for token in query.lower().split() if len(token) >= 2)


def _run_deadline(fn, seconds, *args):
    """urlopen timeout이 큰 본문에서 안 먹을 때를 대비한 하드 제한."""
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
        raise YouthApiError("timeout", "시간 초과")
    if "error" in box:
        raise box["error"]
    return box.get("value")


def fetch_source_page(source):
    # getContent 목록은 항목 1개도 본문이 약 1MB라 Vercel에서 자주 멈춘다.
    if source == "content":
        raise YouthApiError("skipped", "콘텐츠 목록 응답이 커서 고르기에서 생략")
    meta = SOURCE_META[source]
    params = policy_list_params(1)
    params["pageSize"] = SOURCE_PAGE_SIZE.get(source, PAGE_SIZE)
    payload = youth_get(meta["url"], params, meta["key"])
    return extract_items(payload)


def _filter_source(source, raw_items, query, age, city, limit=8):
    rows = []
    kept = 0
    for item in raw_items:
        if not _matches_query(item, query, source):
            continue
        ok_age, why_age = age_ok(item, age) if source == "policy" else (True, "해당 없음")
        if not ok_age:
            continue
        ok_region, why_region = region_ok(item, city, source)
        if not ok_region:
            continue
        card = summarize(item, source)
        if not card["id"]:
            continue
        card["age_check"] = why_age
        card["region_check"] = why_region
        kept += 1
        if len(rows) < limit:
            rows.append(card)
    return rows, kept


def _load_one_source(source, query, age, city):
    raw_items = fetch_source_page(source)
    rows, kept = _filter_source(source, raw_items, query, age, city)
    return {
        "source": source,
        "rows": rows,
        "fetched": len(raw_items),
        "kept": kept,
        "error": "",
    }


def list_catalog(query="", age=None, city="", sources=None):
    wanted = sources or ("policy", "content", "space")
    sent = {
        "pageNum": 1,
        "pageSize": PAGE_SIZE,
        "pageType": "1",
        "rtnType": "json",
        "note": "나이·거주는 요청 파라미터가 아니라 응답 필터로 적용(실측: getPlcy/getSpace 쿼리 무시)",
        "age": age,
        "region": city,
        "sources": list(wanted),
    }
    box = {}

    def run(source):
        try:
            box[source] = _run_deadline(
                _load_one_source, SOURCE_DEADLINE, source, query, age, city
            )
        except YouthApiError as exc:
            box[source] = {
                "source": source,
                "rows": [],
                "fetched": 0,
                "kept": 0,
                "error": exc.code,
            }
        except Exception as exc:
            box[source] = {
                "source": source,
                "rows": [],
                "fetched": 0,
                "kept": 0,
                "error": "error",
            }
            print("YOUTH_SOURCE_ERROR:", source, repr(exc))

    threads = []
    for source in wanted:
        thread = threading.Thread(target=run, args=(source,), daemon=True)
        thread.start()
        threads.append(thread)
    wall = SOURCE_DEADLINE + 0.4
    for thread in threads:
        thread.join(wall)

    rows = []
    stats = {}
    for source in wanted:
        row = box.get(source) or {
            "source": source,
            "rows": [],
            "fetched": 0,
            "kept": 0,
            "error": "timeout",
        }
        rows.extend(row["rows"])
        stats[source] = {
            "fetched": row["fetched"],
            "kept": row["kept"],
            "error": row["error"],
        }
    return rows, sent, stats


def list_policies(query, scope):
    city = ""
    if scope == "gunsan":
        city = "군산"
    rows, _, _ = list_catalog(query=query, city=city, sources=("policy",))
    return rows


def policy_detail(item_id, source="policy"):
    meta = SOURCE_META.get(source) or SOURCE_META["policy"]
    if source == "content":
        params = {"pageType": "2", "pstSn": item_id, "rtnType": "json"}
    elif source == "space":
        params = {"pageType": 2, "plcSn": item_id, "rtnType": "json"}
    else:
        params = policy_detail_params(item_id)
    payload = youth_get(meta["url"], params, meta["key"])
    items = extract_items(payload)
    if not items:
        raise YouthApiError("not_found", "item not found")
    item = items[0]
    card = summarize(item, source)
    card["text"] = flatten(item, source)
    return card


def run_cross_check():
    """나이·거주가 세 API 응답 필터에 반영되는지 콘솔에서 확인."""
    cases = [
        {"age": 17, "region": "서울"},
        {"age": 24, "region": "서울"},
        {"age": 24, "region": "부산"},
        {"age": 50, "region": "서울"},
    ]
    print("=== 교차검증: 요청 나이·거주 → 세 API 응답 필터 ===")
    print("참고: getPlcy/getContent/getSpace 목록은 나이·지역 쿼리를 거의 무시한다.")
    print("      그래서 응답의 sprtTrgt* / zipCd / 주소 필드로 거른다.\n")
    baseline, sent, stats = list_catalog()
    print("필터 없음  fetched", {k: v["fetched"] for k, v in stats.items()}, "kept", len(baseline))
    print("보낸 파라미터", sent)
    for case in cases:
        rows, _, st = list_catalog(age=case["age"], city=case["region"])
        by_src = {}
        for row in rows:
            by_src[row["source"]] = by_src.get(row["source"], 0) + 1
        print(
            "age=%s region=%s → kept %s %s  fetched=%s"
            % (case["age"], case["region"], len(rows), by_src, {k: v["fetched"] for k, v in st.items()})
        )
        for row in rows[:2]:
            print("   - [%s] %s (%s / %s)" % (row["source"], row["title"][:40], row.get("age_check"), row.get("region_check")))
    # 대조: 17세는 24세보다 정책 수가 같거나 적어야 한다
    young, _, _ = list_catalog(age=17, city="서울")
    mid, _, _ = list_catalog(age=24, city="서울")
    young_p = sum(1 for r in young if r["source"] == "policy")
    mid_p = sum(1 for r in mid if r["source"] == "policy")
    print("\n나이 필터 정책 수  17세=%s  24세=%s  (17세 <= 24세 이어야 함)" % (young_p, mid_p))
    print("PASS" if young_p <= mid_p else "FAIL 나이 필터")


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
        item_id = (qs.get("id") or [""])[0].strip()
        query = (qs.get("q") or [""])[0].strip()
        source = (qs.get("source") or ["all"])[0].strip().lower()
        if source not in {"policy", "content", "space", "all"}:
            source = "all"
        age_raw = (qs.get("age") or [""])[0].strip()
        try:
            age = int(age_raw) if age_raw else None
        except ValueError:
            age = None
        city = re.sub(r"\s+", " ", (qs.get("region") or [""])[0]).strip()[:30]
        debug = (qs.get("debug") or [""])[0] in {"1", "true", "yes"}

        try:
            if item_id:
                detail_source = source if source in SOURCE_META else "policy"
                item = _run_deadline(policy_detail, SOURCE_DEADLINE + 1.0, item_id, detail_source)
                _send(self, 200, {"item": item})
            else:
                sources = tuple(SOURCE_META) if source == "all" else (source,)
                items, sent, stats = list_catalog(query=query, age=age, city=city, sources=sources)
                payload = {"items": items, "count": len(items), "stats": stats, "applied": {
                    "age": age, "region": city, "sources": list(sources),
                }}
                if debug:
                    payload["request"] = sent
                _send(self, 200, payload)
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


if __name__ == "__main__":
    run_cross_check()
