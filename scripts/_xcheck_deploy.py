"""Cross-check live Vercel welfare + youth APIs. Prints leaf traces."""
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import json

BASE = "https://codyssey-6-pro-ject.vercel.app"


def get(path, params, timeout=18):
    url = BASE + path + "?" + urlencode(params)
    print("\n======== GET", path, params)
    try:
        with urlopen(Request(url, headers={"User-Agent": "doenayo-xcheck/1.0"}), timeout=timeout) as resp:
            raw = resp.read()
            data = json.loads(raw.decode("utf-8", errors="replace"))
            print("status", resp.status, "bytes", len(raw), "count", data.get("count"), "stats", data.get("stats"))
            print("applied", data.get("applied"))
            if data.get("error"):
                print("ERROR", data["error"])
            for line in (data.get("trace") or [])[-40:]:
                print(line)
            for item in (data.get("items") or [])[:5]:
                print(" ITEM", item.get("source") or item.get("remoteSource"), item.get("title", "")[:40], "|", (item.get("org") or "")[:24])
            return data
    except HTTPError as exc:
        body = exc.read()[:500]
        print("HTTP", exc.code, body)
    except URLError as exc:
        print("NET", exc.reason)
    except Exception as exc:
        print("FAIL", type(exc).__name__, exc)
    return None


if __name__ == "__main__":
    get("/api/welfare", {
        "source": "all", "age": 24, "region": "대전",
        "interests": "주거,일자리", "household": "single",
        "marital": "unmarried", "disability": "none", "income": 150, "debug": 1,
    })
    get("/api/welfare", {
        "source": "local", "age": 67, "region": "서울",
        "interests": "건강", "debug": 1,
    })
    get("/api/welfare", {
        "source": "benefit", "age": 45, "region": "부산",
        "interests": "교육", "debug": 1,
    })
    get("/api/policies", {
        "source": "policy", "age": 24, "region": "광주", "debug": 1,
    })
    get("/api/policies", {
        "source": "policy", "age": 24, "region": "서울", "debug": 1,
    })
