#!/usr/bin/env python3
"""확정된 검색 키워드의 JSON을 내려받고, 키워드 맵을 정리해 저장한다."""
import json, sys, urllib.request, urllib.parse
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

BASE = "https://argtutorial.marimaric.workers.dev"
ROOT = Path("C:/Users/user/arg-tutorial-kr")
SEARCH = ROOT / "_original/data/search"
SEARCH.mkdir(parents=True, exist_ok=True)

SINGLES = ["ARG初心者チュートリアル", "目的", "Web探索型ARG", "不自然", "まりc",
           "現実世界", "理不尽", "無理ゲー", "ケロケロハート", "ぬいぐるみ",
           "超!ARG団", "超ARG団", "ユキママ"]
PAIRS = [("超!ARG団", "目的"), ("超!ARG団", "まりc"), ("超!ARG団", "現実世界"),
         ("まりc", "超ARG団"), ("超ARG団", "目的"), ("超ARG団", "現実世界")]

def fetch(name):
    url = f"{BASE}/data/search/{urllib.parse.quote(name)}.json"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read()
    except Exception:
        return None
    (SEARCH / f"{name}.json").write_bytes(raw)
    return json.loads(raw.decode("utf-8", "replace"))

kmap = {"singles": {}, "pairs": {}, "unresolved": {}}

for s in SINGLES:
    d = fetch(s)
    if d is None:
        print(f"    - {s}: 없음");  continue
    items = d.get("results") if isinstance(d, dict) else d
    kmap["singles"][s] = {"file": f"{s}.json",
                          "paths": [i.get("path") for i in (items or [])],
                          "hint": d.get("hint") if isinstance(d, dict) else None}
    print(f"  ok 1어  {s}")

for a, b in PAIRS:
    name = "".join(sorted([a, b]))
    d = fetch(name)
    if d is None:
        print(f"    - {a}+{b}: 없음");  continue
    items = d.get("results") if isinstance(d, dict) else d
    kmap["pairs"][f"{a} + {b}"] = {"file": f"{name}.json",
                                   "paths": [i.get("path") for i in (items or [])]}
    print(f"  ok 2어  {a} + {b}")

# 검색으로 도달하지 않는 페이지 / 아직 못 찾은 키워드
kmap["reached_by_link"] = {
    "contents/clear.html": "complete 페이지에서 링크",
    "contents/complete.html": "hidden-links 등에서 링크",
    "contents/hidden-links.html": "unreasonable 페이지의 숨은 링크(마침표 「。」)",
    "contents/thankyouAlly.html": "allcomplete 등에서 링크",
    "contents/yokuaru3.html": "URL 직접 수정(URL改変 학습 페이지)",
}
kmap["unresolved"] = {
    "contents/allcomplete.html": "키워드 미확인 — 원작자가 본문에서 추측 불가로 설계",
    "contents/maocool.html": "키워드 미확인 (ex1 보너스)",
    "contents/soudesu.html": "키워드 미확인 (ex2 보너스)",
}

(ROOT / "tools/keyword_map.json").write_text(
    json.dumps(kmap, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n1어 {len(kmap['singles'])}개 / 2어 {len(kmap['pairs'])}개 확보")
print(f"검색 JSON 저장: {SEARCH}")
