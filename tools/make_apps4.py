"""Genera la cuarta tanda de recursos de CCEEscopio (noviembre de 2026):
piramides.qmd (pirámides de población de países, regiones y provincias), calculadoras.qmd (portada de las calculadoras),
regresion.qmd (regresión con análisis de supuestos) y estadistica.qmd (análisis cuantitativo de datos).
Uso: python3 tools/make_apps4.py"""
import json, re

HELPERS = open("_helpers.qmd", encoding="utf-8").read().strip()
SPECS = json.load(open("data/indicadores_specs.json", encoding="utf-8"))
EST = "\n".join("  " + l for l in open("tools/estadistica.js", encoding="utf-8").read().splitlines() if not l.startswith("if (typeof module"))
AREAS = {"precios": "Precios e inflación", "empleo": "Mercado laboral", "actividad": "Actividad económica y coyuntura",
         "empresa": "Empresa, innovación y digitalización", "turismo": "Turismo", "publico": "Sector público y mercados financieros",
         "desigualdad": "Desigualdad, pobreza y condiciones de vida", "sostenibilidad": "Energía y sostenibilidad",
         "poblacion": "Población, educación y salud", "internacional": "Economía internacional y sector exterior"}
unicos, vistos = [], set()
for k, lst in SPECS.items():
    if k == "andalucia":
        continue
    for i in lst:
        if i["id"] not in vistos:
            vistos.add(i["id"]); unicos.append(dict(i, pagina=k))

def J(x):
    return json.dumps(x, ensure_ascii=False)

def pagina(nombre, texto, **rep):
    rep.setdefault("HELPERS", HELPERS)
    for k, v in rep.items():
        texto = texto.replace(f"__{k}__", v)
    assert not re.search(r"__[A-Z0-9]+__", texto), f"marcador sin sustituir en {nombre}"
    open(nombre, "w", encoding="utf-8").write(texto)
    print("  ", nombre)

