import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError


def load_env():
    for raw in (Path(__file__).resolve().parents[1] / ".env").read_text(encoding="utf-8-sig").splitlines():
        if not raw.strip() or raw.startswith("#") or "=" not in raw:
            continue
        k, _, v = raw.partition("=")
        os.environ.setdefault(k.strip(), v.strip())


def get(url, params):
    q = dict(params)
    q["serviceKey"] = os.environ["DATA_GO_KR_SERVICE_KEY"]
    full = url + "?" + urlencode(q)
    print("\nGET", url, params)
    try:
        with urlopen(Request(full, headers={"Accept": "*/*", "User-Agent": "doenayo/1.0"}), timeout=12) as resp:
            text = resp.read(2500).decode("utf-8", errors="replace")
            print(text[:1200].replace("\n", " "))
    except HTTPError as exc:
        print("HTTP", exc.code, exc.read()[:300])


if __name__ == "__main__":
    load_env()
    # local with region name
    get("https://apis.data.go.kr/B554287/LocalGovernmentWelfareInformations/LcgvWelfarelist", {
        "pageNo": 1, "numOfRows": 2, "callTp": "L", "srchKeyCode": "001",
        "ctpvNm": "대전광역시",
    })
    get("https://apis.data.go.kr/B554287/LocalGovernmentWelfareInformations/LcgvWelfarelist", {
        "pageNo": 1, "numOfRows": 2, "callTp": "L", "srchKeyCode": "001",
        "sidocode": "30",
    })
    get("https://apis.data.go.kr/B554287/NationalWelfareInformationsV001/NationalWelfaredetailedV001", {
        "callTp": "D", "servId": "WLF00000026",
    })
    get("https://apis.data.go.kr/B554287/LocalGovernmentWelfareInformations/LcgvWelfaredetailed", {
        "servId": "WLF00005330",
    })
    get("https://api.odcloud.kr/api/gov24/v3/serviceDetail", {
        "page": 1, "perPage": 1, "returnType": "JSON",
        "cond[서비스ID::EQ]": "000000465790",
    })
    get("https://api.odcloud.kr/api/gov24/v3/serviceList", {
        "page": 1, "perPage": 2, "returnType": "JSON",
        "cond[서비스분야::LIKE]": "주거",
    })
    get("https://api.odcloud.kr/api/gov24/v3/supportConditions", {
        "page": 1, "perPage": 1, "returnType": "JSON",
        "cond[서비스ID::EQ]": "000000465790",
    })
