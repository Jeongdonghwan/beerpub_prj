"""레이어 팝업 이미지 생성 (500x600) — 네온사인 스타일, 헤드라인 반짝임(APNG).
헤드라인 글로우가 숨쉬듯 세지고 약해지며 주변 별이 교대로 반짝인다. 나머지는 정지.
결과는 .png(APNG) — 브라우저 <img> 에서 그대로 움직인다.
문구를 바꾸려면 아래 EVENT/OPEN 블록만 고치고 실행 → static/images/popup/ 에 저장.
(로컬 전용: 맑은고딕 볼드 사용. 서버는 git 으로 결과 PNG 만 받는다)
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE = Path(__file__).resolve().parent
OUT = BASE / "app" / "static" / "images" / "popup"
DOH = str(BASE / "app" / "static" / "fonts" / "BMDOHYEON.ttf")
MAL = r"C:\Windows\Fonts\malgunbd.ttf"
W, H = 500, 600

BG = (16, 16, 20)
GOLD = (255, 214, 92)
GOLD_HI = (255, 244, 200)
GOLD_GLOW = (255, 170, 40)
RED = (255, 64, 72)
RED_GLOW = (255, 30, 40)
WHITE = (255, 255, 255)
DIM = (120, 112, 90)


def font(path, size):
    return ImageFont.truetype(path, size)


def text_w(text, fnt):
    return ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox((0, 0), text, font=fnt)[2]


def neon(img, xy, text, fnt, color=GOLD, glow=GOLD_GLOW, core=GOLD_HI, strength=1.0):
    """네온 글자: 넓은 글로우(블러 큼) → 좁은 글로우 → 본색 → 흰 코어 순서로 겹쳐 그림"""
    for blur, alpha in ((18, 150), (8, 200), (3, 255)):
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(layer).text(xy, text, font=fnt, fill=glow + (int(alpha * strength),))
        layer = layer.filter(ImageFilter.GaussianBlur(blur))
        img.alpha_composite(layer)
    d = ImageDraw.Draw(img)
    d.text(xy, text, font=fnt, fill=color)
    # 코어: 살짝 작은 오프셋 없이 흰빛 — 글자 가운데가 밝아 보이게
    core_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(core_layer).text(xy, text, font=fnt, fill=core + (110,))
    core_layer = core_layer.filter(ImageFilter.GaussianBlur(1.2))
    img.alpha_composite(core_layer)


def neon_center(img, y, text, fnt, **kw):
    neon(img, ((W - text_w(text, fnt)) / 2, y), text, fnt, **kw)


def bulb(img, x, y, r=5, on=True):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    if on:
        ld.ellipse((x - r * 2.6, y - r * 2.6, x + r * 2.6, y + r * 2.6), fill=(255, 190, 70, 120))
        layer = layer.filter(ImageFilter.GaussianBlur(5))
        img.alpha_composite(layer)
    d = ImageDraw.Draw(img)
    d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 236, 170) if on else (90, 80, 60))
    d.ellipse((x - r * .45, y - r * .55, x + r * .25, y + r * .1), fill=(255, 255, 255))


def marquee_sign(img, box, title, sub):
    """전구가 둘러싼 간판 프레임"""
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(box, radius=14, fill=(32, 26, 18), outline=(150, 115, 50), width=3)
    d.rounded_rectangle((x0 + 7, y0 + 7, x1 - 7, y1 - 7), radius=10, outline=(90, 70, 35), width=1)
    # 전구 — 테두리 따라 등간격, 2개 중 1개는 살짝 어둡게(깜빡이는 느낌)
    n = 0
    step = 22
    for x in range(x0 + 12, x1 - 11, step):
        bulb(img, x, y0, on=n % 3 != 2); bulb(img, x, y1, on=n % 3 != 1); n += 1
    for y in range(y0 + step, y1 - step + 1, step):
        bulb(img, x0, y, on=n % 3 != 0); bulb(img, x1, y, on=n % 3 != 2); n += 1
    tf = font(MAL, 34)   # 브랜드명(딹)은 도현체에 없음
    neon(img, ((W - text_w(title, tf)) / 2, y0 + 10), title, tf, color=GOLD, core=GOLD_HI)
    sf = font(DOH, 13)
    d = ImageDraw.Draw(img)
    d.text(((W - text_w(sub, sf)) / 2, y1 - 24), sub, font=sf, fill=(200, 170, 100))


def confetti(img, n=70, seed=7):
    rnd = random.Random(seed)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    for _ in range(n):
        x, y = rnd.randint(10, W - 10), rnd.randint(140, H - 80)
        w, h = rnd.randint(4, 9), rnd.randint(10, 18)
        ang = rnd.uniform(0, math.pi)
        c = rnd.choice([(255, 214, 92, 210), (255, 244, 200, 170), (255, 120, 60, 170), (230, 200, 120, 150)])
        piece = Image.new("RGBA", (w, h), c)
        piece = piece.rotate(math.degrees(ang), expand=True)
        layer.alpha_composite(piece, (x, y))
    img.alpha_composite(layer)


def stars(img, cx, y, n=5, size=11):
    f = font(MAL, size)
    t = "★" * n
    neon(img, (cx - text_w(t, f) / 2, y), t, f, color=GOLD, strength=.5)


FRAMES = 14          # 한 바퀴 프레임 수
FRAME_MS = 110       # 프레임 간격 → 한 바퀴 약 1.5초


def sparkle(img, x, y, size, a):
    """4갈래 반짝이 별 — a(0~1)로 밝기"""
    if a <= 0.02:
        return
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    s_, c = size * a, (255, 246, 200, int(255 * a))
    ld.line((x - s_, y, x + s_, y), fill=c, width=2)
    ld.line((x, y - s_, x, y + s_), fill=c, width=2)
    ld.line((x - s_ * .45, y - s_ * .45, x + s_ * .45, y + s_ * .45), fill=c, width=1)
    ld.line((x - s_ * .45, y + s_ * .45, x + s_ * .45, y - s_ * .45), fill=c, width=1)
    glow = layer.filter(ImageFilter.GaussianBlur(3))
    img.alpha_composite(glow)
    img.alpha_composite(layer)


def pulse(t, phase=0.0):
    """0~1 사이 부드러운 왕복 (t: 0~1 진행도)"""
    return 0.5 - 0.5 * math.cos(2 * math.pi * (t + phase))


def save_apng(frames, path):
    frames[0].convert("RGB").save(path, save_all=True, append_images=[f.convert("RGB") for f in frames[1:]],
                                  duration=FRAME_MS, loop=0, optimize=True)


def base():
    img = Image.new("RGBA", (W, H), BG + (255,))
    d = ImageDraw.Draw(img)
    # 은은한 다이아 패턴 (레퍼런스의 벽 느낌) — 단색 톤 유지
    for y in range(0, H, 18):
        for x in range(0, W, 18):
            d.point((x + (9 if (y // 18) % 2 else 0), y), fill=(28, 28, 34))
    marquee_sign(img, (34, 26, W - 34, 118), "맥주엔딹", "가맹문의 1522-4995")
    return img


def strike(img, x, y, text, fnt):
    d = ImageDraw.Draw(img)
    d.text((x, y), text, font=fnt, fill=DIM)
    w = text_w(text, fnt)
    d.line((x - 2, y + fnt.size * .55, x + w + 2, y + fnt.size * .55), fill=RED, width=3)
    return w


# ---------------- 1. 창업비용 이벤트 ----------------
EVENT = {
    "tag": "BIG EVENT",
    "title": "10호점까지",
    "title2": "가맹비 지원!",
    "rows": [("가맹비", "500만원", "0원"), ("교육비", "500만원", "300만원")],
    "foot": "좋은 상권은 금방 사라집니다",
}
static = base()
confetti(static, seed=3)
stars(static, W / 2, 128)
neon_center(static, 148, EVENT["tag"], font(DOH, 22), color=RED, glow=RED_GLOW, core=(255, 200, 200))
d = ImageDraw.Draw(static)
d.rounded_rectangle((38, 308, W - 38, 500), radius=12, fill=(24, 22, 24, 255), outline=(110, 85, 40), width=2)
lf, sf, bf = font(DOH, 26), font(DOH, 20), font(DOH, 36)
for i, (label, orig, new) in enumerate(EVENT["rows"]):
    y = 332 + i * 92
    if i:
        d.line((60, y - 12, W - 60, y - 12), fill=(60, 52, 40), width=1)
    neon(static, (60, y + 8), label, lf, color=WHITE, glow=(255, 220, 150), core=WHITE, strength=.45)
    ow = strike(static, 168, y + 12, orig, sf)
    d = ImageDraw.Draw(static)
    d.text((168 + ow + 12, y + 10), "→", font=sf, fill=DIM)
    neon(static, (168 + ow + 44, y + 2), new, bf, color=RED, glow=RED_GLOW, core=(255, 215, 215))
neon_center(static, 530, EVENT["foot"], font(DOH, 19), strength=.6)
stars(static, W / 2, 562, size=10)

SPK_EV = [(52, 190), (448, 186), (40, 262), (462, 258), (118, 296), (384, 170), (250, 292)]
frames = []
for k in range(FRAMES):
    t = k / FRAMES
    img = static.copy()
    g = 0.55 + 0.45 * pulse(t)                      # 글로우 세기 0.55~1.0
    hf = font(DOH, 46)
    neon_center(img, 182, EVENT["title"], hf, strength=g)
    neon_center(img, 236, EVENT["title2"], hf, strength=g)
    for i, (x, y) in enumerate(SPK_EV):
        sparkle(img, x, y, 9, max(0.0, pulse(t, i / len(SPK_EV)) * 2 - 1))
    frames.append(img)
save_apng(frames, OUT / "event_fee.png")

# ---------------- 2. 오픈 예정 지점 ----------------
OPEN = {
    "tag": "OPEN SOON",
    "title": "오픈 예정 지점!",
    "branches": ["양산점", "운암점", "신창점", "문흥점", "화정점"],
    "foot1": "좋은 상권은 금방 사라집니다",
    "foot2": "아직 늦지 않았습니다!",
}
static = base()
confetti(static, seed=11)
stars(static, W / 2, 128)
neon_center(static, 148, OPEN["tag"], font(DOH, 22), color=RED, glow=RED_GLOW, core=(255, 200, 200))
cells = [(38, 250), (254, 250), (38, 350), (254, 350), (146, 450)]
cw, ch = 208, 86
nf, st = font(DOH, 27), font(DOH, 14)
for (x, y), name in zip(cells, OPEN["branches"]):
    d = ImageDraw.Draw(static)
    d.rounded_rectangle((x, y, x + cw, y + ch), radius=10, fill=(24, 22, 24, 255), outline=(70, 58, 36), width=1)
    stars(static, x + cw / 2, y + 7, size=10)
    neon(static, (x + (cw - text_w(name, nf)) / 2, y + 24), name, nf)
    d = ImageDraw.Draw(static)
    t_ = "오픈예정!"; d.text((x + (cw - text_w(t_, st)) / 2, y + 60), t_, font=st, fill=(230, 190, 110))
neon_center(static, 548, OPEN["foot1"], font(DOH, 17), strength=.55)
neon_center(static, 572, OPEN["foot2"], font(DOH, 17), color=RED, glow=RED_GLOW, core=(255, 210, 210), strength=.7)

SPK_OP = [(58, 186), (442, 184), (84, 232), (420, 230), (250, 170), (160, 238), (350, 236)]
frames = []
for k in range(FRAMES):
    t = k / FRAMES
    img = static.copy()
    g = 0.55 + 0.45 * pulse(t)
    neon_center(img, 180, OPEN["title"], font(DOH, 46), strength=g)
    for i, (x, y) in enumerate(SPK_OP):
        sparkle(img, x, y, 9, max(0.0, pulse(t, i / len(SPK_OP)) * 2 - 1))
    frames.append(img)
save_apng(frames, OUT / "open_soon.png")
print("saved:", OUT)