# =====================================================================================
# Pirámides de población
# =====================================================================================
pagina("piramides.qmd", r'''---
title: "Pirámides de población"
subtitle: "Países de Europa, comunidades autónomas y provincias, desde el año 2000 hasta el último dato"
toc: false
---

Elige un territorio y un año. Puedes **animar** la pirámide para ver cómo envejece la población, y **compararla** con otro año o con otro territorio (silueta negra). Debajo tienes los principales indicadores demográficos. Fuente: Eurostat, población a 1 de enero por sexo y grupos de edad de cinco años.

__HELPERS__

```{ojs}
//| echo: false
TABLAS_PIR = ["demo_r_pjangroup", "demo_pjangroup"]
territoriosPir = {
  for (const t of TABLAS_PIR) {
    try {
      const r = await eurostat(t, "&sex=T&age=TOTAL&unit=NR&lastTimePeriod=1");
      if (r.length) return [...new Map(r.map(x => [x.geo, {code: x.geo, label: nombresGeo[x.geo] ?? x.geoLabel}])).values()];
    } catch (e) {}
  }
  return [];
}
paisesPir = territoriosPir.filter(t => t.code.length === 2 || ["EU27_2020", "EA20"].includes(t.code)).sort((a, b) => a.label.localeCompare(b.label, "es"))
NIVELES = new Map([["El país completo", 2], ["Comunidades autónomas / regiones (NUTS 2)", 4], ["Provincias (NUTS 3)", 5], ["Grandes regiones (NUTS 1)", 3]])
viewof paisPir = Inputs.select(new Map(paisesPir.map(t => [t.label, t.code])), {label: "País", value: "ES"})
viewof nivelPir = Inputs.select(NIVELES, {label: "Nivel", value: paisPir === "ES" ? 4 : 2})
```

```{ojs}
//| echo: false
opcionesPir = nivelPir === 2 ? territoriosPir.filter(t => t.code === paisPir) : territoriosPir.filter(t => t.code.startsWith(paisPir) && t.code.length === nivelPir && !/Z+$/.test(t.code)).sort((a, b) => a.label.localeCompare(b.label, "es"))
viewof geoPir = Inputs.select(new Map(opcionesPir.map(t => [`${t.label} (${t.code})`, t.code])), {label: "Territorio", value: opcionesPir.find(t => t.code === "ES61")?.code ?? opcionesPir[0]?.code})
viewof modoPir = Inputs.radio(new Map([["Porcentaje de la población", "pct"], ["Número de personas", "abs"]]), {label: "Escala", value: "pct"})
viewof compPir = Inputs.radio(new Map([["Sin comparar", "no"], ["Con otro año", "anio"], ["Con otro territorio", "geo"]]), {label: "Comparar", value: "anio"})
```

```{ojs}
//| echo: false
// Lee la población por sexo y grupos de edad de un territorio (todos los años)
parseEdad = (c) => { let m; if (c === "Y_LT5") return [0, 5]; if ((m = /^Y(\d+)-(\d+)$/.exec(c))) return [+m[1], +m[2] + 1]; if ((m = /^Y_GE(\d+)$/.exec(c))) return [+m[1], Infinity]; if ((m = /^Y_LT(\d+)$/.exec(c))) return [0, +m[1]]; return null; }
// Elige grupos de edad que no se solapen (los más detallados disponibles)
particion = (codigos) => {
  const iv = codigos.map(c => ({c, r: parseEdad(c)})).filter(x => x.r);
  const out = []; let pos = 0;
  while (true) {
    const cand = iv.filter(x => x.r[0] === pos).sort((a, b) => a.r[1] - b.r[1]);
    if (!cand.length) break;
    out.push(cand[0]); if (cand[0].r[1] === Infinity) break; pos = cand[0].r[1];
  }
  return out;
}
cargarPir = async (geo) => {
  for (const t of TABLAS_PIR) {
    try {
      const r = await eurostat(t, `&sex=M&sex=F&unit=NR&geo=${geo}`);
      if (!r.length) continue;
      const porAnio = d3.group(r, x => +x.time);
      const res = new Map();
      for (const [y, rs] of porAnio) {
        const cods = [...new Set(rs.map(x => x.age))].filter(c => rs.some(x => x.age === c && x.sex === "M") && rs.some(x => x.age === c && x.sex === "F"));
        const p = particion(cods); if (p.length < 8) continue;
        res.set(y, p.map(({c, r: [lo, hi]}) => ({lo, hi, label: hi === Infinity ? `${lo}+` : `${lo}-${hi - 1}`, H: rs.find(x => x.age === c && x.sex === "M")?.value ?? 0, M: rs.find(x => x.age === c && x.sex === "F")?.value ?? 0})));
      }
      if (res.size) return {tabla: t, anios: res};
    } catch (e) {}
  }
  return null;
}
pirA = cargarPir(geoPir)
```

```{ojs}
//| echo: false
aniosPir = pirA ? [...pirA.anios.keys()].sort((a, b) => a - b) : []
viewof anioPir = Inputs.range(aniosPir.length ? [aniosPir[0], aniosPir.at(-1)] : [2000, 2025], {label: "Año", step: 1, value: aniosPir.at(-1) ?? 2025})
{
  const b = html`<button class="copiar">▶ Animar desde ${aniosPir[0] ?? ""}</button>`;
  let timer = null;
  b.onclick = () => {
    if (timer) { clearInterval(timer); timer = null; b.textContent = `▶ Animar desde ${aniosPir[0]}`; return; }
    let i = 0; b.textContent = "⏸ Parar";
    timer = setInterval(() => {
      if (i >= aniosPir.length) { clearInterval(timer); timer = null; b.textContent = `▶ Animar desde ${aniosPir[0]}`; return; }
      const el = viewof anioPir; el.value = aniosPir[i++]; el.dispatchEvent(new Event("input", {bubbles: true}));
    }, 450);
  };
  invalidation.then(() => clearInterval(timer));
  return b;
}
```

```{ojs}
//| echo: false
viewof anioComp = compPir === "anio" ? Inputs.select(aniosPir, {label: "Año para comparar", value: aniosPir[0]}) : Object.assign(html`<span></span>`, {value: null})
viewof geoComp = compPir === "geo" ? Inputs.select(new Map([...paisesPir, ...territoriosPir.filter(t => t.code.startsWith(paisPir) && t.code.length > 2)].map(t => [`${t.label} (${t.code})`, t.code])), {label: "Territorio para comparar", value: paisPir}) : Object.assign(html`<span></span>`, {value: null})
pirB = compPir === "geo" && geoComp ? cargarPir(geoComp) : null
```

```{ojs}
//| echo: false
indicadoresPir = (g) => {
  const tot = d3.sum(g, x => x.H + x.M), suma = (f) => d3.sum(g.filter(f), x => x.H + x.M);
  const j = suma(x => x.hi <= 15), a = suma(x => x.lo >= 15 && x.hi <= 65), v = suma(x => x.lo >= 65), v80 = suma(x => x.lo >= 80);
  const mid = (x) => x.hi === Infinity ? x.lo + 5 : (x.lo + x.hi) / 2;
  let acum = 0, mediana = NaN;
  for (const x of g) { const n = x.H + x.M; if (acum + n >= tot / 2) { mediana = x.lo + (x.hi === Infinity ? 10 : x.hi - x.lo) * (tot / 2 - acum) / n; break; } acum += n; }
  return {total: tot, hombres: d3.sum(g, x => x.H), mujeres: d3.sum(g, x => x.M), j: 100 * j / tot, a: 100 * a / tot, v: 100 * v / tot, v80: 100 * v80 / tot,
    dependencia: 100 * (j + v) / a, envejecimiento: 100 * v / j, media: d3.sum(g, x => mid(x) * (x.H + x.M)) / tot, mediana, masculinidad: 100 * d3.sum(g, x => x.H) / d3.sum(g, x => x.M)};
}
armonizar = (g1, g2) => {
  // Si una pirámide tiene el último grupo abierto antes que la otra, se agrupan las edades altas igual en las dos
  const corte = Math.min(...[g1, g2].filter(Boolean).map(g => g.at(-1).lo));
  const ajusta = (g) => { if (!g) return g; const base = g.filter(x => x.lo < corte), alto = g.filter(x => x.lo >= corte);
    return [...base, {lo: corte, hi: Infinity, label: `${corte}+`, H: d3.sum(alto, x => x.H), M: d3.sum(alto, x => x.M)}]; };
  return [ajusta(g1), ajusta(g2)];
}
{
  if (!pirA) return html`<p class="pending">No se han podido cargar los datos de Eurostat para este territorio.</p>`;
  const nombre = (c) => territoriosPir.find(t => t.code === c)?.label ?? c;
  let gA = pirA.anios.get(anioPir) ?? pirA.anios.get(aniosPir.at(-1)), gB = null, etqB = "";
  if (compPir === "anio" && anioComp && anioComp !== anioPir) { gB = pirA.anios.get(anioComp); etqB = `${nombre(geoPir)}, ${anioComp}`; }
  if (compPir === "geo" && pirB) { gB = pirB.anios.get(anioPir) ?? pirB.anios.get([...pirB.anios.keys()].sort().at(-1)); etqB = `${nombre(geoComp)}, ${pirB.anios.has(anioPir) ? anioPir : [...pirB.anios.keys()].sort().at(-1)}`; }
  [gA, gB] = armonizar(gA, gB);
  const filas = (g, signo = 1) => { const tot = d3.sum(g, x => x.H + x.M); const k = modoPir === "pct" ? 100 / tot : 1;
    return g.flatMap(x => [{label: x.label, sexo: "Hombres", v: -x.H * k}, {label: x.label, sexo: "Mujeres", v: x.M * k}]); };
  const fA = filas(gA), fB = gB ? filas(gB) : [];
  const etiquetas = gA.map(x => x.label).reverse();
  const maxV = d3.max([...fA, ...fB], r => Math.abs(r.v));
  const fmtEje = (v) => modoPir === "pct" ? `${locES.format(",.1~f")(Math.abs(v))} %` : locES.format(",.0f")(Math.abs(v));
  const iA = indicadoresPir(gA), iB = gB ? indicadoresPir(gB) : null;
  window.cceeEvento && window.cceeEvento("piramides/ver", "Pirámides de población", false);
  const fila = (t, k, u = "", d = 1) => html`<tr><td>${t}</td><td><b>${k === "total" || k === "hombres" || k === "mujeres" ? locES.format(",.0f")(iA[k]) : locES.format(`,.${d}f`)(iA[k]) + u}</b></td>${iB ? html`<td>${k === "total" || k === "hombres" || k === "mujeres" ? locES.format(",.0f")(iB[k]) : locES.format(`,.${d}f`)(iB[k]) + u}</td>` : ""}</tr>`;
  return html`<div class="pir-cab"><h3>${nombre(geoPir)} · ${pirA.anios.has(anioPir) ? anioPir : aniosPir.at(-1)}</h3>${gB ? html`<p class="nota">Silueta negra: ${etqB}</p>` : ""}</div>
    ${Plot.plot({height: 30 + 22 * etiquetas.length, width: Math.min(900, width), marginLeft: 60,
      x: {domain: [-maxV * 1.08, maxV * 1.08], tickFormat: fmtEje, label: modoPir === "pct" ? "% de la población total" : "Personas", grid: true},
      y: {domain: etiquetas, label: "Edad"},
      color: {domain: ["Hombres", "Mujeres"], range: ["#2C6FBB", "#A6195E"], legend: true},
      marks: [Plot.barX(fA, {y: "label", x: "v", fill: "sexo", fillOpacity: 0.85, title: r => `${r.sexo}, ${r.label} años: ${fmtEje(r.v)}`}),
        ...(gB ? [Plot.barX(fB, {y: "label", x: "v", fill: "none", stroke: "#111", strokeWidth: 1.4})] : []),
        Plot.ruleX([0], {stroke: "#333"}),
        Plot.text([{x: -maxV * 0.95, t: "Hombres"}, {x: maxV * 0.95, t: "Mujeres"}], {x: "x", y: etiquetas[0], text: "t", fontWeight: 700, fontSize: 13, dy: -4})]})}
    <h3>Indicadores demográficos</h3>
    <table class="uso-tabla"><tr><th>Indicador</th><th>${nombre(geoPir)}</th>${iB ? html`<th>${etqB}</th>` : ""}</tr>
      ${fila("Población total", "total")}${fila("Hombres", "hombres")}${fila("Mujeres", "mujeres")}
      ${fila("Menores de 15 años", "j", " %")}${fila("De 15 a 64 años", "a", " %")}${fila("De 65 años o más", "v", " %")}${fila("De 80 años o más", "v80", " %")}
      ${fila("Índice de dependencia (menores de 15 y mayores de 64 por cada 100 de 15 a 64)", "dependencia")}
      ${fila("Índice de envejecimiento (mayores de 64 por cada 100 menores de 15)", "envejecimiento")}
      ${fila("Edad media (aprox.)", "media", " años")}${fila("Edad mediana (aprox.)", "mediana", " años")}
      ${fila("Hombres por cada 100 mujeres", "masculinidad")}</table>
    <p class="nota">Edad media y mediana aproximadas a partir de grupos de cinco años. Fuente: Eurostat (${pirA.tabla}).</p>
    ${DOM.download(() => new Blob([csv(gA.map(x => ({territorio: nombre(geoPir), anio: anioPir, edad: x.label, hombres: x.H, mujeres: x.M})))], {type: "text/csv"}), `piramide_${geoPir}_${anioPir}.csv`, "⬇ Descargar los datos (CSV)")}`;
}
```

## Evolución del envejecimiento

```{ojs}
//| echo: false
{
  if (!pirA) return html``;
  const serie = aniosPir.map(y => ({anio: y, ...indicadoresPir(pirA.anios.get(y))}));
  const largo = serie.flatMap(s => [{anio: s.anio, ind: "Menores de 15 años (%)", v: s.j}, {anio: s.anio, ind: "65 años o más (%)", v: s.v}, {anio: s.anio, ind: "80 años o más (%)", v: s.v80}]);
  return Plot.plot({height: 280, marginLeft: 45, x: {label: null, tickFormat: d => String(d)}, y: {grid: true, label: "% de la población"},
    color: {legend: true, range: ["#2C6FBB", "#A6195E", "#E6A400"]},
    marks: [Plot.line(largo, {x: "anio", y: "v", stroke: "ind", strokeWidth: 2.2}), Plot.ruleX([anioPir], {stroke: "#999", strokeDasharray: "4,3"}),
      Plot.tip(largo, Plot.pointer({x: "anio", y: "v", title: d => `${d.ind}, ${d.anio}: ${locES.format(",.1f")(d.v)}`}))]});
}
```
''')

