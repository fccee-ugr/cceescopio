"""Precios semanales de los carburantes (Boletín Petrolero de la Comisión Europea, Weekly Oil Bulletin).

Descarga el libro histórico (desde 2005) y genera un JSON compacto con los precios de venta al público
de la gasolina Euro-super 95 y del gasóleo de automoción, con y sin impuestos, en euros por litro.

Uso:  python tools/carburantes.py --salida carburantes.json
      python tools/carburantes.py --xlsx fichero_descargado.xlsx --salida carburantes.json

Lo ejecuta la acción de GitHub .github/workflows/carburantes.yml una vez por semana y publica
el resultado en la rama «carburantes» (la página precios-productos.qmd lo lee de ahí).
"""
import argparse, datetime as dt, io, json, re, sys, urllib.request

PAGINA = "https://energy.ec.europa.eu/data-and-analysis/weekly-oil-bulletin_en"
HISTORICO = ("https://energy.ec.europa.eu/document/download/906e60ca-8b6a-44e7-8589-652854d2fd3f_en"
             "?filename=Weekly_Oil_Bulletin_Prices_History_maticni_4web.xlsx")
PRODUCTOS = {"euro95": "g95", "euro_super_95": "g95", "eurosuper95": "g95", "diesel": "die", "automotive_gas_oil": "die"}
# Cabeceras del tipo «ES_price_with_tax_euro95» o «EU_price_wo_tax_diesel»
CAB = re.compile(r"^([A-Za-z0-9]+?)_price_(with|wo|without)_tax(?:es)?_([a-z0-9_]+)$", re.I)
CODIGOS = {"GR": "EL", "UK": "GB", "EU": "EU27_2020", "EUR": "EU27_2020", "EU27": "EU27_2020", "EUR27": "EU27_2020",
           "EU27_2020": "EU27_2020", "EA": "EA", "EUROAREA": "EA"}


def descargar(url, intentos=3):
    ultimo = None
    for _ in range(intentos):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (CCEEscopio, Universidad de Granada)"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            ultimo = e
    raise RuntimeError(f"No se ha podido descargar {url}: {ultimo}")


def enlace_historico():
    """Busca en la página del boletín el enlace vigente al libro histórico (por si la Comisión lo cambia)."""
    try:
        html = descargar(PAGINA).decode("utf-8", "ignore")
        m = re.findall(r'href="([^"]*?Prices_History[^"]*?\.xlsx[^"]*)"', html, re.I)
        if m:
            u = m[0].replace("&amp;", "&")
            return u if u.startswith("http") else "https://energy.ec.europa.eu" + u
    except Exception:  # noqa: BLE001
        pass
    return HISTORICO


def a_fecha(v):
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    if isinstance(v, (int, float)) and 30000 < v < 80000:  # número de serie de Excel
        return dt.date(1899, 12, 30) + dt.timedelta(days=int(v))
    if isinstance(v, str):
        s = v.strip()
        for f in ("%Y-%m-%d", "%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y"):
            try:
                return dt.datetime.strptime(s[:19] if "%H" in f else s[:10], f).date()
            except ValueError:
                pass
    return None


def a_numero(v):
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip().replace(" ", "").replace(" ", "")
        if not s:
            return None
        if "," in s and "." in s:
            s = s.replace(",", "")
        else:
            s = s.replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return None
    return None


def cabeceras_alternativas(filas, impuestos=None):
    """Otro formato posible: una fila con los códigos de país (celdas combinadas) y otra con los productos."""
    for i, fila in enumerate(filas[:10]):
        cods = [(j, c.strip().upper()) for j, c in enumerate(fila) if isinstance(c, str) and re.fullmatch(r"[A-Za-z]{2}|EU(R)?(27)?(_2020)?", c.strip())]
        if len(cods) < 5:
            continue
        for k in (i + 1, i + 2, i - 1):
            if not 0 <= k < len(filas):
                continue
            prods = {j: c for j, c in enumerate(filas[k]) if isinstance(c, str)}
            if not any(re.search(r"euro.?super|diesel|gas ?oil", c, re.I) for c in prods.values()):
                continue
            col, pais = {}, None
            inicio = {j: c for j, c in cods}
            for j in range(len(filas[k])):
                pais = inicio.get(j, pais)
                c = prods.get(j, "")
                prod = "g95" if re.search(r"euro.?super ?95", c, re.I) else ("die" if re.search(r"diesel|automotive gas ?oil", c, re.I) else None)
                if pais and prod:
                    col[j] = (CODIGOS.get(pais, pais), prod)
            if col:
                return col, max(i, k)
    return {}, None


