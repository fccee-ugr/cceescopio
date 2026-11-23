"""Descarga las cotizaciones de los principales índices bursátiles, materias primas y empresas del IBEX 35
para la página «Bolsa al día», la portada y el simulador de carteras de CCEEscopio.

Lo ejecuta la acción de GitHub .github/workflows/bolsa.yml, que publica el resultado en la rama «bolsa»
(bolsa.json, con las series completas, y bolsa-resumen.json, ligero, para la portada).
También se puede ejecutar a mano:  python tools/bolsa.py --salida /tmp
Solo usa la biblioteca estándar de Python.

Fuente: Yahoo Finance (API de gráficos). Si un valor no se puede descargar, se conservan los datos de la
ejecución anterior (--previas), de modo que la web nunca se queda sin datos.
"""
import json, math, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

# id, símbolo de Yahoo, nombre, grupo, zona horaria de la bolsa
VALORES = [
    ("ibex35", "^IBEX", "IBEX 35", "España", "Europe/Madrid"),
    ("eurostoxx50", "^STOXX50E", "Euro Stoxx 50", "Europa", "Europe/Berlin"),
    ("dax", "^GDAXI", "DAX 40 (Alemania)", "Europa", "Europe/Berlin"),
    ("cac40", "^FCHI", "CAC 40 (Francia)", "Europa", "Europe/Paris"),
    ("ftsemib", "FTSEMIB.MI", "FTSE MIB (Italia)", "Europa", "Europe/Rome"),
    ("ftse100", "^FTSE", "FTSE 100 (Reino Unido)", "Europa", "Europe/London"),
    ("sp500", "^GSPC", "S&P 500 (EE. UU.)", "América", "America/New_York"),
    ("nasdaq", "^IXIC", "Nasdaq Composite (EE. UU.)", "América", "America/New_York"),
    ("dowjones", "^DJI", "Dow Jones (EE. UU.)", "América", "America/New_York"),
    ("bovespa", "^BVSP", "Bovespa (Brasil)", "América", "America/Sao_Paulo"),
    ("nikkei", "^N225", "Nikkei 225 (Japón)", "Asia", "Asia/Tokyo"),
    ("hangseng", "^HSI", "Hang Seng (Hong Kong)", "Asia", "Asia/Hong_Kong"),
    ("shanghai", "000001.SS", "Shanghai Composite (China)", "Asia", "Asia/Shanghai"),
    ("vix", "^VIX", "VIX (volatilidad del S&P 500)", "Riesgo y materias primas", "America/New_York"),
    ("brent", "BZ=F", "Petróleo Brent (dólares por barril)", "Riesgo y materias primas", "America/New_York"),
    ("oro", "GC=F", "Oro (dólares por onza)", "Riesgo y materias primas", "America/New_York"),
    ("bitcoin", "BTC-EUR", "Bitcoin (euros)", "Riesgo y materias primas", "UTC"),
    ("inditex", "ITX.MC", "Inditex", "Empresas del IBEX 35", "Europe/Madrid"),
    ("iberdrola", "IBE.MC", "Iberdrola", "Empresas del IBEX 35", "Europe/Madrid"),
    ("santander", "SAN.MC", "Banco Santander", "Empresas del IBEX 35", "Europe/Madrid"),
    ("bbva", "BBVA.MC", "BBVA", "Empresas del IBEX 35", "Europe/Madrid"),
    ("caixabank", "CABK.MC", "CaixaBank", "Empresas del IBEX 35", "Europe/Madrid"),
    ("telefonica", "TEF.MC", "Telefónica", "Empresas del IBEX 35", "Europe/Madrid"),
    ("repsol", "REP.MC", "Repsol", "Empresas del IBEX 35", "Europe/Madrid"),
    ("aena", "AENA.MC", "Aena", "Empresas del IBEX 35", "Europe/Madrid"),
]

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36 (CCEEscopio; Universidad de Granada)"}


def descargar(sym, rango, intervalo):
    """Devuelve (fechas ISO, cierres, metadatos) de la API de gráficos de Yahoo Finance."""
    q = urllib.parse.urlencode({"range": rango, "interval": intervalo, "includePrePost": "false", "events": "div,splits"})
    error = None
    for host in ("query1", "query2"):
        url = f"https://{host}.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?{q}"
        for intento in range(2):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                    js = json.load(r)
                return leer_grafico(js)
            except Exception as e:
                error = e
                time.sleep(2 + 3 * intento)
    raise RuntimeError(f"{sym}: {error}")


def leer_grafico(js):
    res = js["chart"]["result"][0]
    meta = res.get("meta", {})
    off = meta.get("gmtoffset", 0) or 0
    ts = res.get("timestamp") or []
    cierres = res["indicators"]["quote"][0].get("close") or []
    fechas, valores, vistos = [], [], {}
    for t, c in zip(ts, cierres):
        if c is None or not math.isfinite(c):
            continue
        f = datetime.fromtimestamp(t + off, tz=timezone.utc).strftime("%Y-%m-%d")
        if f in vistos:  # un mismo día repetido (p. ej., la sesión en curso): se queda el último dato
            valores[vistos[f]] = c
            continue
        vistos[f] = len(fechas)
        fechas.append(f); valores.append(c)
    return fechas, valores, meta