# =====================================================================================
# Bloque común de datos para las calculadoras de Métodos Cuantitativos (series de la web o datos propios)
# =====================================================================================
DATOS = r'''```{ojs}
//| echo: false
EST = {
__EST__
  return crearEstadistica();
}
especW = __ESPECS__
FREQ_ORDEN = ({Mensual: 1, Trimestral: 2, Semestral: 3, Anual: 4})
POR_ANIO = ({Mensual: 12, Trimestral: 4, Semestral: 2, Anual: 1})
// Lee un número escrito a la española o a la inglesa
numero = (s) => {
  if (typeof s === "number") return s;
  let t = String(s ?? "").trim().replace(/\s|%|€/g, "");
  if (!t) return NaN;
  if (t.includes(",") && t.includes(".")) t = t.lastIndexOf(",") > t.lastIndexOf(".") ? t.replace(/\./g, "").replace(",", ".") : t.replace(/,/g, "");
  else if (t.includes(",")) t = t.replace(",", ".");
  return /^[-+]?(\d+\.?\d*|\.\d+)(e[-+]?\d+)?$/i.test(t) ? +t : NaN;
}
// Convierte texto pegado (de Excel, CSV…) en una tabla con columnas
parsearTexto = (txt) => {
  const lineas = String(txt ?? "").split(/\r?\n/).map(l => l.trimEnd()).filter(l => l.trim());
  if (!lineas.length) return {cols: [], filas: []};
  const sep = ["\t", ";", ","].map(s => [s, lineas.slice(0, 10).map(l => l.split(s).length - 1)]).find(([s, c]) => c[0] > 0 && c.every(x => x === c[0]))?.[0] ?? (lineas[0].includes("\t") ? "\t" : lineas[0].includes(";") ? ";" : /\s/.test(lineas[0].trim()) ? /\s+/ : ",");
  const celdas = lineas.map(l => l.split(sep).map(c => c.trim().replace(/^"|"$/g, "")));
  const cabecera = celdas[0].some(c => !Number.isFinite(numero(c)));
  const nc = d3.max(celdas, f => f.length);
  const cols = cabecera ? Array.from({length: nc}, (_, i) => celdas[0][i] || `Columna ${i + 1}`) : Array.from({length: nc}, (_, i) => `Variable ${i + 1}`);
  const filas = (cabecera ? celdas.slice(1) : celdas).map(f => Object.fromEntries(cols.map((c, i) => [c, f[i] ?? ""])));
  return {cols, filas};
}
leerFichero = async (f) => {
  if (!f) return null;
  if (/\.xlsx?$/i.test(f.name)) { const wb = await f.xlsx(); const filas = wb.sheet(0, {headers: true}); return {cols: filas.columns ?? Object.keys(filas[0] ?? {}), filas}; }
  return parsearTexto(await f.text());
}
// Separa columnas numéricas y una posible columna de etiquetas (fechas, nombres…)
prepararTabla = (t) => {
  if (!t || !t.filas.length) return null;
  const numericas = t.cols.filter(c => t.filas.filter(f => Number.isFinite(numero(f[c]))).length >= Math.max(3, 0.8 * t.filas.filter(f => String(f[c] ?? "").trim() !== "").length));
  // Columna de etiquetas: la primera no numérica, o una columna de años/fechas aunque sea numérica
  const esTiempo = (c) => /^(a[ñn]o|anio|year|fecha|periodo|período|mes|trimestre|date)s?\b/i.test(c.trim()) ||
    (() => { const v = t.filas.map(f => numero(f[c])); return v.length > 2 && v.every(x => Number.isInteger(x) && x >= 1900 && x <= 2100) && v.every((x, i) => !i || x > v[i - 1]); })();
  let etiqueta = t.cols.find(c => !numericas.includes(c)) ?? t.cols.find(esTiempo);
  if (etiqueta && numericas.includes(etiqueta) && numericas.length > 1) numericas.splice(numericas.indexOf(etiqueta), 1);
  else if (etiqueta && numericas.includes(etiqueta)) etiqueta = undefined;
  return {numericas, etiqueta, filas: t.filas.map((f, i) => ({etq: etiqueta ? String(f[etiqueta]) : String(i + 1), ...Object.fromEntries(numericas.map(c => [c, numero(f[c])]))}))};
}
clavePer = (f, freq) => freq === "Anual" ? `${f.getFullYear()}` : freq === "Semestral" ? `${f.getFullYear()}-S${f.getMonth() < 6 ? 1 : 2}` : freq === "Trimestral" ? `${f.getFullYear()}-T${Math.floor(f.getMonth() / 3) + 1}` : `${f.getFullYear()}-${String(f.getMonth() + 1).padStart(2, "0")}`
TRANSF = new Map([["Niveles (el dato tal cual)", "nivel"], ["Variación interanual (%)", "tva"], ["Diferencia interanual (puntos)", "dif"], ["Primeras diferencias", "d1"]])
// Descarga varias series de la web, las lleva a la misma frecuencia y las une por periodo
alinearSeries = async (series, transf) => {
  const datos = await Promise.all(series.map(s => cargar(s.spec)));
  const freq = series.map(s => s.spec.frecuencia).sort((a, b) => FREQ_ORDEN[b] - FREQ_ORDEN[a])[0];
  const n = POR_ANIO[freq] ?? 1;
  const avisos = [];
  const cols = series.map((s, i) => {
    const d = datos[i];
    if (!d.ok) { avisos.push(`${s.nombre}: no se han podido cargar los datos.`); return new Map(); }
    const filas = d.rows.filter(r => s.spec.sinGeo || r.territorio === s.territorio);
    if (!filas.length) avisos.push(`${s.nombre}: no hay datos para ${s.territorio}.`);
    let m = [...d3.rollup(filas, v => ({v: d3.mean(v, r => r.valor), f: v[0].fecha}), r => clavePer(r.fecha, freq))].map(([k, o]) => ({k, ...o})).sort((a, b) => a.f - b.f);
    if (transf !== "nivel") {
      const lag = transf === "d1" ? 1 : n, idx = new Map(m.map((o, j) => [o.k, j]));
      m = m.map((o, j) => { const a = m[j - lag]; if (!a) return null;
        const v = transf === "tva" ? (a.v ? 100 * (o.v / a.v - 1) : NaN) : o.v - a.v; return {...o, v}; }).filter(o => o && Number.isFinite(o.v));
    }
    return new Map(m.map(o => [o.k, o]));
  });
  const claves = [...new Set(cols.flatMap(c => [...c.keys()]))].sort();
  const filas = claves.filter(k => cols.every(c => c.has(k))).map(k => ({etq: k, fecha: cols[0].get(k).f, ...Object.fromEntries(series.map((s, i) => [s.nombre, cols[i].get(k).v]))}));
  return {filas, numericas: series.map(s => s.nombre), etiqueta: "Periodo", freq, avisos, fuente: [...new Set(datos.filter(d => d.ok).map(d => d.code))].join(", ")};
}
territoriosW = [...new Set(Object.values(nombresGeo))].sort((a, b) => a.localeCompare(b, "es"))
f4 = (x) => Number.isFinite(x) ? (Math.abs(x) >= 1e4 || (Math.abs(x) < 1e-3 && x !== 0) ? x.toExponential(3).replace(".", ",") : locES.format(",.4~f")(x)) : "–"
fp = (p) => !Number.isFinite(p) ? "–" : p < 0.0001 ? "< 0,0001" : locES.format(",.4f")(p)
```'''

ENTRADA = r'''```{ojs}
//| echo: false
viewof fuente__P__ = Inputs.radio(new Map([["Indicadores de CCEEscopio", "web"], ["Mis datos (pegar o subir un fichero)", "propios"]]), {label: "Datos", value: "web"})
```

```{ojs}
//| echo: false
viewof texto__P__ = fuente__P__ === "propios" ? Inputs.textarea({label: "Pega aquí tus datos (con una fila de títulos; copia y pega desde Excel)", rows: 8, width: 560, placeholder: "Año;Ventas;Publicidad\n2019;120;15\n2020;98;12\n…", value: __EJEMPLO__}) : Object.assign(html`<span></span>`, {value: ""})
viewof fichero__P__ = fuente__P__ === "propios" ? Inputs.file({label: "…o sube un fichero", accept: ".csv,.txt,.xlsx"}) : Object.assign(html`<span></span>`, {value: null})
```
'''

EJ_REG = J("Año;Ventas (miles €);Publicidad (miles €);Precio (€)\n2012;410;32;9,5\n2013;432;35;9,6\n2014;455;37;9,4\n2015;470;40;9,8\n2016;498;44;9,7\n2017;511;45;10,1\n2018;540;49;10,0\n2019;552;50;10,4\n2020;480;41;10,2\n2021;530;47;10,6\n2022;575;53;10,9\n2023;590;56;11,3\n2024;612;58;11,2\n2025;640;62;11,5")

