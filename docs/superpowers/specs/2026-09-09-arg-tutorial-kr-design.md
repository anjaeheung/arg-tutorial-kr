# ARG 초보자 튜토리얼 한국어판 — 설계

작성일: 2026-09-09

## 목표

일본어 Web 탐색형 ARG 연습 사이트 `argtutorial.marimaric.workers.dev` 를
한국어판으로 옮겨 GitHub Pages(`anjaeheung/arg-tutorial-kr`)에 배포한다.
원작자: まりc (marimaric). 엔진: YACHO(SIM3).

## 원본 구조 분석

완전 정적 사이트. 서버 로직 없음.

| 구성 | 내용 |
|---|---|
| 페이지 | 23개 (`index.html` + `contents/*.html` 22개) |
| 엔진 | ES 모듈 10개. `structure.json` 으로 페이지 목록·번호 관리 |
| 검색 | `data/search/{키워드}.json` 을 그대로 fetch — **키워드가 곧 파일명** |
| 2단어 검색 | 두 토큰을 정렬 후 이어붙인 이름의 JSON을 fetch |
| 힌트 | `needMore`(더 필요) / `partial`(일부 정답). 원본은 이 둘을 CSS로 숨김 |
| 자산 | CSS 10, 이미지 4 |

입력 정규화는 `dataProvider.sanitize()` 가 담당한다. 앞뒤 공백 제거,
제어문자 제거, 전각공백(U+3000) → 반각공백 치환. 그 외 변형은 없다.
즉 키워드는 **입력 문자열과 정확히 일치**해야 한다.

## 채택한 방식 — 원본 미러 + 텍스트 치환

원본 파일 트리를 그대로 두고 HTML의 번역 대상 텍스트만 한국어로 교체한다.
CSS·JS 엔진·디렉터리 구조·`structure.json` 은 건드리지 않는다.

이유: ARG 기믹(숨김 요소, 세로읽기, 숨은 링크)이 CSS와 DOM 구조에 직접
얹혀 있다. 재구축하면 이것들이 조용히 깨지고, 깨진 걸 발견하기도 어렵다.
얻는 것에 비해 위험이 크다.

## 게임 진행 지도

검색으로 도달하는 페이지:

| 키워드 | 도달 페이지 |
|---|---|
| ARG初心者チュートリアル | tutorial |
| 目的 | markuteki |
| Web探索型ARG | webttusaku |
| 不自然 | youc1aru1 |
| まりc | yokuaru2 |
| 現実世界 | yokuaru4 |
| 理不尽 / 無理ゲー | unreasonable |
| ケロケロハート | mituketane |
| ぬいぐるみ | continue |
| 超!ARG団 (= 超ARG団) | 2wordtutorial |
| ユキママ | yukimama |
| 超!ARG団 + 目的 | mokuteki-choARGdan |
| 超!ARG団 + まりc | maric-choARGdan |
| 超!ARG団 + 現実世界 | theARGworld |

검색이 아닌 경로로 도달하는 페이지:

- `yokuaru3` — URL을 직접 고쳐서 도달 (URL改変 학습 페이지)
- `hidden-links` — `unreasonable` 페이지의 마침표에 숨긴 링크
- `complete`, `clear`, `thankyouAlly` — 진행 중 직접 링크

**미해결**: `allcomplete`, `maocool`(ex1), `soudesu`(ex2) 의 키워드.
원작자가 본문에서 "스토리로는 추측 불가능하게 설계했다"고 명시한 구간이라
본문 분석으로는 나오지 않는다. 원작자에게 문의하는 것이 유일한 정공법.
그때까지 페이지 자체는 배포에 포함하되 검색으로는 열리지 않는다.

## 현지화 결정

### 1. 키워드 — 한글·일본어 양쪽 수용

같은 JSON을 한글 이름과 일본어 이름 양쪽으로 둔다. 파일 복제라 비용이 없고,
한국어로 자연스럽게 플레이하면서도 원본 공략이 그대로 통해 막히지 않는다.

### 2. 세로읽기 퍼즐 — 글자 수를 9칸에 맞춘다

9개 페이지에 한 글자씩 숨겨 세로로 읽으면 `ケロケロハート検索` (9자)가 된다.
직역한 `케로케로하트검색` 은 8자라 한 칸이 빈다.
→ **`케로케로하트를검색`** (9자)을 쓴다. 칸 수가 정확히 맞고 문장으로도 읽힌다.
검색할 키워드는 앞 6자인 `케로케로하트`.

배치 순서(원본과 동일한 페이지에 동일한 자리):
tutorial=케, markuteki=로, webttusaku=케, youc1aru1=로, yokuaru2=하,
yokuaru4=트, yokuaru3=를, unreasonable=검, hidden-links=색

### 3. 손번역

ARG 텍스트는 유도 문구와 말장난이 퍼즐 그 자체다. 기계번역은 단서를
망가뜨린다. 23페이지뿐이므로 전부 손으로 옮긴다.

### 4. 보존 대상

- `robots: noindex, nofollow` — 스포일러 방지. 유지.
- 숨김 요소의 CSS·DOM 구조 — 내용만 번역, 구조는 그대로.
- 푸터에 원작 크레딧과 원본 사이트 링크를 추가한다.

## 작업 파이프라인

1. `tools/mirror.py` — 원본 미러 (완료)
2. `tools/extract_strings.py` — 번역 대상 문자열을 카탈로그로 추출
3. 손번역 — 카탈로그의 한국어 칸을 채운다
4. `tools/apply_strings.py` — 카탈로그를 HTML에 다시 주입
5. `tools/build_search.py` — 한글 키워드 검색 JSON 생성
6. 검증 — 브라우저로 실제 진행하며 각 키워드가 정확히 목표 페이지를 여는지 확인
7. GitHub Pages 배포

## 권리 관계

원작자 まりc 의 창작물이다. 공개 재배포에 해당하므로 배포 전에 원작자에게
번역·재게시 허락을 받는 것을 권한다. 문의용 일본어 초안을
`docs/permission-request.ja.md` 에 함께 둔다.
