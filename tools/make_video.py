import math, subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1920, 1080, 30
BG = (255, 255, 255)
MG = (181, 23, 95)
OR = (242, 146, 0)
DK = (60, 60, 59)
GR = (120, 120, 120)
CREAM = (251, 247, 243)
FD = "/usr/share/fonts/opentype/inter/"
def F(w, s): return ImageFont.truetype(FD + f"Inter-{w}.otf", s)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO = Image.open(f"{ROOT}/images/brand/cceescopio_logo_di.png").convert("RGBA")
ICON = Image.open(f"{ROOT}/images/brand/cceescopio_icono.png").convert("RGBA")
INST = Image.open(f"{ROOT}/images/logos_ugr_fccee.jpg").convert("RGBA")

def clamp(x, a=0, b=1): return max(a, min(b, x))
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def appear(t, t0, d=0.6): return ease((t - t0) / d)
def mix(c, a): return tuple(int(BG[i] + (c[i] - BG[i]) * a) for i in range(3))
def env(t, dur, fi=0.4, fo=0.4): return clamp(min(t / fi if fi else 1, (dur - t) / fo if fo else 1))
def text(d, xy, s, f, col, a=1, anchor="mm"):
    if a > 0: d.text(xy, s, font=f, fill=mix(col, a), anchor=anchor)
def paste(img, src, cx, cy, width, a):
    if a <= 0: return
    h = int(src.height * width / src.width)
    im = src.resize((int(width), h), Image.LANCZOS)
    r, g, b, al = im.split()
    al = al.point(lambda v: int(v * a))
    im.putalpha(al)
    img.paste(im, (int(cx - width / 2), int(cy - h / 2)), im)
def band(d, a=1):  # franjas de color de la Facultad
    d.rectangle([0, 0, W, 14], fill=mix(MG, a)); d.rectangle([0, H - 14, W, H], fill=mix(OR, a))

def s0(t, dur):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img); e = env(t, dur, 0.5)
    band(d, e)
    paste(img, LOGO, W / 2, 380, 1500, appear(t, 0.2, 1.0) * e)
    text(d, (W / 2, 640), "D+I: Docencia + Investigación", F("ExtraBold", 60), OR, appear(t, 1.4) * e)
    text(d, (W / 2, 730), "Datos de la economía y la empresa para aprender, enseñar e investigar", F("SemiBold", 46), DK, appear(t, 2.0) * e)
    paste(img, INST, W / 2, 920, 820, appear(t, 2.6) * e)
    return img

EMO = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 109)
_emo = {}
def emoji(img, ch, cx, cy, size, a):
    if a <= 0: return
    if ch not in _emo:
        im = Image.new("RGBA", (136, 128), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((68, 64), ch, font=EMO, embedded_color=True, anchor="mm")
        _emo[ch] = im.crop(im.getbbox())
    src = _emo[ch]
    k = size / max(src.width, src.height); w = int(src.width * k); h = int(src.height * k)
    im = src.resize((int(w), h), Image.LANCZOS)
    al = im.split()[3].point(lambda v: int(v * a)); im.putalpha(al)
    img.paste(im, (int(cx - w / 2), int(cy - h / 2)), im)

def cursor(d, x, y, a):
    if a <= 0: return
    pts = [(x, y), (x, y + 46), (x + 12, y + 35), (x + 22, y + 56), (x + 31, y + 52), (x + 21, y + 31), (x + 37, y + 31)]
    d.polygon(pts, fill=mix(DK, a), outline=mix((255, 255, 255), a))
def title(d, s, t, e, y=120, size=74):
    text(d, (W / 2, y), s, F("ExtraBold", size), MG, appear(t, 0.2) * e)
def lerp(a, b, u): return a + (b - a) * u
def chip(d, x, y, s, col, a, f=None, pad=34, h=46, fg=(255, 255, 255)):
    f = f or F("Bold", 34)
    w = d.textlength(s, font=f)
    d.rounded_rectangle([x - w / 2 - pad, y - h, x + w / 2 + pad, y + h], radius=h, fill=mix(col, a))
    text(d, (x, y), s, f, fg, a)
def tri(d, x, y, a, col=GR):
    d.polygon([(x - 11, y - 6), (x + 11, y - 6), (x, y + 8)], fill=mix(col, a))
def arrow_dn(d, x, y, a, col=(255, 255, 255)):
    d.rectangle([x - 4, y - 16, x + 4, y + 4], fill=mix(col, a)); d.polygon([(x - 13, y), (x + 13, y), (x, y + 15)], fill=mix(col, a))
    d.rectangle([x - 14, y + 18, x + 14, y + 22], fill=mix(col, a))
def ilus(d, a): text(d, (W - 60, H - 50), "Ilustración", F("Medium", 26), GR, a, anchor="rm")

def s1(t, dur):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img); e = env(t, dur)
    band(d, e)
    title(d, "¿Qué es CCEEscopio D+I?", t, e, 210, 84)
    text(d, (W / 2, 350), "Los principales datos de la economía y la empresa, en un solo lugar", F("SemiBold", 50), DK, appear(t, 0.9) * e)
    nums = [("99", "indicadores"), ("11", "áreas temáticas"), ("5", "grados de la Facultad")]
    for i, (n, l) in enumerate(nums):
        a = appear(t, 1.8 + i * 0.6) * e
        if a <= 0: continue
        x = W / 2 + (i - 1) * 520; y = 590 + (1 - a) * 40
        d.rounded_rectangle([x - 230, y - 140, x + 230, y + 140], radius=30, fill=mix(CREAM, a))
        text(d, (x, y - 30), n, F("Black", 140), MG if i != 1 else OR, a)
        text(d, (x, y + 85), l, F("SemiBold", 40), DK, a)
    text(d, (W / 2, 900), "España · Andalucía y las comunidades autónomas · Unión Europea", F("Medium", 42), GR, appear(t, 4.0) * e)
    return img