# =====================================================================================
# Regresión con análisis de supuestos
# =====================================================================================
pagina("regresion.qmd", r'''---
title: "Regresión lineal con análisis de supuestos"
subtitle: "Estima una regresión por mínimos cuadrados ordinarios con series de CCEEscopio o con tus datos, y comprueba si se cumplen los supuestos"
toc: true
toc-depth: 2
---

Elige una **variable dependiente (Y)** y hasta **cuatro variables explicativas (X)**, de los indicadores de CCEEscopio o de tus propios datos. La calculadora estima el modelo $Y = \beta_0 + \beta_1 X_1 + \dots + \beta_k X_k + u$, interpreta los coeficientes y contrasta los supuestos básicos: **linealidad, normalidad, homocedasticidad, ausencia de autocorrelación y de multicolinealidad**.

__HELPERS__

__DATOS__

__ENTRADA__

```{ojs}
//| echo: false
viewof yW = fuenteR === "web" ? Inputs.select(new Map(especW.map(s => [`${s.nombre} (${s.frecuencia})`, s])), {label: "Variable dependiente (Y)", value: especW.find(s => s.id === "tasa-de-paro"), width: 520}) : Object.assign(html`<span></span>`, {value: null})
viewof xW = fuenteR === "web" ? Inputs.select(new Map(especW.map(s => [`${s.nombre} (${s.frecuencia})`, s])), {label: "Variables explicativas (X) · Ctrl o ⌘ para varias", multiple: true, size: 8, value: [especW.find(s => s.id === "pib-crecimiento-interanual-trimestral")].filter(Boolean), width: 520}) : Object.assign(html`<span></span>`, {value: []})
viewof geoW = fuenteR === "web" ? Inputs.select(territoriosW, {label: "Territorio", value: "España"}) : Object.assign(html`<span></span>`, {value: null})
viewof transfW = fuenteR === "web" ? Inputs.select(TRANSF, {label: "Transformación de las series", value: "nivel"}) : Object.assign(html`<span></span>`, {value: "nivel"})
viewof desdeW = fuenteR === "web" ? Inputs.range([2000, new Date().getFullYear() - 2], {label: "Desde el año", value: 2005, step: 1}) : Object.assign(html`<span></span>`, {value: 1900})
```

```{ojs}
//| echo: false
tablaR = {
  if (fuenteR === "web") {
    if (!yW || !xW.length) return {error: "Elige la variable dependiente y al menos una variable explicativa."};
    const xs = xW.filter(s => s.id !== yW.id).slice(0, 4);
    const r = await alinearSeries([yW, ...xs].map(s => ({spec: s, nombre: s.nombre, territorio: geoW})), transfW);
    r.filas = r.filas.filter(f => !f.fecha || f.fecha.getFullYear() >= desdeW);
    return {...r, y: yW.nombre, xs: xs.map(s => s.nombre), temporal: true};
  }
  const t = prepararTabla(ficheroR ? await leerFichero(ficheroR) : parsearTexto(textoR));
  if (!t || t.numericas.length < 2) return {error: "Necesito al menos dos columnas numéricas (una para Y y otra para X)."};
  return {...t, temporal: !!t.etiqueta && /año|ano|fecha|periodo|year|mes|trim/i.test(t.etiqueta)};
}
```

```{ojs}
//| echo: false
viewof yP = fuenteR === "propios" && tablaR?.numericas ? Inputs.select(tablaR.numericas, {label: "Variable dependiente (Y)", value: tablaR.numericas[0]}) : Object.assign(html`<span></span>`, {value: null})
viewof xP = fuenteR === "propios" && tablaR?.numericas ? Inputs.checkbox(tablaR.numericas.filter(c => c !== yP), {label: "Variables explicativas (X)", value: tablaR.numericas.filter(c => c !== yP).slice(0, 1)}) : Object.assign(html`<span></span>`, {value: []})
viewof tendR = Inputs.toggle({label: "Añadir una tendencia temporal (t = 1, 2, 3…)", value: false})
```

```{ojs}
//| echo: false
modeloR = {
  if (!tablaR || tablaR.error) return {error: tablaR?.error ?? ""};
  const yN = fuenteR === "web" ? tablaR.y : yP, xN = [...(fuenteR === "web" ? tablaR.xs : xP).slice(0, 4)];
  if (!yN || !xN.length) return {error: "Elige al menos una variable explicativa."};
  const filas = tablaR.filas.filter(f => [yN, ...xN].every(c => Number.isFinite(f[c])));
  const nombresX = tendR ? [...xN, "Tendencia (t)"] : xN;
  const y = filas.map(f => f[yN]), X = filas.map((f, i) => [...xN.map(c => f[c]), ...(tendR ? [i + 1] : [])]);
  if (filas.length < nombresX.length + 4) return {error: `Hay solo ${filas.length} observaciones completas: son pocas para estimar el modelo.`};
  const m = EST.mco(y, X);
  if (!m) return {error: "No se puede estimar el modelo: alguna variable es combinación lineal de las demás (multicolinealidad perfecta)."};
  return {m, s: EST.supuestos(y, X, m), y, X, yN, nombresX, filas};
}
```

## Resultados de la estimación

```{ojs}
//| echo: false
{
  if (modeloR.error) return html`<p class="pending">${modeloR.error}</p>`;
  const {m, yN, nombresX, filas} = modeloR, nom = ["Constante", ...nombresX], tc = EST.tInv(0.05, m.gl);
  window.cceeEvento && window.cceeEvento("calculadoras/regresion", "Regresión", true);
  const eq = `${yN} = ${f4(m.b[0])} ${m.b.slice(1).map((b, i) => `${b < 0 ? "−" : "+"} ${f4(Math.abs(b))} · ${nombresX[i]}`).join(" ")}`;
  const sig = (p) => p < 0.01 ? "***" : p < 0.05 ? "**" : p < 0.1 ? "*" : "";
  const interp = m.b.slice(1).map((b, i) => {
    const p = m.p[i + 1];
    return html`<li><b>${nombresX[i]}</b>: si aumenta en una unidad, ${yN} ${b >= 0 ? "aumenta" : "disminuye"} en promedio ${f4(Math.abs(b))} unidades, manteniendo constante el resto. ${p < 0.05 ? html`El efecto es <b>estadísticamente significativo</b> al 5 % (p = ${fp(p)}).` : html`El efecto <b>no es significativo</b> al 5 % (p = ${fp(p)}).`}</li>`;
  });
  return html`${tablaR.avisos?.length ? html`<p class="pending">${tablaR.avisos.join(" ")}</p>` : ""}
    <p class="reg-ecuacion">${eq}</p>
    <table class="uso-tabla"><tr><th>Variable</th><th>Coeficiente</th><th>Error típico</th><th>t</th><th>p-valor</th><th>Intervalo de confianza al 95 %</th></tr>
      ${nom.map((v, i) => html`<tr><td>${v}</td><td><b>${f4(m.b[i])}</b> ${sig(m.p[i])}</td><td>${f4(m.se[i])}</td><td>${f4(m.t[i])}</td><td>${fp(m.p[i])}</td><td>[${f4(m.b[i] - tc * m.se[i])} ; ${f4(m.b[i] + tc * m.se[i])}]</td></tr>`)}</table>
    <p class="nota">*** p < 0,01; ** p < 0,05; * p < 0,1.</p>
    <div class="kpi-grid">
      <div class="kpi"><div class="kpi-l">R²</div><div class="kpi-n">${locES.format(",.3f")(m.r2)}</div><div class="kpi-s">el modelo explica el ${locES.format(",.1f")(100 * m.r2)} % de la variabilidad de Y</div></div>
      <div class="kpi"><div class="kpi-l">R² ajustado</div><div class="kpi-n">${locES.format(",.3f")(m.r2a)}</div></div>
      <div class="kpi"><div class="kpi-l">F de significación conjunta</div><div class="kpi-n">${f4(m.F)}</div><div class="kpi-s">p = ${fp(m.pFv)} ${m.pFv < 0.05 ? "· el modelo es significativo" : "· el modelo no es significativo"}</div></div>
      <div class="kpi"><div class="kpi-l">Observaciones</div><div class="kpi-n">${m.n}</div><div class="kpi-s">${tablaR.freq ? `datos ${tablaR.freq.toLowerCase()}es` : ""} ${filas.length ? `· ${filas[0].etq} a ${filas.at(-1).etq}` : ""}</div></div>
      <div class="kpi"><div class="kpi-l">Error típico de la regresión</div><div class="kpi-n">${f4(Math.sqrt(m.s2))}</div></div>
      <div class="kpi"><div class="kpi-l">AIC · BIC</div><div class="kpi-n" style="font-size:1.2rem">${locES.format(",.1f")(m.aic)} · ${locES.format(",.1f")(m.bic)}</div></div></div>
    <h3>Interpretación</h3><ul>${interp}</ul>`;
}
```

## Gráficos

```{ojs}
//| echo: false
{
  if (modeloR.error) return html``;
  const {m, y, X, yN, nombresX, filas} = modeloR;
  const d = filas.map((f, i) => ({etq: f.etq, fecha: f.fecha, i: i + 1, y: y[i], yh: m.ajuste[i], e: m.e[i], x: X[i][0]}));
  const sd = Math.sqrt(m.scr / m.n);
  const ordenados = d.map(r => r.e).sort((a, b) => a - b);
  const qq = ordenados.map((e, i) => ({teo: EST.normInv((i + 0.5) / ordenados.length) * sd, e}));
  const ejeT = tablaR.temporal && d[0].fecha ? {x: "fecha"} : {x: "i"};
  const graf1 = nombresX.length === 1
    ? Plot.plot({height: 300, marginLeft: 55, x: {label: nombresX[0], grid: true}, y: {label: yN, grid: true}, marks: [Plot.dot(d, {x: "x", y: "y", fill: "#2C6FBB", r: 3.5, title: r => `${r.etq}: (${f4(r.x)}, ${f4(r.y)})`}), Plot.line(d.slice().sort((a, b) => a.x - b.x), {x: "x", y: "yh", stroke: "#A6195E", strokeWidth: 2.5})]})
    : Plot.plot({height: 300, marginLeft: 55, x: {label: `${yN} estimado`, grid: true}, y: {label: `${yN} observado`, grid: true}, marks: [Plot.line([[d3.min(d, r => r.yh), d3.min(d, r => r.yh)], [d3.max(d, r => r.yh), d3.max(d, r => r.yh)]], {stroke: "#999", strokeDasharray: "4,3"}), Plot.dot(d, {x: "yh", y: "y", fill: "#2C6FBB", r: 3.5, title: r => r.etq})]});
  return html`<div class="graf-2">
    <div><h4>${nombresX.length === 1 ? "Nube de puntos y recta de regresión" : "Observado frente a estimado"}</h4>${graf1}</div>
    <div><h4>Observado y estimado ${tablaR.temporal ? "a lo largo del tiempo" : "por observación"}</h4>${Plot.plot({height: 300, marginLeft: 55, x: {label: null}, y: {label: yN, grid: true}, color: {legend: true, domain: ["Observado", "Estimado"], range: ["#2C6FBB", "#A6195E"]},
      marks: [Plot.line(d, {...ejeT, y: "y", stroke: () => "Observado", strokeWidth: 2}), Plot.line(d, {...ejeT, y: "yh", stroke: () => "Estimado", strokeWidth: 2, strokeDasharray: "5,3"})]})}</div>
    <div><h4>Residuos frente a valores estimados</h4>${Plot.plot({height: 260, marginLeft: 55, x: {label: "Valor estimado", grid: true}, y: {label: "Residuo", grid: true}, marks: [Plot.ruleY([0], {stroke: "#A6195E"}), Plot.dot(d, {x: "yh", y: "e", fill: "#555", r: 3, title: r => `${r.etq}: ${f4(r.e)}`})]})}</div>
    <div><h4>Residuos ${tablaR.temporal ? "en el tiempo" : "por orden de observación"}</h4>${Plot.plot({height: 260, marginLeft: 55, x: {label: null}, y: {label: "Residuo", grid: true}, marks: [Plot.ruleY([0], {stroke: "#A6195E"}), Plot.line(d, {...ejeT, y: "e", stroke: "#555"}), Plot.dot(d, {...ejeT, y: "e", fill: "#555", r: 2.5})]})}</div>
    <div><h4>Histograma de los residuos</h4>${Plot.plot({height: 260, marginLeft: 45, x: {label: "Residuo"}, y: {label: "Frecuencia", grid: true}, marks: [Plot.rectY(d, Plot.binX({y: "count"}, {x: "e", fill: "#2C6FBB", thresholds: Math.max(5, Math.round(Math.sqrt(d.length)))})), Plot.ruleY([0])]})}</div>
    <div><h4>Gráfico Q-Q normal de los residuos</h4>${Plot.plot({height: 260, marginLeft: 55, x: {label: "Cuantil teórico (normal)", grid: true}, y: {label: "Residuo", grid: true}, marks: [Plot.line([[d3.min(qq, q => q.teo), d3.min(qq, q => q.teo)], [d3.max(qq, q => q.teo), d3.max(qq, q => q.teo)]], {stroke: "#A6195E"}), Plot.dot(qq, {x: "teo", y: "e", fill: "#555", r: 2.5})]})}</div>
  </div>
  ${DOM.download(() => new Blob([csv(d.map(r => ({observacion: r.etq, [yN]: r.y, estimado: r.yh, residuo: r.e})))], {type: "text/csv"}), "regresion_ajuste_residuos.csv", "⬇ Descargar valores estimados y residuos (CSV)")}`;
}
```

## Análisis de los supuestos

```{ojs}
//| echo: false
{
  if (modeloR.error) return html``;
  const {s, m, nombresX} = modeloR;
  const fila = (o, h0, si, no, nota) => { if (!o) return ""; const ok = o.p >= 0.05;
    return html`<tr><td><b>${o.nombre}</b><br><small>H₀: ${h0}</small></td><td>${f4(o.est)}</td><td>${fp(o.p)}</td><td class="${ok ? "sup-ok" : "sup-mal"}">${ok ? "✅ " + si : "⚠️ " + no}</td><td><small>${nota ?? ""}</small></td></tr>`; };
  const dw = s.autocorrelacion.dw;
  const vifs = s.vif ? s.vif.map((v, i) => ({x: nombresX[i], v})) : null;
  const vifMax = vifs ? d3.max(vifs, d => d.v) : null;
  return html`<p>Se usa un nivel de significación del 5 %: si el p-valor es menor que 0,05, se rechaza la hipótesis nula (H₀) y el supuesto <b>no</b> se cumple.</p>
  <table class="uso-tabla sup-tabla"><tr><th>Supuesto y contraste</th><th>Estadístico</th><th>p-valor</th><th>Conclusión</th><th>Si no se cumple…</th></tr>
    ${fila(s.linealidad, "la forma funcional lineal es correcta", "Se acepta la linealidad", "Posible error de especificación", "Prueba a transformar las variables (logaritmos, tasas de variación) o a añadir variables omitidas.")}
    ${fila(s.normalidad, "los residuos siguen una distribución normal", "Se acepta la normalidad", "Los residuos no son normales", `Asimetría ${f4(s.normalidad.asimetria)}, curtosis ${f4(s.normalidad.curtosis)}. Con muestras grandes, los contrastes t y F siguen siendo aproximadamente válidos; revisa si hay datos atípicos.`)}
    ${fila(s.homocedasticidad, "la varianza de los residuos es constante", "Se acepta la homocedasticidad", "Hay heterocedasticidad", "Los coeficientes siguen siendo insesgados, pero los errores típicos no son fiables: usa errores típicos robustos o transforma las variables.")}
    ${fila(s.autocorrelacion, "los residuos no están autocorrelacionados", "No hay autocorrelación", "Hay autocorrelación", `Durbin-Watson = ${f4(dw)} (cerca de 2: sin autocorrelación; cerca de 0: positiva; cerca de 4: negativa). Es habitual en series temporales en niveles: prueba con tasas de variación o diferencias.`)}
    ${vifs ? html`<tr><td><b>Ausencia de multicolinealidad (VIF)</b><br><small>Regla: VIF > 10 indica multicolinealidad grave</small></td><td colspan="2">${vifs.map(d => html`${d.x}: <b>${f4(d.v)}</b><br>`)}</td>
      <td class="${vifMax <= 10 ? "sup-ok" : "sup-mal"}">${vifMax <= 5 ? "✅ Sin problemas" : vifMax <= 10 ? "✅ Moderada" : "⚠️ Multicolinealidad alta"}</td><td><small>Con multicolinealidad alta, los coeficientes son imprecisos: valora eliminar alguna variable explicativa muy correlacionada con las demás.</small></td></tr>` : html`<tr><td><b>Ausencia de multicolinealidad</b></td><td colspan="4"><small>Con una sola variable explicativa no hay multicolinealidad.</small></td></tr>`}
  </table>
  <p class="nota">Contrastes: RESET de Ramsey con ŷ² y ŷ³ (F); Jarque-Bera (χ² con 2 g.l.); Breusch-Pagan en la versión de Koenker (n·R², χ²); Breusch-Godfrey de orden 1 (n·R², χ² con 1 g.l.) y Durbin-Watson; factores de inflación de la varianza (VIF). ${tablaR.temporal ? "Recuerda que una regresión entre series temporales con tendencia puede ser espuria: si R² es alto pero el Durbin-Watson es muy bajo, desconfía del resultado." : ""}</p>`;
}
```
''', DATOS=DATOS, ENTRADA=ENTRADA.replace("__P__", "R").replace("__EJEMPLO__", EJ_REG), EST=EST, ESPECS=J(unicos))

