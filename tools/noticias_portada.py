"""Selecciona las noticias económicas y empresariales más destacadas del día (últimas 24 horas) en tres bloques
—España, Europa y el mundo— para la portada de CCEEscopio.

Lo ejecuta cada mañana la acción de GitHub .github/workflows/portada.yml, que publica portada.json en la rama «portada».
También se puede ejecutar a mano:  python tools/noticias_portada.py --salida portada.json
Solo usa la biblioteca estándar de Python.

Cómo se decide qué noticias son las más destacadas:
  1. Se reúnen los titulares de las portadas de Economía de Google Noticias (ediciones de España e internacional en español)
     y de varias búsquedas por temas, solo de las últimas 24 horas.
  2. Se agrupan los titulares que cuentan la misma noticia (palabras en común).
  3. Cada grupo recibe una puntuación: número de medios distintos que la publican (lo más importante),
     si aparece en la portada de Economía de Google Noticias y lo reciente que es.
  4. Se clasifica cada noticia en España, Europa o el mundo según su contenido y se eligen las cinco mejores de cada bloque.
"""
import json, re, sys, time, math, urllib.parse, urllib.request, unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from noticias import TEMAS, indicadores, leer_rss, sin_tildes  # mismas reglas que la página «Noticias e indicadores»

UA = {"User-Agent": "Mozilla/5.0 (CCEEscopio; Universidad de Granada)"}
ES = {"hl": "es", "gl": "ES", "ceid": "ES:es"}
INT = {"hl": "es-419", "gl": "US", "ceid": "US:es-419"}

# (nombre, url o búsqueda, edición, bloque sugerido, ¿es portada?)
FUENTES = [
    ("portada-es", "topic:BUSINESS", ES, None, True),
    ("portada-int", "topic:BUSINESS", INT, "mundo", True),
    ("es-economia", "economía España", ES, "espana", False),
    ("es-empresas", "empresas OR Ibex OR beneficios OR resultados OR fusión OR OPA", ES, "espana", False),
    ("es-empleo", "paro OR empleo OR afiliación OR salarios OR IPC OR vivienda", ES, "espana", False),
    ("es-andalucia", "economía Andalucía OR Granada empresas", ES, "espana", False),
    ("eu-economia", "economía europea OR eurozona OR \"Unión Europea\" OR Bruselas OR \"Comisión Europea\"", ES, "europa", False),
    ("eu-bce", "BCE OR Lagarde OR \"Banco Central Europeo\" OR Eurostat OR \"Bolsas europeas\"", ES, "europa", False),
    ("mundo-economia", "economía mundial OR \"Wall Street\" OR \"Reserva Federal\" OR China OR aranceles OR FMI", ES, "mundo", False),
    ("mundo-empresas", "multinacionales OR Apple OR Microsoft OR Nvidia OR Amazon OR Tesla OR petróleo OR OPEP", INT, "mundo", False),
]

# Palabras que sitúan una noticia en Europa o en el mundo (si no, se considera de España)
EUROPA = (r"\b(bce|lagarde|eurozona|zona euro|union europea|ue|bruselas|comision europea|eurostat|eurogrupo|parlamento europeo|"
          r"alemania|aleman\w*|francia|frances\w*|italia|italian\w*|portugal|portugues\w*|paises bajos|belgica|austria|irlanda|grecia|"
          r"polonia|suecia|dinamarca|finlandia|reino unido|britanic\w*|londres|paris|berlin|roma|merz|macron|meloni|von der leyen|"
          r"dax|cac 40|euro stoxx|stoxx|europe\w*)\b")
MUNDO = (r"\b(ee\.? ?uu\.?|estados unidos|eeuu|estadounidense\w*|trump|casa blanca|reserva federal|fed|powell|wall street|nasdaq|"
         r"dow jones|s&p|china|chin[ao]s?|pekin|japon\w*|india|rusia|ucrania|brasil\w*|mexic\w*|argentin\w*|chile|colombia|canada|"
         r"oriente medio|israel|iran|opep|fmi|banco mundial|ocde|g7|g20|nvidia|apple|microsoft|amazon|tesla|google|openai|"
         r"petroleo|brent|bitcoin|criptomoneda\w*|aranceles?|mundial\w*|global\w*)\b")
ESPANA = (r"\b(espana|espanol\w*|ibex|ibex 35|moncloa|sanchez|hacienda|banco de espana|airef|ine|epa|seguridad social|"
          r"andaluc\w*|madrid|cataluna|barcelona|valencia\w*|sevilla|malaga|granada|bilbao|cnmv|cnmc|inditex|iberdrola|santander|"
          r"bbva|caixabank|telefonica|repsol|sabadell|mercadona|el corte ingles|ferrovial|acs|naturgy|endesa|aena|iag|indra)\b")

# Titulares sobre los mercados: se enlazan con la página «Bolsa al día»
BOLSA = r"\b(bolsas?|ibex|wall street|nasdaq|dow jones|s&p|dax|cac|stoxx|nikkei|cotiza\w*|acciones|parque|brent|oro|bitcoin)\b"

VACIAS = set("""a al algo ante bajo con contra de del desde durante e el ella en entre era es esa ese eso esta este esto ha han hasta
hay la las le les lo los mas me mi muy ni no o os para pero por que se sea ser si sin sobre su sus te tras tu un una uno unos unas
y ya ano anos hoy ayer como cuando donde segun tiene tienen sera han ha dice cree""".split())