AREAS = [("🛒", "Precios e inflación"), ("👥", "Mercado laboral"), ("📈", "Actividad y coyuntura"), ("💡", "Empresa e innovación"),
         ("✈️", "Turismo"), ("🏛️", "Sector público y mercados"), ("⚖️", "Desigualdad y pobreza"), ("🌱", "Energía y sostenibilidad"),
         ("👪", "Población, educación y salud"), ("🌍", "Economía internacional"), ("🗺️", "Andalucía y regiones"), ("⛽", "Precios de productos")]
def s2(t, dur):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img); e = env(t, dur)
    band(d, e)
    title(d, "Doce áreas, 99 indicadores", t, e, 130)
    f = F("Bold", 30)
    for k, (ic, a_) in enumerate(AREAS):
        a = appear(t, 1.0 + k * 0.5) * e
        if a <= 0: continue
        col, row = k % 4, k // 4
        x = 270 + col * 460; y = 330 + row * 230; dy = (1 - a) * 40
        d.rounded_rectangle([x - 210, y - 95 + dy, x + 210, y + 95 + dy], radius=22, fill=mix(CREAM, a), outline=mix((225, 215, 210), a), width=3)
        d.rounded_rectangle([x - 210, y - 95 + dy, x + 210, y - 80 + dy], radius=8, fill=mix(OR if k == 11 else (MG if k % 2 == 0 else OR), a))
        emoji(img, ic, x, y - 25 + dy, 64, a)
        text(d, (x, y + 50 + dy), a_, f, DK, a)
    text(d, (W / 2, 1010), "Datos oficiales de Eurostat, descargados en directo cada vez que abres la página", F("Medium", 38), GR, appear(t, 7.5) * e)
    return img

YEARS = list(range(2008, 2026))
def serie(u, k):
    # formas ilustrativas (no son datos): España, Andalucía, UE-27
    base = [0.42, 0.62, 0.22][k]; amp = [0.40, 0.42, 0.12][k]
    bump = math.exp(-((u - 0.30) / 0.22) ** 2)
    return base + amp * bump - 0.10 * u + 0.02 * math.sin(9 * u + k)
def s3(t, dur):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img); e = env(t, dur)
    band(d, e)
    title(d, "Gráficos interactivos de series temporales", t, e, 110, 66)
    a = appear(t, 0.8) * e
    # controles tipo web
    if a > 0:
        d.rounded_rectangle([140, 190, 760, 260], radius=12, fill=mix(CREAM, a), outline=mix((215, 205, 200), a), width=2)
        text(d, (165, 225), "Indicador:  Tasa de paro", F("SemiBold", 32), DK, a, anchor="lm")
        tri(d, 725, 225, a)
        for i, (n, c) in enumerate([("España", MG), ("Andalucía", OR), ("UE-27", DK)]):
            chip(d, 940 + i * 230, 225, n, c, a, F("Bold", 28), 26, 30)
    x0, x1, y0, y1 = 200, 1720, 320, 870
    a = appear(t, 1.2) * e
    if a > 0:
        for g in range(5):
            yy = y1 - g * (y1 - y0) / 4
            d.line([(x0, yy), (x1, yy)], fill=mix((232, 228, 226), a), width=2)
        d.line([(x0, y1), (x1, y1)], fill=mix(GR, a), width=3)
        for i, yr in enumerate(YEARS):
            if yr % 2 == 0:
                x = x0 + i / (len(YEARS) - 1) * (x1 - x0)
                text(d, (x, y1 + 32), str(yr), F("Medium", 26), GR, a)
    prog = ease((t - 1.6) / 3.0)
    def P(u, k): return (x0 + u * (x1 - x0), y1 - serie(u, k) * (y1 - y0))
    cols = [MG, OR, DK]
    for k in range(3):
        if prog <= 0: continue
        n = 160; pts = [P(i / n, k) for i in range(int(n * prog) + 1)]
        if len(pts) > 1: d.line(pts, fill=mix(cols[k], e), width=7, joint="curve")
    # cursor y tooltip
    ca = appear(t, 5.0) * e
    if ca > 0:
        u = 0.15 + 0.17 * ease((t - 5.0) / 1.8)
        xr = x0 + u * (x1 - x0)
        d.line([(xr, y0), (xr, y1)], fill=mix(GR, ca), width=2)
        for k in range(3):
            px, py = P(u, k); d.ellipse([px - 11, py - 11, px + 11, py + 11], fill=mix(cols[k], ca), outline=mix((255, 255, 255), ca), width=3)
        yr = YEARS[round(u * (len(YEARS) - 1))]
        bx, by = xr + 40, 360
        d.rounded_rectangle([bx, by, bx + 330, by + 190], radius=14, fill=mix((255, 255, 255), ca), outline=mix((205, 195, 190), ca), width=2)
        text(d, (bx + 24, by + 38), str(yr), F("ExtraBold", 34), DK, ca, anchor="lm")
        for k, n in enumerate(["España", "Andalucía", "UE-27"]):
            yy = by + 85 + k * 38
            d.ellipse([bx + 24, yy - 9, bx + 42, yy + 9], fill=mix(cols[k], ca))
            text(d, (bx + 56, yy), n, F("SemiBold", 28), DK, ca, anchor="lm")
        px, py = P(u, 0); cursor(d, xr + 6, py + 20, ca)
    # botón de descarga
    ba = appear(t, 7.6) * e
    if ba > 0:
        pulse = 1 + 0.04 * math.sin(max(0, t - 7.6) * 6) * (1 if t < 9.2 else 0)
        w, h = 300 * pulse, 34 * pulse
        d.rounded_rectangle([W / 2 - w, 960 - h, W / 2 + w, 960 + h], radius=12, fill=mix(MG, ba))
        text(d, (W / 2 + 22, 960), "Datos (CSV) y gráfico (PNG/SVG)", F("Bold", 32), (255, 255, 255), ba); arrow_dn(d, W / 2 - 272, 955, ba)
    ilus(d, a)
    return img