def leer_hoja(ws, impuestos):
    filas = list(ws.iter_rows(values_only=True))
    # 1) Columnas: se buscan las cabeceras con nombre de máquina en las primeras filas
    columnas, fila_cab = {}, None
    for i, fila in enumerate(filas[:10]):
        for j, c in enumerate(fila):
            if not isinstance(c, str):
                continue
            m = CAB.match(c.strip())
            if not m:
                continue
            prod = PRODUCTOS.get(m.group(3).lower())
            if not prod:
                continue
            pais = CODIGOS.get(m.group(1).upper(), m.group(1).upper())
            columnas[j] = (pais, prod)
            fila_cab = i
    if not columnas:
        columnas, fila_cab = cabeceras_alternativas(filas)
    if not columnas:
        return {}
    # 2) Columna de fechas: la que tiene más celdas con fecha por debajo de las cabeceras
    datos = filas[fila_cab + 1:]
    ncol = max(len(f) for f in datos) if datos else 0
    cuenta = [sum(1 for f in datos[:200] if j < len(f) and a_fecha(f[j])) for j in range(min(ncol, 6))]
    if not cuenta or max(cuenta) == 0:
        return {}
    jf = cuenta.index(max(cuenta))
    # 3) Valores (euros por 1.000 litros en el boletín; se pasan a euros por litro)
    out = {}
    for f in datos:
        if jf >= len(f):
            continue
        d = a_fecha(f[jf])
        if not d or d.year < 2004:
            continue
        for j, (pais, serie) in columnas.items():
            v = a_numero(f[j]) if j < len(f) else None
            if v is None or v <= 0:
                continue
            if v > 20:
                v /= 1000
            if not 0.2 < v < 6:
                continue
            out.setdefault(d.isoformat(), {}).setdefault(pais, {})[f"{serie}_{impuestos}"] = round(v, 3)
    return out


def procesar(contenido):
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(contenido), read_only=True, data_only=True)
    total = {}
    for ws in wb.worksheets:
        nombre = ws.title.lower()
        if "tax" not in nombre or not nombre.startswith("price"):
            continue
        imp = "sin" if re.search(r"\bwo\b|without|w/o|excl", nombre) else "con"
        for d, paises in leer_hoja(ws, imp).items():
            for p, s in paises.items():
                total.setdefault(d, {}).setdefault(p, {}).update(s)
    if not total:
        raise RuntimeError("No se han encontrado precios en el libro (¿ha cambiado el formato del boletín?)")
    fechas = sorted(total)
    paises = sorted({p for d in total.values() for p in d})
    series = {}
    for p in paises:
        s = {}
        for k in ("g95_con", "g95_sin", "die_con", "die_sin"):
            v = [total[d].get(p, {}).get(k) for d in fechas]
            if sum(x is not None for x in v) >= 10:
                s[k] = v
        if s:
            series[p] = s
    if "ES" not in series or "g95_con" not in series["ES"]:
        raise RuntimeError("Faltan los precios de España en el boletín")
    return {"actualizado": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "fuente": "Comisión Europea, Weekly Oil Bulletin (precios de venta al público, euros por litro)",
            "unidad": "€/litro", "fechas": fechas, "series": series}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", default="carburantes.json")
    ap.add_argument("--xlsx", help="usar un libro ya descargado en lugar de descargarlo")
    a = ap.parse_args()
    contenido = open(a.xlsx, "rb").read() if a.xlsx else descargar(enlace_historico())
    res = procesar(contenido)
    with open(a.salida, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, separators=(",", ":"))
    es = res["series"]["ES"]["g95_con"]
    ult = next(x for x in reversed(es) if x is not None)
    print(f"{len(res['fechas'])} semanas ({res['fechas'][0]} a {res['fechas'][-1]}), {len(res['series'])} territorios. "
          f"Gasolina 95 en España, último dato: {ult} €/l")


if __name__ == "__main__":
    sys.exit(main())
