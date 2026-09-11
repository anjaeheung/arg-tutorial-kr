#!/usr/bin/env python3
"""원본 사진은 손대지 않고, 빨간 글자 옆에 한글을 적어 넣는다.

지우고 덮어쓰면 종이 질감이 뜨고 얼룩이 남는다. 원본을 그대로 두고 옆에
주석처럼 달면 원작자의 종이·손글씨·접힘이 온전히 남고, 한국인은 어느 글자가
무엇인지 바로 안다. 손으로 메모를 끼적인 것처럼 보이게 파란 펜 색을 쓴다.
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding="utf-8")
FONT = "C:/Windows/Fonts/malgun.ttf"
NOTE = (38, 78, 158)          # 파란 볼펜

# (파일, 종이경계, {칸: (한글, 칸 안에서의 위치)})
#   위치는 칸 안 상대좌표 (0~1). 원래 글자를 가리지 않는 쪽에 둔다.
JOBS = [
    ("image1 (1).jpeg", (92, 140, 2644, 2520), {
        (1, 1): ("실", 0.22, 0.80), (1, 2): ("사", 0.78, 0.80),
        (2, 1): ("해", 0.22, 0.22), (2, 2): ("세", 0.78, 0.22)}),
    ("image2.jpeg", (172, 172, 2672, 2628), {
        (0, 0): ("봐", 0.72, 0.78), (0, 3): ("현", 0.28, 0.78),
        (3, 0): ("계", 0.72, 0.22), (3, 3): ("조", 0.28, 0.22)}),
    ("image0 (1).jpeg", (0, 0, 2424, 2248), {
        (0, 0): ("현", 0.74, 0.76), (0, 3): ("조", 0.26, 0.76),
        (3, 0): ("봐", 0.74, 0.24), (3, 3): ("계", 0.26, 0.24),
        (1, 1): ("실", 0.24, 0.80), (1, 2): ("사", 0.76, 0.80),
        (2, 1): ("해", 0.24, 0.20), (2, 2): ("세", 0.76, 0.20)}),
]


def run(src, dst, box, cells):
    im = Image.open(src).convert("RGB")
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = box
    cw, ch = (x1 - x0) / 4, (y1 - y0) / 4
    size = int(min(cw, ch) * 0.30)
    f = ImageFont.truetype(FONT, size)

    for (r, c), (ko, fx, fy) in cells.items():
        cx = x0 + cw * (c + fx)
        cy = y0 + ch * (r + fy)
        bb = d.textbbox((0, 0), ko, font=f)
        w, h = bb[2] - bb[0], bb[3] - bb[1]
        # 글자가 읽히도록 살짝 밝은 받침을 깐다
        pad = size * 0.16
        d.rounded_rectangle([cx - w/2 - pad, cy - h/2 - pad, cx + w/2 + pad, cy + h/2 + pad],
                            radius=pad, fill=(252, 251, 246))
        d.text((cx - w/2 - bb[0], cy - h/2 - bb[1]), ko, font=f, fill=NOTE)
        print("    %s  칸%s" % (ko, (r, c)))

    s = 1600 / max(im.size)
    if s < 1:
        im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    im.save(dst, "JPEG", quality=88, optimize=True)
    print("    저장 %s  %sx%s  %.2fMB" % (Path(dst).name, im.size[0], im.size[1],
                                          Path(dst).stat().st_size / 1e6))


OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
for name, box, cells in JOBS:
    print("--- %s" % name)
    run(f"_original/media/img/{name}", OUT / name, box, cells)
