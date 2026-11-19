"""Recoge noticias económicas recientes (Google Noticias, España) y las relaciona con los indicadores de CCEEscopio.
Lo ejecuta cada día la acción de GitHub .github/workflows/noticias.yml, que publica el resultado en la rama «noticias».
También se puede ejecutar a mano:  python tools/noticias.py --salida noticias.json
Solo usa la biblioteca estándar de Python."""
import json, re, sys, time, urllib.parse, urllib.request, email.utils, unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SPECS = json.load(open(RAIZ / "data/indicadores_specs.json", encoding="utf-8"))

# tema: búsqueda en Google Noticias, palabras clave para relacionar titulares e indicadores asociados
TEMAS = [
    ("inflacion", "IPC inflación España", r"\bipc\b|inflaci|precios? de consumo|subida de precios|carest", ["ipca-inflacion-general-tasa-anual", "ipca-inflacion-subyacente-sin-energia-ni-alimentos"]),
    ("alimentos", "precio alimentos España", r"precio de (los )?alimentos|cesta de la compra|aceite de oliva|precio del huevo|supermercad", ["ipca-alimentos-y-bebidas-no-alcoholicas-tasa-anual"]),
    ("energia", "precio luz gas España", r"precio de la luz|factura de la luz|electricidad|tarifa el[eé]ctrica|precio del gas|carburantes|gasolina", ["precio-de-la-electricidad-para-hogares", "precio-del-gas-natural-para-hogares", "ipca-energia-tasa-anual"]),
    ("paro", "paro desempleo España EPA", r"\bparo\b|desemple|\bepa\b|afiliaci|seguridad social|ocupados|mercado laboral", ["tasa-de-paro", "tasa-de-empleo-20-64-anos", "tasa-de-paro-por-regiones"]),
    ("paro-juvenil", "paro juvenil jóvenes empleo", r"paro juvenil|j[oó]venes.*(paro|empleo|trabajo)|ninis?\b", ["tasa-de-paro-juvenil-menores-de-25-anos", "jovenes-que-ni-estudian-ni-trabajan-15-29-anos"]),
    ("salarios", "salario mínimo sueldos España", r"salario m[ií]nimo|\bsmi\b|salarios|sueldos|brecha salarial", ["salario-minimo-mensual", "coste-laboral-por-hora", "brecha-salarial-de-genero"]),
    ("pib", "PIB economía española crecimiento", r"\bpib\b|crecimiento econ[oó]mico|econom[ií]a espa[nñ]ola crece|recesi[oó]n|banco de espa[nñ]a.*previsi|airef", ["pib-crecimiento-interanual-trimestral", "pib-per-capita-en-paridad-de-poder-de-compra"]),
    ("consumo", "consumo hogares ventas comercio", r"consumo de los hogares|ventas del comercio|comercio minorista|rebajas|black friday|gasto de las familias", ["consumo-de-los-hogares-crecimiento-interanual", "indice-de-comercio-minorista", "confianza-del-consumidor"]),
    ("industria", "producción industrial España", r"producci[oó]n industrial|industria|f[aá]bricas?\b|automoci[oó]n", ["indice-de-produccion-industrial", "confianza-de-la-industria"]),
    ("vivienda", "precio vivienda alquiler España", r"vivienda|alquiler|hipotec|inmobiliari|pisos?\b", ["precio-de-la-vivienda-tasa-anual", "sobrecarga-del-coste-de-la-vivienda", "produccion-en-la-construccion"]),
    ("euribor", "euríbor hipotecas BCE tipos", r"eur[ií]bor|\bbce\b|tipos de inter[eé]s|lagarde", ["euribor-a-3-meses"]),
    ("deuda", "deuda pública déficit España", r"deuda p[uú]blica|d[eé]ficit|prima de riesgo|bono a 10 a[nñ]os|presupuestos", ["deuda-publica-del-pib", "deficit-o-superavit-publico-del-pib", "rentabilidad-del-bono-a-10-anos"]),
    ("impuestos", "recaudación impuestos Hacienda", r"recaudaci[oó]n|hacienda|impuesto|irpf|\biva\b|fiscal", ["ingresos-fiscales-del-pib", "gasto-publico-total-del-pib"]),
    ("turismo", "turismo España turistas récord", r"turis|pernoctaci|hotel|viajeros|vacaciones", ["pernoctaciones-en-hoteles", "pernoctaciones-de-no-residentes-en-hoteles", "tasa-de-ocupacion-de-las-plazas-hoteleras"]),
    ("andalucia", "economía Andalucía", r"andaluc|granada|sevilla|m[aá]laga|c[oó]rdoba|almer[ií]a|ja[eé]n|huelva|c[aá]diz", ["tasa-de-paro-por-regiones", "pernoctaciones-por-regiones", "riesgo-de-pobreza-o-exclusion-social-por-regiones"]),
    ("pobreza", "pobreza desigualdad España informe", r"pobreza|desigualdad|exclusi[oó]n social|arope|gini|renta de los hogares", ["riesgo-de-pobreza-o-exclusion-social-arope", "indice-de-gini", "tasa-de-riesgo-de-pobreza-60-de-la-mediana"]),
    ("exterior", "exportaciones España comercio exterior aranceles", r"exportaci|importaci|aranceles?|comercio exterior|d[eé]ficit comercial", ["exportaciones-crecimiento-interanual-trimestral", "exportaciones-de-bienes-y-servicios-del-pib", "saldo-por-cuenta-corriente-del-pib"]),
    ("empresas", "empresas concurso acreedores creación empresas", r"concurso de acreedores|quiebra|creaci[oó]n de empresas|nuevas empresas|emprend|aut[oó]nomos", ["registros-de-nuevas-empresas-indice", "declaraciones-de-quiebra-de-empresas-indice"]),
    ("digital", "inteligencia artificial empresas comercio electrónico", r"inteligencia artificial|\bia\b|comercio electr[oó]nico|compras? (por|en) internet|digitaliz", ["empresas-que-usan-inteligencia-artificial", "personas-que-compran-por-internet"]),
    ("i+d", "inversión I+D innovación España", r"\bi\+d\b|innovaci[oó]n|investigaci[oó]n cient", ["gasto-en-i-d-del-pib"]),
    ("renovables", "energías renovables emisiones España", r"renovable|solar|e[oó]lic|emisiones|clim[aá]tic|co2", ["cuota-de-energias-renovables", "emisiones-netas-de-gases-de-efecto-invernadero"]),
    ("poblacion", "población natalidad envejecimiento España", r"natalidad|nacimientos|fecundidad|envejec|pensiones|poblaci[oó]n|demogr", ["tasa-de-fecundidad", "tasa-de-dependencia-de-las-personas-mayores", "poblacion"]),
    ("dolar", "euro dólar tipo de cambio", r"d[oó]lar|tipo de cambio|divisa", ["tipo-de-cambio-euro-dolar"]),
]

