"""Extract URL fields from live APIs and HTTP-check them."""
import json
import os
import re
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import ssl

URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.I)
CTX = ssl.create_default_context()


def load_env():
    env = Path(__file__).resolve().parents[1] / ".env"
    if not env.is_file():
        return
    for raw in env.read_text(encoding="utf-8-sig").splitlines():
        if not raw.strip() or raw.startswith("#") or "=" not in raw:
            continue
        k, _, v = raw.partition("=")
        os.environ.setdefault(k.strip(), v.strip())


def http_status(url, timeout=10):
    url = url.replace("&amp;", "&").rstrip(").,]")
    req = Request(url, headers={"User-Agent": "doenayo-urlcheck/1.0", "Accept": "text/html,*/*"})
    try:
        with urlopen(req, timeout=timeout, context=CTX) as resp:
            return resp.status, resp.geturl()[:120]
    except HTTPError as exc:
        return exc.code, url[:120]
    except Exception as exc:
        return "ERR", "%s %s" % (type(exc).__name__, exc)


def portal_get(url, params):
    q = dict(params)
    q["serviceKey"] = os.environ["DATA_GO_KR_SERVICE_KEY"]
    full = url + "?" + urlencode(q, safe="")
    with urlopen(Request(full, headers={"User-Agent": "doenayo/1.0"}), timeout=12) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def main():
    load_env()
    print("=== 1) 배포 JSON이 내려주는 link 필드 ===")
    cases = [
        ("/api/welfare", {"source": "all", "age": 24, "region": "대전", "interests": "주거", "debug": "0"}),
        ("/api/policies", {"source": "policy", "age": 24, "region": "광주", "debug": "0"}),
    ]
    mapped = []
    for path, params in cases:
        url = "https://codyssey-6-pro-ject.vercel.app" + path + "?" + urlencode(params)
        print("\nGET", path, params)
        with urlopen(Request(url, headers={"User-Agent": "xcheck"}), timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        for item in data.get("items") or []:
            link = item.get("link") or ""
            print(" MAP", item.get("source") or item.get("remoteSource"), item.get("title", "")[:28], "->", link[:90])
            mapped.append((item.get("title", "")[:40], link, item.get("source") or item.get("remoteSource")))

    print("\n=== 2) 정부24 원본 JSON URL 필드 ===")
    gov = portal_get("https://api.odcloud.kr/api/gov24/v3/serviceList", {
        "page": 1, "perPage": 5, "returnType": "JSON",
    })
    raw_urls = []
    for row in gov.get("data") or []:
        print(" RAW benefit", row.get("서비스명", "")[:28])
        for key in ("상세조회URL", "온라인신청사이트URL"):
            val = row.get(key)
            if val:
                print("   ", key, val[:100])
                raw_urls.append((row.get("서비스명", "")[:30], key, val))

    print("\n=== 3) HTTP 상태 (매핑된 link + 원본 URL) ===")
    seen = set()
    for title, link, src in mapped:
        if not link or link in seen:
            continue
        seen.add(link)
        code, final = http_status(link)
        print(" CHK", code, src, title[:24], "|", link[:80], "| final", final)
    for title, key, link in raw_urls:
        if link in seen:
            continue
        seen.add(link)
        code, final = http_status(link)
        print(" RAWCHK", code, key, title[:24], "|", link[:80])


if __name__ == "__main__":
    main()
