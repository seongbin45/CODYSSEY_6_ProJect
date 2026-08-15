"""온통청년 정책 스냅샷.

군산 대시보드 finfit_youth.cache_store.CacheStore + service.sync_source('policy')
와 같은 역할이다.

- 동기화: getPlcy 를 pageSize=100 으로 마지막 페이지까지 받아 snapshot 에 저장
- 조회: 사용자 요청은 API 를 다시 돌리지 않고 스냅샷만 나이·지역으로 거른다
- 저장: data/youth_policy_snapshot.json (배포에 포함) + /tmp (런타임 갱신)
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path


CACHE_TTL_SECONDS = int(os.environ.get("YOUTH_CACHE_TTL_SECONDS") or "1800")

_SHIPPED = Path(__file__).resolve().parents[1] / "data" / "youth_policy_snapshot.json"
_RUNTIME = Path(os.environ.get("TEMP") or os.environ.get("TMP") or "/tmp") / "youth_policy_snapshot.json"

_memory = {"payload": None, "path": None, "mtime": None}


def snapshot_paths():
    return (_RUNTIME, _SHIPPED)


def _read_file(path):
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        return None
    data["_path"] = str(path)
    data["_mtime"] = int(path.stat().st_mtime)
    return data


def load_snapshot():
    """가장 최근 스냅샷. TTL이 지나도 돌려 준다(군산 get(max_age=None)과 같음)."""
    newest = None
    for path in snapshot_paths():
        data = _read_file(path)
        if not data:
            continue
        if newest is None or int(data.get("updated_at") or 0) >= int(newest.get("updated_at") or 0):
            newest = data
    if newest is None:
        return None
    mem_key = (newest.get("_path"), newest.get("updated_at"))
    if _memory.get("mtime") != mem_key:
        _memory["payload"] = newest
        _memory["mtime"] = mem_key
    return newest


def age_seconds(payload=None):
    payload = payload if payload is not None else load_snapshot()
    if not payload:
        return None
    updated = int(payload.get("updated_at") or 0)
    if not updated:
        return None
    return max(0, int(time.time()) - updated)


def is_stale(payload=None):
    age = age_seconds(payload)
    if age is None:
        return True
    return age > CACHE_TTL_SECONDS


def save_snapshot(items, extra=None):
    payload = {
        "updated_at": int(time.time()),
        "count": len(items),
        "items": items,
    }
    if extra:
        payload.update(extra)
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    written = None
    for path in snapshot_paths():
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".json.tmp")
            tmp.write_text(text, encoding="utf-8")
            tmp.replace(path)
            written = str(path)
        except OSError:
            continue
    if written is None:
        raise OSError("youth policy snapshot 을 쓸 수 없습니다")
    payload["_path"] = written
    _memory["payload"] = payload
    _memory["mtime"] = (written, payload["updated_at"])
    return payload


def meta(payload=None):
    payload = payload if payload is not None else load_snapshot()
    if not payload:
        return {"size": 0, "age_seconds": None, "stale": True, "path": ""}
    age = age_seconds(payload)
    return {
        "size": int(payload.get("count") or len(payload.get("items") or [])),
        "age_seconds": age,
        "stale": is_stale(payload),
        "path": payload.get("_path") or "",
        "tot_count": payload.get("tot_count"),
        "pages": payload.get("pages"),
    }
