#!/usr/bin/env python3
"""종이접기 퍼즐 이미지 3장을 한국어판으로 생성한다.

원본은 손으로 접고 쓴 종이 사진이다. 사진을 흉내 내는 대신 같은 구조를
깨끗한 그래픽으로 다시 그린다. 구조만 지키면 퍼즐은 그대로 작동한다.

배치 (4x4 격자):
  노란 종이 — 네 모서리 칸이 정답 글자.  [0][0]현 [0][3]조 [3][0]봐 [3][3]계
  흰 종이   — 가운데 네 칸이 정답 글자.  [1][1]실 [1][2]사 [2][1]해 [2][2]세

접으면 노란 종이는 모서리만, 흰 종이는 가운데만 남아 여덟 글자가 모인다.
  좌상→우하 대각선 : 현 실 세 계   (검색 정답)
  우상→좌하 대각선 : 조 사 해 봐   (숨은 지시문)
"""
import random, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.stdout.reconfigure(encoding="utf-8")
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
FONT = "C:/Windows/Fonts/batang.ttc"      # 붓 느낌이 나는 명조 계열
FONT_IDX = 2                               # 궁서

S = 1400                                   # 종이 한 변(px)
PAD = 90                                   # 캔버스 여백
N = 4                                      # 격자
CELL = S // N

WHITE_PAPER = (243, 240, 233)
WHITE_EDGE  = (214, 209, 197)
WASHI       = (226, 189, 100)
WASHI_EDGE  = (190, 152, 66)
INK         = (58, 54, 48)
PENCIL      = (150, 146, 138)
RED         = (196, 52, 40)
BG          = (250, 249, 246)

# 정답 글자 배치
YELLOW_RED = {(0, 0): "현", (0, 3): "조", (3, 0): "봐", (3, 3): "계"}
WHITE_RED  = {(1, 1): "실", (1, 2): "사", (2, 1): "해", (2, 2): "세"}

# 미끼용 음절. 이어 읽어도 뜻이 생기지 않도록 흩어 쓴다.
FILLER = list("가녀돌뭄삭쥐틀펴흠컹뚝샅욱짚캄녹빔웅챠킁덤랏춤팥흙븟쩡")


def font(size):
    try:
        return ImageFont.truetype(FONT, size, index=FONT_IDX)
    except Exception:
        return ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", size)


