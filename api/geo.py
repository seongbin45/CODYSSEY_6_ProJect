"""접속 IP로 거주 지역을 추천한다.

우선순위
  1) Vercel 이 붙이는 x-vercel-ip-city / x-vercel-ip-country-region
  2) 공개 HTTPS 조회 (ipwho.is) — 로컬·헤더 없을 때
"""

from http.server import BaseHTTPRequestHandler
from urllib.parse import quote
from urllib.request import Request, urlopen
import json
import re

def _place_label(city, region):
    city = (city or "").strip()
    region = (region or "").strip()
    if city:
        return city
    if region:
        return region
    return ""


def _send(handler, status, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "private, max-age=300")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _header(handler, name):
    return (handler.headers.get(name) or "").strip()


def _client_ip(handler):
    forwarded = _header(handler, "x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real = _header(handler, "x-real-ip")
    if real:
        return real
    return (handler.client_address[0] if handler.client_address else "") or ""


def _is_public_ip(ip):
    if not ip or ip in {"127.0.0.1", "::1"}:
        return False
    if ip.startswith("10.") or ip.startswith("192.168.") or ip.startswith("169.254."):
        return False
    if re.match(r"^172\.(1[6-9]|2\d|3[0-1])\.", ip):
        return False
    return True


def classify(city, region):
    """입력란에 넣을 시·군 이름. 특정 광역을 고정하지 않는다."""
    label = _place_label(city, region)
    return label or "other"


def lookup_ipwho(ip):
    path = "https://ipwho.is/"
    if _is_public_ip(ip):
        path += quote(ip)
    req = Request(path, headers={"User-Agent": "doenayo/1.0", "Accept": "application/json"})
    with urlopen(req, timeout=4) as resp:
        data = json.loads(resp.read().decode("utf-8", errors="replace"))
    if not data or data.get("success") is False:
        return "", ""
    city = data.get("city") or ""
    region = data.get("region") or data.get("region_code") or ""
    return str(city), str(region)


def suggest(handler):
    city = _header(handler, "x-vercel-ip-city")
    region = _header(handler, "x-vercel-ip-country-region")
    source = "vercel"
    if not city and not region:
        city, region = lookup_ipwho(_client_ip(handler))
        source = "ipwho"
    label = classify(city, region)
    if label == "other":
        label = ""
    return {
        "region": label,
        "label": label,
        "city": city,
        "area": region,
        "source": source,
    }


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            _send(self, 200, suggest(self))
        except Exception as exc:
            print("GEO_ERROR:", type(exc).__name__)
            _send(self, 200, {
                "region": "",
                "label": "",
                "city": "",
                "area": "",
                "source": "fallback",
            })

    def do_POST(self):
        _send(self, 405, {"error": "GET /api/geo 만 지원합니다."})

    def log_message(self, format, *args):
        print("%s - %s" % (self.address_string(), format % args))