def url_rss(q, ed):
    if q.startswith("topic:"):
        return "https://news.google.com/rss/headlines/section/topic/" + q[6:] + "?" + urllib.parse.urlencode(ed)
    return "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": f"{q} when:1d", **ed})


def descargar(url):
    for intento in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return list(leer_rss(r.read()))
        except Exception as e:
            err = e
            time.sleep(2 + 3 * intento)
    raise err


def palabras(t):
    """Palabras con contenido (recortadas a 5 letras para unir «sube» y «subida») y cifras del titular."""
    t = sin_tildes(t)
    pal = {w[:5] for w in re.findall(r"[a-z]{3,}", t) if w not in VACIAS}
    return pal | set(re.findall(r"\d+(?:[.,]\d+)*", t))


def bloque(texto, sugerido):
    t = sin_tildes(texto)
    eu, mu, es = re.search(EUROPA, t), re.search(MUNDO, t), re.search(ESPANA, t)
    if es and not (eu or mu):
        return "espana"
    if eu and not mu:
        return "europa" if not es or sugerido == "europa" else (sugerido or "espana")
    if mu and not eu:
        return "mundo" if not es or sugerido == "mundo" else (sugerido or "espana")
    if eu and mu:
        return sugerido if sugerido in ("europa", "mundo") else "mundo"
    return sugerido or "espana"


def main(salida, horas=24, por_bloque=5, fuentes=FUENTES, descargar=descargar, ahora=None):
    ahora = ahora or time.time()
    ind = indicadores()
    items = []
    for nombre, q, ed, sug, portada in fuentes:
        try:
            lst = descargar(url_rss(q, ed))
        except Exception as e:
            print(f"  aviso: {nombre}: {e}", file=sys.stderr)
            continue
        for k, it in enumerate(lst):
            if not it["t"] or not it["ts"] or it["ts"] < ahora - horas * 3600 or it["ts"] > ahora + 3600:
                continue
            items.append({**it, "sug": sug, "portada": portada, "pos": k, "pal": palabras(it["t"])})
        time.sleep(1)
    # agrupar los titulares que cuentan la misma noticia
    grupos = []
    for it in sorted(items, key=lambda x: (not x["portada"], x["pos"])):
        mejor, sim = None, 0
        for g in grupos:
            inter = len(it["pal"] & g["pal"])
            j = inter / max(1, min(len(it["pal"]), len(g["pal"])))
            if inter >= 3 and j > sim and j >= 0.45:
                mejor, sim = g, j
        if mejor:
            mejor["items"].append(it); mejor["pal"] |= it["pal"]
        else:
            grupos.append({"items": [it], "pal": set(it["pal"])})
    out = {"espana": [], "europa": [], "mundo": []}
    for g in grupos:
        medios = {i["fuente"] for i in g["items"] if i["fuente"]}
        en_portada = [i for i in g["items"] if i["portada"]]
        rep = min(en_portada or g["items"], key=lambda i: (i["pos"], -(i["ts"] or 0)))  # titular representativo
        edad = (ahora - max(i["ts"] for i in g["items"])) / 3600
        puntos = 3 * math.log2(1 + len(medios)) + (4 if en_portada else 0) + (2 - min(rep["pos"], 20) / 10 if en_portada else 0) + max(0, 2 - edad / 6)
        sugs = [i["sug"] for i in g["items"] if i["sug"]]
        sug = max(set(sugs), key=sugs.count) if sugs else None
        b = bloque(" ".join(i["t"] for i in g["items"][:4]), sug)
        # indicadores de CCEEscopio relacionados con el titular (mismas reglas que «Noticias e indicadores»)
        rel = []
        for _, _, rx, ids in TEMAS:
            if re.search(rx, rep["t"], re.I):
                rel += [x for x in ids[:1] if x in ind and x not in rel]
        out[b].append({"t": rep["t"], "fuente": rep["fuente"], "url": rep["url"], "ts": int(rep["ts"]),
                       "medios": len(medios), "puntos": round(puntos, 2), "ind": rel[:2],
                       "bolsa": bool(re.search(BOLSA, sin_tildes(rep["t"])))})
    for b in out:
        out[b] = sorted(out[b], key=lambda x: -x["puntos"])[:por_bloque]
    usados = {i for b in out.values() for n in b for i in n["ind"]}
    res = {"actualizado": int(ahora), "horas": horas,
           "bloques": [{"id": "espana", "titulo": "España", "noticias": out["espana"]},
                       {"id": "europa", "titulo": "Europa", "noticias": out["europa"]},
                       {"id": "mundo", "titulo": "Mundo", "noticias": out["mundo"]}],
           "indicadores": {k: {"nombre": v["nombre"], "pagina": v["pagina"]} for k, v in ind.items() if k in usados}}
    json.dump(res, open(salida, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"{len(items)} titulares, {len(grupos)} noticias distintas; en portada: " + ", ".join(f"{b} {len(v)}" for b, v in out.items()))
    if sum(len(v) for v in out.values()) == 0:
        sys.exit("No se ha encontrado ninguna noticia del día.")
    return res


if __name__ == "__main__":
    arg = lambda k, d=None: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
    main(arg("--salida", "portada.json"))
