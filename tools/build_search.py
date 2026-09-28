#!/usr/bin/env python3
"""한글 키워드용 검색 인덱스를 생성한다.

엔진 규칙상 검색어가 곧 파일명이고, 두 단어일 때는 토큰을 정렬해 이어붙인다.
한국어는 띄어쓰기가 흔한데 엔진은 토큰을 2개까지만 보므로,
플레이어가 띄어 쓸 법한 변형까지 별칭 파일로 만들어 받아준다.
"""
import json, shutil, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path("C:/Users/user/arg-tutorial-kr")
SEARCH = ROOT / "data/search"

# 일본어 원본 키워드 → 한국어 키워드 (붙여쓴 형태가 정답)
KO = {
    "ARG初心者チュートリアル": "ARG초보자튜토리얼",
    "目的": "목적",
    "Web探索型ARG": "웹탐색형ARG",
    "不自然": "부자연",
    "まりc": "마리c",
    "現実世界": "현실세계",
    "理不尽": "부조리",
    "無理ゲー": "노답",
    "ケロケロハート": "케로케로하트",
    "ぬいぐるみ": "인형",
    "超!ARG団": "초!ARG단",
    "超ARG団": "초ARG단",
    "ユキママ": "유키마마",
    "新世界": "신세계",
    "まおくぅる": "마오쿠우루",
    "まおくーる": "마오쿠우루",
}

# 플레이어가 띄어 쓸 법한 변형. 엔진은 앞 두 토큰만 보므로 그 결합도 만들어 둔다.
SPACED = {
    "ARG초보자튜토리얼": ["ARG 초보자튜토리얼", "ARG 초보자 튜토리얼"],
    "웹탐색형ARG": ["웹 탐색형ARG", "웹 탐색형 ARG"],
    "초!ARG단": ["초! ARG단"],
    "케로케로하트": [],
}

# 검색 결과 목록에 뜨는 표시용 제목. 키워드와는 별개라 따로 옮긴다.
TITLES = {
    "ARG初心者チュートリアル": "ARG초보자튜토리얼",
    "おめでとう": "축하합니다",
    "それだけですか？": "그것뿐인가요?",
    "ユキママさん": "유키마마 씨",
    "不自然さ": "부자연스러움",
    "強調表示": "강조 표시",
    "現実世界": "현실세계",
    "理不尽・無理ゲー要素": "부조리·노답 요소",
    "目的": "목적",
    "超！ARG団": "초！ARG단",
    "超！ARG団の構成員": "초！ARG단의 구성원",
    "超！ARG団の目的": "초！ARG단의 목적",
    "超！ARG団は現実世界を変えていく": "초！ARG단은 현실 세계를 바꿔 나간다",
    "選択・反転・固有名詞": "선택·반전·고유명사",
    "まおくぅる": "마오쿠우루",
    "そうですね": "그렇군요",
}


def combined(tokens):
    """엔진이 실제로 fetch 하는 파일명을 계산한다."""
    t = [x for x in tokens if x]
    if len(t) == 1:
        return t[0]
    return "".join(sorted(t[:2]))

def localize(dest: Path):
    """검색 결과에 뜨는 title 을 한국어 페이지 제목으로 바꾼다.

    이 게임은 페이지 제목이 곧 그 페이지를 여는 키워드라서 KO 표를 그대로 쓴다.
    """
    data = json.loads(dest.read_text(encoding="utf-8"))
    items = data.get("results") if isinstance(data, dict) else data
    for it in items or []:
        t = it.get("title")
        if t in TITLES:
            it["title"] = TITLES[t]
        elif t in KO:
            it["title"] = KO[t]
    dest.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# 화면에 뜨는 제목은 전각 「！」를 쓰는데(초！ARG단) 검색 파일 이름은 반각 「!」다.
# 제목을 보고 그대로 치면 안 열린다. 게다가 한국어는 「초!ARG단의 목적」처럼
# 조사 「의」를 붙여 치기 십상이라 그 형태도 함께 받아 준다.
DAN_FORMS = ["초!ARG단", "초！ARG단", "초ARG단",
             "초!ARG단의", "초！ARG단의", "초ARG단의"]

# 두 단어 조합에서 「초!ARG단」과 짝이 되는 말 → 복사해 올 원본(1)에서 만들어진 파일
DAN_PAIRS = {
    "목적": "목적초!ARG단.json",
    "마리c": "마리c초!ARG단.json",
    "현실세계": "초!ARG단현실세계.json",
    "신세계": "신세계초!ARG단.json",
}


def build_dan_aliases():
    """「초!ARG단」의 전각·조사 변형을 한 단어·두 단어 모두 받아 준다."""
    made = 0
    base = SEARCH / "초!ARG단.json"
    for form in DAN_FORMS:
        if base.exists():
            dest = SEARCH / f"{combined([form])}.json"
            if not dest.exists():
                shutil.copyfile(base, dest)
                made += 1
        for partner, srcname in DAN_PAIRS.items():
            src = SEARCH / srcname
            if not src.exists():
                continue
            dest = SEARCH / f"{combined([form, partner])}.json"
            if dest.exists():
                continue
            shutil.copyfile(src, dest)
            made += 1
    print("  초!ARG단 변형(전각 ！·조사 의) %d개" % made)
    return made


def main():
    if not SEARCH.exists():
        print("data/search 가 없다"); return
    made = 0

    # 1) 1단어 키워드: 일본어 파일을 한글 이름으로 복제
    for ja, ko in KO.items():
        src = SEARCH / f"{ja}.json"
        if not src.exists():
            print(f"    - 원본 없음: {ja}");  continue
        shutil.copyfile(src, SEARCH / f"{ko}.json")
        localize(SEARCH / f"{ko}.json")
        made += 1
        for variant in SPACED.get(ko, []):
            name = combined(variant.split())
            if name != ko:
                shutil.copyfile(src, SEARCH / f"{name}.json")
                localize(SEARCH / f"{name}.json")
                made += 1
                print(f"  별칭 {variant!r} -> {name}.json")

    # 2) 2단어 조합: 일본어 조합 파일을 한글 조합 이름으로 복제
    kmap = json.loads((ROOT / "tools/keyword_map.json").read_text(encoding="utf-8"))
    for label, info in kmap.get("pairs", {}).items():
        a, b = [x.strip() for x in label.split("+")]
        if a not in KO or b not in KO:
            continue
        src = SEARCH / info["file"]
        if not src.exists():
            continue
        name = combined([KO[a], KO[b]])
        shutil.copyfile(src, SEARCH / f"{name}.json")
        localize(SEARCH / f"{name}.json")
        made += 1
        print(f"  2단어 {KO[a]} + {KO[b]} -> {name}.json")

    made += build_dan_aliases()

    # 일본어 이름 파일에도 한국어 제목이 뜨도록 data/search 전체를 훑는다
    swept = 0
    for f in sorted(SEARCH.glob("*.json")):
        before = f.read_text(encoding="utf-8")
        localize(f)
        if f.read_text(encoding="utf-8") != before:
            swept += 1
    print("제목 한국어화: %d개 파일" % swept)

    print(f"\n한글 검색 파일 {made}개 생성 / 총 {len(list(SEARCH.glob('*.json')))}개")

main()