EJ_EST = J("Mes;Ventas tienda A;Ventas tienda B\nene;120;95\nfeb;132;101\nmar;128;99\nabr;141;110\nmay;150;108\njun;162;121\njul;171;118\nago;158;102\nsep;149;112\noct;155;119\nnov;168;125\ndic;190;140")

# =====================================================================================
# Análisis cuantitativo de datos
# =====================================================================================
pagina("estadistica.qmd", r'''---
title: "Análisis cuantitativo de datos"
subtitle: "Análisis descriptivo, crecimiento, tendencia y correlaciones de tus datos o de las series de CCEEscopio"
toc: true
toc-depth: 2
---

Elige **una o varias series** de CCEEscopio (un indicador en varios territorios o varios indicadores) o **pega tus datos**. La calculadora obtiene las medidas descriptivas de cada variable, las tasas de crecimiento, la tendencia y la volatilidad (si son series temporales) y la matriz de correlaciones.

__HELPERS__

__DATOS__

__ENTRADA__

```{ojs}
//| echo: false
viewof indE = fuenteE === "web" ? Inputs.select(new Map(especW.map(s => [`${s.nombre} (${s.frecuencia})`, s])), {label: "Indicadores · Ctrl o ⌘ para varios", multiple: true, size: 8, value: [especW.find(s => s.id === "tasa-de-paro")].filter(Boolean), width: 520}) : Object.assign(html`<span></span>`, {value: []})
viewof terrE = fuenteE === "web" ? Inputs.select(territoriosW, {label: "Territorios · Ctrl o ⌘ para varios", multiple: true, size: 6, value: ["España", "UE-27"]}) : Object.assign(html`<span></span>`, {value: []})
viewof transfE = fuenteE === "web" ? Inputs.select(TRANSF, {label: "Transformación", value: "nivel"}) : Object.assign(html`<span></span>`, {value: "nivel"})
viewof desdeE = fuenteE === "web" ? Inputs.range([2000, new Date().getFullYear() - 1], {label: "Desde el año", value: 2010, step: 1}) : Object.assign(html`<span></span>`, {value: 1900})
```

```{ojs}
//| echo: false
tablaE = {
  if (fuenteE === "web") {
    if (!indE.length || !terrE.length) return {error: "Elige al menos un indicador y un territorio."};
    const combos = indE.flatMap(s => s.sinGeo ? [{spec: s, territorio: null, nombre: s.nombre}] : terrE.map(t => ({spec: s, territorio: t, nombre: indE.length > 1 ? (terrE.length > 1 ? `${s.nombre} · ${t}` : s.nombre) : t}))).slice(0, 8);
    const r = await alinearSeries(combos, transfE);
    r.filas = r.filas.filter(f => !f.fecha || f.fecha.getFullYear() >= desdeE);
    return {...r, temporal: true};
  }
  const t = prepararTabla(ficheroE ? await leerFichero(ficheroE) : parsearTexto(textoE));
  if (!t || !t.numericas.length) return {error: "No encuentro columnas numéricas en tus datos."};
  return {...t, temporal: !!t.etiqueta, freq: null};
}
viewof temporalE = Inputs.toggle({label: "Los datos son una serie temporal (ordenados en el tiempo)", value: tablaE?.temporal ?? false})
viewof anualE = temporalE && fuenteE === "propios" ? Inputs.select(new Map([["Anual", 1], ["Semestral", 2], ["Trimestral", 4], ["Mensual", 12]]), {label: "Frecuencia de los datos", value: 1}) : Object.assign(html`<span></span>`, {value: POR_ANIO[tablaE?.freq] ?? 1})
```

## Medidas descriptivas

```{ojs}
//| echo: false
{
  if (!tablaE || tablaE.error) return html`<p class="pending">${tablaE?.error ?? ""}</p>`;
  if (!tablaE.filas.length) return html`<p class="pending">No hay datos en común para las series elegidas. ${tablaE.avisos?.join(" ") ?? ""}</p>`;
  window.cceeEvento && window.cceeEvento("calculadoras/estadistica", "Análisis cuantitativo", true);
  const vars = tablaE.numericas, D = vars.map(v => ({v, ...EST.describir(tablaE.filas.map(f => f[v]))}));
  const filasT = [["Observaciones", "n", 0], ["Media", "media"], ["Mediana", "mediana"], ["Desviación típica", "sd"], ["Coeficiente de variación (%)", "cv"], ["Mínimo", "min"], ["Primer cuartil (Q1)", "q1"],
    ["Tercer cuartil (Q3)", "q3"], ["Máximo", "max"], ["Recorrido intercuartílico", "iqr"], ["Asimetría (Fisher)", "asimetria"], ["Curtosis (exceso)", "curtosis"]];
  return html`${tablaE.avisos?.length ? html`<p class="pending">${tablaE.avisos.join(" ")}</p>` : ""}
    <p class="nota">${tablaE.filas.length} observaciones${tablaE.filas.length ? ` (${tablaE.filas[0].etq} a ${tablaE.filas.at(-1).etq})` : ""}${tablaE.fuente ? ` · Fuente: Eurostat (${tablaE.fuente})` : ""}.</p>
    <div class="tabla-scroll"><table class="uso-tabla"><tr><th>Medida</th>${vars.map(v => html`<th>${v}</th>`)}</tr>
    ${filasT.map(([t, k]) => html`<tr><td>${t}</td>${D.map(d => html`<td>${k === "n" ? d.n : f4(d[k])}</td>`)}</tr>`)}</table></div>
    <p class="nota">Asimetría positiva: cola a la derecha (valores muy altos poco frecuentes). Curtosis positiva: más datos extremos que en una normal. Coeficiente de variación: dispersión relativa a la media (útil para comparar variables con unidades distintas).</p>
    ${Plot.plot({height: 60 + 46 * vars.length, marginLeft: 220, x: {grid: true, label: null}, y: {label: null},
      marks: [Plot.boxX(vars.flatMap(v => tablaE.filas.map(f => ({v, x: f[v]}))).filter(d => Number.isFinite(d.x)), {x: "x", y: "v", fill: "#F6EEF2", stroke: "#A6195E"})]})}`;
}
```

## Crecimiento, tendencia y volatilidad

```{ojs}
//| echo: false
{
  if (!tablaE || tablaE.error || !tablaE.filas.length) return html``;
  if (!temporalE) return html`<p class="nota">Marca «Los datos son una serie temporal» para calcular tasas de crecimiento y tendencia.</p>`;
  const k = anualE, vars = tablaE.numericas;
  const filas = vars.map(v => {
    const s = tablaE.filas.map((f, i) => ({i, etq: f.etq, y: f[v]})).filter(d => Number.isFinite(d.y));
    if (s.length < 3) return null;
    const a = s[0], b = s.at(-1), anios = (s.length - 1) / k;
    const tmaa = a.y > 0 && b.y > 0 && anios > 0 ? 100 * (Math.pow(b.y / a.y, 1 / anios) - 1) : NaN;
    const mt = EST.mco(s.map(d => d.y), s.map(d => [d.i]));
    const tasas = s.slice(k).map((d, j) => s[j].y ? 100 * (d.y / s[j].y - 1) : NaN).filter(Number.isFinite);
    const mx = d3.greatest(s, d => d.y), mn = d3.least(s, d => d.y);
    return {v, ini: a, fin: b, varTot: a.y ? 100 * (b.y / a.y - 1) : NaN, difTot: b.y - a.y, tmaa, pend: mt ? mt.b[1] * k : NaN, pPend: mt ? mt.p[1] : NaN, r2: mt?.r2,
      vol: tasas.length > 2 ? d3.deviation(tasas) : NaN, mx, mn};
  }).filter(Boolean);
  const largo = vars.flatMap(v => tablaE.filas.map((f, i) => ({v, x: tablaE.filas[0].fecha ? f.fecha : i + 1, y: f[v], etq: f.etq}))).filter(d => Number.isFinite(d.y));
  return html`<div class="tabla-scroll"><table class="uso-tabla"><tr><th>Medida</th>${filas.map(f => html`<th>${f.v}</th>`)}</tr>
    <tr><td>Primer y último valor</td>${filas.map(f => html`<td>${f4(f.ini.y)} (${f.ini.etq}) → ${f4(f.fin.y)} (${f.fin.etq})</td>`)}</tr>
    <tr><td>Variación total</td>${filas.map(f => html`<td>${f4(f.difTot)} (${Number.isFinite(f.varTot) ? locES.format(",.2f")(f.varTot) + " %" : "–"})</td>`)}</tr>
    <tr><td>Tasa media anual acumulativa</td>${filas.map(f => html`<td>${Number.isFinite(f.tmaa) ? locES.format(",.2f")(f.tmaa) + " %" : "–"}</td>`)}</tr>
    <tr><td>Tendencia lineal (cambio medio por año)</td>${filas.map(f => html`<td>${f4(f.pend)} <small>(p = ${fp(f.pPend)}${f.pPend < 0.05 ? ", significativa" : ", no significativa"}; R² = ${locES.format(",.2f")(f.r2)})</small></td>`)}</tr>
    <tr><td>Volatilidad (desv. típica de las tasas interanuales)</td>${filas.map(f => html`<td>${Number.isFinite(f.vol) ? locES.format(",.2f")(f.vol) + " puntos" : "–"}</td>`)}</tr>
    <tr><td>Máximo</td>${filas.map(f => html`<td>${f4(f.mx.y)} (${f.mx.etq})</td>`)}</tr>
    <tr><td>Mínimo</td>${filas.map(f => html`<td>${f4(f.mn.y)} (${f.mn.etq})</td>`)}</tr></table></div>
    ${Plot.plot({height: 320, marginLeft: 55, x: {label: null}, y: {grid: true, label: null}, color: {legend: vars.length > 1},
      marks: [Plot.line(largo, {x: "x", y: "y", stroke: "v", strokeWidth: 2}), Plot.linearRegressionY(largo, {x: "x", y: "y", stroke: "v", strokeDasharray: "4,3", ci: 0}),
        Plot.tip(largo, Plot.pointer({x: "x", y: "y", title: d => `${d.v}, ${d.etq}: ${f4(d.y)}`}))]})}
    <p class="nota">Línea discontinua: tendencia lineal. La tasa media anual acumulativa solo se calcula con valores positivos.</p>`;
}
```

## Correlaciones

```{ojs}
//| echo: false
{
  if (!tablaE || tablaE.error || !tablaE.filas.length) return html``;
  const vars = tablaE.numericas;
  if (vars.length < 2) return html`<p class="nota">Elige al menos dos series para calcular correlaciones.</p>`;
  const celdas = vars.flatMap(a => vars.map(b => ({a, b, ...EST.correlacion(tablaE.filas.map(f => f[a]), tablaE.filas.map(f => f[b]))})));
  return html`${Plot.plot({height: 80 + 50 * vars.length, width: Math.min(width, 140 + 120 * vars.length), marginLeft: 200, marginBottom: 110,
    x: {domain: vars, label: null, tickRotate: -30}, y: {domain: vars, label: null}, color: {type: "diverging", scheme: "RdBu", domain: [-1, 1], legend: true, label: "Correlación de Pearson"},
    marks: [Plot.cell(celdas, {x: "b", y: "a", fill: "r"}), Plot.text(celdas, {x: "b", y: "a", text: d => `${locES.format(",.2f")(d.r)}${d.a !== d.b && d.p < 0.05 ? "*" : ""}`, fill: d => Math.abs(d.r) > 0.6 ? "white" : "black"})]})}
  <p class="nota">* Correlación significativamente distinta de cero al 5 %. Recuerda que correlación no implica causalidad. Para modelizar la relación, usa la <a href="regresion.html">regresión con análisis de supuestos</a>.</p>
  ${DOM.download(() => new Blob([csv(tablaE.filas.map(f => ({observacion: f.etq, ...Object.fromEntries(vars.map(v => [v, f[v]]))})))], {type: "text/csv"}), "datos_analizados.csv", "⬇ Descargar los datos (CSV)")}`;
}
```
''', DATOS=DATOS, ENTRADA=ENTRADA.replace("__P__", "E").replace("__EJEMPLO__", EJ_EST), EST=EST, ESPECS=J(unicos))

