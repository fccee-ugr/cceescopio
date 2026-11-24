"""Genera la quinta tanda de recursos de CCEEscopio (noviembre de 2026):
precios-productos.qmd (precios de carburantes, luz, gas y productos de la cesta, comparados con el IPC) y
concurso-precios.qmd (concurso con código QR «¿Cuánto costaba?»).
Los precios de los carburantes los descarga cada semana la acción .github/workflows/carburantes.yml (tools/carburantes.py).
Uso: python3 tools/make_apps5.py"""
import json, re

HELPERS = open("_helpers.qmd", encoding="utf-8").read().strip()


def J(x):
    return json.dumps(x, ensure_ascii=False)


def pagina(nombre, texto, **rep):
    rep.setdefault("HELPERS", HELPERS)
    rep.setdefault("PRECIOS", PRECIOS)
    for k, v in rep.items():
        texto = texto.replace(f"__{k}__", v)
    assert not re.search(r"__[A-Z0-9]+__", texto), f"marcador sin sustituir en {nombre}"
    open(nombre, "w", encoding="utf-8").write(texto)
    print("  ", nombre)


# Productos con su nombre en español, un dibujo y un precio de referencia orientativo en España (editable en el concurso
# y en la calculadora). Los patrones localizan la subclase del IPCA por su nombre en inglés en Eurostat (ECOICOP 2 o ECOICOP).
PRODUCTOS = [
    dict(id="gasolina", nombre="Gasolina 95", emoji="⛽", unidad="litro", ref=1.50, carb="g95", pat=[r"petrol|gasoline"]),
    dict(id="gasoleo", nombre="Gasóleo (diésel)", emoji="🛻", unidad="litro", ref=1.45, carb="die", pat=[r"diesel"]),
    dict(id="luz", nombre="Electricidad", emoji="💡", unidad="kWh (hogares)", ref=0.20, pat=[r"^electricity"]),
    dict(id="gas", nombre="Gas natural", emoji="🔥", unidad="kWh (hogares)", ref=0.09, pat=[r"natural gas", r"^gas$"]),
    dict(id="pan", nombre="Pan", emoji="🥖", unidad="barra de 250 g", ref=1.10, pat=[r"^bread"]),
    dict(id="leche", nombre="Leche entera", emoji="🥛", unidad="litro", ref=1.05, pat=[r"whole milk", r"^(fresh )?milk$", r"^raw milk", r"^milk"]),
    dict(id="huevos", nombre="Huevos", emoji="🥚", unidad="docena", ref=2.90, pat=[r"^eggs"]),
    dict(id="aceite", nombre="Aceite de oliva", emoji="🫒", unidad="litro", ref=5.00, pat=[r"olive oil"]),
    dict(id="cafe", nombre="Café", emoji="☕", unidad="paquete de 250 g", ref=4.00, pat=[r"^coffee"]),
    dict(id="azucar", nombre="Azúcar", emoji="🍬", unidad="kg", ref=1.10, pat=[r"^sugar"]),
    dict(id="pollo", nombre="Pollo", emoji="🍗", unidad="kg", ref=3.80, pat=[r"poultry"]),
    dict(id="ternera", nombre="Carne de vacuno", emoji="🥩", unidad="kg", ref=16.00, pat=[r"beef|bovine"]),
    dict(id="patatas", nombre="Patatas", emoji="🥔", unidad="kg", ref=1.40, pat=[r"^potatoes"]),
    dict(id="cerveza", nombre="Cerveza", emoji="🍺", unidad="lata de 33 cl", ref=0.75, pat=[r"^beer", r"lager"]),
    dict(id="tabaco", nombre="Tabaco", emoji="🚬", unidad="cajetilla", ref=5.50, pat=[r"cigarettes"]),
    dict(id="menu", nombre="Comer en un restaurante", emoji="🍽️", unidad="menú del día", ref=15.00, pat=[r"restaurant"]),
    dict(id="pelo", nombre="Peluquería", emoji="💇", unidad="corte de pelo", ref=15.00, pat=[r"^hairdressing salons", r"hairdressing"]),
    dict(id="libro", nombre="Libros", emoji="📚", unidad="libro", ref=20.00, pat=[r"^books"]),
    dict(id="ropa", nombre="Ropa", emoji="👕", unidad="camiseta", ref=12.00, pat=[r"^garments$", r"^garments"]),
    dict(id="avion", nombre="Billetes de avión", emoji="✈️", unidad="billete", ref=90.00, pat=[r"passenger transport by air"]),
    dict(id="alquiler", nombre="Alquiler de vivienda", emoji="🏠", unidad="mes", ref=900.00, pat=[r"actual rentals.*main residence", r"actual rentals paid by tenants", r"actual rental"], concurso=False),
]

PRECIOS = r'''```{ojs}
//| echo: false
// Módulo de precios: carburantes (Boletín Petrolero de la Comisión Europea) e índices de precios por producto (IPCA, Eurostat)
PRECIOS = {
  const PRODUCTOS = __PRODUCTOS__;
  const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
  const mesTexto = (p) => { const m = /^(\d{4})-(\d{2})/.exec(p); return m ? `${MESES[+m[2] - 1]} de ${m[1]}` : p; };
  const nombreP = (c) => c === "EU27_2020" ? "UE-27 (media)" : c === "EA" ? "Zona euro (media)" : (nombresGeo[c] ?? c);
  async function cargarCarburantes() {
    const h = location.hostname, seg = location.pathname.split("/").filter(Boolean)[0];
    const urls = [];
    if (h.endsWith("github.io") && seg) urls.push(`https://raw.githubusercontent.com/${h.split(".")[0]}/${seg}/carburantes/carburantes.json`);
    urls.push("carburantes.json", "data/carburantes.json");
    for (const u of urls) { try { const r = await fetch(u, {cache: "no-store"}); if (r.ok) { const d = await r.json(); if (d.series) return d; } } catch (e) {} }
    return null;
  }
  // Serie semanal de un territorio -> [{fecha, periodo, valor}]
  function semanal(carb, pais, serie) {
    const v = carb?.series?.[pais]?.[serie]; if (!v) return [];
    return carb.fechas.map((f, i) => ({fecha: new Date(f + "T00:00:00"), periodo: f, valor: v[i]})).filter(d => d.valor != null);
  }
  // Media mensual de una serie semanal
  function mensual(sem) {
    return [...d3.rollup(sem, v => d3.mean(v, d => d.valor), d => d.periodo.slice(0, 7))].sort((a, b) => a[0] < b[0] ? -1 : 1)
      .map(([p, v]) => ({periodo: p, fecha: fecha(p), valor: v}));
  }
  async function eurostatCrudo(code, query) {
    const url = `https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/${code}?format=JSON&lang=EN${query}`;
    const r = await fetch(url);
    if (!r.ok) throw new Error(`Eurostat ${code}: HTTP ${r.status}`);
    const js = await r.json();
    return {recs: jsonstat(js), labels: Object.fromEntries(js.id.map(d => [d, js.dimension[d].category.label || {}]))};
  }
  // Catálogo de subclases del IPCA: primero la tabla nueva (ECOICOP 2, 2025 = 100) y, si falla, la anterior
  const anioBase = (u) => { const n = +u.slice(1); return n < 50 ? 2000 + n : 1900 + n; };
  let catalogo = null;
  async function catalogoIPC() {
    if (catalogo) return catalogo;
    for (const tabla of ["prc_hicp_minr", "prc_hicp_minx", "prc_hicp_midx"]) {
      for (const q of ["&geo=ES&unit=I25", "&geo=ES&unit=I15", "&geo=ES"]) {
        try {
          const {recs, labels} = await eurostatCrudo(tabla, q + "&lastTimePeriod=1");
          if (!recs.length) continue;
          const dim = Object.keys(recs[0]).find(k => /coicop/i.test(k));
          const uds = [...new Set(recs.map(r => r.unit))].filter(u => /^I\d\d$/.test(u ?? "")).sort((a, b) => anioBase(b) - anioBase(a));
          if (!dim || !uds.length) continue;
          const codigos = new Map();
          for (const r of recs) if (r.unit === uds[0]) codigos.set(r[dim], labels[dim]?.[r[dim]] ?? r[dim]);
          const total = ["TOTAL", "CP00"].find(c => codigos.has(c)) ?? "CP00";
          return (catalogo = {tabla, dim, unidad: uds[0], base: anioBase(uds[0]), codigos, total});
        } catch (e) {}
      }
    }
    return null;
  }
  function emparejar(cat) {
    const subclases = [...cat.codigos].filter(([k]) => /^CP\d{3,}$/.test(k));
    const out = [];
    for (const p of PRODUCTOS) {
      for (const pat of p.pat) {
        const re = new RegExp(pat, "i");
        const c = subclases.filter(([k, l]) => re.test(l)).sort((a, b) => b[0].length - a[0].length || (a[0] < b[0] ? -1 : 1))[0];
        if (c) { out.push({...p, code: c[0], etiqueta: c[1]}); break; }
      }
    }
    return out;
  }
  const cache = new Map();
  async function seriesIPC(cat, geo, codes, desde = 1996) {
    const falta = codes.filter(c => !cache.has(`${geo}|${c}`));
    for (let i = 0; i < falta.length; i += 25) {
      const lote = falta.slice(i, i + 25);
      try {
        const {recs} = await eurostatCrudo(cat.tabla, `&geo=${geo}&unit=${cat.unidad}` + lote.map(c => `&${cat.dim}=${c}`).join("") + `&sinceTimePeriod=${desde}`);
        for (const c of lote) cache.set(`${geo}|${c}`, recs.filter(r => r[cat.dim] === c && Number.isFinite(r.value))
          .map(r => ({periodo: r.time, fecha: fecha(r.time), valor: r.value})).filter(r => r.fecha).sort((a, b) => a.fecha - b.fecha));
      } catch (e) { for (const c of lote) cache.set(`${geo}|${c}`, []); }
    }
    return new Map(codes.map(c => [c, cache.get(`${geo}|${c}`) ?? []]));
  }
  // Índice con base 100 en la media de un año
  function base100(serie, anio) {
    const b = d3.mean(serie.filter(d => d.fecha.getFullYear() === anio), d => d.valor);
    return b ? serie.map(d => ({...d, valor: 100 * d.valor / b})) : [];
  }
  const valorEn = (serie, periodo) => serie.find(d => d.periodo.slice(0, 7) === periodo.slice(0, 7))?.valor;
  const euros = (v, dec = 2) => Number.isFinite(v) ? locES.format(`,.${dec}f`)(v) + " €" : "–";
  const pct = (v) => Number.isFinite(v) ? (v > 0 ? "+" : "") + locES.format(",.1f")(v) + " %" : "–";
  return {PRODUCTOS, MESES, mesTexto, nombreP, cargarCarburantes, semanal, mensual, eurostatCrudo, catalogoIPC, emparejar, seriesIPC, base100, valorEn, euros, pct};
}
```'''.replace("__PRODUCTOS__", J(PRODUCTOS))

