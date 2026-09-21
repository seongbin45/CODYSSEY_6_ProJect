"""Probe data.go.kr welfare/gov24 APIs. Do not print the raw key."""
import os
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


def load_env():
    for raw in (Path(__file__).resolve().parents[1] / ".env").read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip("'").strip('"'))


def get(url, params):
    key = os.environ["DATA_GO_KR_SERVICE_KEY"]
    query = dict(params)
    query["serviceKey"] = key
    full = url + "?" + urlencode(query, safe="")
    shown = url + "?" + urlencode({**params, "serviceKey": "set(len=%s)" % len(key)})
    print("GET", shown)
    req = Request(full, headers={"User-Agent": "doenayo/1.0", "Accept": "application/json, application/xml"})
    try:
        with urlopen(req, timeout=12) as resp:
            raw = resp.read(200000)
            print("status", resp.status, "bytes", len(raw), "ctype", resp.headers.get("Content-Type"))
            text = raw.decode("utf-8", errors="replace")
            print(text[:900].replace("\n", " "))
            print("---")
            return text
    except HTTPError as exc:
        print("HTTP", exc.code, exc.read()[:400])
    except URLError as exc:
        print("NET", exc.reason)


if __name__ == "__main__":
    load_env()
    print("key_set", bool(os.environ.get("DATA_GO_KR_SERVICE_KEY")))

    get("https://api.odcloud.kr/api/gov24/v3/serviceList", {
        "page": 1, "perPage": 3, "returnType": "JSON",
        "cond[사용자구분::LIKE]": "개인",
    })
    get("https://apis.data.go.kr/B554287/NationalWelfareInformationsV001/NationalWelfarelistV001", {
        "pageNo": 1, "numOfRows": 3, "callTp": "L", "srchKeyCode": "001",
        "lifeArray": "004",
    })
    get("https://apis.data.go.kr/B554287/LocalGovernmentWelfareInformations/LcgvWelfarelist", {
        "pageNo": 1, "numOfRows": 3, "callTp": "L", "srchKeyCode": "001",
        "lifeArray": "004",
    })
    get("https://apis.data.go.kr/1741000/Subsidy24/getSubsidy24", {
        "pageNo": 1, "numOfRows": 3, "type": "json",
    })
