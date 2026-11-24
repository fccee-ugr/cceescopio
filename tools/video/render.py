"""Graba el vídeo de presentación de CCEEscopio a partir de tools/video/video.html (Chrome sin interfaz + ffmpeg).

  python tools/video/render.py datos              -> actualiza datos.js con las cotizaciones de la rama «bolsa» (bolsa.json en la carpeta actual)
  python tools/video/render.py fotos 3 12.5 40    -> guarda fotogramas sueltos (segundos) en la carpeta de salida, para revisarlos
  python tools/video/render.py tramo 0 10 a.mp4   -> graba el tramo [0, 10) segundos
  python tools/video/render.py todo [procesos]    -> graba todos los tramos en paralelo, los une y añade la música (tools/video/musica.m4a si existe)

Requisitos: pip install playwright (y un Chrome o Chromium), ffmpeg, y las fuentes Inter, Lora y Noto Color Emoji.
"""
import os, subprocess, sys, json
AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.dirname(os.path.dirname(AQUI))
SAL = os.environ.get("VIDEO_DIR", os.path.join(RAIZ, "_video")); FPS = 30
CHROME = os.environ.get("CHROME", "/usr/bin/google-chrome")
ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-r", str(FPS), "-g", "60", "-movflags", "+faststart"]

def pagina(p):
    b = p.chromium.launch(executable_path=CHROME if os.path.exists(CHROME) else None, args=["--no-sandbox", "--force-device-scale-factor=1", "--font-render-hinting=none"])
    pg = b.new_page(viewport={"width": 1920, "height": 1080})
    pg.on("pageerror", lambda e: print("ERROR de la página:", e, file=sys.stderr))
    pg.goto("file://" + os.path.join(AQUI, "video.html")); pg.wait_for_function("window.LISTO === true")
    return b, pg

def fotos(tiempos):
    from playwright.sync_api import sync_playwright
    os.makedirs(SAL, exist_ok=True)
    with sync_playwright() as p:
        b, pg = pagina(p)
        for t in tiempos:
            pg.evaluate(f"render({t})"); pg.screenshot(path=os.path.join(SAL, f"foto_{t:06.2f}.jpg"), type="jpeg", quality=90)
        print("duración:", pg.evaluate("DUR")); b.close()

def tramo(t0, t1, salida):
    from playwright.sync_api import sync_playwright
    tmp = salida[:-4] + ".tmp.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-", *ENC, tmp], stdin=subprocess.PIPE)
    with sync_playwright() as p:
        b, pg = pagina(p)
        for k in range(round(t0 * FPS), round(t1 * FPS)):
            pg.evaluate(f"render({k / FPS})"); ff.stdin.write(pg.screenshot(type="jpeg", quality=92))
        b.close()
    ff.stdin.close()
    if ff.wait() == 0: os.replace(tmp, salida)
    else: sys.exit("ffmpeg ha fallado en " + salida)

def duracion():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b, pg = pagina(p); d = pg.evaluate("DUR"); b.close(); return d

def todo(procesos=2, paso=6.0):
    os.makedirs(SAL, exist_ok=True); d = duracion(); cortes = []; t = 0.0
    while t < d - 1e-6: cortes.append((t, min(d, t + paso))); t += paso
    pend = list(enumerate(cortes)); vivos = []
    while pend or vivos:
        while pend and len(vivos) < procesos:
            i, (a, b) = pend.pop(0); out = os.path.join(SAL, f"tramo{i:02d}.mp4")
            if os.path.exists(out): continue
            vivos.append(subprocess.Popen([sys.executable, __file__, "tramo", str(a), str(b), out]))
        for v in vivos[:]:
            if v.poll() is not None:
                vivos.remove(v)
                if v.returncode: sys.exit("Ha fallado un tramo")
        if vivos: vivos[0].wait()
    lista = os.path.join(SAL, "lista.txt"); open(lista, "w").write("".join(f"file 'tramo{i:02d}.mp4'\n" for i in range(len(cortes))))
    mudo = os.path.join(SAL, "mudo.mp4"); subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lista, "-c", "copy", mudo])
    final = os.path.join(SAL, "cceescopio_video.mp4"); musica = os.path.join(AQUI, "musica.m4a")
    if os.path.exists(musica):
        subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", mudo, "-i", musica, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                               "-af", f"afade=t=in:d=0.4,afade=t=out:st={d - 2.5}:d=2.5", "-c:a", "aac", "-b:a", "192k", "-t", str(d), "-movflags", "+faststart", final])
    else: os.replace(mudo, final)
    print("Vídeo:", final, f"({d:.1f} s)")

def datos(origen="bolsa.json"):
    import datetime
    b = json.load(open(origen, encoding="utf-8")); S = {s["id"]: s for s in b["series"]}; ib = S["ibex35"]["semanal"]
    MES = "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split(); f = datetime.date.fromisoformat(S["ibex35"]["fecha"])
    res = [{"id": s["id"], "n": s["nombre"].split(" (")[0], "v": s["valor"], "d1": s["d1"], "a1": s["a1"], "sp": s["diario"]["c"][-40:]} for s in b["series"]]
    out = {"ibex": {"d": ib["d"], "c": ib["c"]}, "res": res, "fecha": f"{f.day} de {MES[f.month - 1]} de {f.year}"}
    open(os.path.join(AQUI, "datos.js"), "w", encoding="utf-8").write("// Cotizaciones reales (rama «bolsa» del repositorio) para el vídeo. Se regenera con: python tools/video/render.py datos\nconst DATA=" + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n")

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    if a[0] == "fotos": fotos([float(x) for x in a[1:]])
    elif a[0] == "tramo": tramo(float(a[1]), float(a[2]), a[3])
    elif a[0] == "todo": todo(int(a[1]) if len(a) > 1 else 2)
    elif a[0] == "datos": datos(*a[1:2])