# =====================================================================================
# Precios de productos
# =====================================================================================
pagina("precios-productos.qmd", r'''---
title: "Precios de productos"
subtitle: "Gasolina, gasóleo, luz, gas y la cesta de la compra, comparados con el IPC"
toc: true
---

Las fuentes oficiales casi nunca publican **precios medios** de productos concretos: el IPC mide cómo **cambian** los precios, no cuánto cuestan las cosas. Hay dos excepciones importantes que sí aparecen aquí en euros: los **carburantes**, con datos semanales de la Comisión Europea, y la **electricidad y el gas** de los hogares, con datos semestrales de Eurostat. Para el resto de productos (pan, leche, aceite, café…) se usa su **índice de precios** dentro del IPC armonizado, que permite saber cuánto más caros son hoy que en cualquier fecha anterior.

__HELPERS__

__PRECIOS__

```{ojs}
//| echo: false
carb = PRECIOS.cargarCarburantes()
catIPC = PRECIOS.catalogoIPC()
productosIPC = catIPC ? PRECIOS.emparejar(catIPC) : []
paisesCarb = carb ? Object.keys(carb.series).sort((a, b) => a === "ES" ? -1 : b === "ES" ? 1 : PRECIOS.nombreP(a).localeCompare(PRECIOS.nombreP(b), "es")) : []
anioUltCarb = carb ? +carb.fechas.at(-1).slice(0, 4) : 2026
```

## Gasolina y gasóleo

Precio de venta al público en euros por litro, cada lunes desde 2005. Fuente: Comisión Europea, *Weekly Oil Bulletin*.

```{ojs}
//| echo: false
viewof prodC = Inputs.radio(new Map([["Gasolina 95", "g95"], ["Gasóleo (diésel)", "die"]]), {label: "Carburante", value: "g95"})
viewof impC = Inputs.radio(new Map([["Con impuestos (lo que se paga en la gasolinera)", "con"], ["Sin impuestos", "sin"]]), {label: "Precio", value: "con"})
viewof paisesC = Inputs.select(new Map(paisesCarb.map(c => [PRECIOS.nombreP(c), c])), {multiple: true, label: "Territorios (Ctrl/Cmd para elegir varios)", value: ["ES", "EU27_2020", "FR", "DE", "IT", "PT"].filter(c => paisesCarb.includes(c)), size: 8})
viewof desdeC = Inputs.range([2005, anioUltCarb], {label: "Desde el año", step: 1, value: Math.max(2005, anioUltCarb - 6)})
```

```{ojs}
//| echo: false
nomCarb = prodC === "g95" ? "gasolina 95" : "gasóleo"
filasC = paisesC.flatMap(p => PRECIOS.semanal(carb, p, `${prodC}_${impC}`).filter(d => d.fecha.getFullYear() >= desdeC).map(d => ({...d, territorio: PRECIOS.nombreP(p)})))
{
  if (!carb) return html`<div class="callout callout-warning"><p><b>Los precios de los carburantes todavía no están disponibles.</b> Se descargan cada semana del Boletín Petrolero de la Comisión Europea mediante una tarea automática del repositorio de la web; si acabas de instalar esta página, ejecútala una vez a mano (GitHub → Actions → «Carburantes de CCEEscopio» → Run workflow). Mientras tanto puedes consultar los datos en la <a href="https://energy.ec.europa.eu/data-and-analysis/weekly-oil-bulletin_en" target="_blank" rel="noopener">web del boletín</a>.</p></div>`;
  const p0 = paisesC[0] ?? "ES", s = PRECIOS.semanal(carb, p0, `${prodC}_con`), sin = PRECIOS.semanal(carb, p0, `${prodC}_sin`);
  if (!s.length) return html``;
  const ult = s.at(-1), hace = (dias) => s.filter(d => d.fecha <= new Date(+ult.fecha - dias * 864e5)).at(-1);
  const m4 = hace(28), a1 = hace(364), max = d3.greatest(s, d => d.valor);
  const ultSin = sin.find(d => d.periodo === ult.periodo) ?? sin.at(-1), conMismo = s.find(d => d.periodo === ultSin?.periodo);
  const imp = ultSin && conMismo ? 100 * (1 - ultSin.valor / conMismo.valor) : NaN;
  const k = (l, n, sub) => html`<div class="kpi"><div class="kpi-l">${l}</div><div class="kpi-n">${n}</div><div class="kpi-s">${sub}</div></div>`;
  const fd = (d) => d.fecha.toLocaleDateString("es-ES", {day: "numeric", month: "short", year: "numeric"});
  return html`<div class="kpi-grid">
    ${k(`Precio de la ${nomCarb} en ${PRECIOS.nombreP(p0)}`, PRECIOS.euros(ult.valor, 3) + "/l", `Semana del ${fd(ult)}`)}
    ${k("Variación en un mes", m4 ? PRECIOS.pct(100 * (ult.valor / m4.valor - 1)) : "–", m4 ? `Desde ${PRECIOS.euros(m4.valor, 3)}/l` : "")}
    ${k("Variación en un año", a1 ? PRECIOS.pct(100 * (ult.valor / a1.valor - 1)) : "–", a1 ? `Desde ${PRECIOS.euros(a1.valor, 3)}/l` : "")}
    ${k("Máximo desde 2005", PRECIOS.euros(max.valor, 3) + "/l", `Semana del ${fd(max)}`)}
    ${k("Impuestos sobre el precio", Number.isFinite(imp) ? locES.format(",.0f")(imp) + " %" : "–", "IVA, impuesto especial y otros")}
  </div>`;
}
```

```{ojs}
//| echo: false
carb ? (paisesC.length ? Plot.plot({
  title: `Precio de la ${nomCarb} ${impC === "con" ? "con" : "sin"} impuestos`,
  height: 440, marginLeft: 55, marginRight: 120,
  x: {label: null, type: "time"}, y: {label: "€ por litro", grid: true, tickFormat: v => locES.format(",.2f")(v)},
  color: {domain: paisesC.map(PRECIOS.nombreP), range: colores(paisesC.map(PRECIOS.nombreP))},
  marks: [
    Plot.line(filasC, {x: "fecha", y: "valor", stroke: "territorio", strokeWidth: d => d.territorio === "España" ? 2.6 : 1.5}),
    Plot.text(filasC, Plot.selectLast({x: "fecha", y: "valor", z: "territorio", text: "territorio", fill: "territorio", textAnchor: "start", dx: 6})),
    Plot.tip(filasC, Plot.pointer({x: "fecha", y: "valor", title: d => `${d.territorio} · semana del ${d.fecha.toLocaleDateString("es-ES")}\n${PRECIOS.euros(d.valor, 3)} por litro`}))
  ]
}) : html`<p class="pending">Elige al menos un territorio.</p>`) : html``
```

### ¿Cuánto son impuestos?

```{ojs}
//| echo: false
viewof paisImp = carb ? Inputs.select(new Map(paisesCarb.map(c => [PRECIOS.nombreP(c), c])), {label: "Territorio", value: "ES"}) : Object.assign(html`<span></span>`, {value: "ES"})
```

```{ojs}
//| echo: false
{
  if (!carb) return html``;
  const con = PRECIOS.semanal(carb, paisImp, `${prodC}_con`), sin = new Map(PRECIOS.semanal(carb, paisImp, `${prodC}_sin`).map(d => [d.periodo, d.valor]));
  const filas = con.filter(d => d.fecha.getFullYear() >= desdeC && sin.has(d.periodo)).flatMap(d => [
    {fecha: d.fecha, parte: "Precio sin impuestos", valor: sin.get(d.periodo), total: d.valor},
    {fecha: d.fecha, parte: "Impuestos", valor: d.valor - sin.get(d.periodo), total: d.valor}]);
  if (!filas.length) return html`<p class="pending">No hay precios sin impuestos para este territorio.</p>`;
  return Plot.plot({
    title: `${nomCarb[0].toUpperCase() + nomCarb.slice(1)} en ${PRECIOS.nombreP(paisImp)}: precio antes de impuestos e impuestos`,
    height: 380, marginLeft: 55, x: {label: null, type: "time"}, y: {label: "€ por litro", grid: true, tickFormat: v => locES.format(",.2f")(v)},
    color: {domain: ["Precio sin impuestos", "Impuestos"], range: ["#F29200", "#B5175F"], legend: true},
    marks: [Plot.areaY(filas, {x: "fecha", y: "valor", fill: "parte", order: ["Precio sin impuestos", "Impuestos"], fillOpacity: 0.85}),
      Plot.tip(filas.filter(d => d.parte === "Impuestos"), Plot.pointerX({x: "fecha", y: "total", title: d => `Semana del ${d.fecha.toLocaleDateString("es-ES")}\nPrecio final: ${PRECIOS.euros(d.total, 3)}/l\nImpuestos: ${PRECIOS.euros(d.valor, 3)}/l (${locES.format(",.0f")(100 * d.valor / d.total)} %)`}))]
  });
}
```

<p class="source">El precio sin impuestos incluye el coste del petróleo y su refino, el transporte, la distribución y el margen de las estaciones de servicio. Los impuestos son el IVA y el impuesto especial sobre hidrocarburos, que es una cantidad fija por litro: por eso, cuando el petróleo se abarata, los impuestos pesan más en el precio final.</p>

## La gasolina frente al IPC

¿Ha subido la gasolina más o menos que el resto de precios? Para compararlos se pasan las dos series a **índices con base 100** en un mismo año: si en el último dato la gasolina está en 150 y el IPC general en 130, la gasolina se ha encarecido más que la media de los productos. La segunda gráfica responde a otra pregunta: ¿cuánto costaba la gasolina **en euros de hoy**? Se obtiene **deflactando** el precio con el IPC general.

```{ojs}
//| echo: false
viewof paisIPC = carb ? Inputs.select(new Map(paisesCarb.filter(c => c !== "EA").map(c => [PRECIOS.nombreP(c), c])), {label: "Territorio", value: "ES"}) : Object.assign(html`<span></span>`, {value: "ES"})
viewof baseC = Inputs.range([2005, anioUltCarb - 1], {label: "Año base (= 100)", step: 1, value: 2015})
```

```{ojs}
//| echo: false
compIPC = {
  if (!carb || !catIPC) return null;
  const prodIPC = productosIPC.find(p => p.carb === prodC);
  const codes = [catIPC.total, ...(prodIPC ? [prodIPC.code] : [])];
  const s = await PRECIOS.seriesIPC(catIPC, paisIPC, codes, 2005);
  const general = s.get(catIPC.total), sub = prodIPC ? s.get(prodIPC.code) : [];
  const precio = PRECIOS.mensual(PRECIOS.semanal(carb, paisIPC, `${prodC}_con`));
  if (!general.length || !precio.length) return null;
  return {general, sub, precio, prodIPC};
}
```

```{ojs}
//| echo: false
{
  if (!carb) return html``;
  if (!catIPC) return html`<p class="pending">No se han podido cargar los datos del IPC de Eurostat. Inténtalo de nuevo más tarde.</p>`;
  if (!compIPC) return html`<p class="pending">No hay datos del IPC para este territorio.</p>`;
  const {general, sub, precio} = compIPC;
  const series = [
    ...PRECIOS.base100(precio, baseC).map(d => ({...d, serie: `Precio de la ${nomCarb} en surtidor`})),
    ...PRECIOS.base100(sub, baseC).map(d => ({...d, serie: `IPC de la ${nomCarb}`})),
    ...PRECIOS.base100(general, baseC).map(d => ({...d, serie: "IPC general"}))
  ].filter(d => d.fecha.getFullYear() >= Math.min(desdeC, baseC));
  const dom = [...new Set(series.map(d => d.serie))];
  return Plot.plot({
    title: `${nomCarb[0].toUpperCase() + nomCarb.slice(1)} e IPC general en ${PRECIOS.nombreP(paisIPC)} (índices, ${baseC} = 100)`,
    height: 420, marginLeft: 50, marginRight: 10, x: {label: null, type: "time"}, y: {label: `Índice (${baseC} = 100)`, grid: true},
    color: {domain: dom, range: ["#B5175F", "#F29200", "#3C3C3B"].slice(0, dom.length), legend: true},
    marks: [Plot.ruleY([100], {stroke: "#999"}),
      Plot.line(series, {x: "fecha", y: "valor", stroke: "serie", strokeWidth: d => d.serie === "IPC general" ? 2.6 : 1.8, strokeDasharray: d => d.serie.startsWith("IPC de") ? "5,3" : null}),
      Plot.tip(series, Plot.pointer({x: "fecha", y: "valor", title: d => `${d.serie} · ${PRECIOS.mesTexto(d.periodo)}\n${locES.format(",.1f")(d.valor)}`}))]
  });
}
```

```{ojs}
//| echo: false
{
  if (!carb || !compIPC) return html``;
  const {general, precio} = compIPC;
  const ultI = general.at(-1), mapa = new Map(general.map(d => [d.periodo.slice(0, 7), d.valor]));
  const filas = precio.filter(d => mapa.has(d.periodo) && d.fecha.getFullYear() >= Math.min(desdeC, baseC)).flatMap(d => [
    {fecha: d.fecha, periodo: d.periodo, serie: "Precio de cada momento (nominal)", valor: d.valor},
    {fecha: d.fecha, periodo: d.periodo, serie: `En euros de ${PRECIOS.mesTexto(ultI.periodo)} (real)`, valor: d.valor * ultI.valor / mapa.get(d.periodo)}]);
  const nom = filas.filter((d, i) => i % 2 === 0), real = filas.filter((d, i) => i % 2 === 1);
  const mN = d3.greatest(nom, d => d.valor), mR = d3.greatest(real, d => d.valor);
  const b = precio.filter(d => d.fecha.getFullYear() === baseC), bI = general.filter(d => d.fecha.getFullYear() === baseC);
  const ultP = precio.filter(d => mapa.has(d.periodo)).at(-1);
  const subeP = 100 * (ultP.valor / d3.mean(b, d => d.valor) - 1), subeI = 100 * (mapa.get(ultP.periodo) / d3.mean(bI, d => d.valor) - 1);
  const rel = 100 * ((1 + subeP / 100) / (1 + subeI / 100) - 1);
  return html`<div class="calc-result"><p class="calc-big">Desde ${baseC}, la ${nomCarb} ha subido un <b>${PRECIOS.pct(subeP)}</b> y el IPC general un <b>${PRECIOS.pct(subeI)}</b>: en términos reales (descontada la inflación), la ${nomCarb} es hoy un <b>${PRECIOS.pct(rel)}</b> ${rel >= 0 ? "más cara" : "más barata"} que en ${baseC}.</p>
    <p class="calc-small">Máximo en euros de cada momento: ${PRECIOS.euros(mN.valor, 3)}/l (${PRECIOS.mesTexto(mN.periodo)}). Máximo en euros de hoy: ${PRECIOS.euros(mR.valor, 3)}/l (${PRECIOS.mesTexto(mR.periodo)}). Medias mensuales del precio con impuestos en ${PRECIOS.nombreP(paisIPC)}.</p></div>
  ${Plot.plot({
    title: `${nomCarb[0].toUpperCase() + nomCarb.slice(1)} en ${PRECIOS.nombreP(paisIPC)}: precio nominal y precio real`,
    height: 380, marginLeft: 55, x: {label: null, type: "time"}, y: {label: "€ por litro", grid: true, tickFormat: v => locES.format(",.2f")(v)},
    color: {domain: [...new Set(filas.map(d => d.serie))], range: ["#3C3C3B", "#B5175F"], legend: true},
    marks: [Plot.line(filas, {x: "fecha", y: "valor", stroke: "serie", strokeWidth: 2}),
      Plot.tip(filas, Plot.pointer({x: "fecha", y: "valor", title: d => `${d.serie}\n${PRECIOS.mesTexto(d.periodo)}: ${PRECIOS.euros(d.valor, 3)}/l`}))]
  })}`;
}
```

<p class="source">Precio real del mes <i>t</i> = precio del mes <i>t</i> × IPC del último mes ÷ IPC del mes <i>t</i>. El «IPC de la gasolina» es la subclase de carburantes del Índice de Precios de Consumo Armonizado (Eurostat); debe seguir muy de cerca al precio del boletín, porque mide lo mismo con otra fuente.</p>

## Electricidad y gas de los hogares

Precio medio por kWh que pagan los hogares con un consumo medio, impuestos incluidos. Eurostat lo publica cada semestre.

```{ojs}
//| echo: false
viewof energiaE = Inputs.radio(new Map([["Electricidad", "luz"], ["Gas natural", "gas"]]), {label: "Energía", value: "luz"})
viewof paisesE = Inputs.select(new Map(geosPaises.map(c => [nombresGeo[c] ?? c, c])), {multiple: true, label: "Territorios", value: ["ES", "EU27_2020", "FR", "DE", "IT", "PT"], size: 8})
```

```{ojs}
//| echo: false
datosE = {
  const tabla = energiaE === "luz" ? "nrg_pc_204" : "nrg_pc_202", cons = energiaE === "luz" ? "KWH2500-4999" : "GJ20-199";
  const geos = paisesE.map(g => `&geo=${g}`).join("");
  for (const [u, f] of [["KWH", 1], ["GJ", 1 / 277.7778]]) {
    try {
      const r = await eurostat(tabla, `&nrg_cons=${cons}&unit=${u}&tax=I_TAX&currency=EUR&sinceTimePeriod=2008${geos}`);
      const filas = r.filter(d => Number.isFinite(d.value) && d.value > 0).map(d => ({territorio: nombresGeo[d.geo] ?? d.geoLabel, periodo: d.time, fecha: fecha(d.time), valor: d.value * f})).filter(d => d.fecha);
      if (filas.length) return {filas, tabla};
    } catch (e) {}
  }
  return null;
}
```

```{ojs}
//| echo: false
datosE ? Plot.plot({
  title: `${energiaE === "luz" ? "Electricidad" : "Gas natural"}: precio para los hogares con impuestos`,
  height: 420, marginLeft: 55, marginRight: 120, x: {label: null, type: "time"}, y: {label: "€ por kWh", grid: true, tickFormat: v => locES.format(",.2f")(v)},
  color: {domain: [...new Set(datosE.filas.map(d => d.territorio))], range: colores([...new Set(datosE.filas.map(d => d.territorio))])},
  marks: [Plot.line(datosE.filas, {x: "fecha", y: "valor", stroke: "territorio", curve: "step-after", strokeWidth: d => d.territorio === "España" ? 2.6 : 1.5}),
    Plot.text(datosE.filas, Plot.selectLast({x: "fecha", y: "valor", z: "territorio", text: "territorio", fill: "territorio", textAnchor: "start", dx: 6})),
    Plot.tip(datosE.filas, Plot.pointer({x: "fecha", y: "valor", title: d => `${d.territorio} · ${d.periodo.replace("-S", ", semestre ")}\n${PRECIOS.euros(d.valor, 3)} por kWh`}))]
}) : html`<p class="pending">No se han podido cargar los precios de la energía de Eurostat. Inténtalo de nuevo más tarde.</p>`
```

<p class="source">Fuente: Eurostat (nrg_pc_204 y nrg_pc_202): hogares con un consumo anual de 2.500 a 5.000 kWh de electricidad o de 20 a 200 GJ de gas; todos los impuestos incluidos. Es un precio medio del semestre: no recoge las variaciones diarias del mercado eléctrico.</p>

## La cesta de la compra

Para el resto de productos no hay un precio medio oficial, pero sí su **índice de precios** dentro del IPC armonizado. Con él se puede comparar cada producto con el IPC general y **estimar cuánto costaba** en cualquier fecha a partir de lo que cuesta hoy.

```{ojs}
//| echo: false
viewof geoP = Inputs.select(new Map(geosPaises.map(c => [nombresGeo[c] ?? c, c])), {label: "Territorio", value: "ES"})
opcionesP = {
  if (!catIPC) return new Map();
  const cur = productosIPC.map(p => [`${p.emoji} ${p.nombre}`, p]);
  const usados = new Set(productosIPC.map(p => p.code));
  const otros = [...catIPC.codigos].filter(([k]) => /^CP\d{3,}$/.test(k) && !usados.has(k)).sort((a, b) => a[0] < b[0] ? -1 : 1)
    .map(([k, l]) => [`Otras categorías de Eurostat (en inglés) · ${k.replace(/^CP/, "")} ${l}`, {id: k, code: k, nombre: l, emoji: "🏷️", unidad: "unidad", ref: 10, etiqueta: l}]);
  return new Map([...cur, ...otros]);
}
viewof prodP = Inputs.select(opcionesP, {label: "Producto", value: opcionesP.get("🥖 Pan") ?? [...opcionesP.values()][0]})
viewof baseP = Inputs.range([1996, (new Date()).getFullYear() - 1], {label: "Desde el año (= 100)", step: 1, value: 2019})
```

```{ojs}
//| echo: false
seriesP = {
  if (!catIPC || !prodP) return null;
  const codes = [...new Set([catIPC.total, prodP.code, ...productosIPC.map(p => p.code)])];
  return await PRECIOS.seriesIPC(catIPC, geoP, codes, 1996);
}
```

```{ojs}
//| echo: false
{
  if (!catIPC) return html`<p class="pending">No se han podido cargar los índices de precios de Eurostat. Inténtalo de nuevo más tarde.</p>`;
  if (!seriesP) return html``;
  const sp = PRECIOS.base100(seriesP.get(prodP.code), baseP), sg = PRECIOS.base100(seriesP.get(catIPC.total), baseP);
  if (!sp.length) return html`<p class="pending">No hay datos de este producto para ${nombresGeo[geoP] ?? geoP} en ${baseP}. Prueba con un año posterior.</p>`;
  const filas = [...sp.map(d => ({...d, serie: prodP.nombre})), ...sg.map(d => ({...d, serie: "IPC general"}))].filter(d => d.fecha.getFullYear() >= baseP);
  return Plot.plot({
    title: `${prodP.nombre} frente al IPC general en ${nombresGeo[geoP] ?? geoP} (${baseP} = 100)`,
    height: 400, marginLeft: 50, x: {label: null, type: "time"}, y: {label: `Índice (${baseP} = 100)`, grid: true},
    color: {domain: [prodP.nombre, "IPC general"], range: ["#B5175F", "#3C3C3B"], legend: true},
    marks: [Plot.ruleY([100], {stroke: "#999"}), Plot.line(filas, {x: "fecha", y: "valor", stroke: "serie", strokeWidth: 2}),
      Plot.tip(filas, Plot.pointer({x: "fecha", y: "valor", title: d => `${d.serie} · ${PRECIOS.mesTexto(d.periodo)}\n${locES.format(",.1f")(d.valor)}`}))]
  });
}
```

### ¿Cuánto costaba? {#cuanto-costaba}

```{ojs}
//| echo: false
viewof precioHoy = Inputs.number([0.01, 100000], {label: `Precio actual (${prodP?.unidad ?? "unidad"}), en euros`, value: prodP?.ref ?? 1, step: 0.01})
```

```{ojs}
//| echo: false
{
  if (!seriesP || !prodP) return html``;
  const s = seriesP.get(prodP.code), g = seriesP.get(catIPC.total);
  if (!s?.length) return html``;
  const ult = s.at(-1);
  const est = s.map(d => ({...d, precio: precioHoy * d.valor / ult.valor}));
  const hitos = [...new Set([baseP, 2000, 2005, 2010, 2015, 2020, ult.fecha.getFullYear() - 1].filter(a => a >= est[0].fecha.getFullYear() && a <= ult.fecha.getFullYear()))].sort();
  const tabla = hitos.map(a => { const v = est.filter(d => d.fecha.getFullYear() === a); return {a, p: d3.mean(v, d => d.precio)}; }).filter(d => Number.isFinite(d.p));
  const ini = est.filter(d => d.fecha.getFullYear() === baseP), gi = g.filter(d => d.fecha.getFullYear() === baseP);
  const subeP = ini.length ? 100 * (ult.valor / d3.mean(ini, d => d.valor) - 1) : NaN, subeG = gi.length ? 100 * (g.at(-1).valor / d3.mean(gi, d => d.valor) - 1) : NaN;
  return html`<div class="calc-result"><p class="calc-big">Si hoy cuesta <b>${PRECIOS.euros(precioHoy)}</b>, en ${baseP} costaba de media unos <b>${PRECIOS.euros(precioHoy / (1 + subeP / 100))}</b>: ha subido un <b>${PRECIOS.pct(subeP)}</b>, frente al ${PRECIOS.pct(subeG)} del IPC general.</p>
    <p class="calc-small">${tabla.map(d => `${d.a}: ${PRECIOS.euros(d.p)}`).join(" · ")}. Último dato del índice: ${PRECIOS.mesTexto(ult.periodo)}. El precio actual es orientativo: cámbialo por el que conozcas.</p></div>
  ${Plot.plot({
    title: `${prodP.emoji} ${prodP.nombre}: precio estimado si hoy cuesta ${PRECIOS.euros(precioHoy)}`,
    height: 320, marginLeft: 55, x: {label: null, type: "time"}, y: {label: "€", grid: true, tickFormat: v => locES.format(",.2f")(v)},
    marks: [Plot.line(est, {x: "fecha", y: "precio", stroke: "#B5175F", strokeWidth: 2}),
      Plot.tip(est, Plot.pointer({x: "fecha", y: "precio", title: d => `${PRECIOS.mesTexto(d.periodo)}: ${PRECIOS.euros(d.precio)}`}))]
  })}`;
}
```

<p class="source">Precio estimado del mes <i>t</i> = precio actual × índice del mes <i>t</i> ÷ índice del último mes. Refleja la evolución media del precio de ese tipo de producto en el territorio elegido, no la de una marca o una tienda concretas.</p>

### ¿Qué productos han subido más?

```{ojs}
//| echo: false
{
  if (!seriesP) return html``;
  const sube = (c) => { const s = seriesP.get(c) ?? [], b = s.filter(d => d.fecha.getFullYear() === baseP); return s.length && b.length ? 100 * (s.at(-1).valor / d3.mean(b, d => d.valor) - 1) : NaN; };
  const g = sube(catIPC.total);
  const filas = productosIPC.map(p => ({producto: `${p.emoji} ${p.nombre}`, v: sube(p.code)})).filter(d => Number.isFinite(d.v));
  if (!filas.length) return html``;
  return Plot.plot({
    title: `Variación de precios desde ${baseP} en ${nombresGeo[geoP] ?? geoP}, por producto`,
    height: Math.max(300, 26 * filas.length), marginLeft: 190, marginRight: 60,
    x: {label: "Variación acumulada (%)", grid: true, tickFormat: v => locES.format(",.0f")(v)}, y: {label: null},
    marks: [
      Plot.barX(filas, {y: "producto", x: "v", sort: {y: "-x"}, fill: d => d.v > g ? "#B5175F" : "#D9C2CC", tip: true, title: d => `${d.producto}: ${PRECIOS.pct(d.v)}`}),
      Plot.text(filas, {y: "producto", x: "v", text: d => PRECIOS.pct(d.v), dx: d => d.v >= 0 ? 4 : -4, textAnchor: d => d.v >= 0 ? "start" : "end", fontSize: 10}),
      Plot.ruleX([g], {stroke: "#3C3C3B", strokeWidth: 2, strokeDasharray: "4,3"}),
      Plot.text([g], {x: d => d, frameAnchor: "top", dy: -2, text: d => `IPC general ${PRECIOS.pct(d)}`, fill: "#3C3C3B", fontWeight: 700, textAnchor: "start", dx: 4}),
      Plot.ruleX([0])
    ]
  });
}
```

<p class="source">En color intenso, los productos que se han encarecido más que el conjunto de los precios (IPC general, línea discontinua). Fuente: Eurostat, Índice de Precios de Consumo Armonizado por subclases (base 2025 = 100).</p>

## Descargar los datos

```{ojs}
//| echo: false
carb ? html`<div class="descargas">
  ${DOM.download(() => csv(paisesCarb.flatMap(p => ["g95", "die"].flatMap(pr => ["con", "sin"].flatMap(im => PRECIOS.semanal(carb, p, `${pr}_${im}`).map(d => ({territorio: PRECIOS.nombreP(p), codigo: p, carburante: pr === "g95" ? "Gasolina 95" : "Gasóleo", impuestos: im === "con" ? "con impuestos" : "sin impuestos", semana: d.periodo, euros_litro: d.valor})))))), "cceescopio_carburantes.csv", "⬇ Precios semanales de los carburantes (CSV)")}
  ${seriesP ? DOM.download(() => csv([catIPC.total, ...productosIPC.map(p => p.code)].flatMap(c => (seriesP.get(c) ?? []).map(d => ({territorio: nombresGeo[geoP] ?? geoP, producto: c === catIPC.total ? "IPC general" : productosIPC.find(p => p.code === c).nombre, codigo_ecoicop: c, mes: d.periodo, indice: d.valor})))), `cceescopio_ipc_productos_${geoP}.csv`, "⬇ Índices de precios por producto (CSV)") : ""}
</div>
<p class="source">Carburantes: Comisión Europea, Weekly Oil Bulletin (actualizado: ${carb.actualizado}). Índices de precios y energía: Eurostat. Reutilización libre citando la fuente, a través de Muñoz, Álvarez (2026), CCEEscopio D+I, Facultad de Ciencias Económicas y Empresariales, Universidad de Granada.</p>` : html``
```

::: {.callout-tip appearance="simple"}
**Para clase.** Juega con tus estudiantes a [«¿Cuánto costaba?»](concurso-precios.qmd): ven un producto con su precio actual y tienen que adivinar cuánto costaba en una fecha del pasado. Y en la [calculadora de inflación](calculadora.qmd) puedes actualizar cualquier cantidad con el IPC general.
:::
''')

