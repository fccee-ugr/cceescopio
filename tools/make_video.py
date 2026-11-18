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
LOGO = Image.open(f"{ROOT}/images/brand/cceescopio_logo.png").convert("RGBA")
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
    paste(img, LOGO, W / 2, 400, 1350, appear(t, 0.2, 1.0) * e)
    text(d, (W / 2, 700), "Observatorio de indicadores económicos y empresariales", F("SemiBold", 54), DK, appear(t, 1.5) * e)
    paste(img, INST, W / 2, 900, 900, appear(t, 2.3) * e)
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
    w = size; h = int(src.height * w / src.width)
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
    title(d, "¿Qué es CCEEscopio?", t, e, 210, 84)
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
         ("👪", "Población, educación y salud"), ("🌍", "Economía internacional"), ("🗺️", "Andalucía y regiones"), ("🏆", "Rankings")]
def s2(t, dur):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img); e = env(t, dur)
    band(d, e)
    title(d, "Once áreas, 99 indicadores", t, e, 130)
    f = F("Bold", 34)
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
        w, h = 260 * pulse, 34 * pulse
        d.rounded_rectangle([W / 2 - w, 960 - h, W / 2 + w, 960 + h], radius=12, fill=mix(MG, ba))
        text(d, (W / 2 + 22, 960), "Descargar los datos (CSV)", F("Bold", 32), (255, 255, 255), ba); arrow_dn(d, W / 2 - 215, 955, ba)
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
    title(d, "Mapas interactivos", t, e, 110, 76)
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

TOOLS = [("🧮", "Calculadora de inflación", "¿Cuánto valen hoy los euros de otro año?"),
         ("🪪", "Ficha de país o región", "Los indicadores clave de un vistazo"),
         ("🔗", "Relaciona dos indicadores", "Curva de Phillips, ley de Okun…"),
         ("🔎", "Buscador de indicadores", "Los 99 indicadores en una tabla")]
def s5(t, dur):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img); e = env(t, dur)
    band(d, e)
    title(d, "Herramientas", t, e, 140, 84)
    for k, (ic, n, s) in enumerate(TOOLS):
        a = appear(t, 0.9 + k * 0.7) * e
        if a <= 0: continue
        col, row = k % 2, k // 2
        x = 520 + col * 880; y = 400 + row * 330; dy = (1 - a) * 40
        d.rounded_rectangle([x - 400, y - 130 + dy, x + 400, y + 130 + dy], radius=28, fill=mix(CREAM, a), outline=mix(MG if (k in (0, 3)) else OR, a), width=4)
        emoji(img, ic, x - 290, y + dy, 110, a)
        text(d, (x - 200, y - 30 + dy), n, F("ExtraBold", 42), DK, a, anchor="lm")
        text(d, (x - 200, y + 35 + dy), s, F("Medium", 32), GR, a, anchor="lm")
    text(d, (W / 2, 1000), "Y en cada gráfico: enlace directo para compartirlo y datos descargables", F("Medium", 36), GR, appear(t, 4.6) * e)
    return img

GRADOS = [("GADE", "Administración y Dirección de Empresas", 47), ("GECO", "Economía", 46), ("GFICO", "Finanzas y Contabilidad", 45),
          ("GMIM", "Marketing e Investigación de Mercados", 45), ("GTUR", "Turismo", 32)]