# mapa de teselas de las comunidades autónomas (cada cuadrado es una comunidad)
TILES = [("GAL", "Galicia", 0, 0), ("AST", "Asturias", 1, 0), ("CAN", "Cantabria", 2, 0), ("PVA", "País Vasco", 3, 0), ("NAV", "Navarra", 4, 0),
         ("CYL", "Castilla y León", 1, 1), ("RIO", "La Rioja", 3, 1), ("ARA", "Aragón", 4, 1), ("CAT", "Cataluña", 5, 1),
         ("EXT", "Extremadura", 0, 2), ("MAD", "Madrid", 2, 2), ("CLM", "Castilla-La Mancha", 3, 2), ("VAL", "C. Valenciana", 4, 2), ("BAL", "Illes Balears", 5.6, 2.2),
         ("AND", "Andalucía", 1.5, 3), ("MUR", "Murcia", 3, 3),
         ("CNR", "Canarias", 0, 4.3), ("CEU", "Ceuta", 1.5, 4.1), ("MEL", "Melilla", 2.5, 4.1)]
NIVEL = {"GAL": .35, "AST": .40, "CAN": .30, "PVA": .18, "NAV": .15, "CYL": .32, "RIO": .22, "ARA": .20, "CAT": .28, "EXT": .78,
         "MAD": .30, "CLM": .55, "VAL": .52, "BAL": .25, "AND": .88, "MUR": .50, "CNR": .70, "CEU": .95, "MEL": .92}
PAL = [(254, 235, 226), (251, 180, 185), (247, 104, 161), (197, 27, 138), (122, 1, 119)]
def pal(v):
    v = clamp(v) * (len(PAL) - 1); i = min(int(v), len(PAL) - 2); u = v - i
    return tuple(int(lerp(PAL[i][j], PAL[i + 1][j], u)) for j in range(3))
def s4(t, dur):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img); e = env(t, dur)
    band(d, e)
    title(d, "Mapas interactivos y animados", t, e, 110, 76)
    text(d, (W / 2, 190), "Cada indicador, en el mapa de las comunidades autónomas o de los países de la UE", F("Medium", 38), DK, appear(t, 0.6) * e)
    S, gx, gy = 122, 470, 265
    yr_u = clamp((t - 4.0) / 3.0)
    for k, (c, n, cx, cy) in enumerate(TILES):
        a = appear(t, 1.0 + k * 0.08) * e
        if a <= 0: continue
        v = NIVEL[c] * (1 - 0.25 * yr_u) + 0.04 * math.sin(k)
        x = gx + cx * (S + 12); y = gy + cy * (S + 12)
        col = pal(v)
        d.rounded_rectangle([x, y, x + S, y + S], radius=16, fill=mix(col, a))
        text(d, (x + S / 2, y + S / 2), c, F("Bold", 30), (255, 255, 255) if v > 0.45 else DK, a)
    # leyenda y selector de periodo
    a = appear(t, 2.2) * e
    if a > 0:
        lx, ly = 1400, 360
        text(d, (lx, ly), "Periodo del mapa", F("SemiBold", 32), DK, a, anchor="lm")
        d.rounded_rectangle([lx, ly + 35, lx + 380, ly + 95], radius=12, fill=mix(CREAM, a), outline=mix((215, 205, 200), a), width=2)
        yr = 2015 + round(9 * yr_u)
        text(d, (lx + 24, ly + 65), str(yr), F("Bold", 34), MG, a, anchor="lm")
        tri(d, lx + 350, ly + 65, a)
        for i in range(100):
            d.line([(lx + i * 3.8, ly + 170), (lx + i * 3.8, ly + 200)], fill=mix(pal(i / 99), a), width=5)
        text(d, (lx, ly + 230), "menos", F("Medium", 26), GR, a, anchor="lm")
        ba = appear(t, 3.4) * e
        if ba > 0:
            on = 4.0 <= t <= 7.2
            d.rounded_rectangle([lx, ly + 290, lx + 380, ly + 360], radius=14, fill=mix(MG if on else CREAM, ba), outline=mix(MG, ba), width=3)
            if on:
                d.rectangle([lx + 120, ly + 310, lx + 132, ly + 340], fill=mix((255, 255, 255), ba)); d.rectangle([lx + 140, ly + 310, lx + 152, ly + 340], fill=mix((255, 255, 255), ba))
                text(d, (lx + 170, ly + 325), "Parar", F("Bold", 32), (255, 255, 255), ba, anchor="lm")
            else:
                d.polygon([(lx + 40, ly + 308), (lx + 40, ly + 342), (lx + 68, ly + 325)], fill=mix(MG, ba))
                text(d, (lx + 85, ly + 325), "Animar el mapa", F("Bold", 32), MG, ba, anchor="lm")
            if 3.4 < t < 4.2: cursor(d, lx + 300, ly + 330, ba)
        text(d, (lx + 380, ly + 230), "más", F("Medium", 26), GR, a, anchor="rm")
    # tooltip sobre Andalucía
    ta = appear(t, 7.4) * e
    if ta > 0:
        x = gx + 1.5 * (S + 12) + S / 2; y = gy + 3 * (S + 12) + S / 2
        d.rounded_rectangle([gx + 1.5 * (S + 12) - 4, gy + 3 * (S + 12) - 4, gx + 1.5 * (S + 12) + S + 4, gy + 3 * (S + 12) + S + 4], radius=18, outline=mix(DK, ta), width=5)
        bx, by = x - S / 2 - 480, y - 60
        d.rounded_rectangle([bx, by, bx + 455, by + 120], radius=14, fill=mix((255, 255, 255), ta), outline=mix((205, 195, 190), ta), width=2)
        text(d, (bx + 24, by + 40), "Andalucía", F("ExtraBold", 34), DK, ta, anchor="lm")
        text(d, (bx + 24, by + 86), "Valor y periodo al pasar el ratón", F("Medium", 26), GR, ta, anchor="lm")
        cursor(d, x + 10, y + 10, ta)
    ilus(d, appear(t, 1) * e)
    return img

