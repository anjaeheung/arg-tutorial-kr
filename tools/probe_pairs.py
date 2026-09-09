#!/usr/bin/env python3
"""후반부 2단어 조합을 전수 탐색한다.

엔진 규칙: 두 토큰을 정렬해 이어붙인 이름의 JSON을 fetch.
따라서 '超!ARG団' + X 조합을 X 후보 풀에 대해 돌려보면 정답이 드러난다.
"""
import json, re, sys, time, urllib.request, urllib.parse
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

BASE = "https://argtutorial.marimaric.workers.dev"
ROOT = Path("C:/Users/user/arg-tutorial-kr/_original")
OUT = Path("C:/Users/user/arg-tutorial-kr/tools")

def probe(kw):
    url = f"{BASE}/data/search/{urllib.parse.quote(kw)}.json"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode("utf-8", "replace")) if r.status == 200 else None
    except Exception:
        return None

def plain(html):
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    return t.replace("&nbsp;", " ").replace("　", " ")

# --- 후보 토큰 풀 만들기 ---
pool = set()
for f in sorted(ROOT.rglob("*.html")):
    t = plain(f.read_text(encoding="utf-8", errors="replace"))
    # 한자/가타카나/영숫자가 이어지는 덩어리를 명사 후보로 본다
    for m in re.finditer(r"[一-龥]{2,8}|[ァ-ヴー]{2,12}|[A-Za-z][A-Za-z0-9!\-]{1,14}", t):
        w = m.group(0).strip("-!")
        if 2 <= len(w) <= 14:
            pool.add(w)

known = ["超!ARG団", "まりc", "目的", "現実世界", "ぬいぐるみ", "ケロケロハート",
         "ARG初心者チュートリアル", "Web探索型ARG", "不自然", "無理ゲー", "理不尽"]
pool |= set(known)
pool = sorted(pool)
print(f"후보 토큰 {len(pool)}개")

ANCHORS = ["超!ARG団", "まりc", "目的", "現実世界", "ぬいぐるみ"]
hits, tried = {}, set()

for anchor in ANCHORS:
    found_here = 0
    for w in pool:
        if w == anchor:
            continue
        combined = "".join(sorted([anchor, w]))
        if combined in tried:
            continue
        tried.add(combined)
        d = probe(combined)
        if d is not None:
            items = d.get("results") if isinstance(d, dict) else d
            paths = [i.get("path") for i in (items or [])]
            hits[f"{anchor} + {w}"] = {"file": combined, "paths": paths,
                                       "hint": d.get("hint") if isinstance(d, dict) else None}
            found_here += 1
            print(f"  ★ {anchor} + {w}  ->  {paths}", flush=True)
    print(f"  [{anchor}] {found_here}건 / 조회 {len(tried)}", flush=True)

(OUT / "pairs.json").write_text(json.dumps(hits, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n2단어 조합 확정 {len(hits)}개 (총 {len(tried)}회 조회)")
