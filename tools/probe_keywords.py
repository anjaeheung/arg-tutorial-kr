#!/usr/bin/env python3
"""키워드 후보를 뽑아 원본 서버의 data/search/{kw}.json 존재 여부로 정답을 확정한다."""
import json, re, sys, time, urllib.request, urllib.parse
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
BASE = "https://argtutorial.marimaric.workers.dev"
ROOT = Path("_original")

def probe(kw):
    """검색 JSON이 있으면 그 내용을, 없으면 None."""
    url = f"{BASE}/data/search/{urllib.parse.quote(kw)}.json"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            if r.status != 200:
                return None
            return json.loads(r.read().decode("utf-8", "replace"))
    except Exception:
        return None

# --- 후보 추출: 원본 HTML에서 전각공백/괄호로 구분된 토막을 긁는다 ---
STOP = ("と", "を", "で", "は", "が", "の", "、", "。", "　", " ")
cands = set()

for f in sorted(ROOT.rglob("*.html")):
    html = f.read_text(encoding="utf-8", errors="replace")
    plain = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    plain = re.sub(r"<[^>]+>", "\n", plain)

    # 「」『』"" 안의 문자열
    for m in re.finditer(r"[「『\"]([^」』\"\n]{1,40})[」』\"]", plain):
        cands.add(m.group(1))
    # 전각공백으로 둘러싸인 토막
    for m in re.finditer(r"　([^　\n]{2,40})　", plain):
        cands.add(m.group(1))
    # 「…と検索」「…と入力」 앞의 토막
    for m in re.finditer(r"([^\s　、。\n]{2,40})\s*[と を]\s*(?:検索|入力)", plain):
        cands.add(m.group(1))
    # 전각공백 뒤 줄 끝까지 (지시문 들여쓰기 패턴)
    for m in re.finditer(r"　　([^\n]{2,40})", plain):
        cands.add(m.group(1))

# 조사/구두점 꼬리 정리해서 변형도 추가
expanded = set()
for c in cands:
    c = c.strip()
    if not c:
        continue
    expanded.add(c)
    t = c
    while t and t[-1] in STOP:
        t = t[:-1].strip()
        if len(t) >= 2:
            expanded.add(t)

expanded = {c for c in expanded if 2 <= len(c) <= 40}
print(f"후보 {len(expanded)}개 조회 시작", flush=True)

hits = {}
for i, c in enumerate(sorted(expanded), 1):
    data = probe(c)
    if data is not None:
        hits[c] = data
        print(f"  ★ HIT  {c}", flush=True)
    if i % 40 == 0:
        print(f"  ... {i}/{len(expanded)}", flush=True)

Path("tools/keywords.json").write_text(
    json.dumps(hits, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n확정 키워드 {len(hits)}개 → tools/keywords.json")
