#!/usr/bin/env python3
"""원작자의 실제 종이 사진 위에서 빨간 글자만 한글로 바꾼다.

검은 글자는 전부 의미 없는 미끼라 손대지 않는다. 바꿔야 하는 건 빨간 8자뿐이고,
그러면 원작자의 진짜 종이·손글씨·접힘·조명이 그대로 남는다. 종이가 몇 장인지,
어느 방향으로 뒤집혔는지 추론할 필요도 없다 — 있던 자리에 그대로 덮어쓰면 된다.

現実世界 → 현실세계   (검색 정답)
しらべて → 조사해봐   (숨은 지시문)
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
FONT = "C:/Windows/Fonts/batang.ttc"
FONT_IDX = 2

# (파일, 종이경계, {칸: (원래글자, 한글)})
JOBS = [
    ("image1 (1).jpeg", (92, 140, 2644, 2520), {
        (1, 1): ("実", "실"), (1, 2): ("ら", "사"),
        (2, 1): ("ベ", "해"), (2, 2): ("世", "세")}),
    ("image2.jpeg", (172, 172, 2672, 2628), {
        (0, 0): ("て", "봐"), (0, 3): ("現", "현"),
        (3, 0): ("界", "계"), (3, 3): ("し", "조")}),
    ("image0 (1).jpeg", (0, 0, 2424, 2248), {
        (0, 0): ("現", "현"), (0, 3): ("し", "조"),
        (3, 0): ("て", "봐"), (3, 3): ("界", "계"),
        (1, 1): ("実", "실"), (1, 2): ("ら", "사"),
        (2, 1): ("ベ", "해"), (2, 2): ("世", "세")}),
]


def red_mask(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return (r > 110) & (r - g > 70) & (r - b > 85)


def inpaint(arr, mask, rounds=3, sigma=8):
    """가려진 곳을 주변 종이색으로 메운다 (정규화 합성곱)."""
    out = arr.astype(np.float32).copy()
    m = mask.astype(np.float32)
    for _ in range(rounds):
        w = ndimage.gaussian_filter(1.0 - m, sigma)
        for c in range(3):
            v = ndimage.gaussian_filter(out[..., c] * (1.0 - m), sigma)
            filled = np.divide(v, w, out=np.zeros_like(v), where=w > 1e-4)
            out[..., c] = np.where(m > 0, filled, out[..., c])
        m = np.maximum(m - 0.35, 0)
    return np.clip(out, 0, 255).astype(np.uint8)


def run(src, dst, box, cells):
    im = Image.open(src).convert("RGB")
    a = np.asarray(im)
    x0, y0, x1, y1 = box
    cw, ch = (x1 - x0) / 4, (y1 - y0) / 4

    full = red_mask(a)
    if full.any():
        px = a[full].astype(int)
        ink = np.percentile(px, 25, axis=0).astype(int)   # 진한 쪽
    else:
        ink = np.array([190, 45, 35])

    # 대상 칸의 빨간 획만 골라 마스크로 삼는다
    target = np.zeros_like(full)
    spots = {}
    for (r, c) in cells:
        cx0, cy0 = int(x0 + c * cw), int(y0 + r * ch)
        cx1, cy1 = int(x0 + (c + 1) * cw), int(y0 + (r + 1) * ch)
        sub = np.zeros_like(full); sub[cy0:cy1, cx0:cx1] = full[cy0:cy1, cx0:cx1]
        if not sub.any():
            print("    !! 빨간 획 없음: 칸 %s" % ((r, c),)); continue
        ys, xs = np.nonzero(sub)
        spots[(r, c)] = (int(xs.mean()), int(ys.mean()),
                         int(max(xs.max() - xs.min(), ys.max() - ys.min())))
        target |= sub

    target = ndimage.binary_dilation(target, np.ones((7, 7)))
    cleaned = Image.fromarray(inpaint(a, target))

    d = ImageDraw.Draw(cleaned)
    for (r, c), (cx, cy, size) in spots.items():
        ja, ko = cells[(r, c)]
        cap = int(min(cw, ch) * 0.46)
        f = ImageFont.truetype(FONT, max(40, min(cap, int(size * 1.12))), index=FONT_IDX)
        bb = d.textbbox((0, 0), ko, font=f)
        d.text((cx - (bb[2] - bb[0]) / 2 - bb[0], cy - (bb[3] - bb[1]) / 2 - bb[1]),
               ko, font=f, fill=tuple(int(v) for v in ink))
        print("    %s → %s  (%d,%d) 크기 %d" % (ja, ko, cx, cy, size))

    s = 1600 / max(cleaned.size)
    if s < 1:
        cleaned = cleaned.resize((int(cleaned.width * s), int(cleaned.height * s)), Image.LANCZOS)
    cleaned.save(dst, "JPEG", quality=88, optimize=True)
    print("    저장 %s  %sx%s  %.2fMB" % (Path(dst).name, cleaned.size[0], cleaned.size[1],
                                          Path(dst).stat().st_size / 1e6))


OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
for name, box, cells in JOBS:
    print("--- %s" % name)
    run(f"_original/media/img/{name}", OUT / name, box, cells)
