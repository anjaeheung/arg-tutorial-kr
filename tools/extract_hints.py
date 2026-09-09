#!/usr/bin/env python3
"""각 페이지에서 검색 지시문·숨은 텍스트·주석을 뽑아 키워드 후보를 찾는다."""
import json, re, sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path("_original")

class Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.skip = [], 0
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        if tag == "br":
            self.parts.append("\n")
    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1
    def handle_data(self, d):
        if not self.skip:
            self.parts.append(d)

def text_of(html):
    p = Text(); p.feed(html)
    t = "".join(p.parts).replace("　", " ")
    return re.sub(r"\n{3,}", "\n\n", "\n".join(l.strip() for l in t.splitlines()))

# 검색을 지시하는 문장에 등장하는 신호어
SIGNALS = ("検索", "けんさく", "調べ", "キーワード", "探し", "さがし", "入力")

structure = json.loads((ROOT / "data/structure.json").read_text(encoding="utf-8"))
report = {}

for page in structure["pages"]:
    rel = page["path"].lstrip("/")
    f = ROOT / rel
    if not f.exists():
        continue
    html = f.read_text(encoding="utf-8", errors="replace")

    # 검색을 지시하는 줄
    hints = [l.strip() for l in text_of(html).splitlines()
             if l.strip() and any(s in l for s in SIGNALS)]

    # 숨겨진 요소 (ARG 기믹): 인라인 스타일로 감춘 태그의 내용
    hidden = re.findall(
        r'<([a-z]+)[^>]*style="[^"]*(?:display\s*:\s*none|visibility\s*:\s*hidden|opacity\s*:\s*0|font-size\s*:\s*0|color\s*:\s*#?f{3,6})[^"]*"[^>]*>(.*?)</\1>',
        html, re.I | re.S)
    hidden = [re.sub(r"<[^>]+>", "", h[1]).strip()[:120] for h in hidden]

    # HTML 주석 (라이선스성 상용구 제외)
    comments = [c.strip()[:120] for c in re.findall(r"<!--(.*?)-->", html, re.S)]
    comments = [c for c in comments if c and not c.startswith(("上部", "page counter", "特定の"))]

    report[page.get("slug") or rel] = {
        "title": (re.search(r"<title>(.*?)</title>", html, re.S) or [None, ""])[1].strip(),
        "hints": hints,
        "hidden": [h for h in hidden if h],
        "comments": comments,
    }

Path("tools/hints.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

for slug, d in report.items():
    print(f"\n=== {slug} :: {d['title']}")
    for h in d["hints"]:
        print(f"   지시| {h}")
    for h in d["hidden"]:
        print(f"   숨김| {h}")
    for c in d["comments"]:
        print(f"   주석| {c}")
