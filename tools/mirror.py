#!/usr/bin/env python3
"""원본 ARG 튜토리얼 사이트를 로컬로 미러링한다.

정적 사이트라 서버 로직이 없다. 받아야 할 것:
  - data/structure.json (23페이지 목록), data/meta.json
  - 각 페이지 HTML
  - HTML이 참조하는 css / img
  - JS 모듈 그래프 (import 재귀 추적)
"""
import json, os, re, sys, urllib.request, urllib.parse
from pathlib import Path

BASE = "https://argtutorial.marimaric.workers.dev"
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "_original")

seen = set()

def get(path):
    """사이트 루트 기준 경로를 받아 bytes 반환. 실패하면 None."""
    url = BASE + "/" + path.lstrip("/")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read()
    except Exception as e:
        print(f"  !! {path}: {e}")
        return None

def save(path, data):
    dest = OUT / urllib.parse.unquote(path.lstrip("/"))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return dest

def fetch(path):
    """다운로드 후 저장. 이미 받은 건 건너뛴다."""
    path = path.lstrip("/")
    if path in seen:
        return None
    seen.add(path)
    data = get(path)
    if data is None:
        return None
    dest = save(path, data)
    print(f"  ok  {path}  ({len(data)}B)")
    return data

def norm(ref, from_path):
    """HTML/JS 안의 상대 경로를 사이트 루트 기준 경로로 변환."""
    ref = ref.split("#")[0].split("?")[0].strip()
    if not ref or ref.startswith(("http://", "https://", "//", "data:", "mailto:", "javascript:")):
        return None
    if ref.startswith("/"):
        return ref.lstrip("/")
    base_dir = os.path.dirname(from_path.lstrip("/"))
    return os.path.normpath(os.path.join(base_dir, ref)).replace("\\", "/")

def crawl_js(path, depth=0):
    """JS 모듈의 import 를 재귀적으로 따라간다."""
    if depth > 8:
        return
    data = fetch(path)
    if data is None:
        return
    text = data.decode("utf-8", "replace")
    for m in re.finditer(r"""(?:from|import)\s+['"]([^'"]+)['"]""", text):
        dep = norm(m.group(1), path)
        if dep and dep.endswith(".js") and dep not in seen:
            crawl_js(dep, depth + 1)

def crawl_html(path):
    data = fetch(path)
    if data is None:
        return
    text = data.decode("utf-8", "replace")
    for pat in (r'<link[^>]+href="([^"]+)"', r'<img[^>]+src="([^"]+)"',
                r'<script[^>]+src="([^"]+)"', r'<a[^>]+href="([^"]+)"'):
        for m in re.finditer(pat, text, re.I):
            ref = norm(m.group(1), path)
            if not ref or ref in seen:
                continue
            if ref.endswith(".js"):
                crawl_js(ref)
            elif ref.endswith((".css", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico")):
                fetch(ref)
            elif ref.endswith(".html"):
                crawl_html(ref)

print("[1/3] structure.json / meta.json")
raw = fetch("data/structure.json")
fetch("data/meta.json")
structure = json.loads(raw)

print(f"[2/3] 페이지 {len(structure['pages'])}개")
crawl_html("index.html")
for p in structure["pages"]:
    crawl_html(p["path"])

print("[3/3] 완료")
print(f"파일 {len(seen)}개, 저장 위치 {OUT.resolve()}")
