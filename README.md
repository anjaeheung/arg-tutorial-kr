# ARG 초보자 튜토리얼 — 한국어판

일본어 Web 탐색형 ARG 연습 사이트의 한국어 팬 번역판.

- 원작: **まりc** — https://argtutorial.marimaric.workers.dev/
- 원작자 X: https://x.com/nstzg3Cq4s3rsAU
- 엔진: YACHO(SIM3)

비영리·무료. 원작 구조를 그대로 두고 텍스트만 한국어로 옮겼습니다.

## 상태

**아직 공개 배포 전입니다.** 원작자 허락을 받은 뒤 공개하세요.
문의 초안: [docs/permission-request.ja.md](docs/permission-request.ja.md)

| 항목 | 상태 |
|---|---|
| 원본 미러 | 완료 (23페이지 + 자산 49파일) |
| 검색 키워드 역산 | 1단어 13개 / 2단어 6개 확보 |
| 한글 검색 인덱스 | 완료 (띄어쓰기 변형 별칭 포함) |
| 번역 | **30/665** — `index.html` + 엔진 UI만 완료 |
| 미해결 키워드 | allcomplete, maocool, soudesu 3개 |

## 작업 방법

```bash
python tools/i18n.py extract              # 원문에서 문자열 카탈로그 생성
python tools/i18n.py dump contents/xxx    # 미번역 문자열을 인덱스와 함께 확인
python tools/i18n.py set tools/patch.json # {파일:{인덱스:한국어}} 반영
python tools/i18n.py apply                # 실제 파일에 주입
python tools/i18n.py status               # 진행률
python tools/build_search.py              # 한글 검색 인덱스 재생성
```

카탈로그(`tools/catalog.json`)가 원본 파일의 문자 위치를 들고 있어,
번역을 넣어도 태그·CSS·숨김 요소 구조는 건드리지 않습니다.

## 로컬 실행

정적 사이트지만 `fetch` 를 쓰므로 `file://` 로는 안 됩니다.

```bash
python -m http.server 4173 --directory .
```

## 현지화에서 조심할 것

- **세로읽기 퍼즐** — 9개 페이지에 한 글자씩 숨겨 `케로케로하트를검색` (9자)이
  되도록 배치합니다. 원문은 `ケロケロハート検索`. 글자 수가 어긋나면 퍼즐이 깨집니다.
- **검색 토큰 수** — 엔진은 공백으로 나눈 토큰을 2개까지만 봅니다.
  한글 정답은 붙여 쓰고, 띄어쓰기 변형은 별칭 파일로 받습니다.
- **숨김 요소** — `display:none` 등으로 감춘 단서가 페이지마다 있습니다.
  내용만 번역하고 구조는 그대로 두세요.
- **`noindex` 유지** — 스포일러 방지.

자세한 설계는 [docs/superpowers/specs/2026-09-09-arg-tutorial-kr-design.md](docs/superpowers/specs/2026-09-09-arg-tutorial-kr-design.md).