def indicadores():
    out = {}
    for pag, lst in SPECS.items():
        if pag == "andalucia":
            continue
        for i in lst:
            out.setdefault(i["id"], {"nombre": i["nombre"], "pagina": pag, "regional": bool(i.get("regional")), "sinGeo": bool(i.get("sinGeo"))})
    return out

def sin_tildes(s):
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower()

def leer_rss(xml_bytes):
    raiz = ET.fromstring(xml_bytes)
    for it in raiz.iter("item"):
        titulo = (it.findtext("title") or "").strip()
        fuente = (it.findtext("source") or "").strip()
        if fuente and titulo.endswith(" - " + fuente):
            titulo = titulo[: -len(fuente) - 3].strip()
        fecha = it.findtext("pubDate")
        try:
            ts = email.utils.parsedate_to_datetime(fecha).timestamp() if fecha else None
        except Exception:
            ts = None
        yield {"t": titulo, "fuente": fuente, "url": (it.findtext("link") or "").strip(), "ts": ts}

def buscar(q, dias=14):
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": f"{q} when:{dias}d", "hl": "es", "gl": "ES", "ceid": "ES:es"})
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (CCEEscopio; Universidad de Granada)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return list(leer_rss(r.read()))

def main(salida, por_tema=10, previas=None, dias_guardar=30):
    ind = indicadores()
    noticias, vistos = [], set()
    nuevas = 0
    for tema, q, regex, ids in TEMAS:
        try:
            items = buscar(q)
        except Exception as e:
            print(f"  aviso: {tema}: {e}", file=sys.stderr)
            continue
        n = 0
        for it in sorted(items, key=lambda x: -(x["ts"] or 0)):
            clave = sin_tildes(re.sub(r"\W+", " ", it["t"]))[:90]
            if not it["t"] or clave in vistos:
                continue
            # indicadores: los de los temas cuyas palabras clave aparecen en el titular (si no hay ninguno, los del tema de búsqueda)
            rel = []
            encontrados = sorted((m.start(), ids2) for _, _, rx, ids2 in TEMAS for m in [re.search(rx, it["t"], re.I)] if m)
            for _, ids2 in encontrados:
                rel += [x for x in ids2[:2] if x not in rel]
            rel = [x for x in (rel or ids) if x in ind][:3]
            if not rel:
                continue
            vistos.add(clave)
            noticias.append({**it, "tema": tema, "ind": rel})
            n += 1; nuevas += 1
            if n >= por_tema:
                break
        time.sleep(1)
    # se conservan las noticias de días anteriores (hasta 30 días), por si algún día falla la búsqueda
    if previas:
        try:
            ant = json.load(open(previas, encoding="utf-8")).get("noticias", [])
        except Exception:
            ant = []
        limite = time.time() - dias_guardar * 86400
        for it in ant:
            clave = sin_tildes(re.sub(r"\W+", " ", it.get("t", "")))[:90]
            if clave and clave not in vistos and (it.get("ts") or 0) >= limite and all(i in ind for i in it.get("ind", [])):
                vistos.add(clave); noticias.append(it)
    noticias.sort(key=lambda x: -(x["ts"] or 0))
    noticias = noticias[:400]
    usados = {i for n in noticias for i in n["ind"]}
    json.dump({"actualizado": int(time.time()), "noticias": noticias, "indicadores": {k: v for k, v in ind.items() if k in usados}},
              open(salida, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"{nuevas} noticias nuevas; {len(noticias)} en total guardadas en {salida}")
    if not noticias:
        sys.exit("No se ha encontrado ninguna noticia.")

if __name__ == "__main__":
    arg = lambda k, d=None: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
    main(arg("--salida", str(RAIZ / "noticias.json")), previas=arg("--previas"))
