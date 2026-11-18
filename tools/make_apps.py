"""Genera las herramientas interactivas de CCEEscopio: calculadora de inflación (calculadora.qmd),
ficha de país o región (ficha.qmd) y relación entre dos indicadores (relaciona.qmd).
Uso (desde la carpeta del proyecto): python3 tools/make_pages.py && python3 tools/make_apps.py"""
import json

HELPERS = open("_helpers.qmd", encoding="utf-8").read().strip()
SPECS = json.load(open("data/indicadores_specs.json", encoding="utf-8"))
porid = {}
for k, lst in SPECS.items():
    if k == "andalucia":
        continue
    for i in lst:
        porid.setdefault(i["id"], dict(i, pagina=k))

def specs(ids):
    return json.dumps([porid[i] for i in ids], ensure_ascii=False)

# ------------------------------------------------------------------ Calculadora de inflación
IPC_ANUAL = dict(nombre="IPCA (índice, media anual)", code="prc_hicp_aind", query="&unit=INX_A_AVG&coicop=CP00",
                 unidad="Índice", frecuencia="Anual", descripcion="", desde=1996,
                 alt=[dict(code="prc_hicp_aind", query="&unit=INX_A_AVG&coicop18=TOTAL"),
                      dict(code="prc_hicp_ainr", query="&unit=INX_A_AVG&coicop18=TOTAL")])
calc = f'''---
title: "Calculadora de inflación"
subtitle: "¿Cuánto valen hoy los euros de otro año? Poder adquisitivo y actualización de cantidades con el IPCA"
toc: false
---

Esta calculadora **actualiza una cantidad de dinero** de un año a otro con el Índice de Precios de Consumo Armonizado (IPCA, media anual) de Eurostat. Sirve para comparar salarios, precios o rentas de distintos años en términos reales, para practicar números índice en clase o para entender cuánto poder adquisitivo se ha perdido con la inflación.

{HELPERS}

```{{ojs}}
//| echo: false
especIPC = ({json.dumps(IPC_ANUAL, ensure_ascii=False)})
datosIPC = cargar(especIPC)
paisesIPC = datosIPC.ok ? [...new Set(datosIPC.rows.map(r => r.territorio))].sort((a, b) => a.localeCompare(b, "es")) : []
viewof paisC = Inputs.select(paisesIPC, {{label: "País o zona", value: paisesIPC.includes("España") ? "España" : paisesIPC[0]}})
```

```{{ojs}}
//| echo: false
serieC = datosIPC.ok ? datosIPC.rows.filter(r => r.territorio === paisC).sort((a, b) => a.fecha - b.fecha) : []
aniosC = serieC.map(r => r.periodo)
viewof cantidadC = Inputs.number([0, 1e12], {{label: "Cantidad (€)", value: 1000, step: 1}})
viewof anioDe = Inputs.select(aniosC, {{label: "Euros del año", value: aniosC.includes("2015") ? "2015" : aniosC[0]}})
viewof anioA = Inputs.select(aniosC, {{label: "Expresados en euros de", value: aniosC[aniosC.length - 1]}})
```

```{{ojs}}
//| echo: false
resC = {{
  if (!datosIPC.ok) return null;
  const i1 = serieC.find(r => r.periodo === anioDe)?.valor, i2 = serieC.find(r => r.periodo === anioA)?.valor;
  if (!i1 || !i2) return null;
  const n = Math.abs(+anioA - +anioDe);
  return {{valor: cantidadC * i2 / i1, acum: 100 * (i2 / i1 - 1), media: n ? 100 * (Math.pow(i2 / i1, 1 / n) - 1) * Math.sign(+anioA - +anioDe) : 0, i1, i2}};
}}
datosIPC.ok ? (resC ? html`<div class="calc-result">
  <div class="calc-big">${{fmt(cantidadC)}} € de ${{anioDe}} equivalen a <b>${{locES.format(",.2f")(resC.valor)}} €</b> de ${{anioA}}</div>
  <div class="calc-small">Variación acumulada de los precios: <b>${{locES.format(",.1f")(resC.acum)}} %</b> · Inflación media anual: <b>${{locES.format(",.2f")(resC.media)}} %</b> · Índices: ${{locES.format(",.2f")(resC.i1)}} → ${{locES.format(",.2f")(resC.i2)}} (${{paisC}})</div>
</div>` : html`<p class="pending">Elige dos años con datos.</p>`)
: html`<div class="callout callout-warning"><p><b>No se han podido cargar los datos del IPCA</b> (${{datosIPC.error}}). Puedes usar la calculadora oficial del INE: <a href="https://www.ine.es/varipc/" target="_blank">ine.es/varipc</a>.</p></div>`
```

```{{ojs}}
//| echo: false
datosIPC.ok ? Plot.plot({{
  height: 300, marginLeft: 50, x: {{label: null, type: "time"}}, y: {{label: "Índice (media anual)", grid: true}},
  marks: [
    Plot.line(serieC, {{x: "fecha", y: "valor", stroke: "#B5175F", strokeWidth: 2.2}}),
    Plot.dot(serieC.filter(r => r.periodo === anioDe || r.periodo === anioA), {{x: "fecha", y: "valor", r: 6, fill: "#F29200"}}),
    Plot.tip(serieC, Plot.pointer({{x: "fecha", y: "valor", title: d => `${{d.periodo}}: ${{locES.format(",.2f")(d.valor)}}`}}))
  ]
}}) : html``
```

::: {{.callout-note appearance="simple"}}
**Cómo se calcula.** Cantidad en euros del año B = cantidad en euros del año A × IPCA(B) / IPCA(A), con la media anual del índice. La inflación media anual es la tasa constante que produce la misma variación acumulada. En España, la cifra oficial para actualizar rentas y contratos es el **IPC del INE** ([calculadora del INE](https://www.ine.es/varipc/)); el IPCA, armonizado en la UE, puede diferir ligeramente.
:::

**Para clase.** ¿Ha crecido tu salario (o el salario mínimo) más o menos que los precios? Actualiza una cantidad de hace diez años y compárala con la actual; relaciona el resultado con la [inflación por componentes](precios.qmd).
'''
open("calculadora.qmd", "w", encoding="utf-8").write(calc)

