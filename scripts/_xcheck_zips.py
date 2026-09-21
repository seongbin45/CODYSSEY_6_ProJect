import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))
import policies as p

items = p.fetch_source_page("policy")
print("raw", len(items))
for i, item in enumerate(items):
    title = str(item.get("plcyNm") or "")[:50]
    zip_cd = str(item.get("zipCd") or "")
    codes = __import__("re").findall(r"\d{5}", zip_cd)
    prefixes = sorted({c[:2] for c in codes})
    inst = str(item.get("sprvsnInstCdNm") or item.get("rgtrInstCdNm") or "")
    print(
        "%02d codes=%s n=%s prefixes=%s inst=%s | %s"
        % (i, codes[:8], len(codes), prefixes, inst[:20], title)
    )