# =====================================================================================
# Portada de las calculadoras
# =====================================================================================
GRUPOS = [
    ("📊 Métodos Cuantitativos y econometría", [
        ("regresion", "Regresión lineal con análisis de supuestos", "MCO con hasta cuatro variables explicativas, interpretación y contrastes de linealidad, normalidad, homocedasticidad, autocorrelación y multicolinealidad.", True),
        ("estadistica", "Análisis cuantitativo de datos", "Medidas descriptivas, crecimiento, tendencia, volatilidad y correlaciones de tus datos o de las series de la web.", True),
        ("desfases", "¿Qué indicador se adelanta?", "Correlación con desfase entre dos series para detectar indicadores adelantados y retrasados.", False),
        ("relaciona", "Relaciona dos indicadores", "Nube de puntos entre dos indicadores para todos los países o regiones.", False),
    ]),
    ("📈 Series temporales y previsión", [
        ("prevision", "Previsión sencilla", "Tendencia más estacionalidad con intervalo de confianza y prueba hacia atrás.", False),
        ("descomposiciones", "¿Qué explica cada indicador?", "Contribuciones de cada componente a la inflación, al crecimiento del PIB, a la cuenta corriente, a la población y al turismo.", False),
        ("convergencia", "Convergencia sigma y beta", "¿Se reducen las diferencias entre países o regiones?", False),
        ("ciclo", "Ciclo económico", "Reloj del ciclo y semáforo de coyuntura.", False),
    ]),
    ("💶 Precios, dinero y finanzas", [
        ("calculadora", "Calculadora de inflación", "¿Cuánto valen hoy los euros de otro año?", False),
        ("conversor", "Conversor de unidades económicas", "Euros constantes, paridad de poder de compra, por habitante y cambios de base.", False),
        ("hipoteca", "Simulador de hipotecas y préstamos", "Cuota, cuadro de amortización y TAE con el euríbor actual.", False),
    ]),
    ("⚖️ Desigualdad y política económica", [
        ("desigualdad-calc", "Calculadora de desigualdad", "Gini, curva de Lorenz, S80/S20 e índices de Theil con tus datos, con inferencia jackknife.", False),
        ("politica-fiscal", "Simulador de política fiscal", "Dinámica de la deuda pública y efecto de un ajuste fiscal.", False),
    ]),
    ("👥 Población", [
        ("piramides", "Pirámides de población", "Países, comunidades autónomas y provincias, con animación y comparación entre años y territorios.", True),
    ]),
]
tarjetas = []
for titulo, items in GRUPOS:
    tarjetas.append(f"## {titulo}\n\n```{{=html}}\n<div class=\"calc-grid\">\n")
    for href, t, d, nuevo in items:
        tarjetas.append(f'<a class="calc-card" href="{href}.html"><b>{t}</b>{" <span class=\"badge-nuevo\">nuevo</span>" if nuevo else ""}<span>{d}</span></a>\n')
    tarjetas.append("</div>\n```\n")