# ------------------------------------------------------------------ Ficha de país o región
FP = ["pib-crecimiento-interanual-trimestral", "ipca-inflacion-general-tasa-anual", "tasa-de-paro",
      "tasa-de-paro-juvenil-menores-de-25-anos", "tasa-de-empleo-20-64-anos", "pib-per-capita-en-ppc-ue-27-100",
      "deuda-publica-del-pib", "deficit-o-superavit-publico-del-pib", "indice-de-gini",
      "riesgo-de-pobreza-o-exclusion-social-arope", "gasto-en-i-d-del-pib", "cuota-de-energias-renovables",
      "poblacion", "esperanza-de-vida-al-nacer"]
FR = ["pib-per-capita-en-paridad-de-poder-de-compra", "tasa-de-paro-por-regiones", "tasa-de-empleo-por-regiones-20-64-anos",
      "gasto-en-i-d-por-regiones-del-pib", "riesgo-de-pobreza-o-exclusion-social-por-regiones",
      "tasa-de-riesgo-de-pobreza-por-regiones", "pernoctaciones-por-regiones", "poblacion-por-regiones"]
ficha = f'''---
title: "Ficha de país o región"
subtitle: "Los principales indicadores de un territorio de un vistazo, con su comparación con la UE y con España"
toc: false
---

Elige un país de la UE o una comunidad autónoma para ver su **último dato** en los indicadores clave de CCEEscopio, compararlo con la UE-27 (y con España, en el caso de las regiones) y ver su evolución reciente. Útil para preparar un **informe de coyuntura**, un análisis de entorno (PESTEL) o la introducción de un TFG.

{HELPERS}

```{{ojs}}
//| echo: false
especPaises = {specs(FP)}
especRegiones = {specs(FR)}
viewof ambito = Inputs.radio(["Países", "Comunidades autónomas"], {{label: "Ámbito", value: "Países"}})
```

```{{ojs}}
//| echo: false
opciones = ambito === "Países" ? geosPaises.map(g => nombresGeo[g]) : geosRegiones.filter(g => g.length > 2).map(g => nombresGeo[g])
viewof terrF = Inputs.select(opciones, {{label: "Territorio", value: ambito === "Países" ? "España" : "Andalucía"}})
```

```{{ojs}}
//| echo: false
especF = ambito === "Países" ? especPaises : especRegiones
cargasF = Promise.all(especF.map(s => cargar(s).catch(e => ({{ok: false, rows: [], error: e.message}}))))
```

```{{ojs}}
//| echo: false
{{
  const refs = ambito === "Países" ? ["UE-27"] : ["España", "UE-27"];
  const ultimo = (rows, t) => rows.filter(r => r.territorio === t).sort((a, b) => b.fecha - a.fecha)[0];
  const tarjetas = especF.map((s, k) => {{
    const d = cargasF[k];
    const enlace = `${{porPagina[s.id] ?? ""}}.html?i=${{s.id}}`;
    if (!d.ok) return html`<div class="kpi"><div class="kpi-l">${{s.nombre}}</div><div class="kpi-n">–</div><div class="kpi-s">Sin datos ahora mismo</div></div>`;
    const u = ultimo(d.rows, terrF);
    if (!u) return html`<div class="kpi"><div class="kpi-l"><a href="${{enlace}}">${{s.nombre}}</a></div><div class="kpi-n">–</div><div class="kpi-s">Sin datos para ${{terrF}}</div></div>`;
    const comp = refs.map(r => {{ const x = ultimo(d.rows, r); return x ? `${{r}}: ${{fmt(x.valor)}}` : null; }}).filter(Boolean).join(" · ");
    const serie = d.rows.filter(r => r.territorio === terrF).sort((a, b) => a.fecha - b.fecha).slice(-40);
    const spark = Plot.plot({{height: 46, width: 210, margin: 2, axis: null, marks: [Plot.line(serie, {{x: "fecha", y: "valor", stroke: "#B5175F", strokeWidth: 1.6}})]}});
    return html`<div class="kpi"><div class="kpi-l"><a href="${{enlace}}">${{s.nombre}}</a></div>
      <div class="kpi-n">${{fmt(u.valor)}}</div><div class="kpi-s">${{s.unidad}} · ${{u.periodo}}</div>${{spark}}<div class="kpi-s">${{comp}}</div></div>`;
  }});
  return html`<h3 class="ficha-t">${{terrF}}</h3><div class="kpi-grid">${{tarjetas}}</div>
  <p class="source">Datos descargados en directo de Eurostat. Cada tarjeta enlaza con el gráfico completo del indicador.</p>`;
}}
```

```{{ojs}}
//| echo: false
porPagina = ({json.dumps({i: porid[i]["pagina"] for i in FP + FR}, ensure_ascii=False)})
```
'''
open("ficha.qmd", "w", encoding="utf-8").write(ficha)