CALC = [("🧮", "Calculadora de inflación", "¿Cuánto valen hoy los euros de otro año?"),
        ("⛽", "Precios de productos", "Gasolina, luz y cesta de la compra"),
        ("📉", "Regresión con supuestos", "MCO con contraste de supuestos"),
        ("⚖️", "Desigualdad: Gini y Theil", "Curva de Lorenz e intervalos de confianza"),
        ("🏠", "Simulador de hipotecas", "Cuota y amortización con el euríbor"),
        ("🗺️", "Mapa de calor de coyuntura", "Todos los países de un vistazo")]
def s5(t, dur):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img); e = env(t, dur)
    band(d, e)
    title(d, "Calculadoras y herramientas de análisis", t, e, 120, 70)
    for k, (ic, n, s_) in enumerate(CALC):
        a = appear(t, 0.8 + k * 0.55) * e
        if a <= 0: continue
        col, row = k % 2, k // 2
        x = 520 + col * 880; y = 320 + row * 240; dy = (1 - a) * 40
        d.rounded_rectangle([x - 410, y - 100 + dy, x + 410, y + 100 + dy], radius=26, fill=mix(CREAM, a), outline=mix(MG if k % 2 == 0 else OR, a), width=4)
        emoji(img, ic, x - 315, y + dy, 96, a)
        text(d, (x - 230, y - 26 + dy), n, F("ExtraBold", 40), DK, a, anchor="lm")
        text(d, (x - 230, y + 32 + dy), s_, F("Medium", 29), GR, a, anchor="lm")
    text(d, (W / 2, 1010), "Más de 20 calculadoras, con tus datos o con los de la web", F("Medium", 36), GR, appear(t, 4.6) * e)
    return img

GRADOS = [("GADE", MG), ("GECO", OR), ("GFICO", MG), ("GMIM", OR), ("GTUR", MG)]
DOC = [("🧪", "Laboratorio de números índice", "Cambio de base, deflactar, Laspeyres…"),
       ("✅", "Ejercicios autocorregibles", "Con datos reales que cambian cada día"),
       ("📝", "Generador de exámenes", "Versiones distintas con sus soluciones"),
       ("📽️", "Modo presentación", "Proyecta los datos en clase")]
def s6(t, dur):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img); e = env(t, dur)
    band(d, e)
    title(d, "Docencia", t, e, 115, 84)
    text(d, (W / 2, 205), "Indicadores y ejemplos para cada grado y asignatura de la Facultad", F("SemiBold", 40), DK, appear(t, 0.6) * e)
    for k, (g, col) in enumerate(GRADOS):
        a = appear(t, 1.0 + k * 0.3) * e
        if a <= 0: continue
        x = W / 2 + (k - 2) * 300; y = 310
        chip(d, x, y, g, col, a, F("ExtraBold", 36), 40, 42)
    a = appear(t, 2.6) * e
    text(d, (W / 2, 400), "215 asignaturas con indicadores recomendados y ejemplos de uso en clase", F("Medium", 34), GR, a)
    for k, (ic, n, s_) in enumerate(DOC):
        a = appear(t, 3.4 + k * 0.6) * e
        if a <= 0: continue
        col, row = k % 2, k // 2
        x = 520 + col * 880; y = 580 + row * 220; dy = (1 - a) * 40
        d.rounded_rectangle([x - 410, y - 90 + dy, x + 410, y + 90 + dy], radius=26, fill=mix(CREAM, a))
        d.rectangle([x - 410, y - 90 + dy, x - 396, y + 90 + dy], fill=mix(MG if k in (0, 3) else OR, a))
        emoji(img, ic, x - 320, y + dy, 84, a)
        text(d, (x - 245, y - 24 + dy), n, F("ExtraBold", 38), DK, a, anchor="lm")
        text(d, (x - 245, y + 30 + dy), s_, F("Medium", 28), GR, a, anchor="lm")
    return img

def qr_dibujo(d, x, y, cel, a):
    import random
    rnd = random.Random(7); n = 25
    d.rectangle([x - cel, y - cel, x + (n + 1) * cel, y + (n + 1) * cel], fill=mix((255, 255, 255), a))
    def finder(px, py):
        d.rectangle([x + px * cel, y + py * cel, x + (px + 7) * cel - 1, y + (py + 7) * cel - 1], fill=mix(DK, a))
        d.rectangle([x + (px + 1) * cel, y + (py + 1) * cel, x + (px + 6) * cel - 1, y + (py + 6) * cel - 1], fill=mix((255, 255, 255), a))
        d.rectangle([x + (px + 2) * cel, y + (py + 2) * cel, x + (px + 5) * cel - 1, y + (py + 5) * cel - 1], fill=mix(DK, a))
    for i in range(n):
        for j in range(n):
            if (i < 8 and j < 8) or (i < 8 and j > n - 9) or (i > n - 9 and j < 8): continue
            if rnd.random() < 0.48: d.rectangle([x + i * cel, y + j * cel, x + (i + 1) * cel - 1, y + (j + 1) * cel - 1], fill=mix(DK, a))
    finder(0, 0); finder(n - 7, 0); finder(0, n - 7)

