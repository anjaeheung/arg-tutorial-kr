#!/usr/bin/env python3
"""가설: 페이지 제목 = 그 페이지를 여는 키워드. 전수 조회로 검증한다."""
import json, re, sys, urllib.request, urllib.parse, itertools
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

BASE = "https://argtutorial.marimaric.workers.dev"
ROOT = Path("_original")

def probe(kw):
    url = f"{BASE}/data/search/{urllib.parse.quote(kw)}.json"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode("utf-8", "replace")) if r.status == 200 else None
    except Exception:
        return None

structure = json.loads((ROOT / "data/structure.json").read_text(encoding="utf-8"))
titles = {}
for p in structure["pages"]:
    f = ROOT / p["path"].lstrip("/")
    if f.exists():
        m = re.search(r"<title>(.*?)</title>", f.read_text(encoding="utf-8", errors="replace"), re.S)
        if m:
            titles[p.get("slug") or p["path"]] = m.group(1).strip()

# 제목 + 세로읽기 정답 + 기존 확정분
cands = set(titles.values())
cands |= {"ケロケロハート", "無理ゲー", "ARG初心者チュートリアル", "Web探索型ARG"}
# 제목에 붙은 장식 문자를 뗀 변형도 시도
for t in list(cands):
    s = t.strip("！!？?。、 　")
    if s and s != t:
        cands.add(s)

print(f"제목 {len(titles)}개 / 후보 {len(cands)}개 조회")
hits = {}
for c in sorted(cands):
    d = probe(c)
    if d is not None:
        hits[c] = d
        paths = [i.get("path") for i in (d.get("results") if isinstance(d, dict) else d) or []]
        hint = d.get("hint") if isinstance(d, dict) else None
        print(f"  ★ {c}  ->  {paths}{'  [hint:'+hint+']' if hint else ''}")

Path("tools/keywords.json").write_text(json.dumps(hits, ensure_ascii=False, indent=2), encoding="utf-8")
Path("tools/titles.json").write_text(json.dumps(titles, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n확정 {len(hits)}/{len(cands)}")
missing = [s for s, t in titles.items() if t not in hits and t.strip('！!？?。、 　') not in hits]
print("제목이 키워드가 아닌 페이지:", missing)
