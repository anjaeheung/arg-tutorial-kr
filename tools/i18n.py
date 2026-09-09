#!/usr/bin/env python3
"""번역 대상 문자열을 HTML/JS에서 뽑아내고, 번역본을 다시 주입한다.

구조를 절대 건드리지 않는 것이 목적이다. 태그·속성·공백은 그대로 두고
텍스트 노드, 지정 속성값, 인라인 스크립트의 문자열 리터럴만 교체한다.
추출과 주입이 같은 토크나이저를 쓰므로 위치가 일대일로 대응된다.

  extract            원문에서 문자열 카탈로그를 만든다 (기존 번역은 보존)
  dump [파일...]     미번역 문자열을 인덱스와 함께 출력한다
  set <패치.json>    {파일: {인덱스: 한국어}} 를 카탈로그에 반영한다
  apply              카탈로그의 번역을 실제 파일에 주입한다
  status             진행률을 본다
"""
import json, re, sys
from pathlib import Path

ROOT = Path("C:/Users/user/arg-tutorial-kr")
CATALOG = ROOT / "tools/catalog.json"

JA = re.compile(r"[\u3040-\u30ff\u3400-\u9fff\uff66-\uff9f]")   # 가나 + 한자
TAG = re.compile(r"<[^>]*>", re.S)
ATTRS = ("placeholder", "alt", "title", "aria-label", "value", "content")

STR_LIT = re.compile(r"""(['"])((?:\.|(?!\1)[^\\n])*)\1""")
TPL_LIT = re.compile(r"`((?:\.|[^\`])*)`", re.S)
BLOCK = re.compile(r"<(script|style)\b[^>]*>(.*?)</\1\s*>", re.S | re.I)


def js_segments(js, offset=0):
    """JS 문자열 리터럴 위치. 따옴표 3종을 모두 본다."""
    out = []
    for m in STR_LIT.finditer(js):
        if m.group(2):
            out.append(("js", offset + m.start(2), offset + m.end(2)))
    # 템플릿 리터럴 — 타이핑 연출 대사가 주로 여기 있다
    for m in TPL_LIT.finditer(js):
        if m.group(1):
            out.append(("tpl", offset + m.start(1), offset + m.end(1)))
    return out


def segments(html):
    """text / attr / js·tpl 조각의 (kind, start, end) 목록."""
    out, blocked = [], []
    for m in BLOCK.finditer(html):
        blocked.append((m.start(), m.end()))
        if m.group(1).lower() == "script":
            out.extend(js_segments(m.group(2), m.start(2)))

    def blocked_at(a, b):
        return any(s < b and a < e for s, e in blocked)

    pos = 0
    for m in TAG.finditer(html):
        if m.start() > pos and not blocked_at(pos, m.start()):
            out.append(("text", pos, m.start()))
        tag = m.group(0)
        if not tag.startswith("</") and not blocked_at(m.start(), m.end()):
            for am in re.finditer(r'\b(' + "|".join(ATTRS) + r')\s*=\s*"([^"]*)"', tag, re.I):
                s = m.start() + am.start(2)
                out.append(("attr", s, s + len(am.group(2))))
        pos = m.end()
    if pos < len(html) and not blocked_at(pos, len(html)):
        out.append(("text", pos, len(html)))
    return sorted(out, key=lambda x: x[1])


def collect(path):
    raw = path.read_text(encoding="utf-8", errors="replace")
    segs = js_segments(raw) if path.suffix == ".js" else segments(raw)
    items, seen = [], set()
    for kind, s, e in segs:
        if (s, e) in seen:
            continue
        seen.add((s, e))
        piece = raw[s:e]
        if piece.strip() and JA.search(piece):
            items.append({"kind": kind, "start": s, "end": e, "ja": piece, "ko": ""})
    return raw, items


def targets():
    return (sorted(ROOT.glob("*.html")) + sorted(ROOT.glob("contents/*.html"))
            + sorted(ROOT.glob("assets/js/**/*.js")))


def load():
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def save(catalog):
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=1), encoding="utf-8")


def cmd_extract():
    old = {}
    if CATALOG.exists():          # 이미 번역한 내용은 보존한다
        for rel, items in load().items():
            for it in items:
                if it["ko"]:
                    old[(rel, it["ja"])] = it["ko"]

    catalog, total = {}, 0
    for f in targets():
        rel = f.relative_to(ROOT).as_posix()
        _, items = collect(f)
        if not items:
            continue
        for it in items:
            it["ko"] = old.get((rel, it["ja"]), "")
        catalog[rel] = items
        total += len(items)

    save(catalog)
    chars = sum(len(i["ja"]) for v in catalog.values() for i in v)
    kept = sum(1 for v in catalog.values() for i in v if i["ko"])
    print(f"파일 {len(catalog)}개 / 문자열 {total}개 / 원문 {chars}자 / 번역 유지 {kept}개")
    for rel, items in catalog.items():
        print(f"  {len(items):3d}  {rel}")


def cmd_dump():
    catalog = load()
    wanted = sys.argv[2:]
    for rel, items in catalog.items():
        if wanted and not any(w in rel for w in wanted):
            continue
        pending = [(n, it) for n, it in enumerate(items) if not it["ko"]]
        if not pending:
            continue
        print("")
        print("##### " + rel)
        for n, it in pending:
            print("[%d] (%s) %r" % (n, it["kind"], it["ja"]))


def cmd_set():
    patch = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    catalog = load()
    n = 0
    for rel, entries in patch.items():
        if rel not in catalog:
            print("  !! 카탈로그에 없는 파일: " + rel)
            continue
        for idx, ko in entries.items():
            i = int(idx)
            if i >= len(catalog[rel]):
                print("  !! 범위 초과: %s[%s]" % (rel, idx))
                continue
            catalog[rel][i]["ko"] = ko
            n += 1
    save(catalog)
    print("%d개 반영" % n)


def cmd_apply():
    catalog = load()
    changed = 0
    for rel, items in catalog.items():
        edits = [i for i in items if i["ko"]]
        if not edits:
            continue
        f = ROOT / rel
        raw = f.read_text(encoding="utf-8", errors="replace")
        ok = 0
        # 뒤에서부터 치환해야 앞쪽 위치가 밀리지 않는다
        for it in sorted(edits, key=lambda x: x["start"], reverse=True):
            if raw[it["start"]:it["end"]] != it["ja"]:
                print("  !! 위치 불일치, 건너뜀: %s @%d" % (rel, it["start"]))
                continue
            raw = raw[:it["start"]] + it["ko"] + raw[it["end"]:]
            ok += 1
        f.write_text(raw, encoding="utf-8")
        changed += 1
        print("  적용 %3d개  %s" % (ok, rel))
    print("")
    print("%d개 파일 갱신" % changed)


def cmd_status():
    catalog = load()
    done = sum(1 for v in catalog.values() for i in v if i["ko"])
    total = sum(len(v) for v in catalog.values())
    print("번역 %d/%d" % (done, total))
    for rel, items in catalog.items():
        d = sum(1 for i in items if i["ko"])
        print("  %9s  %s" % ("완료" if d == len(items) else "%d/%d" % (d, len(items)), rel))


if __name__ == "__main__":
    {"extract": cmd_extract, "dump": cmd_dump, "set": cmd_set,
     "apply": cmd_apply, "status": cmd_status}[sys.argv[1]]()