JUEGOS = ["Concurso de preguntas", "¿Cuánto costaba?", "Memoria de datos", "Ordena la malla", "¿Quién es quién?", "Bingo de indicadores"]
def s7(t, dur):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img); e = env(t, dur)
    band(d, e)
    title(d, "Juegos para clase con código QR", t, e, 110, 72)
    # pantalla del aula: QR y ranking
    a = appear(t, 0.7) * e
    if a > 0:
        d.rounded_rectangle([110, 190, 1010, 780], radius=24, fill=mix(CREAM, a), outline=mix((215, 205, 200), a), width=3)
        text(d, (560, 235), "Pantalla del aula", F("Bold", 32), GR, a)
        qr_dibujo(d, 160, 300, 13, a)
        text(d, (330, 680), "Escanea y juega", F("Bold", 32), MG, a)
        nombres = [("Analista_7", 0.92), ("Keynesiana", 0.78), ("Paro0", 0.66), ("SmithFan", 0.45)]
        for k, (n, v) in enumerate(nombres):
            ra = appear(t, 2.6 + k * 0.4) * e
            if ra <= 0: continue
            yy = 330 + k * 95; prog = v * ease((t - 2.6 - k * 0.4) / 2.5)
            if k < 3: emoji(img, ["🥇", "🥈", "🥉"][k], 580, yy, 40, ra)
            else: text(d, (565, yy), "4.", F("Bold", 30), DK, ra, anchor="lm")
            text(d, (615, yy - 18), n, F("Bold", 28), DK, ra, anchor="lm")
            d.rounded_rectangle([615, yy + 10, 615 + 360, yy + 30], radius=10, fill=mix((235, 228, 224), ra))
            d.rounded_rectangle([615, yy + 10, 615 + 360 * max(prog, 0.03), yy + 30], radius=10, fill=mix(MG if k == 0 else OR, ra))
    # móvil con la malla 3 × 3
    a = appear(t, 1.6) * e
    if a > 0:
        px, py = 1180, 180
        d.rounded_rectangle([px, py, px + 360, py + 640], radius=46, fill=mix(DK, a))
        d.rounded_rectangle([px + 18, py + 60, px + 342, py + 600], radius=20, fill=mix((255, 255, 255), a))
        text(d, (px + 180, py + 100), "¿Dónde estaba 12,5 %?", F("Bold", 26), MG, a)
        cel = 92
        for i in range(9):
            r, c = divmod(i, 3); x0 = px + 36 + c * (cel + 8); y0 = py + 140 + r * (cel + 8)
            ver = t > 4.2 + i * 0.45
            d.rounded_rectangle([x0, y0, x0 + cel, y0 + cel], radius=12, fill=mix(CREAM if ver else (245, 245, 245), a), outline=mix(MG if ver else (220, 210, 214), a), width=3)
            text(d, (x0 + cel / 2, y0 + cel / 2), ["10,5", "3,4", "7,5", "12,5", "5,9", "8,1", "6,6", "9,2", "4,0"][i] if ver else "?", F("ExtraBold", 28), MG if ver else GR, a)
        text(d, (px + 180, py + 470), "Cada acierto descubre", F("Medium", 24), GR, a)
        text(d, (px + 180, py + 505), "una casilla", F("Medium", 24), GR, a)
    for k, n in enumerate(JUEGOS):
        ga = appear(t, 5.0 + k * 0.45) * e
        if ga <= 0: continue
        col, row = k % 3, k // 3
        chip(d, 330 + col * 630, 880 + row * 105, n, MG if k % 2 == 0 else OR, ga, F("Bold", 32), 30, 40)
    return img

IDEA = ["Convergencia del PIB per cápita en las", "comunidades autónomas desde 2008"]
def s8(t, dur):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img); e = env(t, dur)
    band(d, e)
    title(d, "Investigación", t, e, 115, 84)
    text(d, (W / 2, 205), "Para TFG, TFM, tesis y artículos", F("SemiBold", 42), DK, appear(t, 0.6) * e)
    # tarjeta de idea de TFG
    a = appear(t, 1.2) * e
    if a > 0:
        x0, y0 = 140, 290
        d.rounded_rectangle([x0, y0, x0 + 880, y0 + 560], radius=26, fill=mix((255, 255, 255), a), outline=mix((225, 215, 210), a), width=3)
        d.rectangle([x0, y0, x0 + 14, y0 + 560], fill=mix(MG, a))
        emoji(img, "🎲", x0 + 75, y0 + 52, 48, a)
        text(d, (x0 + 115, y0 + 50), "Ideas para tu TFG o TFM", F("ExtraBold", 38), MG, a, anchor="lm")
        n = int(clamp((t - 2.0) / 2.2) * sum(len(x) for x in IDEA)); k = 0
        for i, linea in enumerate(IDEA):
            frag = linea[:max(0, n - k)]; k += len(linea)
            text(d, (x0 + 50, y0 + 130 + i * 52), frag, F("Bold", 36), DK, a, anchor="lm")
        for i, (et, v) in enumerate([("Pregunta", "¿Crecen más las regiones más pobres?"), ("Datos", "PIB per cápita por regiones (Eurostat)"), ("Método", "Convergencia beta y sigma"), ("Estructura", "Introducción · Datos · Método · Resultados")]):
            ia = appear(t, 4.4 + i * 0.4) * e
            text(d, (x0 + 50, y0 + 290 + i * 62), et + ":", F("Bold", 28), MG, ia, anchor="lm")
            text(d, (x0 + 230, y0 + 290 + i * 62), v, F("Medium", 28), DK, ia, anchor="lm")
    INV = [("📊", "Gráficos con la cita de la fuente"), ("⬇️", "Datos en CSV y gráficos en PNG/SVG"), ("📚", "Bases de datos de la Biblioteca"), ("🔬", "Gini, Theil, convergencia y regresión")]
    for k, (ic, n) in enumerate(INV):
        ia = appear(t, 2.0 + k * 0.6) * e
        if ia <= 0: continue
        y = 330 + k * 135; dx = (1 - ia) * 40
        d.rounded_rectangle([1080 + dx, y - 55, 1790 + dx, y + 55], radius=24, fill=mix(CREAM, ia))
        emoji(img, ic, 1140 + dx, y, 60, ia)
        text(d, (1195 + dx, y), n, F("Bold", 32), DK, ia, anchor="lm")
    text(d, (W / 2, 1000), "Más de 60 temas y miles de combinaciones para todas las titulaciones", F("Medium", 36), GR, appear(t, 6.2) * e)
    return img