# =====================================================================================
# Concurso «¿Cuánto costaba?»
# =====================================================================================
pagina("concurso-precios.qmd", r'''---
title: "¿Cuánto costaba?"
subtitle: "Concurso con código QR: adivina el precio que tenían los productos en una fecha del pasado"
toc: false
---

__HELPERS__

__PRECIOS__

```{ojs}
//| echo: false
paramsP = new URLSearchParams(location.search)
SALA = paramsP.get("sala")
BROKERS = [
  {id: "h", nombre: "HiveMQ", url: "wss://broker.hivemq.com:8884/mqtt"},
  {id: "e", nombre: "EMQX", url: "wss://broker.emqx.io:8084/mqtt"},
  {id: "m", nombre: "Mosquitto", url: "wss://test.mosquitto.org:8081/mqtt"}
]
mqttLib = { try { const m = await import("https://cdn.jsdelivr.net/npm/mqtt@5.10.1/dist/mqtt.esm.js"); return m.default ?? m; } catch (e) { return null; } }
conectarBroker = (b) => new Promise((ok, mal) => {
  if (!mqttLib) return mal(new Error("sin librería"));
  const c = mqttLib.connect(b.url, {clientId: "ccee_" + Math.random().toString(16).slice(2, 10), connectTimeout: 6000, reconnectPeriod: 2000, clean: true});
  const t = setTimeout(() => { c.end(true); mal(new Error("tiempo agotado")); }, 7000);
  c.once("connect", () => { clearTimeout(t); ok(c); });
})
temaEstado = (s) => `cceescopio/precios/${s}/estado`
temaJug = (s) => `cceescopio/precios/${s}/jugadores`
```

```{ojs}
//| echo: false
// Utilidades del concurso (sin dependencias del navegador, para poder probarlas)
CP = {
  const h = (sala, i) => [...`${sala}|${i}`].reduce((a, ch) => (a * 31 + ch.charCodeAt(0)) >>> 0, 7) % 100000;
  const ofuscar = (sala, i, v) => Math.round(v * 1000) + h(sala, i);
  const desofuscar = (sala, i, x) => (x - h(sala, i)) / 1000;
  // Puntos: 100 si se acierta el precio exacto; 0 si el error es del 50 % o más
  const puntos = (resp, real) => Number.isFinite(resp) && real > 0 ? Math.max(0, Math.round(100 * (1 - Math.abs(resp - real) / real / 0.5))) : 0;
  const leer = (t) => { const s = String(t).trim().replace(/\s|€/g, ""); const n = /,/.test(s) ? +s.replace(/\./g, "").replace(",", ".") : +s; return Number.isFinite(n) && n > 0 ? n : NaN; };
  const ordenar = (jug) => [...jug.values()].sort((a, b) => (b.puntos - a.puntos) || ((b.fin ? 1 : 0) - (a.fin ? 1 : 0)) || (a.tiempo - b.tiempo) || a.alias.localeCompare(b.alias));
  const nuevaSala = () => Array.from(crypto.getRandomValues(new Uint8Array(8)), b => "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"[b % 32]).join("");
  const segundos = (ms) => `${(ms / 1000).toFixed(1).replace(".", ",")} s`;
  // Elige n preguntas: productos sin repetir mientras se pueda y meses al azar entre «desde» y un año antes del último dato
  function sortear(productos, n, desde, ultimo, azar = Math.random) {
    const out = [], bolsa = [];
    const [ua, um] = ultimo.split("-").map(Number), fin = ua * 12 + um - 1 - 12, ini = desde * 12;
    for (let i = 0; i < n; i++) {
      if (!bolsa.length) bolsa.push(...productos.map((p, k) => k).sort(() => azar() - 0.5));
      const p = productos[bolsa.pop()];
      const [pa, pm] = (p.inicio ?? "1996-01").split("-").map(Number), ip = Math.max(ini, pa * 12 + pm - 1);
      const m = ip + Math.floor(azar() * Math.max(1, fin - ip + 1));
      out.push({p, periodo: `${Math.floor(m / 12)}-${String(m % 12 + 1).padStart(2, "0")}`});
    }
    return out;
  }
  return {ofuscar, desofuscar, puntos, leer, ordenar, nuevaSala, segundos, sortear};
}
```

```{ojs}
//| echo: false
// ============================ PANTALLA DEL PROFESOR ============================
datosCP = {
  if (SALA) return null;
  const [carb, cat] = await Promise.all([PRECIOS.cargarCarburantes(), PRECIOS.catalogoIPC()]);
  const prods = cat ? PRECIOS.emparejar(cat).filter(p => p.concurso !== false) : [];
  const series = cat ? await PRECIOS.seriesIPC(cat, "ES", [cat.total, ...prods.map(p => p.code)], 1996) : new Map();
  // Carburantes: precio real del boletín (media del mes) si está disponible
  const precioCarb = (p) => carb && p.carb ? PRECIOS.mensual(PRECIOS.semanal(carb, "ES", `${p.carb}_con`)) : null;
  const lista = prods.map(p => ({...p, serie: series.get(p.code) ?? [], carbM: precioCarb(p)})).filter(p => p.serie.length > 60 || p.carbM?.length > 60)
    .map(p => ({...p, inicio: d3.min([p.serie[0]?.periodo, p.carbM?.[0]?.periodo].filter(Boolean).map(x => x.slice(0, 7)))}));
  return {carb, cat, lista, general: series.get(cat?.total) ?? []};
}
viewof productosCP = SALA ? Object.assign(html`<span></span>`, {value: []}) : (datosCP.lista.length ? Inputs.checkbox(datosCP.lista, {label: "Productos", format: p => `${p.emoji} ${p.nombre}`, value: datosCP.lista}) : html`<p class="pending">No se han podido cargar los índices de precios de Eurostat. Comprueba la conexión y recarga la página.</p>`)
```

```{ojs}
//| echo: false
// Precios actuales de referencia (editables). Los carburantes usan el último precio del Boletín Petrolero.
viewof preciosCP = {
  if (SALA || !datosCP?.lista.length) return Object.assign(html`<span></span>`, {value: new Map()});
  const val = new Map(), filas = [];
  for (const p of productosCP) {
    const carbS = p.carb && datosCP.carb ? PRECIOS.semanal(datosCP.carb, "ES", `${p.carb}_con`) : [];
    if (carbS.length) { val.set(p.id, carbS.at(-1).valor); filas.push(html`<tr><td>${p.emoji} ${p.nombre}</td><td>${p.unidad}</td><td><b>${PRECIOS.euros(carbS.at(-1).valor, 3)}</b> <span class="kpi-s">(Boletín Petrolero, ${carbS.at(-1).fecha.toLocaleDateString("es-ES")})</span></td></tr>`); continue; }
    val.set(p.id, p.ref);
    const inp = html`<input type="number" min="0.01" step="0.01" style="width:7rem">`; inp.value = p.ref;
    inp.oninput = () => { const v = +inp.value; if (v > 0) { val.set(p.id, v); el.value = new Map(val); el.dispatchEvent(new Event("input", {bubbles: true})); } };
    filas.push(html`<tr><td>${p.emoji} ${p.nombre}</td><td>${p.unidad}</td><td>${inp} €</td></tr>`);
  }
  const el = html`<details class="cp-precios"><summary>Precios actuales de referencia (puedes cambiarlos por los del supermercado de tu barrio)</summary><table class="uso-tabla">${filas}</table></details>`;
  el.value = new Map(val);
  return el;
}
```

```{ojs}
//| echo: false
viewof nCP = SALA ? Object.assign(html`<span></span>`, {value: null}) : Inputs.range([4, 12], {label: "Número de preguntas", value: 6, step: 1})
viewof desdeCP = SALA ? Object.assign(html`<span></span>`, {value: null}) : Inputs.range([1996, (new Date()).getFullYear() - 3], {label: "Fechas desde el año", value: 2005, step: 1})
viewof abrirCP = SALA ? Object.assign(html`<span></span>`, {value: 0}) : Inputs.button("▶ Abrir concurso", {value: 0, reduce: v => v + 1})
```

```{ojs}
//| echo: false
{
  if (SALA) return html``;
  if (!abrirCP) return html`<div class="conc-intro">
    <p><b>Cómo funciona:</b> en cada pregunta aparece un producto con su <b>precio actual</b> y los estudiantes tienen que adivinar <b>cuánto costaba en una fecha del pasado</b>. Ganan más puntos cuanto más se acerquen: 100 si aciertan el precio exacto y 0 si se equivocan en un 50 % o más. Pulsa «Abrir concurso», proyecta esta pantalla y que los estudiantes escaneen el código QR con el móvil y escriban un <b>alias</b>.</p>
    <p>El precio correcto de la gasolina y el gasóleo es la media del mes en el Boletín Petrolero de la Comisión Europea. Para los demás productos se estima a partir del precio actual de referencia y del índice de precios de ese producto en el IPC de España (Eurostat). Al terminar verás todas las soluciones para comentarlas en clase.</p>
    <p class="nota">Los resultados viajan por un servicio público de mensajería en tiempo real y no se guardan en ningún sitio. Antes de usarlo en clase por primera vez, haz una prueba con tu móvil.</p></div>`;
  // Los ajustes se leen al pulsar el botón: cambiarlos después no reinicia el concurso abierto
  const productosSel = (viewof productosCP).value, precios = (viewof preciosCP).value, n = (viewof nCP).value, desde = (viewof desdeCP).value;
  if (!productosSel.length) return html`<p class="pending">Elige al menos un producto y vuelve a pulsar «Abrir concurso».</p>`;
  const caja = html`<div class="conc-panel"><p class="pending">Preparando las preguntas…</p></div>`;
  (async () => {
    const sala = CP.nuevaSala(), {general} = datosCP;
    const ultimo = d3.min(productosSel.map(p => (p.carbM?.length ? p.carbM : p.serie).at(-1).periodo.slice(0, 7)));
    const sorteo = CP.sortear(productosSel, n, desde, ultimo);
    const soluciones = [];
    const preguntas = sorteo.map(({p, periodo}, i) => {
      const hoy = precios.get(p.id) ?? p.ref, dec = p.carb ? 3 : 2;
      let real;
      if (p.carbM?.length) real = PRECIOS.valorEn(p.carbM, periodo);
      if (!Number.isFinite(real) && p.serie.length) { const iu = p.serie.at(-1).valor, it = PRECIOS.valorEn(p.serie, periodo) ?? p.serie.find(d => d.periodo >= periodo)?.valor; real = hoy * it / iu; }
      if (!Number.isFinite(real) && p.carbM?.length) real = p.carbM.find(d => d.periodo >= periodo)?.valor;
      real = Math.round(real * 10 ** dec) / 10 ** dec;
      const gI = PRECIOS.valorEn(general, periodo), gU = general.at(-1)?.valor;
      const g = gI && gU ? Math.round(1000 * (gU / gI - 1)) / 10 : null;
      soluciones.push({n: i + 1, producto: `${p.emoji} ${p.nombre}`, unidad: p.unidad, fecha: PRECIOS.mesTexto(periodo), hoy, real, dec, g});
      return {e: p.emoji, n: p.nombre, u: p.unidad, hoy, f: PRECIOS.mesTexto(periodo), c: CP.ofuscar(sala, i, real), d: dec, g};
    });
    caja.innerHTML = `<p class="pending">Conectando con el servicio de mensajería…</p>`;
    let cli = null, broker = null;
    for (const b of BROKERS) { try { cli = await conectarBroker(b); broker = b; break; } catch (e) {} }
    if (!cli) { caja.innerHTML = `<p class="pending">❌ No se ha podido conectar con ningún servicio de mensajería. Es posible que la red bloquee estas conexiones: prueba con otra red (por ejemplo, los datos del móvil compartidos).</p>`; return; }
    const publicar = (estado) => cli.publish(temaEstado(sala), JSON.stringify(estado), {retain: true, qos: 1});
    publicar({fase: "espera", preguntas});
    const jug = new Map();
    let fase = "espera";
    cli.subscribe(temaJug(sala), {qos: 1});
    const enlace = `${location.href.split("?")[0].split("#")[0]}?sala=${sala}&b=${broker.id}`;
    caja.innerHTML = "";
    caja.append(html`<div class="conc-cab"><div class="conc-qr"></div><div><p class="asis-et">Escanea el código o entra en</p><p class="conc-url">${enlace.replace(/^https?:\/\//, "")}</p>
        <p class="conc-cuenta">0 participantes</p>
        <div class="graf-botones"><button class="asis-boton conc-empezar">▶ Empezar</button><button class="copiar conc-terminar" disabled>🏁 Terminar</button><button class="copiar conc-full">⛶ Pantalla completa</button></div></div></div>
      <div class="conc-ranking"></div><div class="cp-soluciones"></div>`);
    const $ = (s) => caja.querySelector(s);
    try { const qrlib = await require("qrcode-generator@1.4.4"); const qr = qrlib(0, "M"); qr.addData(enlace); qr.make(); $(".conc-qr").innerHTML = qr.createSvgTag({cellSize: 6, margin: 2, scalable: true}); } catch (e) { $(".conc-qr").textContent = "(no se ha podido crear el QR)"; }
    const N = preguntas.length;
    const pintar = () => {
      const r = CP.ordenar(jug);
      $(".conc-cuenta").textContent = `${jug.size} participante${jug.size === 1 ? "" : "s"}`;
      if (fase === "espera") { $(".conc-ranking").innerHTML = `<div class="conc-alias">${r.map(j => `<span>${j.alias}</span>`).join("")}</div>`; return; }
      const medalla = (i) => fase === "fin" ? ["🥇", "🥈", "🥉"][i] ?? `${i + 1}.` : `${i + 1}.`;
      $(".conc-ranking").innerHTML = `${fase === "fin" ? `<h2 class="conc-podio">🏆 ${r[0] ? r[0].alias : ""}</h2>` : ""}<table class="uso-tabla conc-tabla"><tr><th></th><th>Alias</th><th>Puntos</th><th>Pregunta</th><th>Tiempo</th></tr>` +
        r.slice(0, 15).map((j, i) => `<tr class="${i < 3 && fase === "fin" ? "conc-top" : ""}"><td>${medalla(i)}</td><td>${j.alias}</td><td><b>${j.puntos}</b> / ${100 * N}</td><td>${j.fin ? "✔ terminado" : `${j.resp ?? 0} / ${N}`}</td><td>${j.tiempo ? CP.segundos(j.tiempo) : "–"}</td></tr>`).join("") + "</table>";
    };
    cli.on("message", (t, m) => { try { const d = JSON.parse(m.toString()); if (!d.id || !d.alias) return; const prev = jug.get(d.id) ?? {puntos: 0, resp: 0, tiempo: 0};
      jug.set(d.id, {...prev, ...d, puntos: Math.min(100 * N, Math.max(0, +d.puntos || 0)), alias: String(d.alias).slice(0, 20).replace(/[<>&"]/g, "")}); pintar(); } catch (e) {} });
    $(".conc-empezar").onclick = () => { fase = "juego"; publicar({fase: "juego", preguntas, inicio: Date.now()}); $(".conc-empezar").disabled = true; $(".conc-terminar").disabled = false; pintar();
      window.cceeEvento && window.cceeEvento("concurso-precios/empezar", "¿Cuánto costaba?", true); };
    $(".conc-terminar").onclick = () => { fase = "fin"; const r = CP.ordenar(jug).slice(0, 10).map(j => ({alias: j.alias, puntos: j.puntos, tiempo: j.tiempo}));
      publicar({fase: "fin", preguntas, ranking: r}); $(".conc-terminar").disabled = true; pintar();
      $(".cp-soluciones").innerHTML = `<h3>Soluciones</h3><table class="uso-tabla"><tr><th>#</th><th>Producto</th><th>Precio actual</th><th>Fecha</th><th>Precio entonces</th><th>Variación del producto</th><th>Variación del IPC general</th></tr>` +
        soluciones.map(s => `<tr><td>${s.n}</td><td>${s.producto} <span class="kpi-s">(${s.unidad})</span></td><td>${PRECIOS.euros(s.hoy, s.dec)}</td><td>${s.fecha}</td><td><b>${PRECIOS.euros(s.real, s.dec)}</b></td><td>${PRECIOS.pct(100 * (s.hoy / s.real - 1))}</td><td>${s.g == null ? "–" : PRECIOS.pct(s.g)}</td></tr>`).join("") + "</table>";
      caja.append(DOM.download(() => new Blob([csv(CP.ordenar(jug).map((j, i) => ({puesto: i + 1, alias: j.alias, puntos: j.puntos, maximo: 100 * N, tiempo_segundos: Math.round(j.tiempo / 100) / 10, terminado: j.fin ? "sí" : "no"})))], {type: "text/csv"}), `cuanto_costaba_${sala}.csv`, "⬇ Descargar los resultados (CSV)")); };
    $(".conc-full").onclick = () => document.fullscreenElement ? document.exitFullscreen() : caja.requestFullscreen?.();
    invalidation.then(() => { try { cli.end(true); } catch (e) {} });
    pintar();
  })();
  return caja;
}
```

```{ojs}
//| echo: false
// ============================ MÓVIL DEL ESTUDIANTE ============================
{
  if (!SALA) return html``;
  const broker = BROKERS.find(b => b.id === paramsP.get("b")) ?? BROKERS[0];
  const caja = html`<div class="conc-movil"><p class="pending">Conectando con el concurso…</p></div>`;
  (async () => {
    let cli;
    try { cli = await conectarBroker(broker); } catch (e) { caja.innerHTML = `<p class="pending">❌ No se ha podido conectar. Comprueba la conexión a internet (si estás en la wifi de la universidad, prueba con los datos del móvil) y recarga la página.</p>`; return; }
    let id; try { id = localStorage.getItem(`ccee-cp-${SALA}`) || crypto.randomUUID(); localStorage.setItem(`ccee-cp-${SALA}`, id); } catch (e) { id = crypto.randomUUID(); }
    let alias = ""; try { alias = localStorage.getItem("ccee-conc-alias") || ""; } catch (e) {}
    let estado = null, unido = false, i = 0, puntos = 0, t0 = null, jugando = false;
    const enviar = (extra) => cli.publish(temaJug(SALA), JSON.stringify({id, alias, puntos, resp: i, tiempo: t0 ? Date.now() - t0 : 0, ...extra}), {qos: 1});
    const eur = (v, d) => PRECIOS.euros(v, d);
    const pantalla = () => {
      caja.innerHTML = "";
      if (!unido) {
        const f = html`<form class="asis-caja"><label class="asis-et">Tu alias para el ranking</label><input type="text" name="alias" required maxlength="20" autocomplete="off" placeholder="p. ej. Analista_7"><button class="asis-boton">Entrar al concurso</button><p class="asis-nota">No escribas tu nombre real si no quieres que aparezca en la pantalla de clase.</p></form>`;
        f.alias.value = alias;
        f.onsubmit = (e) => { e.preventDefault(); alias = f.alias.value.trim().slice(0, 20).replace(/[<>&"]/g, ""); if (!alias) return; try { localStorage.setItem("ccee-conc-alias", alias); } catch (err) {} unido = true; enviar({fin: false}); pantalla(); };
        caja.append(f); return;
      }
      if (!estado || estado.fase === "espera") { caja.append(html`<div class="asis-caja conc-espera"><p class="juego-grande">⏳</p><p>Hola, <b>${alias}</b>. Espera a que el profesor empiece el concurso…</p></div>`); return; }
      const P = estado.preguntas;
      if (estado.fase === "fin" || i >= P.length) {
        const pos = estado.ranking ? estado.ranking.findIndex(r => r.alias === alias) : -1;
        caja.append(html`<div class="asis-caja conc-espera"><p class="juego-grande">${puntos} puntos</p><p>de ${100 * P.length} posibles · Tiempo: <b>${CP.segundos(t0 ? Date.now() - t0 : 0)}</b></p>
          ${estado.fase === "fin" ? html`<p>${pos >= 0 ? html`Has quedado en el puesto <b>${pos + 1}</b> ${["🥇", "🥈", "🥉"][pos] ?? ""}` : "Mira el ranking en la pantalla de clase."}</p>` : html`<p>¡Terminado! Mira el ranking en la pantalla de clase.</p>`}</div>`);
        return;
      }
      if (!t0) t0 = Date.now();
      const q = P[i], real = CP.desofuscar(SALA, i, q.c);
      const f = html`<form class="asis-caja cp-pregunta"><p class="juego-ind">Pregunta ${i + 1} de ${P.length} · ${puntos} puntos</p>
        <p class="cp-emoji">${q.e}</p><p class="cp-prod"><b>${q.n}</b> <span>(${q.u})</span></p>
        <p>Hoy cuesta <b>${eur(q.hoy, q.d)}</b></p>
        <label class="asis-et">¿Cuánto costaba en ${q.f}?</label>
        <input type="text" name="r" inputmode="decimal" autocomplete="off" placeholder="Precio en euros, p. ej. ${locES.format(",.2f")(q.hoy * 0.8)}">
        <button class="asis-boton">Responder</button><div class="cp-fb"></div></form>`;
      f.onsubmit = (e) => {
        e.preventDefault();
        if (!jugando) return;
        const r = CP.leer(f.r.value);
        if (!Number.isFinite(r)) { f.querySelector(".cp-fb").innerHTML = `<p class="asis-nota">Escribe un precio, por ejemplo 1,25.</p>`; return; }
        jugando = false;
        const pts = CP.puntos(r, real); puntos += pts; i++; enviar({fin: i >= P.length});
        f.r.disabled = true; f.querySelector("button").remove();
        const err = 100 * (r / real - 1);
        const fb = html`<div class="cp-sol ${pts >= 70 ? "ok" : pts > 0 ? "medio" : "ko"}"><p>Costaba <b>${eur(real, q.d)}</b>. Tu respuesta: ${eur(r, q.d)} (${PRECIOS.pct(err)}).</p><p class="juego-grande">+${pts}</p>
          <p class="asis-nota">Desde entonces, este producto ha subido un ${PRECIOS.pct(100 * (q.hoy / real - 1))}${q.g == null ? "" : ` y el IPC general un ${PRECIOS.pct(q.g)}`}.</p></div>`;
        const sig = html`<button type="button" class="asis-boton">${i >= P.length ? "Ver mi resultado" : "Siguiente ▶"}</button>`;
        sig.onclick = () => pantalla();
        f.querySelector(".cp-fb").append(fb, sig);
      };
      jugando = true;
      caja.append(f);
      f.r.focus();
    };
    cli.subscribe(temaEstado(SALA), {qos: 1});
    cli.on("message", (t, m) => { try { const d = JSON.parse(m.toString()); const antes = estado?.fase; estado = d; if (antes !== d.fase) pantalla(); } catch (e) {} });
    invalidation.then(() => { try { cli.end(true); } catch (e) {} });
    pantalla();
  })();
  return caja;
}
```
''')
print("Listo")
