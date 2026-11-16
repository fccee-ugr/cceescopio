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

def s1(t, dur):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img); e = env(t, dur)
    band(d, e)
    text(d, (W / 2, 260), "¿Qué es CCEEscopio?", F("ExtraBold", 84), MG, appear(t, 0.2) * e)
    text(d, (W / 2, 430), "Los principales datos de la economía y la empresa,", F("SemiBold", 60), DK, appear(t, 1.0) * e)
    text(d, (W / 2, 515), "en un solo lugar", F("SemiBold", 60), DK, appear(t, 1.4) * e)
    chips = ["España", "Andalucía", "Unión Europea"]
    f = F("Bold", 50)
    for i, c in enumerate(chips):
        a = appear(t, 2.6 + i * 0.6) * e
        if a <= 0: continue
        x = W / 2 + (i - 1) * 470; y = 720
        d.rounded_rectangle([x - 200, y - 55, x + 200, y + 55], radius=55, fill=mix(OR if i == 1 else MG, a))
        text(d, (x, y), c, f, (255, 255, 255), a)
    text(d, (W / 2, 900), "Facultad de Ciencias Económicas y Empresariales · Universidad de Granada", F("Medium", 40), GR, appear(t, 4.4) * e)
    return img

AREAS = ["Precios e inflación", "Mercado laboral", "Actividad y coyuntura", "Empresa e innovación", "Turismo",
         "Sector público y mercados", "Desigualdad", "Energía y sostenibilidad", "Andalucía y regiones"]
def s2(t, dur):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img); e = env(t, dur)
    band(d, e)
    text(d, (W / 2, 140), "Nueve áreas, más de 40 indicadores", F("ExtraBold", 76), MG, appear(t, 0.2) * e)
    f = F("Bold", 38)
    for k, a_ in enumerate(AREAS):
        a = appear(t, 1.2 + k * 0.75) * e
        if a <= 0: continue
        col, row = k % 3, k // 3
        x = 360 + col * 600; y = 330 + row * 230
        dy = (1 - a) * 40
        d.rounded_rectangle([x - 270, y - 85 + dy, x + 270, y + 85 + dy], radius=22, fill=mix(CREAM, a), outline=mix((225, 215, 210), a), width=3)
        d.rounded_rectangle([x - 270, y - 85 + dy, x + 270, y - 70 + dy], radius=8, fill=mix(MG if k % 2 == 0 else OR, a))
        text(d, (x, y + 8 + dy), a_, f, DK, a)
    text(d, (W / 2, 1010), "España, Andalucía, las comunidades autónomas y los países de la UE", F("Medium", 40), GR, appear(t, 8.5) * e)
    return img

def s3(t, dur):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img); e = env(t, dur)
    band(d, e)
    text(d, (W / 2, 150), "Datos oficiales, siempre actualizados", F("ExtraBold", 76), MG, appear(t, 0.2) * e)
    text(d, (W / 2, 245), "Se descargan en directo de Eurostat cada vez que abres la página", F("Medium", 46), DK, appear(t, 0.8) * e)
    x0, x1, y0, y1 = 300, 1500, 360, 880
    a = appear(t, 1.4) * e
    if a > 0:
        d.line([(x0, y1), (x1, y1)], fill=mix(GR, a), width=4); d.line([(x0, y0), (x0, y1)], fill=mix(GR, a), width=4)
    prog = ease((t - 1.8) / 3.5)
    series = [("España", MG, lambda u: 0.55 + 0.25 * math.sin(6 * u) * (1 - u) - 0.10 * u),
              ("Andalucía", OR, lambda u: 0.80 + 0.15 * math.sin(6 * u + 0.4) * (1 - u) - 0.15 * u),
              ("UE-27", DK, lambda u: 0.35 + 0.12 * math.sin(6 * u - 0.3) * (1 - u) - 0.15 * u)]
    for name, col, fn in series:
        if prog <= 0: continue
        n = 120; pts = []
        for i in range(int(n * prog) + 1):
            u = i / n; pts.append((x0 + 20 + u * (x1 - x0 - 40), y1 - 30 - fn(u) * (y1 - y0 - 60)))
        if len(pts) > 1: d.line(pts, fill=mix(col, e), width=8, joint="curve")
        if prog > 0.98: text(d, (pts[-1][0] + 20, pts[-1][1]), name, F("Bold", 40), col, e * appear(t, 5.4), anchor="lm")
    text(d, (W / 2, 990), "Ilustración", F("Regular", 28), GR, appear(t, 1.4) * e)
    return img