EVO = [(2019, 250), (2020, 88), (2021, 63), (2022, 63), (2023, 63), (2025, 88), (2026, 88)]
def s9(t, dur):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img); e = env(t, dur)
    band(d, e)
    title(d, "La UGR en los rankings", t, e, 115, 80)
    text(d, (W / 2, 200), "Posición y evolución de las áreas de la Facultad (ARWU, QS y THE)", F("SemiBold", 38), DK, appear(t, 0.6) * e)
    # gráfico de evolución: Turismo en el Ranking de Shanghái (más arriba es mejor)
    a = appear(t, 1.0) * e
    x0, x1, y0, y1 = 170, 1050, 330, 840
    if a > 0:
        d.rounded_rectangle([110, 270, 1110, 930], radius=24, fill=mix(CREAM, a))
        text(d, (610, 305), "Turismo · Ranking de Shanghái por materias", F("Bold", 30), DK, a)
        for v in (50, 100, 200, 300):
            yy = y0 + (v / 300) * (y1 - y0)
            d.line([(x0, yy), (x1, yy)], fill=mix((225, 218, 214), a), width=2)
            text(d, (x0 - 15, yy), str(v), F("Medium", 24), GR, a, anchor="rm")
        for yr in range(2019, 2027):
            xx = x0 + (yr - 2019) / 7 * (x1 - x0)
            text(d, (xx, y1 + 35), str(yr), F("Medium", 24), GR, a)
    prog = ease((t - 1.8) / 3.0)
    pts = [(x0 + (yr - 2019) / 7 * (x1 - x0), y0 + (v / 300) * (y1 - y0)) for yr, v in EVO]
    m = prog * (len(pts) - 1)
    for i in range(len(pts) - 1):
        if i >= m: break
        u = min(1, m - i); pa, pb = pts[i], pts[i + 1]
        if EVO[i + 1][0] - EVO[i][0] > 1: continue
        d.line([pa, (lerp(pa[0], pb[0], u), lerp(pa[1], pb[1], u))], fill=mix(MG, e), width=8)
    for i, p in enumerate(pts):
        if i <= m + 0.01 and prog > 0: d.ellipse([p[0] - 12, p[1] - 12, p[0] + 12, p[1] + 12], fill=mix(MG, e), outline=mix((255, 255, 255), e), width=3)
    ta = appear(t, 5.0) * e
    text(d, (pts[2][0], pts[2][1] - 45), "Top 75", F("ExtraBold", 30), MG, ta)
    rows = [("Turismo", "Top 100 mundial"), ("Gestión (Management)", "2.ª de España"), ("Administración de Empresas", "1.ª de Andalucía")]
    for i, (a1, a2) in enumerate(rows):
        ra = appear(t, 2.4 + i * 0.6) * e
        if ra <= 0: continue
        y = 360 + i * 175; col = OR if i % 2 else MG
        d.rounded_rectangle([1180, y - 70, 1810, y + 70], radius=22, fill=mix(CREAM, ra))
        d.rectangle([1180, y - 70, 1194, y + 70], fill=mix(col, ra))
        text(d, (1225, y - 22), a1, F("ExtraBold", 36), DK, ra, anchor="lm")
        text(d, (1225, y + 30), a2 + " · Shanghái 2026", F("Bold", 30), col, ra, anchor="lm")
    text(d, (W / 2, 1010), "Fuente: Unidad de Analítica de la UGR y noticias de la Facultad", F("Regular", 28), GR, appear(t, 3.4) * e)
    return img

def s10(t, dur):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img); e = env(t, dur)
    band(d, e)
    title(d, "Tu opinión cuenta", t, e, 200, 84)
    text(d, (W / 2, 320), "Responde a la encuesta de satisfacción: menos de un minuto", F("SemiBold", 46), DK, appear(t, 0.8) * e)
    for i in range(5):
        a = appear(t, 1.6 + i * 0.25) * e
        if a <= 0: continue
        on = t > 3.2 + i * 0.15
        cx = W / 2 + (i - 2) * 170; cy = 520; r = 70; ri = 30
        pts = []
        for j in range(10):
            ang = -math.pi / 2 + j * math.pi / 5; rr = r if j % 2 == 0 else ri
            pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
        d.polygon(pts, fill=mix(OR if on else (230, 222, 218), a))
    a = appear(t, 3.8) * e
    if a > 0:
        chip(d, W / 2, 720, "Botón «¿Nos valoras?» en todas las páginas", MG, a, F("Bold", 40), 40, 50)
    text(d, (W / 2, 880), "Nos ayuda a mejorar CCEEscopio D+I y a saber qué recursos son más útiles", F("Medium", 38), GR, appear(t, 4.4) * e)
    return img

def s11(t, dur):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img); e = env(t, dur, 0.4, 1.0)
    band(d, e)
    paste(img, LOGO, W / 2, 290, 1150, appear(t, 0.1) * e)
    a = appear(t, 0.9) * e
    if a > 0:
        d.rounded_rectangle([W / 2 - 560, 500, W / 2 + 560, 700], radius=30, fill=mix(CREAM, a), outline=mix(MG, a), width=4)
        text(d, (W / 2, 560), "¿Propuestas o dudas? Escríbenos", F("SemiBold", 44), DK, a)
        text(d, (W / 2, 640), "investiga_ccee@ugr.es", F("ExtraBold", 60), MG, a)
    text(d, (W / 2, 770), "Vicedecanato de Investigación, Transferencia y Posgrado", F("Medium", 40), DK, appear(t, 1.5) * e)
    paste(img, INST, W / 2, 920, 820, appear(t, 1.8) * e)
    return img


# ---------- Novedades de noviembre de 2026: noticias del día, bolsa y simuladores ----------
def reloj(d, cx, cy, r, a, t):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=mix((255, 255, 255), a), outline=mix(MG, a), width=8)
    for k in range(12):
        ang = k * math.pi / 6; d.line([(cx + 0.8 * r * math.sin(ang), cy - 0.8 * r * math.cos(ang)), (cx + 0.9 * r * math.sin(ang), cy - 0.9 * r * math.cos(ang))], fill=mix(DK, a), width=5)
    m = ease(t / 2.5)  # las agujas avanzan de las 8:00 a las 9:00
    am = 2 * math.pi * m; ah = math.radians(240 + 30 * m)
    d.line([(cx, cy), (cx + 0.75 * r * math.sin(am), cy - 0.75 * r * math.cos(am))], fill=mix(DK, a), width=7)
    d.line([(cx, cy), (cx + 0.5 * r * math.sin(ah), cy - 0.5 * r * math.cos(ah))], fill=mix(MG, a), width=10)
    d.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], fill=mix(MG, a))

