#!/usr/bin/env python3
"""생성된 빈 종이 사진 위에 한글을 얹는다.

이미지 모델은 한글을 제대로 못 쓴다. 그래서 종이 질감·조명은 사진에서 얻고
글자는 여기서 직접 그린다. 잉크가 종이에 스민 것처럼 보이도록 곱하기 합성을
쓰고, 글자마다 기울기와 위치를 조금씩 흔들어 손으로 쓴 느낌을 낸다.

배치 (4x4 격자):
  흰 종이   가운데 네 칸  [1][1]실 [1][2]사 [2][1]해 [2][2]세
  노란 종이 네 모서리 칸  [0][0]현 [0][3]조 [3][0]봐 [3][3]계
"""
import random, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.stdout.reconfigure(encoding="utf-8")

FONT = "C:/Windows/Fonts/batang.ttc"
FONT_IDX = 2                      # 궁서 — 붓 느낌
RED = (176, 42, 32)
INK = (48, 44, 40)
PENCIL = (128, 124, 118)
N = 4

FILLER = list("가녀돌뭄삭쥐틀펴흠컹뚝샅욱짚캄녹빔웅챠킁덤랏춤팥흙븟쩡뎌콥")


def paper_bounds(im):
    """노트 배경과 구분되는 종이 영역의 사각형을 찾는다."""
    a = np.asarray(im.convert("RGB"), dtype=np.int16)
    h, w, _ = a.shape
    # 네 귀퉁이를 배경 표본으로 삼는다
    k = 30
    bg = np.concatenate([a[:k, :k].reshape(-1, 3), a[:k, -k:].reshape(-1, 3),
                         a[-k:, :k].reshape(-1, 3), a[-k:, -k:].reshape(-1, 3)])
    bg = np.median(bg, axis=0)
    dist = np.abs(a - bg).sum(axis=2)
    mask = dist > 26
    # 행/열별로 충분히 많은 화소가 배경과 다른 구간을 종이로 본다
    cols = np.where(mask.sum(axis=0) > h * 0.35)[0]
    rows = np.where(mask.sum(axis=1) > w * 0.35)[0]
    if len(cols) < 10 or len(rows) < 10:
        raise SystemExit("종이 경계를 못 찾았다")
    return int(cols[0]), int(rows[0]), int(cols[-1]), int(rows[-1])


def font(size):
    try:
        return ImageFont.truetype(FONT, size, index=FONT_IDX)
    except Exception:
        return ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", size)


def ink_layer(size_wh, placements, scale):
    """글자만 그린 투명 레이어. 나중에 곱하기로 종이에 스며들게 한다."""
    w, h = size_wh
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for ch, cx, cy, color, size, seed, alpha in placements:
        rnd = random.Random(seed)
        pad = size
        g = Image.new("RGBA", (size + pad * 2, size + pad * 2), (0, 0, 0, 0))
        gd = ImageDraw.Draw(g)
        f = font(size)
        bb = gd.textbbox((0, 0), ch, font=f)
        gd.text(((g.width - (bb[2] - bb[0])) // 2 - bb[0],
                 (g.height - (bb[3] - bb[1])) // 2 - bb[1]),
                ch, font=f, fill=color + (alpha,))
        g = g.rotate(rnd.uniform(-6, 6), resample=Image.BICUBIC)
        # 펜 자국이 균일하지 않도록 아주 살짝 번지게
        g = g.filter(ImageFilter.GaussianBlur(0.6 * scale))
        layer.alpha_composite(g, (int(cx - g.width // 2 + rnd.randint(-7, 7) * scale),
                                  int(cy - g.height // 2 + rnd.randint(-7, 7) * scale)))
    return layer


def compose(src, reds, seed, out, upscale=2, box=None):
    im = Image.open(src).convert("RGB")
    x0, y0, x1, y1 = box or paper_bounds(im)
    print("  종이 영역 %d,%d ~ %d,%d  (%dx%d)" % (x0, y0, x1, y1, x1 - x0, y1 - y0))

    if upscale > 1:
        im = im.resize((im.width * upscale, im.height * upscale), Image.LANCZOS)
        x0, y0, x1, y1 = [v * upscale for v in (x0, y0, x1, y1)]

    pw, ph = x1 - x0, y1 - y0
    cw, chh = pw / N, ph / N
    size = int(min(cw, chh) * 0.62)

    rnd = random.Random(seed)
    pool = FILLER[:]
    rnd.shuffle(pool)

    placements, k = [], 0
    for r in range(N):
        for c in range(N):
            cx = x0 + cw * (c + 0.5)
            cy = y0 + chh * (r + 0.5)
            if (r, c) in reds:
                placements.append((reds[(r, c)], cx, cy, RED, size, seed + r * 10 + c, 236))
            else:
                col = INK if (r + c) % 3 else PENCIL
                placements.append((pool[k % len(pool)], cx, cy, col,
                                   int(size * 0.88), seed + 500 + r * 10 + c,
                                   210 if col == INK else 165))
                k += 1

    layer = ink_layer(im.size, placements, upscale)
    # 곱하기 합성 — 잉크가 종이 결 위에 얹히지 않고 스며든다
    base = np.asarray(im, dtype=np.float32) / 255.0
    lay = np.asarray(layer, dtype=np.float32) / 255.0
    rgb, alpha = lay[..., :3], lay[..., 3:4]
    out_arr = base * (1 - alpha) + base * rgb * alpha
    res = Image.fromarray((np.clip(out_arr, 0, 1) * 255).astype(np.uint8))

    # 웹용으로 긴 변 1600px
    scale = 1600 / max(res.size)
    if scale < 1:
        res = res.resize((int(res.width * scale), int(res.height * scale)), Image.LANCZOS)
    res.save(out, quality=88, optimize=True)
    print("  저장 %s  %sx%s  %.2fMB" % (Path(out).name, res.size[0], res.size[1],
                                        Path(out).stat().st_size / 1e6))


if __name__ == "__main__":
    src, kind, out = sys.argv[1], sys.argv[2], sys.argv[3]
    # 노란 종이에서 정확히 검출된 경계. 두 장이 같은 구도로 생성돼 그대로 쓴다.
    box = tuple(int(v) for v in sys.argv[4].split(",")) if len(sys.argv) > 4 else None
    reds = ({(1, 1): "실", (1, 2): "사", (2, 1): "해", (2, 2): "세"} if kind == "white"
            else {(0, 0): "현", (0, 3): "조", (3, 0): "봐", (3, 3): "계"})
    compose(src, reds, 11 if kind == "white" else 23, out, box=box)