open("calculadoras.qmd", "w", encoding="utf-8").write('''---
title: "Calculadoras y laboratorio de datos"
subtitle: "Herramientas para calcular, estimar y analizar con datos oficiales o con tus propios datos"
toc: false
---

Todas las calculadoras funcionan en tu navegador: si usas tus propios datos, **no salen de tu ordenador**. Las que usan datos de CCEEscopio los descargan de Eurostat al momento.

''' + "\n".join(tarjetas))
print("   calculadoras.qmd")

# =====================================================================================
# Concurso en clase con código QR y ranking en directo (tipo Kahoot)
# Los mensajes viajan por un servidor público de mensajería MQTT: solo alias y puntuaciones.
# =====================================================================================
_src3 = open("tools/make_apps3.py", encoding="utf-8").read()
PREG = _src3[_src3.index("PREG = r'''") + len("PREG = r'''"): _src3.index("'''", _src3.index("PREG = r'''") + 12)]

CONC = r'''```{ojs}
//| echo: false
// Utilidades del concurso (sin dependencias del navegador, para poder probarlas)
CONC = {
  const ofuscar = (sala, i, c, n) => (c + [...`${sala}|${i}`].reduce((h, ch) => (h * 31 + ch.charCodeAt(0)) >>> 0, 7)) % n;
  const desofuscar = (sala, i, x, n) => ((x - [...`${sala}|${i}`].reduce((h, ch) => (h * 31 + ch.charCodeAt(0)) >>> 0, 7)) % n + n) % n;
  const ordenar = (jug) => [...jug.values()].sort((a, b) => (b.aciertos - a.aciertos) || ((b.fin ? 1 : 0) - (a.fin ? 1 : 0)) || (a.tiempo - b.tiempo) || a.alias.localeCompare(b.alias));
  const nuevaSala = () => Array.from(crypto.getRandomValues(new Uint8Array(8)), b => "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"[b % 32]).join("");
  const segundos = (ms) => `${(ms / 1000).toFixed(1).replace(".", ",")} s`;
  return {ofuscar, desofuscar, ordenar, nuevaSala, segundos};
}
```'''