def s6(t, dur):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img); e = env(t, dur)
    band(d, e)
    title(d, "Para cada asignatura de la Facultad", t, e, 120, 72)
    for k, (sg, n, c) in enumerate(GRADOS):
        a = appear(t, 0.9 + k * 0.45) * e
        if a <= 0: continue
        y = 250 + k * 100; x = 120 + (1 - a) * 40
        col = MG if k % 2 == 0 else OR
        d.rounded_rectangle([x, y - 40, x + 200, y + 40], radius=40, fill=mix(col, a))
        text(d, (x + 100, y), sg, F("ExtraBold", 36), (255, 255, 255), a)
        text(d, (x + 230, y), n, F("SemiBold", 31), DK, a, anchor="lm")
        text(d, (1330, y), f"{c} asignaturas", F("Bold", 34), col, a, anchor="rm")
    a = appear(t, 4.2) * e
    if a > 0:
        y0 = 770 + (1 - a) * 30
        d.rounded_rectangle([120, y0, W - 120, y0 + 230], radius=24, fill=mix(CREAM, a))
        d.rectangle([120, y0, 136, y0 + 230], fill=mix(MG, a))
        text(d, (170, y0 + 45), "GECO · Introducción a las Operaciones Financieras", F("ExtraBold", 36), DK, a, anchor="lm")
        text(d, (170, y0 + 105), "Indicadores: Euríbor a 3 meses · Bono a 10 años · Inflación", F("SemiBold", 32), MG, a, anchor="lm")
        text(d, (170, y0 + 165), "Ejemplo de uso: calcular la cuota de una hipoteca con el euríbor actual y obtener el tipo real.", F("Medium", 30), DK, a, anchor="lm")
    a = appear(t, 1.2) * e
    if a > 0:
        x = 1610; y = 450
        d.rounded_rectangle([x - 185, y - 200, x + 185, y + 200], radius=30, fill=mix(CREAM, a))
        emoji(img, "🎓", x, y - 50, 150, a)
        text(d, (x, y + 90), "215 asignaturas", F("ExtraBold", 40), MG, a)
        text(d, (x, y + 140), "con indicadores y ejemplos", F("Medium", 28), GR, a)
    return img

def s7(t, dur):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img); e = env(t, dur)
    band(d, e)
    title(d, "La UGR en los rankings", t, e, 150, 80)
    rows = [("Turismo", "ARWU (Shanghái) 2025", "Top 100 mundial"),
            ("Gestión (Management)", "ARWU (Shanghái) 2025", "2.ª de España"),
            ("Administración de Empresas", "ARWU (Shanghái) 2025", "1.ª de Andalucía"),
            ("Contabilidad y Finanzas", "QS 2026", "1.ª de Andalucía")]
    for i, (a1, a3, a2) in enumerate(rows):
        a = appear(t, 0.8 + i * 0.6) * e
        if a <= 0: continue
        y = 330 + i * 165; col = OR if i % 2 else MG
        d.rounded_rectangle([200, y - 70, W - 200, y + 70], radius=22, fill=mix(CREAM, a))
        d.rectangle([200, y - 70, 216, y + 70], fill=mix(col, a))
        text(d, (260, y - 18), a1, F("ExtraBold", 46), DK, a, anchor="lm")
        text(d, (260, y + 36), a3, F("Medium", 28), GR, a, anchor="lm")
        text(d, (W - 250, y), a2, F("ExtraBold", 54), col, a, anchor="rm")
    text(d, (W / 2, 1010), "Economía, Empresa, Finanzas y Turismo en ARWU, QS y THE · Fuente: Unidad de Analítica de la UGR", F("Regular", 28), GR, appear(t, 3.4) * e)
    return img

def s8(t, dur):
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
    text(d, (W / 2, 880), "Nos ayuda a mejorar CCEEscopio y a saber qué recursos son más útiles", F("Medium", 38), GR, appear(t, 4.4) * e)
    return img

def s9(t, dur):
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

SCENES = [(s0, 6), (s1, 7), (s2, 10), (s3, 10.5), (s4, 10), (s5, 8.5), (s6, 10), (s7, 7.5), (s8, 7), (s9, 6)]

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
    outdir = "/home/claude/cceescopio_video2"; os.makedirs(outdir, exist_ok=True)
    if sys.argv[1] == "still":
        i, t = int(sys.argv[2]), float(sys.argv[3]); fn, dur = SCENES[i]; fn(t, dur).save(f"{outdir}/still_{i}.png")
    else:
        for i in map(int, sys.argv[2:]): render(i, outdir)
