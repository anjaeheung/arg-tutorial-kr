#!/usr/bin/env python3
"""남은 보너스 페이지의 키워드를 slug 유추로 좁게 확인한다. 무차별 조회는 하지 않는다."""
import json, sys, urllib.request, urllib.parse
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
BASE = "https://argtutorial.marimaric.workers.dev"

def probe(kw):
    url = f"{BASE}/data/search/{urllib.parse.quote(kw)}.json"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode("utf-8", "replace")) if r.status == 200 else None
    except Exception:
        return None

# slug(maocool / soudesu / yukimama)와 본문 맥락(協力者·同志)에서 나온 후보만
singles = ["まお", "マオ", "まおクール", "ゆきまま", "ゆきママ", "ユキママ", "そうです",
           "協力者", "同志", "ARGの世界", "ARG団", "超ARG団", "まりまりc"]
anchors = ["超!ARG団", "まりc"]

hits = {}
for s in singles:
    d = probe(s)
    if d is not None:
        items = d.get("results") if isinstance(d, dict) else d
        hits[s] = [i.get("path") for i in (items or [])]
        print(f"  ★ 1어  {s}  ->  {hits[s]}")

for a in anchors:
    for s in singles:
        combined = "".join(sorted([a, s]))
        d = probe(combined)
        if d is not None:
            items = d.get("results") if isinstance(d, dict) else d
            hits[f"{a} + {s}"] = [i.get("path") for i in (items or [])]
            print(f"  ★ 2어  {a} + {s}  ->  {hits[f'{a} + {s}']}")

print(f"\n추가 확정 {len(hits)}개 / 조회 {len(singles)*(1+len(anchors))}회")
Path("C:/Users/user/arg-tutorial-kr/tools/targeted.json").write_text(
    json.dumps(hits, ensure_ascii=False, indent=2), encoding="utf-8")