def paper_texture(img, seed):
    """종이 결을 흉내 낸 옅은 노이즈."""
    rnd = random.Random(seed)
    w, h = img.size
    noise = Image.new("L", (w // 3, h // 3))
    noise.putdata([rnd.randint(118, 138) for _ in range((w // 3) * (h // 3))])
    noise = noise.resize((w, h), Image.BILINEAR).filter(ImageFilter.GaussianBlur(1.2))
    return Image.composite(img, Image.new("RGB", (w, h), (255, 255, 255)),
                           noise.point(lambda v: 235 + (v - 128) // 6))


def draw_creases(d, x0, y0, edge):
    """접힘선 — 격자 + 각 사분면 대각선."""
    for i in range(1, N):
        p = i * CELL
        d.line([(x0, y0 + p), (x0 + S, y0 + p)], fill=edge, width=2)
        d.line([(x0 + p, y0), (x0 + p, y0 + S)], fill=edge, width=2)
    d.line([(x0, y0), (x0 + S, y0 + S)], fill=edge, width=2)
    d.line([(x0 + S, y0), (x0, y0 + S)], fill=edge, width=2)
    h = S // 2
    for ox, oy in [(0, 0), (h, 0), (0, h), (h, h)]:
        d.line([(x0 + ox, y0 + oy + h), (x0 + ox + h, y0 + oy)], fill=edge, width=1)
        d.line([(x0 + ox, y0 + oy), (x0 + ox + h, y0 + oy + h)], fill=edge, width=1)


def glyph(base, ch, cx, cy, color, size, seed):
    """글자 한 자를 살짝 기울여 얹는다. 손으로 쓴 느낌을 내기 위한 흔들림."""
    rnd = random.Random(seed)
    pad = size
    layer = Image.new("RGBA", (size + pad * 2, size + pad * 2), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    f = font(size)
    bb = ld.textbbox((0, 0), ch, font=f)
    ld.text(((layer.width - (bb[2] - bb[0])) // 2 - bb[0],
             (layer.height - (bb[3] - bb[1])) // 2 - bb[1]), ch, font=f, fill=color + (255,))
    layer = layer.rotate(rnd.uniform(-7, 7), resample=Image.BICUBIC)
    base.paste(layer, (int(cx - layer.width // 2 + rnd.randint(-9, 9)),
                       int(cy - layer.height // 2 + rnd.randint(-9, 9))), layer)


def sheet(fill, edge, reds, seed, name):
    """펼친 종이 한 장."""
    W = S + PAD * 2
    img = Image.new("RGB", (W, W), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([PAD, PAD, PAD + S, PAD + S], fill=fill, outline=edge, width=3)
    draw_creases(d, PAD, PAD, edge)

    rnd = random.Random(seed)
    pool = FILLER[:]
    rnd.shuffle(pool)
    k = 0
    for r in range(N):
        for c in range(N):
            cx = PAD + c * CELL + CELL // 2
            cy = PAD + r * CELL + CELL // 2
            if (r, c) in reds:
                glyph(img, reds[(r, c)], cx, cy, RED, 150, seed + r * 10 + c)
            else:
                col = INK if (r + c) % 3 else PENCIL
                glyph(img, pool[k % len(pool)], cx, cy, col, 128, seed + 500 + r * 10 + c)
                k += 1

    img = paper_texture(img, seed)
    img.save(OUT / name, quality=92)
    print("  생성  %s" % name)
    return img


def folded(name):
    """두 장을 겹쳐 접은 상태. 노란 모서리 + 흰 팔각형만 남는다."""
    W = S + PAD * 2
    img = Image.new("RGB", (W, W), BG)
    d = ImageDraw.Draw(img)

    # 노란 종이
    d.rectangle([PAD, PAD, PAD + S, PAD + S], fill=WASHI, outline=WASHI_EDGE, width=3)
    for ox, oy in [(0, 0), (S, 0), (0, S), (S, S)]:
        pass
    # 접힌 자국
    d.line([(PAD, PAD), (PAD + S, PAD + S)], fill=WASHI_EDGE, width=2)
    d.line([(PAD + S, PAD), (PAD, PAD + S)], fill=WASHI_EDGE, width=2)

    # 흰 종이 — 모서리를 접어 만든 팔각형
    c = S * 0.28
    oct_pts = [(PAD + c, PAD), (PAD + S - c, PAD), (PAD + S, PAD + c), (PAD + S, PAD + S - c),
               (PAD + S - c, PAD + S), (PAD + c, PAD + S), (PAD, PAD + S - c), (PAD, PAD + c)]
    shadow = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).polygon([(x + 6, y + 10) for x, y in oct_pts], fill=(0, 0, 0, 60))
    img.paste(Image.alpha_composite(img.convert("RGBA"), shadow.filter(
        ImageFilter.GaussianBlur(9))).convert("RGB"), (0, 0))
    d = ImageDraw.Draw(img)
    d.polygon(oct_pts, fill=WHITE_PAPER, outline=WHITE_EDGE)
    d.line([(PAD + c, PAD), (PAD + S, PAD + S - c)], fill=WHITE_EDGE, width=1)
    d.line([(PAD + S - c, PAD), (PAD, PAD + S - c)], fill=WHITE_EDGE, width=1)
    d.line([(PAD + S // 2, PAD), (PAD + S // 2, PAD + S)], fill=WHITE_EDGE, width=1)
    d.line([(PAD, PAD + S // 2), (PAD + S, PAD + S // 2)], fill=WHITE_EDGE, width=1)

    # 노란 종이의 네 모서리 글자
    m = CELL // 2
    for (r, ch) in [((0, 0), "현"), ((0, 3), "조"), ((3, 0), "봐"), ((3, 3), "계")]:
        rr, cc = r
        glyph(img, ch, PAD + cc * CELL + m, PAD + rr * CELL + m, RED, 150, 900 + rr * 10 + cc)

    # 흰 종이의 가운데 네 글자
    for (r, ch) in [((1, 1), "실"), ((1, 2), "사"), ((2, 1), "해"), ((2, 2), "세")]:
        rr, cc = r
        glyph(img, ch, PAD + cc * CELL + m, PAD + rr * CELL + m, RED, 150, 700 + rr * 10 + cc)

    img = paper_texture(img, 42)
    img.save(OUT / name, quality=92)
    print("  생성  %s" % name)


OUT.mkdir(parents=True, exist_ok=True)
sheet(WHITE_PAPER, WHITE_EDGE, WHITE_RED, 11, "white_unfolded.jpg")
sheet(WASHI, WASHI_EDGE, YELLOW_RED, 23, "yellow_unfolded.jpg")
folded("folded.jpg")
print("완료:", OUT.resolve())