def sN1(t, dur):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img); e = env(t, dur)
    band(d, e)
    title(d, "Hoy en la economía", t, e, 110, 80)
    text(d, (W / 2, 195), "Cada mañana, antes de las 9:00, en la portada", F("SemiBold", 44), DK, appear(t, 0.6) * e)
    reloj(d, 230, 520, 130, appear(t, 0.8) * e, t - 0.8)
    text(d, (230, 700), "9:00", F("Black", 64), MG, appear(t, 2.6) * e)
    cols = [("🇪🇸", "España", MG), ("🇪🇺", "Europa", OR), ("🌍", "Mundo", DK)]
    for k, (ic, n, col) in enumerate(cols):
        a = appear(t, 1.4 + k * 0.5) * e
        if a <= 0: continue
        x0 = 470 + k * 480; y0 = 290 + (1 - a) * 40
        d.rounded_rectangle([x0, y0, x0 + 440, y0 + 560], radius=22, fill=mix((255, 255, 255), a), outline=mix((225, 215, 210), a), width=3)
        d.rectangle([x0, y0, x0 + 440, y0 + 14], fill=mix(col, a))
        emoji(img, ic, x0 + 50, y0 + 62, 44, a)
        text(d, (x0 + 90, y0 + 62), n, F("ExtraBold", 38), DK, a, anchor="lm")
        for j in range(5):
            ja = appear(t, 2.2 + k * 0.4 + j * 0.25) * e
            if ja <= 0: continue
            yy = y0 + 130 + j * 84
            d.ellipse([x0 + 26, yy - 4, x0 + 58, yy + 28], fill=mix((246, 238, 242), ja))
            text(d, (x0 + 42, yy + 12), str(j + 1), F("Bold", 22), MG, ja)
            w1 = 330 - (j * 37 + k * 23) % 90; w2 = 250 - (j * 53 + k * 31) % 110
            d.rounded_rectangle([x0 + 78, yy, x0 + 78 + w1, yy + 14], radius=7, fill=mix((70, 70, 70), ja))
            d.rounded_rectangle([x0 + 78, yy + 24, x0 + 78 + w2, yy + 38], radius=7, fill=mix((185, 185, 185), ja))
            if j % 2 == 0: d.rounded_rectangle([x0 + 78, yy + 48, x0 + 78 + 150, yy + 64], radius=8, fill=mix((246, 238, 242), ja))
    text(d, (W / 2, 925), "Las noticias económicas y empresariales que más medios publican", F("SemiBold", 40), DK, appear(t, 4.6) * e)
    text(d, (W / 2, 985), "con los indicadores de CCEEscopio para comprobarlas", F("Medium", 36), GR, appear(t, 5.1) * e)
    ilus(d, appear(t, 1) * e)
    return img

TICKS = [("IBEX 35", 0), ("Euro Stoxx 50", 1), ("S&P 500", 2), ("Nikkei 225", 3), ("Brent", 4), ("Oro", 5)]
def spark_pts(k, n=60):
    import random
    r = random.Random(11 + k); v = 0; pts = []
    for i in range(n): v += r.gauss(0.04 if k % 3 else -0.02, 0.35); pts.append(v)
    return pts
def sN2(t, dur):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img); e = env(t, dur)
    band(d, e)
    title(d, "Bolsa al día", t, e, 110, 84)
    text(d, (W / 2, 195), "Índices de todo el mundo, petróleo, oro y empresas del IBEX 35, tres veces al día", F("SemiBold", 40), DK, appear(t, 0.6) * e)
    for k, (n, _) in enumerate(TICKS):
        a = appear(t, 1.0 + k * 0.3) * e
        if a <= 0: continue
        x0 = 120 + k * 285; y0 = 260 + (1 - a) * 30
        pts = spark_pts(k); sube = pts[-1] >= pts[0]
        d.rounded_rectangle([x0, y0, x0 + 260, y0 + 190], radius=18, fill=mix((255, 255, 255), a), outline=mix((225, 215, 210), a), width=3)
        text(d, (x0 + 20, y0 + 36), n, F("Bold", 30), DK, a, anchor="lm")
        text(d, (x0 + 20, y0 + 84), "▲" if sube else "▼", F("Bold", 34), (46, 125, 50) if sube else (198, 40, 40), a, anchor="lm")
        lo, hi = min(pts), max(pts); m = int(len(pts) * clamp((t - 1.3 - k * 0.3) / 1.5))
        if m > 1:
            sp = [(x0 + 20 + i / (len(pts) - 1) * 220, y0 + 170 - (v - lo) / (hi - lo + 1e-9) * 60) for i, v in enumerate(pts[:m])]
            d.line(sp, fill=mix((46, 125, 50) if sube else (198, 40, 40), a), width=4)
    # gráfico comparado en base 100
    a = appear(t, 3.2) * e
    x0, x1, y0, y1 = 200, 1720, 520, 900
    if a > 0:
        d.rounded_rectangle([140, 490, 1780, 960], radius=22, fill=mix(CREAM, a))
        text(d, (180, 540), "Evolución comparada (base 100)", F("Bold", 32), DK, a, anchor="lm")
        d.line([(x0, 760), (x1, 760)], fill=mix(GR, a), width=2)
        text(d, (x0 - 14, 760), "100", F("Medium", 24), GR, a, anchor="rm")
    prog = ease((t - 3.6) / 3.0)
    for k, col in enumerate([MG, OR, DK]):
        if prog <= 0: continue
        pts = spark_pts(k + 7, 140); n = int(len(pts) * prog)
        sc = [(x0 + i / 139 * (x1 - x0), 760 - pts[i] * 30) for i in range(n)]
        if len(sc) > 1: d.line(sc, fill=mix(col, e), width=6, joint="curve")
    for k, (n, col) in enumerate([("IBEX 35", MG), ("Euro Stoxx 50", OR), ("S&P 500", DK)]):
        la = appear(t, 3.8 + k * 0.2) * e
        chip(d, 1000 + k * 260, 545, n, col, la, F("Bold", 24), 18, 24)
    text(d, (W / 2, 1010), "Rentabilidad, volatilidad y retos que conectan la bolsa con los indicadores", F("Medium", 36), GR, appear(t, 5.5) * e)
    ilus(d, a)
    return img

