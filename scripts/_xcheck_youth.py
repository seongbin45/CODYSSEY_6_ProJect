"""Local leaf-level cross-check. Prints YOUTH_TRACE. Do not commit secrets."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))
import policies as p  # noqa: E402


def run_case(age, city):
    trace = []
    print("\n======== CASE age=%s city=%s ========" % (age, city))
    rows, sent, stats = p.list_catalog(age=age, city=city, sources=("policy",), trace=trace)
    print("SENT", sent)
    print("STATS", stats)
    print("SHOWN", len(rows))
    for row in rows:
        print("  KEEP", row["id"], row.get("age_check"), row.get("region_check"), row["title"][:40])
    return {
        "age": age,
        "city": city,
        "fetched": stats.get("policy", {}).get("fetched"),
        "kept": stats.get("policy", {}).get("kept"),
        "shown": len(rows),
        "error": stats.get("policy", {}).get("error"),
        "ids": [r["id"] for r in rows],
        "reasons": [(r.get("region_check"), r["title"][:24]) for r in rows],
    }


if __name__ == "__main__":
    cases = [
        (24, "서울"),
        (24, "대전"),
        (24, "경기"),
        (24, "부산"),
        (17, "서울"),
        (50, "대전"),
    ]
    summary = [run_case(age, city) for age, city in cases]
    print("\n======== SUMMARY ========")
    for row in summary:
        print(row)
    first_ids = summary[0]["ids"]
    print("\n동일 원본 페이지인가(서울 vs 대전 shown id):", first_ids == summary[1]["ids"])
    print("서울 kept vs 경기 kept:", summary[0]["kept"], summary[2]["kept"])
