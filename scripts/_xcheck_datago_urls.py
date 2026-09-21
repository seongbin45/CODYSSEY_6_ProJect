"""data.go.kr 원본 URL vs 배포 카드 link 1:1 교차검증."""
import json
import os
import re
from pathlib import Path
from urllib.parse import urlencode, unquote
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import ssl
from xml.etree import ElementTree

CTX = ssl.create_default_context()
URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.I)


def load_env():
    env = Path(__file__).resolve().parents[1] / ".env"
    for raw in env.read_text(encoding="utf-8-sig").splitlines():
        if not raw.strip() or raw.startswith("#") or "=" not in raw:
            continue
        k, _, v = raw.partition("=")
        os.environ.setdefault(k.strip(), v.strip())


def http_check(url):
    url = (url or "").replace("&amp;", "&").strip()
    if not url.startswith("http"):
        return "NOURL", url
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 doenayo-urlcheck", "Accept": "text/html,*/*"})
    try:
        with urlopen(req, timeout=10, context=CTX) as resp:
            return str(resp.status), resp.geturl()[:90]
    except HTTPError as exc:
        return str(exc.code), url[:90]
    except Exception as exc:
        return type(exc).__name__, str(exc)[:80]


def get_json(url, params):
    q = dict(params)
    q["serviceKey"] = os.environ["DATA_GO_KR_SERVICE_KEY"]
    full = url + "?" + urlencode(q, safe="")
    with urlopen(Request(full, headers={"User-Agent": "doenayo/1.0"}), timeout=12) as resp:
        raw = resp.read()
        text = raw.decode("utf-8", errors="replace")
        if text[:1] in "{[":
            return json.loads(text)
        return ElementTree.fromstring(text)


def xml_serv_list(root):
    rows = []
    for node in root.findall(".//servList"):
        item = {child.tag: (child.text or "") for child in list(node)}
        rows.append(item)
    return rows


def urls_in(item):
    found = []
    for key, val in item.items():
        text = str(val or "")
        if "http" in text.lower() or "URL" in key or "Link" in key or "url" in key.lower():
            for m in URL_RE.findall(text.replace("&amp;", "&")):
                found.append((key, m))
    return found


def deploy_cards():
    url = "https://codyssey-6-pro-ject.vercel.app/api/welfare?" + urlencode({
        "source": "all", "age": 24, "region": "대전", "interests": "주거,건강", "debug": "0",
    })
    with urlopen(Request(url, headers={"User-Agent": "xcheck"}), timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8", errors="replace"))
    return data.get("items") or []


def main():
    load_env()
    print("KEY", bool(os.environ.get("DATA_GO_KR_SERVICE_KEY")))

    print("\n======== A. 정부24 serviceList 원본 ========")
    gov = get_json("https://api.odcloud.kr/api/gov24/v3/serviceList", {
        "page": 1, "perPage": 6, "returnType": "JSON", "cond[서비스분야::LIKE]": "주거",
    })
    gov_rows = gov.get("data") or []
    for row in gov_rows:
        print("ID", row.get("서비스ID"), row.get("서비스명", "")[:30])
        print("  keys", [k for k in row.keys() if "URL" in k or "url" in k.lower() or "사이트" in k])
        for key, href in urls_in(row):
            print("  RAW", key, href)

    print("\n======== B. 중앙부처 복지 목록 원본 ========")
    nat = get_json("https://apis.data.go.kr/B554287/NationalWelfareInformationsV001/NationalWelfarelistV001", {
        "pageNo": 1, "numOfRows": 6, "callTp": "L", "srchKeyCode": "001", "lifeArray": "004", "intrsThemaArray": "040",
    })
    nat_rows = xml_serv_list(nat)
    for row in nat_rows:
        print("ID", row.get("servId"), row.get("servNm", "")[:30])
        for key, href in urls_in(row):
            print("  RAW", key, href)

    print("\n======== C. 지자체 복지 목록 원본 (대전) ========")
    loc = get_json("https://apis.data.go.kr/B554287/LocalGovernmentWelfareInformations/LcgvWelfarelist", {
        "pageNo": 1, "numOfRows": 6, "callTp": "L", "srchKeyCode": "001", "ctpvNm": "대전광역시",
    })
    loc_rows = xml_serv_list(loc)
    for row in loc_rows:
        print("ID", row.get("servId"), row.get("servNm", "")[:30], row.get("ctpvNm"))
        for key, href in urls_in(row):
            print("  RAW", key, href)

    print("\n======== D. 배포 /api/welfare 카드 link vs 원본 ========")
    cards = deploy_cards()
    raw_by_id = {}
    for row in gov_rows:
        raw_by_id[("benefit", row.get("서비스ID"))] = row.get("상세조회URL") or ""
    for row in nat_rows:
        raw_by_id[("welfare", row.get("servId"))] = (row.get("servDtlLink") or "").replace("&amp;", "&")
    for row in loc_rows:
        raw_by_id[("local", row.get("servId"))] = (row.get("servDtlLink") or "").replace("&amp;", "&")

    print("deploy_count", len(cards))
    mismatch = 0
    checked = []
    for card in cards:
        src = card.get("remoteSource") or card.get("source")
        rid = card.get("remoteId")
        mapped = (card.get("link") or "").replace("&amp;", "&")
        raw = raw_by_id.get((src, rid))
        same = None if raw is None else (unquote(mapped) == unquote(raw) or mapped == raw or (raw and raw in mapped) or (mapped and mapped in raw))
        if raw is None:
            mark = "NO_RAW_THIS_PAGE"
        elif same:
            mark = "MATCH"
        else:
            mark = "MISMATCH"
            mismatch += 1
        print(mark, src, (card.get("title") or "")[:24])
        print("   mapped", mapped[:110])
        if raw is not None:
            print("   raw   ", raw[:110])
        checked.append((card.get("title"), src, mapped))

    print("\n======== E. HTTP 상태 (카드 link) ========")
    seen = set()
    for title, src, href in checked:
        if not href or href in seen:
            continue
        seen.add(href)
        code, final = http_check(href)
        print(code, src, (title or "")[:22], href[:85], "|", final)

    print("\n======== F. 정부24 상세의 온라인신청사이트URL ========")
    if gov_rows:
        sid = gov_rows[0].get("서비스ID")
        detail = get_json("https://api.odcloud.kr/api/gov24/v3/serviceDetail", {
            "page": 1, "perPage": 1, "returnType": "JSON",
            "cond[서비스ID::EQ]": sid,
        })
        drow = (detail.get("data") or [{}])[0]
        print("detail", drow.get("서비스명"))
        for key in ("상세조회URL", "온라인신청사이트URL"):
            print(" ", key, drow.get(key))
        href = drow.get("온라인신청사이트URL") or ""
        if href:
            print(" apply HTTP", http_check(href))

    print("\nMISMATCH_COUNT", mismatch)


if __name__ == "__main__":
    main()