SIMS = [("🏦", "Gobernador del Banco Central", "Tipos de interés, inflación y paro"), ("💼", "Gestiona una cartera", "100.000 € en un periodo secreto de la bolsa"),
        ("💶", "Llega a fin de mes", "Un hogar con la inflación real de cada gasto"), ("🏖️", "Gestiona tu destino turístico", "Empleo, vivienda y sostenibilidad")]
def sN3(t, dur):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img); e = env(t, dur)
    band(d, e)
    title(d, "Simuladores con datos reales", t, e, 110, 76)
    text(d, (W / 2, 195), "Decide como un banco central, una inversora, un hogar o una ciudad", F("SemiBold", 42), DK, appear(t, 0.6) * e)
    for k, (ic, n, s_) in enumerate(SIMS):
        a = appear(t, 1.0 + k * 0.45) * e
        if a <= 0: continue
        x = 140; y = 280 + k * 165; dx = (1 - a) * -40
        d.rounded_rectangle([x + dx, y, x + 860 + dx, y + 140], radius=24, fill=mix(CREAM, a))
        d.rectangle([x + dx, y, x + 14 + dx, y + 140], fill=mix(MG if k % 2 == 0 else OR, a))
        emoji(img, ic, x + 85 + dx, y + 70, 76, a)
        text(d, (x + 150 + dx, y + 48), n, F("ExtraBold", 38), DK, a, anchor="lm")
        text(d, (x + 150 + dx, y + 100), s_, F("Medium", 29), GR, a, anchor="lm")
    # mini simulador: deslizador del tipo de interés y la inflación que responde
    a = appear(t, 2.6) * e
    if a > 0:
        px, py = 1080, 280
        d.rounded_rectangle([px, py, px + 700, py + 640], radius=24, fill=mix((255, 255, 255), a), outline=mix((225, 215, 210), a), width=3)
        text(d, (px + 30, py + 45), "Tipo de interés oficial", F("Bold", 32), DK, a, anchor="lm")
        u = ease((t - 3.4) / 2.5); tipo = 0.5 + 3.5 * u
        d.rounded_rectangle([px + 30, py + 95, px + 520, py + 107], radius=6, fill=mix((237, 227, 231), a))
        d.rounded_rectangle([px + 30, py + 95, px + 30 + 490 * tipo / 8, py + 107], radius=6, fill=mix(MG, a))
        cxk = px + 30 + 490 * tipo / 8
        d.ellipse([cxk - 18, py + 83, cxk + 18, py + 119], fill=mix(MG, a), outline=mix((255, 255, 255), a), width=4)
        text(d, (px + 670, py + 101), f"{tipo:.2f} %".replace(".", ","), F("ExtraBold", 36), MG, a, anchor="rm")
        if 3.4 < t < 6: cursor(d, cxk + 6, py + 110, a)
        gx0, gx1, gy0, gy1 = px + 60, px + 670, py + 180, py + 560
        d.line([(gx0, gy1), (gx1, gy1)], fill=mix(GR, a), width=2)
        y2 = gy1 - 2 / 10 * (gy1 - gy0)
        d.line([(gx0, y2), (gx1, y2)], fill=mix((46, 125, 50), a), width=3)
        text(d, (gx0 + 8, y2 + 24), "Objetivo: 2 %", F("SemiBold", 24), (46, 125, 50), a, anchor="lm")
        pts = []
        for i in range(9):
            infl = 8.5 - 6.3 * (1 - math.exp(-i * 0.35 * u * 1.4)) if i else 8.5
            pts.append((gx0 + i / 8 * (gx1 - gx0), gy1 - infl / 10 * (gy1 - gy0)))
        d.line(pts, fill=mix(MG, a), width=6, joint="curve")
        for p_ in pts: d.ellipse([p_[0] - 8, p_[1] - 8, p_[0] + 8, p_[1] + 8], fill=mix(MG, a))
        text(d, (gx0, gy0 - 20), "Inflación (%)", F("Bold", 26), MG, a, anchor="lm")
        text(d, (px + 350, py + 605), "Ocho trimestres para controlar la inflación", F("Medium", 26), GR, a)
    text(d, (W / 2, 1010), "Con los últimos datos de Eurostat y de las bolsas · puntuación y comparación al final", F("Medium", 34), GR, appear(t, 5.0) * e)
    return img

SCENES = [(s0, 6.5), (s1, 7), (sN1, 9), (sN2, 9.5), (s2, 9.5), (s3, 10), (s4, 10), (s5, 9), (sN3, 10), (s6, 10), (s7, 12), (s8, 10), (s9, 9), (s10, 6.5), (s11, 6.5)]


def render(idx, outdir):
    fn, dur = SCENES[idx]
    out = f"{outdir}/scene{idx}.mp4"; tmp = f"{outdir}/scene{idx}.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                          "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for k in range(int(dur * FPS)):
        p.stdin.write(fn(k / FPS, dur).tobytes())
    p.stdin.close()
    if p.wait() == 0: os.replace(tmp, out)

if __name__ == "__main__":
    outdir = os.environ.get("VIDEO_DIR", "/home/claude/cceescopio_video4"); os.makedirs(outdir, exist_ok=True)
    if sys.argv[1] == "still":
        i, t = int(sys.argv[2]), float(sys.argv[3]); fn, dur = SCENES[i]; fn(t, dur).save(f"{outdir}/still_{i}.png")
    else:
        for i in map(int, sys.argv[2:]): render(i, outdir)
