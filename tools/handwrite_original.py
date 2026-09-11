#!/usr/bin/env python3
"""원본 사진 위에 한글을 손으로 써 넣은 것처럼 얹는다.

지우지 않는다. 원작자의 종이·손글씨·접힘·조명이 그대로 남고, 빨간 원문 옆에
같은 빨간 펜으로 한글을 덧적는다. 받침(흰 네모) 없이 종이에 스며들게 곱하기로
합성하고, 글자마다 기울기와 위치를 흔들어 손으로 쓴 티를 낸다.
"""
import sys, random
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage

sys.stdout.reconfigure(encoding="utf-8")
FONT, FONT_IDX = "C:/Windows/Fonts/batang.ttc", 2      # 궁서 — 붓 느낌

# (파일, 종이경계, {칸: (한글, 원문 옆 어느 쪽에 쓸지)})
#   방향은 원래 글자를 가리지 않는 쪽. (dx, dy) 는 칸 크기 대비 비율.
JOBS = [
    ("image1 (1).jpeg", (92, 140, 2644, 2520), {
        (1, 1): ("실", -0.30,  0.26), (1, 2): ("사",  0.30,  0.26),
        (2, 1): ("해", -0.30, -0.26), (2, 2): ("세",  0.30, -0.26)}),
    ("image2.jpeg", (172, 172, 2672, 2628), {
        (0, 0): ("봐",  0.30,  0.26), (0, 3): ("현", -0.30,  0.26),
        (3, 0): ("계",  0.30, -0.26), (3, 3): ("조", -0.30, -0.26)}),
    ("image0 (1).jpeg", (0, 0, 2424, 2248), {
        (0, 0): ("현",  0.30,  0.26), (0, 3): ("조", -0.30,  0.26),
        (3, 0): ("봐",  0.30, -0.26), (3, 3): ("계", -0.30, -0.26),
        (1, 1): ("실", -0.28,  0.28), (1, 2): ("사",  0.28,  0.28),
        (2, 1): ("해", -0.28, -0.28), (2, 2): ("세",  0.28, -0.28)}),
]


def red_centroid(a, cell):
    """칸 안 빨간 획의 무게중심. 접힘 자국이 섞이지 않게 조인 기준을 쓴다."""
    cx0, cy0, cx1, cy1 = cell
    sub = a[cy0:cy1, cx0:cx1]
    r, g, b = sub[..., 0].astype(int), sub[..., 1].astype(int), sub[..., 2].astype(int)
    m = (r > 110) & (r - g > 70) & (r - b > 85)
    m = ndimage.binary_opening(m, np.ones((3, 3)))
    if m.sum() < 60:
        return None, None
    ys, xs = np.nonzero(m)
    return (cx0 + int(xs.mean()), cy0 + int(ys.mean())), sub[m].astype(int)


def run(src, dst, box, cells):
    im = Image.open(src).convert("RGB")
    a = np.asarray(im)
    x0, y0, x1, y1 = box
    cw, ch = (x1 - x0) / 4, (y1 - y0) / 4
    size = int(min(cw, ch) * 0.30)

    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    for (r, c), (ko, dx, dy) in cells.items():
        cell = (int(x0 + c * cw), int(y0 + r * ch), int(x0 + (c + 1) * cw), int(y0 + (r + 1) * ch))
        cen, px = red_centroid(a, cell)
        if cen is None:
            cen = (int(x0 + cw * (c + 0.5)), int(y0 + ch * (r + 0.5)))
            ink = (176, 42, 32)
            print("    %s  칸%s  빨간 획 못 찾아 칸 중앙에 배치" % (ko, (r, c)))
        else:
            ink = tuple(int(v) for v in np.percentile(px, 25, axis=0))
            print("    %s  칸%s  원문 옆 (%d,%d)" % (ko, (r, c), cen[0], cen[1]))

        rnd = random.Random(hash((r, c, ko)) & 0xffff)
        g = Image.new("RGBA", (size * 3, size * 3), (0, 0, 0, 0))
        gd = ImageDraw.Draw(g)
        f = ImageFont.truetype(FONT, size, index=FONT_IDX)
        bb = gd.textbbox((0, 0), ko, font=f)
        gd.text(((g.width - (bb[2] - bb[0])) / 2 - bb[0],
                 (g.height - (bb[3] - bb[1])) / 2 - bb[1]), ko, font=f, fill=ink + (238,))
        g = g.rotate(rnd.uniform(-8, 8), resample=Image.BICUBIC)
        g = g.filter(ImageFilter.GaussianBlur(1.1))
        layer.alpha_composite(g, (int(cen[0] + cw * dx - g.width / 2),
                                  int(cen[1] + ch * dy - g.height / 2)))

    base = np.asarray(im, dtype=np.float32) / 255.0
    lay = np.asarray(layer, dtype=np.float32) / 255.0
    rgb, al = lay[..., :3], lay[..., 3:4]
    out = Image.fromarray((np.clip(base * (1 - al) + base * rgb * al, 0, 1) * 255).astype(np.uint8))

    s = 1600 / max(out.size)
    if s < 1:
        out = out.resize((int(out.width * s), int(out.height * s)), Image.LANCZOS)
    out.save(dst, "JPEG", quality=88, optimize=True)
    print("    저장 %s  %.2fMB" % (Path(dst).name, Path(dst).stat().st_size / 1e6))


OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
for name, box, cells in JOBS:
    print("--- %s" % name)
    run(f"_original/media/img/{name}", OUT / name, box, cells)