# ------------------------------------------------------------------ Relaciona dos indicadores
REL = [i for k, lst in SPECS.items() if k != "andalucia" for i in lst if not i.get("regional") and not i.get("sinGeo")]
seen, rel = set(), []
for i in REL:
    if i["id"] not in seen:
        seen.add(i["id"]); rel.append(i)
relq = f'''---
title: "Relaciona dos indicadores"
subtitle: "Diagrama de dispersión de los países de la UE para explorar relaciones entre variables económicas"
toc: false
---

Elige dos indicadores y un año: cada punto es un país de la UE. La recta es el ajuste por mínimos cuadrados y se muestra el **coeficiente de correlación**. Ideal para introducir en clase relaciones como la **curva de Phillips** (inflación y paro), la **ley de Okun** (crecimiento y paro), el gasto social y la pobreza, o la renta y la desigualdad. Recuerda que **correlación no implica causalidad**.

{HELPERS}

```{{ojs}}
//| echo: false
especRel = {json.dumps(rel, ensure_ascii=False)}
porIdRel = new Map(especRel.map(d => [d.id, d]))
viewof indX = Inputs.select(especRel, {{label: "Eje horizontal", format: d => d.nombre, value: porIdRel.get("tasa-de-paro")}})
viewof indY = Inputs.select(especRel, {{label: "Eje vertical", format: d => d.nombre, value: porIdRel.get("ipca-inflacion-general-tasa-anual")}})
```

```{{ojs}}
//| echo: false
anual = (d) => {{
  // Media anual por país (para las series mensuales, trimestrales o semestrales)
  if (!d.ok) return new Map();
  return d3.rollup(d.rows.filter(r => geosPaises.includes(r.codigo_territorio)), v => d3.mean(v, r => r.valor), r => r.territorio, r => String(r.fecha.getFullYear()));
}}
dX = cargar(indX)
dY = cargar(indY)
aX = anual(dX)
aY = anual(dY)
aniosRel = {{
  const s = new Map();
  for (const [t, m] of aX) for (const [a] of m) if (aY.get(t)?.has(a)) s.set(a, (s.get(a) ?? 0) + 1);
  return [...s].filter(([, n]) => n >= 8).map(([a]) => a).sort().reverse();
}}
viewof anioRel = Inputs.select(aniosRel, {{label: "Año", value: aniosRel[0]}})
```

```{{ojs}}
//| echo: false
puntos = [...aX].map(([t, m]) => ({{territorio: t, x: m.get(anioRel), y: aY.get(t)?.get(anioRel)}})).filter(d => Number.isFinite(d.x) && Number.isFinite(d.y) && !["UE-27", "Zona euro", "Zona euro (19)"].includes(d.territorio))
corr = {{
  const n = puntos.length; if (n < 3) return NaN;
  const mx = d3.mean(puntos, d => d.x), my = d3.mean(puntos, d => d.y);
  const sxy = d3.sum(puntos, d => (d.x - mx) * (d.y - my)), sx = Math.sqrt(d3.sum(puntos, d => (d.x - mx) ** 2)), sy = Math.sqrt(d3.sum(puntos, d => (d.y - my) ** 2));
  return sxy / (sx * sy);
}}
(dX.ok && dY.ok) ? (puntos.length >= 3 ? html`${{Plot.plot({{
  height: 470, marginLeft: 60, grid: true,
  x: {{label: `${{indX.nombre}} (${{indX.unidad}})`, tickFormat: v => fmt(v)}},
  y: {{label: `${{indY.nombre}} (${{indY.unidad}})`, tickFormat: v => fmt(v)}},
  marks: [
    Plot.linearRegressionY(puntos, {{x: "x", y: "y", stroke: "#3C3C3B", strokeDasharray: "4,3"}}),
    Plot.dot(puntos, {{x: "x", y: "y", r: 6, fill: d => d.territorio === "España" ? "#B5175F" : "#D9C2CC", stroke: "#fff"}}),
    Plot.text(puntos, {{x: "x", y: "y", text: "territorio", dy: -11, fontSize: 10, fill: d => d.territorio === "España" ? "#B5175F" : "#555"}}),
    Plot.tip(puntos, Plot.pointer({{x: "x", y: "y", title: d => `${{d.territorio}} (${{anioRel}})\\n${{indX.nombre}}: ${{fmt(d.x)}}\\n${{indY.nombre}}: ${{fmt(d.y)}}`}}))
  ]
}})}}<p class="calc-small">Año ${{anioRel}} · ${{puntos.length}} países · Coeficiente de correlación de Pearson: <b>${{locES.format(",.2f")(corr)}}</b></p>
${{DOM.download(() => new Blob(["\\ufeff" + d3.csvFormat(puntos.map(d => ({{territorio: d.territorio, anio: anioRel, [indX.nombre]: d.x, [indY.nombre]: d.y}})))], {{type: "text/csv;charset=utf-8"}}), `cceescopio_relacion_${{anioRel}}.csv`, "⬇ Descargar los datos (CSV)")}}`
  : html`<p class="pending">No hay suficientes países con datos de ambos indicadores en ese año.</p>`)
: html`<div class="callout callout-warning"><p><b>No se han podido cargar los datos de Eurostat</b>. Inténtalo de nuevo más tarde.</p></div>`
```

::: {{.callout-tip appearance="simple"}}
**Ideas para clase.** Paro e inflación (curva de Phillips) · Crecimiento del PIB y paro (ley de Okun) · Gasto en protección social y riesgo de pobreza · PIB per cápita y gasto en I+D · Gasto en sanidad y esperanza de vida · Renta mediana y compra por internet. Para las series mensuales o trimestrales se usa la media del año.
:::
'''
open("relaciona.qmd", "w", encoding="utf-8").write(relq)
print("calculadora.qmd, ficha.qmd, relaciona.qmd generados;", len(rel), "indicadores en Relaciona")