pagina("concurso.qmd", r'''---
title: "Concurso en clase"
subtitle: "Preguntas con datos reales de CCEEscopio: los estudiantes juegan desde el móvil y el ranking aparece en directo en la pantalla"
toc: false
---

__HELPERS__

__PREG__

__CONC__

```{ojs}
//| echo: false
especC = __ESPECS__
areasC = (__AREAS__)
paramsC = new URLSearchParams(location.search)
SALA = paramsC.get("sala")
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
temaEstado = (s) => `cceescopio/concurso/${s}/estado`
temaJug = (s) => `cceescopio/concurso/${s}/jugadores`
```

```{ojs}
//| echo: false
// ============================ PANTALLA DEL PROFESOR ============================
viewof areaC = SALA ? Object.assign(html`<span></span>`, {value: null}) : Inputs.select(new Map([["Todas las áreas", "todas"], ...Object.entries(areasC).map(([k, v]) => [v, k])]), {label: "Tema de las preguntas"})
viewof nC = SALA ? Object.assign(html`<span></span>`, {value: null}) : Inputs.range([5, 15], {label: "Número de preguntas", value: 8, step: 1})
viewof abrirC = SALA ? Object.assign(html`<span></span>`, {value: 0}) : Inputs.button("▶ Abrir concurso", {value: 0, reduce: v => v + 1})
```

```{ojs}
//| echo: false
{
  if (SALA) return html``;
  if (!abrirC) return html`<div class="conc-intro">
    <p><b>Cómo funciona:</b> pulsa «Abrir concurso» y proyecta esta pantalla. Los estudiantes escanean el código QR con el móvil y escriben un <b>alias</b> (no se piden nombres ni DNI). Cuando estén todos, pulsa «Empezar»: cada estudiante responde las preguntas a su ritmo y en la pantalla verás el <b>ranking en directo</b>, ordenado por aciertos y, en caso de empate, por el tiempo empleado.</p>
    <p>¿Prefieres un concurso sobre precios? Prueba <a href="concurso-precios.html">«¿Cuánto costaba?»</a>: los estudiantes adivinan cuánto costaban la gasolina, el pan o el café en una fecha del pasado.</p>
    <p class="nota">Los resultados viajan por un servicio público de mensajería en tiempo real y no se guardan en ningún sitio. Antes de usarlo en clase por primera vez, haz una prueba con tu móvil: si la red del aula bloquea la conexión, la página lo indicará.</p></div>`;
  const caja = html`<div class="conc-panel"><p class="pending">Preparando las preguntas con los datos de Eurostat…</p></div>`;
  (async () => {
    const pool = especC.filter(s => !s.sinGeo && !s.regional && (areaC === "todas" || s.pagina === areaC));
    const sala = CONC.nuevaSala();
    const qs = await generarSerie(pool, ["test", "vf", "test"], nC, `concurso-${sala}`);
    if (qs.length < 3) { caja.innerHTML = `<p class="pending">No se han podido preparar las preguntas (¿hay conexión con Eurostat?). Inténtalo de nuevo.</p>`; return; }
    caja.innerHTML = `<p class="pending">Conectando con el servicio de mensajería…</p>`;
    let cli = null, broker = null;
    for (const b of BROKERS) { try { cli = await conectarBroker(b); broker = b; break; } catch (e) {} }
    if (!cli) { caja.innerHTML = `<p class="pending">❌ No se ha podido conectar con ningún servicio de mensajería. Es posible que la red bloquee estas conexiones: prueba con otra red (por ejemplo, los datos del móvil compartidos).</p>`; return; }
    const preguntas = qs.map((q, i) => ({e: q.enunciado, o: q.opciones, c: CONC.ofuscar(sala, i, q.respuesta, q.opciones.length), s: q.solucion}));
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
      <div class="conc-ranking"></div>`);
    const $ = (s) => caja.querySelector(s);
    try { const qrlib = await require("qrcode-generator@1.4.4"); const qr = qrlib(0, "M"); qr.addData(enlace); qr.make(); $(".conc-qr").innerHTML = qr.createSvgTag({cellSize: 6, margin: 2, scalable: true}); } catch (e) { $(".conc-qr").textContent = "(no se ha podido crear el QR)"; }
    const pintar = () => {
      const r = CONC.ordenar(jug);
      $(".conc-cuenta").textContent = `${jug.size} participante${jug.size === 1 ? "" : "s"}`;
      if (fase === "espera") { $(".conc-ranking").innerHTML = `<div class="conc-alias">${r.map(j => `<span>${j.alias}</span>`).join("")}</div>`; return; }
      const medalla = (i) => fase === "fin" ? ["🥇", "🥈", "🥉"][i] ?? `${i + 1}.` : `${i + 1}.`;
      $(".conc-ranking").innerHTML = `${fase === "fin" ? `<h2 class="conc-podio">🏆 ${r[0] ? r[0].alias : ""}</h2>` : ""}<table class="uso-tabla conc-tabla"><tr><th></th><th>Alias</th><th>Aciertos</th><th>Pregunta</th><th>Tiempo</th></tr>` +
        r.slice(0, 15).map((j, i) => `<tr class="${i < 3 && fase === "fin" ? "conc-top" : ""}"><td>${medalla(i)}</td><td>${j.alias}</td><td><b>${j.aciertos}</b> / ${preguntas.length}</td><td>${j.fin ? "✔ terminado" : `${j.resp ?? 0} / ${preguntas.length}`}</td><td>${j.tiempo ? CONC.segundos(j.tiempo) : "–"}</td></tr>`).join("") + "</table>";
    };
    cli.on("message", (t, m) => { try { const d = JSON.parse(m.toString()); if (!d.id || !d.alias) return; const prev = jug.get(d.id) ?? {aciertos: 0, resp: 0, tiempo: 0};
      jug.set(d.id, {...prev, ...d, alias: String(d.alias).slice(0, 20).replace(/[<>&"]/g, "")}); pintar(); } catch (e) {} });
    $(".conc-empezar").onclick = () => { fase = "juego"; publicar({fase: "juego", preguntas, inicio: Date.now()}); $(".conc-empezar").disabled = true; $(".conc-terminar").disabled = false; pintar();
      window.cceeEvento && window.cceeEvento("concurso/empezar", "Concurso en clase", true); };
    $(".conc-terminar").onclick = () => { fase = "fin"; const r = CONC.ordenar(jug).slice(0, 10).map(j => ({alias: j.alias, aciertos: j.aciertos, tiempo: j.tiempo}));
      publicar({fase: "fin", preguntas, ranking: r}); $(".conc-terminar").disabled = true; pintar();
      caja.append(DOM.download(() => new Blob([csv(CONC.ordenar(jug).map((j, i) => ({puesto: i + 1, alias: j.alias, aciertos: j.aciertos, preguntas: preguntas.length, tiempo_segundos: Math.round(j.tiempo / 100) / 10, terminado: j.fin ? "sí" : "no"})))], {type: "text/csv"}), `concurso_${sala}.csv`, "⬇ Descargar los resultados (CSV)")); };
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
  const broker = BROKERS.find(b => b.id === paramsC.get("b")) ?? BROKERS[0];
  const caja = html`<div class="conc-movil"><p class="pending">Conectando con el concurso…</p></div>`;
  (async () => {
    let cli;
    try { cli = await conectarBroker(broker); } catch (e) { caja.innerHTML = `<p class="pending">❌ No se ha podido conectar. Comprueba la conexión a internet (si estás en la wifi de la universidad, prueba con los datos del móvil) y recarga la página.</p>`; return; }
    let id; try { id = localStorage.getItem(`ccee-conc-${SALA}`) || crypto.randomUUID(); localStorage.setItem(`ccee-conc-${SALA}`, id); } catch (e) { id = crypto.randomUUID(); }
    let alias = ""; try { alias = localStorage.getItem("ccee-conc-alias") || ""; } catch (e) {}
    let estado = null, unido = false, i = 0, aciertos = 0, t0 = null, jugando = false;
    const enviar = (extra) => cli.publish(temaJug(SALA), JSON.stringify({id, alias, aciertos, resp: i, tiempo: t0 ? Date.now() - t0 : 0, ...extra}), {qos: 1});
    const pantalla = () => {
      caja.innerHTML = "";
      if (!unido) {
        const f = html`<form class="asis-caja"><label>Tu alias para el ranking<input name="alias" required maxlength="20" autocomplete="off" placeholder="p. ej. Analista_7" value="${alias}"></label><button class="asis-boton">Entrar al concurso</button><p class="asis-nota">No escribas tu nombre real si no quieres que aparezca en la pantalla de clase.</p></form>`;
        f.onsubmit = (e) => { e.preventDefault(); alias = f.alias.value.trim().slice(0, 20).replace(/[<>&"]/g, ""); if (!alias) return; try { localStorage.setItem("ccee-conc-alias", alias); } catch (err) {} unido = true; enviar({fin: false}); pantalla(); };
        caja.append(f); return;
      }
      if (!estado || estado.fase === "espera") { caja.append(html`<div class="asis-caja conc-espera"><p class="juego-grande">⏳</p><p>Hola, <b>${alias}</b>. Espera a que el profesor empiece el concurso…</p></div>`); return; }
      const P = estado.preguntas;
      if (estado.fase === "fin" || i >= P.length) {
        const pos = estado.ranking ? estado.ranking.findIndex(r => r.alias === alias) : -1;
        caja.append(html`<div class="asis-caja conc-espera"><p class="juego-grande">${aciertos} / ${P.length}</p><p>Tiempo: <b>${CONC.segundos(t0 ? Date.now() - t0 : 0)}</b></p>
          ${estado.fase === "fin" ? html`<p>${pos >= 0 ? html`Has quedado en el puesto <b>${pos + 1}</b> ${["🥇", "🥈", "🥉"][pos] ?? ""}` : "Mira el ranking en la pantalla de clase."}</p>` : html`<p>¡Terminado! Mira el ranking en la pantalla de clase.</p>`}</div>`);
        return;
      }
      if (!t0) t0 = Date.now();
      const q = P[i], correcta = CONC.desofuscar(SALA, i, q.c, q.o.length);
      const ops = html`<div class="juego-ops juego-ops-v">`;
      q.o.forEach((o, k) => { const b = html`<button class="juego-op">${o}</button>`; b.onclick = () => {
        if (!jugando) return; jugando = false;
        const bien = k === correcta; if (bien) aciertos++;
        ops.querySelectorAll("button").forEach((x, j) => { x.disabled = true; if (j === correcta) x.classList.add("ok"); }); if (!bien) b.classList.add("ko");
        i++; enviar({fin: i >= P.length});
        setTimeout(pantalla, bien ? 700 : 1500);
      }; ops.append(b); });
      jugando = true;
      caja.append(html`<div class="juego"><p class="juego-ind">Pregunta ${i + 1} de ${P.length} · Aciertos: ${aciertos}</p><p class="juego-p">${q.e.split("**").map((t, j) => j % 2 ? html`<b>${t}</b>` : t)}</p></div>`, ops);
    };
    cli.subscribe(temaEstado(SALA), {qos: 1});
    cli.on("message", (t, m) => { try { const d = JSON.parse(m.toString()); const antes = estado?.fase; estado = d; if (antes !== d.fase || !jugando) pantalla(); } catch (e) {} });
    invalidation.then(() => { try { cli.end(true); } catch (e) {} });
    pantalla();
  })();
  return caja;
}
```
''', PREG=PREG, CONC=CONC, ESPECS=J(unicos), AREAS=J(AREAS))