def s4(t, dur):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img); e = env(t, dur)
    band(d, e)
    text(d, (W / 2, 160), "Descarga los datos", F("ExtraBold", 84), MG, appear(t, 0.2) * e)
    a = appear(t, 1.0) * e
    cx, cy = 560, 560
    if a > 0:  # icono de fichero CSV
        dy = (1 - a) * 50
        d.polygon([(cx - 170, cy - 230 + dy), (cx + 90, cy - 230 + dy), (cx + 170, cy - 150 + dy), (cx + 170, cy + 230 + dy), (cx - 170, cy + 230 + dy)], fill=mix(CREAM, a), outline=mix(MG, a))
        d.polygon([(cx + 90, cy - 230 + dy), (cx + 90, cy - 150 + dy), (cx + 170, cy - 150 + dy)], fill=mix(MG, a))
        for r in range(5):
            d.line([(cx - 120, cy - 90 + r * 60 + dy), (cx + 120, cy - 90 + r * 60 + dy)], fill=mix((210, 200, 200), a), width=6)
        d.rounded_rectangle([cx - 130, cy + 130 + dy, cx + 130, cy + 205 + dy], radius=14, fill=mix(OR, a))
        text(d, (cx, cy + 168 + dy), "CSV", F("ExtraBold", 54), (255, 255, 255), a)
    items = ["Cada gráfico, con su fuente y su unidad", "Listo para Excel, R, Python o Stata", "Código para repetir la descarga"]
    for i, s in enumerate(items):
        a2 = appear(t, 2.2 + i * 1.2) * e
        if a2 <= 0: continue
        y = 420 + i * 140; x = 840 + (1 - a2) * 40
        d.ellipse([x - 20, y - 20, x + 20, y + 20], fill=mix(MG if i % 2 == 0 else OR, a2))
        text(d, (x + 50, y), s, F("SemiBold", 48), DK, a2, anchor="lm")
    return img

def s5(t, dur):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img); e = env(t, dur)
    band(d, e)
    text(d, (W / 2, 150), "Una herramienta para la Facultad", F("ExtraBold", 80), MG, appear(t, 0.2) * e)
    cols = [("Docencia", MG, ["Datos reales para las clases", "Prácticas de Econometría", "TFG y TFM"]),
            ("Investigación", OR, ["Datos descargables y citables", "Artículos, tesis y proyectos", "Investigación reproducible"])]
    for k, (tit, col, its) in enumerate(cols):
        a = appear(t, 0.9 + k * 0.8) * e
        if a <= 0: continue
        x = 520 + k * 880
        d.rounded_rectangle([x - 390, 300, x + 390, 900], radius=30, fill=mix(CREAM, a), outline=mix(col, a), width=5)
        text(d, (x, 390), tit, F("ExtraBold", 66), col, a)
        for i, s in enumerate(its):
            a2 = appear(t, 2.2 + k * 0.8 + i * 0.7) * e
            text(d, (x, 530 + i * 110), s, F("SemiBold", 42), DK, a2)
    return img

def s6(t, dur):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img); e = env(t, dur)
    band(d, e)
    text(d, (W / 2, 170), "Y la UGR en los rankings", F("ExtraBold", 80), MG, appear(t, 0.2) * e)
    rows = [("Turismo", "Top 100 mundial", "Ranking de Shanghái 2025"),
            ("Management", "2.ª de España", "Ranking de Shanghái 2025")]
    for i, (a1, a2, a3) in enumerate(rows):
        a = appear(t, 0.9 + i * 0.9) * e
        if a <= 0: continue
        y = 430 + i * 250
        d.rounded_rectangle([260, y - 95, W - 260, y + 95], radius=24, fill=mix(CREAM, a))
        d.rectangle([260, y - 95, 280, y + 95], fill=mix(OR if i else MG, a))
        text(d, (330, y - 25), a1, F("ExtraBold", 60), DK, a, anchor="lm")
        text(d, (330, y + 45), a3, F("Medium", 34), GR, a, anchor="lm")
        text(d, (W - 320, y), a2, F("ExtraBold", 64), OR if i else MG, a, anchor="rm")
    text(d, (W / 2, 960), "Fuente: Unidad de Analítica de la UGR", F("Regular", 30), GR, appear(t, 2.5) * e)
    return img

def s7(t, dur):
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

SCENES = [(s0, 6), (s1, 8), (s2, 12), (s3, 8), (s4, 8), (s5, 8), (s6, 5), (s7, 5)]

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
    outdir = "/home/claude/cceescopio_video"; os.makedirs(outdir, exist_ok=True)
    if sys.argv[1] == "still":
        i, t = int(sys.argv[2]), float(sys.argv[3]); fn, dur = SCENES[i]; fn(t, dur).save(f"{outdir}/still_{i}.png")
    else:
        for i in map(int, sys.argv[2:]): render(i, outdir)