def r2(x):
    """Redondeo con 5-6 cifras significativas (suficiente para gráficos y variaciones)."""
    if x is None:
        return None
    return round(x, 4 if abs(x) < 10 else 2 if abs(x) < 1000 else 1 if abs(x) < 1e5 else 0)


def dias(fechas):
    """Fechas ISO -> días desde el 1-1-1970 (enteros, para que el fichero ocupe menos)."""
    return [(datetime.strptime(f, "%Y-%m-%d") - datetime(1970, 1, 1)).days for f in fechas]


def variacion(valores, fechas, dias=None, desde_fecha=None):
    """Variación porcentual del último dato frente al último cierre anterior a una fecha."""
    if len(valores) < 2:
        return None
    ult = datetime.strptime(fechas[-1], "%Y-%m-%d")
    lim = desde_fecha or (ult - timedelta(days=dias)).strftime("%Y-%m-%d")
    base = None
    for f, v in zip(fechas, valores):
        if f <= lim:
            base = v
        else:
            break
    if base is None or base == 0:
        return None
    return round(100 * (valores[-1] / base - 1), 2)


def resumen(fechas, valores):
    ult = datetime.strptime(fechas[-1], "%Y-%m-%d")
    hace_un_ano = (ult - timedelta(days=365)).strftime("%Y-%m-%d")
    anual = [v for f, v in zip(fechas, valores) if f > hace_un_ano]
    rent = [math.log(b / a) for a, b in zip(anual, anual[1:]) if a > 0 and b > 0]
    vol = None
    if len(rent) > 20:
        m = sum(rent) / len(rent)
        vol = round(100 * math.sqrt(sum((x - m) ** 2 for x in rent) / (len(rent) - 1) * 252), 1)
    return {
        "fecha": fechas[-1], "valor": r2(valores[-1]), "anterior": r2(valores[-2]) if len(valores) > 1 else None,
        "d1": round(100 * (valores[-1] / valores[-2] - 1), 2) if len(valores) > 1 and valores[-2] else None,
        "s1": variacion(valores, fechas, 7), "m1": variacion(valores, fechas, 30),
        "ytd": variacion(valores, fechas, desde_fecha=f"{ult.year - 1}-12-31"),
        "a1": variacion(valores, fechas, 365),
        "max52": r2(max(anual)) if anual else None, "min52": r2(min(anual)) if anual else None,
        "vol": vol,
    }


def main(salida, previas=None):
    salida = Path(salida); salida.mkdir(parents=True, exist_ok=True)
    ant = {}
    if previas and Path(previas).exists():
        try:
            ant = {s["id"]: s for s in json.load(open(previas, encoding="utf-8")).get("series", [])}
        except Exception:
            ant = {}
    series, fallos = [], []
    for vid, sym, nombre, grupo, tz in VALORES:
        try:
            fd, vd, meta = descargar(sym, "2y", "1d")
            time.sleep(0.8)
            fs, vs, _ = descargar(sym, "10y", "1wk")
            time.sleep(0.8)
            if len(fd) < 30:
                raise RuntimeError("serie diaria demasiado corta")
            s = {"id": vid, "sym": sym, "nombre": nombre, "grupo": grupo, "tz": tz,
                 "moneda": meta.get("currency") or "", "bolsa": meta.get("fullExchangeName") or meta.get("exchangeName") or "",
                 **resumen(fd, vd),
                 # series: d = días desde 1-1-1970, c = cierres
                 "diario": {"d": dias(fd[-300:]), "c": [r2(v) for v in vd[-300:]]},
                 "semanal": {"d": dias(fs), "c": [r2(v) for v in vs]}}
            series.append(s)
            print(f"  {nombre}: {s['valor']} ({s['fecha']}, {s['d1']:+.2f} %)" if s["d1"] is not None else f"  {nombre}: {s['valor']}")
        except Exception as e:
            fallos.append(nombre)
            print(f"  aviso: {nombre}: {e}", file=sys.stderr)
            if vid in ant:
                series.append({**ant[vid], "antiguo": True})
    if not series:
        sys.exit("No se ha podido descargar ninguna cotización.")
    ahora = int(time.time())
    completo = {"actualizado": ahora, "fuente": "Yahoo Finance", "series": series}
    json.dump(completo, open(salida / "bolsa.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    # resumen ligero para la portada: último dato, variaciones y los últimos 30 cierres
    ligero = {"actualizado": ahora, "fuente": "Yahoo Finance",
              "series": [{k: v for k, v in s.items() if k not in ("diario", "semanal")} | {"spark": s["diario"]["c"][-30:]} for s in series]}
    json.dump(ligero, open(salida / "bolsa-resumen.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"{len(series) - len([s for s in series if s.get('antiguo')])} valores actualizados; {len(fallos)} con fallos: {', '.join(fallos) or 'ninguno'}")


if __name__ == "__main__":
    arg = lambda k, d=None: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
    main(arg("--salida", "."), previas=arg("--previas"))
