"""온통청년 getPlcy 전체 페이지를 받아 data/youth_policy_snapshot.json 에 저장.

군산 대시보드 pages/7_청년혜택업데이트.py 의 '지금 동기화' 와 같다.
Vercel 사용자 요청에서는 이 파일을 읽기만 한다.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "api"))

from policies import sync_policy_snapshot  # noqa: E402


def main():
    trace = []
    payload = sync_policy_snapshot(trace)
    for line in trace:
        if "sync." in line or "youth_get.ok" in line or "youth_get.http" in line:
            print(line)
    print("count", payload.get("count"), "tot_count", payload.get("tot_count"), "pages", payload.get("pages"))
    print("path", payload.get("_path"))


if __name__ == "__main__":
    main()
