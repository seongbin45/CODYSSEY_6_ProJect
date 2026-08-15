"""위치 추정.

우선순위
  1) 브라우저가 준 위도·경도 → Nominatim 역지오코딩
  2) Vercel IP 헤더
  3) ipwho.is
"""

from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, quote, urlencode, urlparse
from urllib.request import Request, urlopen
import json
import re


def _send(handler, status, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "private, max-age=120")
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


def shorten_place(name):
    name = re.sub(r"\s+", "", str(name or ""))
    for suffix in ("특별자치시", "특별자치도", "광역시", "특별시", "자치시", "시", "군"):
        if name.endswith(suffix) and len(name) > len(suffix) + 1:
            return name[: -len(suffix)]
    return name


def payload(city="", area="", source=""):
    label = shorten_place(city) or shorten_place(area)
    return {
        "region": label,
        "label": label,
        "city": city,
        "area": area,
        "source": source,
    }


def reverse_geocode(lat, lon):
    query = urlencode({
        "lat": "%.6f" % lat,
        "lon": "%.6f" % lon,
        "format": "json",
        "accept-language": "ko",
        "zoom": 10,
    })
    req = Request(
        "https://nominatim.openstreetmap.org/reverse?" + query,
        headers={"User-Agent": "doenayo/1.0 (youth policy helper)", "Accept": "application/json"},
    )
    with urlopen(req, timeout=6) as resp:
        data = json.loads(resp.read().decode("utf-8", errors="replace"))
    addr = data.get("address") or {}
    city = (
        addr.get("city")
        or addr.get("town")
        or addr.get("village")
        or addr.get("municipality")
        or addr.get("county")
        or addr.get("city_district")
        or ""
    )
    area = addr.get("state") or addr.get("province") or addr.get("region") or ""
    return str(city), str(area)


def lookup_ipwho(ip):
    path = "https://ipwho.is/"
    if _is_public_ip(ip):
        path += quote(ip)
    req = Request(path, headers={"User-Agent": "doenayo/1.0", "Accept": "application/json"})
    with urlopen(req, timeout=4) as resp:
        data = json.loads(resp.read().decode("utf-8", errors="replace"))
    if not data or data.get("success") is False:
        return "", ""
    return str(data.get("city") or ""), str(data.get("region") or data.get("region_code") or "")


def suggest_from_coords(lat, lon):
    city, area = reverse_geocode(lat, lon)
    return payload(city, area, "gps")


def suggest_from_ip(handler):
    city = _header(handler, "x-vercel-ip-city")
    area = _header(handler, "x-vercel-ip-country-region")
    source = "vercel-ip"
    if not city and not area:
        city, area = lookup_ipwho(_client_ip(handler))
        source = "ipwho"
    return payload(city, area, source)


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        qs = parse_qs(urlparse(self.path).query)
        try:
            if qs.get("lat") and qs.get("lon"):
                lat = float(qs["lat"][0])
                lon = float(qs["lon"][0])
                if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    raise ValueError("range")
                _send(self, 200, suggest_from_coords(lat, lon))
                return
            _send(self, 200, suggest_from_ip(self))
        except Exception as exc:
            print("GEO_ERROR:", type(exc).__name__)
            _send(self, 200, payload(source="fallback"))

    def do_POST(self):
        _send(self, 405, {"error": "GET /api/geo 만 지원합니다."})

    def log_message(self, format, *args):
        print("%s - %s" % (self.address_string(), format % args))
