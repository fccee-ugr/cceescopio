"""Genera los recursos nuevos de CCEEscopio (noviembre de 2026):
ejercicios, graficos, hipoteca, glosario, comparador, calendario, mercados, conversor,
turismo-andalucia, empresas, consumo, boletin y biblioteca.
Uso (desde la carpeta del proyecto): python3 tools/make_pages.py && python3 tools/make_apps.py && python3 tools/make_apps2.py
Las páginas usan plantillas con marcadores __NOMBRE__ (no f-strings) para no escapar las llaves del código OJS."""
import json, re, unicodedata

HELPERS = open("_helpers.qmd", encoding="utf-8").read().strip()
SPECS = json.load(open("data/indicadores_specs.json", encoding="utf-8"))
AREAS = {"precios": "Precios e inflación", "empleo": "Mercado laboral", "actividad": "Actividad económica y coyuntura",
         "empresa": "Empresa, innovación y digitalización", "turismo": "Turismo", "publico": "Sector público y mercados financieros",
         "desigualdad": "Desigualdad, pobreza y condiciones de vida", "sostenibilidad": "Energía y sostenibilidad",
         "poblacion": "Población, educación y salud", "internacional": "Economía internacional y sector exterior"}
porid, unicos = {}, []
for k, lst in SPECS.items():
    if k == "andalucia":
        continue
    for i in lst:
        if i["id"] not in porid:
            porid[i["id"]] = dict(i, pagina=k)
            unicos.append(porid[i["id"]])

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
# 1. Ejercicios autocorregibles
# =====================================================================================
pagina("ejercicios.qmd", r'''---
title: "Ejercicios autocorregibles"
subtitle: "Practica con los datos más recientes: preguntas al azar o de un área, con la solución explicada"
toc: false
---

Cada pregunta se genera **con el último dato publicado por Eurostat**, así que nunca hay dos iguales. Escribe tu respuesta (puedes usar coma decimal) y pulsa **Comprobar**: verás si es correcta y cómo se calcula. Elige preguntas **al azar** de todas las áreas o céntrate en **un área** concreta.

__HELPERS__

```{ojs}
//| echo: false
especEj = __ESPECS__
areasEj = (__AREAS__)
viewof modoEj = Inputs.radio(["Al azar, de todas las áreas", "De un área concreta"], {label: "Preguntas", value: "Al azar, de todas las áreas"})
```

```{ojs}
//| echo: false
viewof areaEj = Inputs.select(Object.keys(areasEj), {label: "Área", format: k => areasEj[k], disabled: modoEj.startsWith("Al azar")})
viewof nuevaEj = Inputs.button("🎲 Nueva pregunta", {value: 0, reduce: v => v + 1})
```

```{ojs}
//| echo: false
generarEj = (s, rows) => {
  const terrs = [...new Set(rows.map(r => r.territorio))];
  const objetivo = s.regional ? (terrs.includes("Andalucía") ? "Andalucía" : terrs[0]) : (terrs.includes("España") ? "España" : terrs[0]);
  const serie = rows.filter(r => r.territorio === objetivo).sort((a, b) => a.fecha - b.fecha);
  if (serie.length < 6) return null;
  const esPct = /%|puntos|saldo/i.test(s.unidad);
  const r2 = (v) => Math.round(v * 100) / 100;
  const ult = serie[serie.length - 1];
  const tipos = ["variacion", "media"];
  if (!s.sinGeo) tipos.push("comparar");
  if (s.frecuencia === "Anual" && !esPct && serie.every(r => r.valor > 0)) tipos.push("tmaa");
  const tipo = tipos[Math.floor(Math.random() * tipos.length)];
  const enlace = `${s.pagina}.html?i=${s.id}`;
  const en = s.sinGeo ? "" : ` en ${objetivo}`;
  if (tipo === "variacion") {
    const hace = serie.filter(r => r.fecha.getFullYear() === ult.fecha.getFullYear() - 1 && r.fecha.getMonth() === ult.fecha.getMonth()).pop();
    if (!hace) return null;
    if (esPct) {
      const sol = r2(ult.valor - hace.valor);
      return {s, enlace, tipo, sol, tol: 0.051, unidadResp: "puntos",
        texto: `${s.nombre}${en}: ${fmt(hace.valor)} (${hace.periodo}) y ${fmt(ult.valor)} (${ult.periodo}). ¿Cuántos **puntos** ha variado en un año? (escribe un número negativo si ha bajado)`,
        expl: `Cuando el indicador ya es un porcentaje o un saldo, la variación se mide en puntos: ${fmt(ult.valor)} − ${fmt(hace.valor)} = <b>${fmt(sol)} puntos</b>. No es lo mismo que una variación porcentual.`};
    }
    const sol = r2(100 * (ult.valor / hace.valor - 1));
    return {s, enlace, tipo, sol, tol: Math.max(0.11, Math.abs(sol) * 0.005), unidadResp: "%",
      texto: `${s.nombre}${en}: ${fmt(hace.valor)} (${hace.periodo}) y ${fmt(ult.valor)} (${ult.periodo}). Calcula la **tasa de variación interanual** en % (con dos decimales).`,
      expl: `Tasa de variación = (valor final / valor inicial − 1) × 100 = (${fmt(ult.valor)} / ${fmt(hace.valor)} − 1) × 100 = <b>${fmt(sol)} %</b>.`};
  }
  if (tipo === "media") {
    const ult4 = serie.slice(-4);
    const sol = r2(d3.mean(ult4, r => r.valor));
    return {s, enlace, tipo, sol, tol: Math.max(0.011, Math.abs(sol) * 0.001), unidadResp: s.unidad,
      texto: `Estos son los cuatro últimos datos de ${s.nombre}${en}: ${ult4.map(r => `${r.periodo}: ${fmt(r.valor)}`).join(" · ")}. Calcula su **media aritmética** (con dos decimales).`,
      expl: `Media = suma de los valores / número de valores = ${fmt(d3.sum(ult4, r => r.valor))} / 4 = <b>${fmt(sol)}</b> ${s.unidad}.`};
  }
  if (tipo === "tmaa") {
    const n = Math.min(10, serie.length - 1);
    const ini = serie[serie.length - 1 - n];
    const sol = r2(100 * (Math.pow(ult.valor / ini.valor, 1 / n) - 1));
    return {s, enlace, tipo, sol, tol: Math.max(0.051, Math.abs(sol) * 0.01), unidadResp: "%",
      texto: `${s.nombre}${en}: ${fmt(ini.valor)} en ${ini.periodo} y ${fmt(ult.valor)} en ${ult.periodo}. Calcula la **tasa media anual acumulativa** de crecimiento en % (con dos decimales).`,
      expl: `Tasa media anual acumulativa = [(valor final / valor inicial)^(1/n) − 1] × 100, con n = ${n} años: [(${fmt(ult.valor)} / ${fmt(ini.valor)})^(1/${n}) − 1] × 100 = <b>${fmt(sol)} %</b>.`};
  }
  // comparar: ¿qué territorio tiene el valor más alto o más bajo?
  const periodos = d3.rollup(rows, v => v.length, r => r.periodo);
  const per = [...periodos].filter(([, c]) => c >= 5).map(([p]) => p).sort().pop();
  if (!per) return null;
  const enPer = rows.filter(r => r.periodo === per && !["UE-27", "Zona euro", "Zona euro (19)"].includes(r.territorio));
  const opciones = d3.shuffle(enPer.slice()).slice(0, 4);
  if (opciones.length < 4) return null;
  const mayor = Math.random() < 0.5;
  const correcta = (mayor ? d3.greatest : d3.least)(opciones, r => r.valor);
  return {s, enlace, tipo, opciones: opciones.map(r => r.territorio), sol: correcta.territorio,
    texto: `¿Cuál de estos territorios tenía el valor **más ${mayor ? "alto" : "bajo"}** de ${s.nombre} en ${per}?`,
    expl: opciones.sort((a, b) => b.valor - a.valor).map(r => `${r.territorio}: ${fmt(r.valor)}`).join(" · ") + ` (${s.unidad}). La respuesta correcta es <b>${correcta.territorio}</b>.`};
}
```

```{ojs}
//| echo: false
preguntaEj = {
  nuevaEj;
  const pool = especEj.filter(s => modoEj.startsWith("Al azar") || s.pagina === areaEj);
  for (let k = 0; k < 8; k++) {
    const s = pool[Math.floor(Math.random() * pool.length)];
    const d = await cargar(s).catch(() => ({ok: false}));
    if (!d.ok) continue;
    const q = generarEj(s, d.rows);
    if (q) return q;
  }
  return null;
}
```

```{ojs}
//| echo: false
{
  const marcador = window.__cceeEj ?? (window.__cceeEj = {ok: 0, total: 0});
  if (!preguntaEj) return html`<div class="callout callout-warning"><p>No se ha podido generar una pregunta con datos de Eurostat. Pulsa <b>Nueva pregunta</b> otra vez.</p></div>`;
  const q = preguntaEj;
  const md = (t) => t.replace(/\*\*(.+?)\*\*/g, "<b>$1</b>");
  const fb = html`<div class="ej-fb"></div>`;
  const pts = html`<span class="ej-pts">Aciertos: ${marcador.ok} de ${marcador.total}</span>`;
  let respondida = false;
  const corregir = (ok, resp) => {
    if (!respondida) { respondida = true; marcador.total += 1; if (ok) marcador.ok += 1; }
    pts.textContent = `Aciertos: ${marcador.ok} de ${marcador.total}`;
    fb.className = "ej-fb " + (ok ? "ej-ok" : "ej-mal");
    fb.innerHTML = (ok ? "✅ <b>¡Correcto!</b> " : `❌ <b>No es correcto</b>${resp !== undefined ? ` (tu respuesta: ${resp})` : ""}. `) + q.expl +
      ` <a href="${q.enlace}">Ver el indicador y su gráfico</a>.`;
    window.cceeEvento && window.cceeEvento(`ejercicio/${q.s.pagina}/${ok ? "acierto" : "fallo"}`, `Ejercicio ${ok ? "acertado" : "fallado"}: ${q.s.pagina}`, true);
  };
  let entrada;
  if (q.opciones) {
    entrada = html`<div class="ej-opciones">${q.opciones.map(o => {
      const b = html`<button class="ej-op">${o}</button>`;
      b.onclick = () => corregir(o === q.sol, o);
      return b;
    })}</div>`;
  } else {
    const inp = html`<input class="ej-input" type="text" inputmode="decimal" placeholder="Tu respuesta">`;
    const btn = html`<button class="ej-check">Comprobar</button>`;
    const leer = () => {
      const t = inp.value.trim().replace(/\s/g, "").replace(/\.(?=\d{3}(\D|$))/g, "").replace(",", ".");
      const v = parseFloat(t);
      if (!Number.isFinite(v)) { fb.className = "ej-fb ej-mal"; fb.textContent = "Escribe un número (por ejemplo, 2,35)."; return; }
      corregir(Math.abs(v - q.sol) <= q.tol, inp.value);
    };
    btn.onclick = leer;
    inp.onkeydown = (e) => { if (e.key === "Enter") leer(); };
    entrada = html`<div class="ej-row">${inp}<span class="ej-unidad">${q.unidadResp}</span>${btn}</div>`;
  }
  return html`<div class="ej-card">
    <div class="ej-meta"><span class="ej-area">${areasEj[q.s.pagina]}</span>${pts}</div>
    ${Object.assign(document.createElement("p"), {className: "ej-q", innerHTML: md(q.texto)})}
    ${entrada}${fb}
    <p class="source">Datos: Eurostat (${q.s.code}), descargados ahora mismo.</p>
  </div>`;
}
```

::: {.callout-tip appearance="simple"}
**Para el profesorado.** Proyecta la página en clase y resuelve las preguntas con el grupo, o pide que cada estudiante haga cinco preguntas del área de la asignatura y entregue una captura con su marcador. Tipos de preguntas: tasa de variación interanual, variación en puntos, media aritmética, tasa media anual acumulativa y comparación entre territorios.
:::
''', ESPECS=J(unicos), AREAS=J(AREAS))

# =====================================================================================
# 2. Generador de gráficos para el TFG
# =====================================================================================
pagina("graficos.qmd", r'''---
title: "Generador de gráficos para el TFG"
subtitle: "Elige indicador, territorios y periodo, y descarga un gráfico listo para tu trabajo, con la fuente y la cita"
toc: false
---

Crea un gráfico con datos oficiales de Eurostat y descárgalo en **PNG** (para Word o PowerPoint) o en **SVG** (vectorial, para LaTeX o diseño). El gráfico incluye la fuente y la fecha de consulta, y abajo tienes la **cita en formato APA** para la bibliografía.

__HELPERS__

```{ojs}
//| echo: false
especG = __ESPECS__
porIdG = new Map(especG.map(d => [d.id, d]))
viewof indG = Inputs.select(especG, {label: "Indicador", format: d => d.nombre, value: porIdG.get("tasa-de-paro")})
```

```{ojs}
//| echo: false
datosG = cargar(indG)
terrsG = datosG.ok ? [...new Set(datosG.rows.map(r => r.territorio))].sort((a, b) => a.localeCompare(b, "es")) : []
aniosG = datosG.ok ? [...new Set(datosG.rows.map(r => String(r.fecha.getFullYear())))].sort() : []
viewof selG = Inputs.select(terrsG, {label: "Territorios (Ctrl o ⌘ para elegir varios)", multiple: true, size: 7,
  value: ((x) => x.length ? x : terrsG.slice(0, 1))((indG.regional ? ["Andalucía", "España"] : ["España", "UE-27", "Alemania", "Francia", "Italia", "Portugal"]).filter(t => terrsG.includes(t)))})
viewof desdeG = Inputs.select(aniosG, {label: "Desde", value: aniosG[Math.max(0, aniosG.length - 11)]})
viewof hastaG = Inputs.select(aniosG, {label: "Hasta", value: aniosG[aniosG.length - 1]})
viewof tipoG = Inputs.radio(["Líneas (evolución)", "Barras (último dato)"], {label: "Tipo", value: indG.frecuencia === "Anual" && indG.regional ? "Barras (último dato)" : "Líneas (evolución)"})
viewof paletaG = Inputs.radio(["Color", "Escala de grises"], {label: "Colores", value: "Color"})
viewof tituloG = Inputs.text({label: "Título", value: indG.nombre, width: 560})
viewof subtituloG = Inputs.text({label: "Subtítulo", value: indG.unidad, width: 560})
```

```{ojs}
//| echo: false
hoyG = new Date().toLocaleDateString("es-ES", {day: "numeric", month: "long", year: "numeric"})
graficoG = {
  if (!datosG.ok) return html`<div class="callout callout-warning"><p>No se han podido cargar los datos de Eurostat (${datosG.error}).</p></div>`;
  const terrs = selG.length ? selG : terrsG.slice(0, 1);
  const filas = datosG.rows.filter(r => terrs.includes(r.territorio) && String(r.fecha.getFullYear()) >= desdeG && String(r.fecha.getFullYear()) <= hastaG);
  const W = 900, H = 540, top = 112, bottom = 52;
  const base = paletaG === "Color" ? ["#B5175F", "#F29200", "#3C3C3B", "#2A7AB0", "#4C9A2A", "#8E5BB5", "#D3545E", "#7A7A7A"] : ["#111", "#555", "#888", "#aaa", "#333", "#777", "#999", "#bbb"];
  const color = {domain: terrs, range: base};
  let chart;
  if (tipoG.startsWith("Líneas")) {
    chart = Plot.plot({width: W, height: H - top - bottom, marginLeft: 64, marginRight: 24, marginTop: 10,
      x: {type: "time", label: null}, y: {label: null, grid: true, tickFormat: v => fmt(v)}, color,
      style: {fontSize: "13px", fontFamily: "Inter, Arial, sans-serif"},
      marks: [indG.cero ? Plot.ruleY([0], {stroke: "#999"}) : null,
        Plot.line(filas, {x: "fecha", y: "valor", stroke: "territorio", strokeWidth: 2.4}),
        Plot.dot(filas.filter((r, i, a) => r === d3.greatest(a.filter(x => x.territorio === r.territorio), x => x.fecha)), {x: "fecha", y: "valor", fill: "territorio", r: 4})]});
  } else {
    const ult = terrs.map(t => d3.greatest(filas.filter(r => r.territorio === t), r => r.fecha)).filter(Boolean).sort((a, b) => b.valor - a.valor);
    chart = Plot.plot({width: W, height: H - top - bottom, marginLeft: 150, marginRight: 70, marginTop: 10,
      x: {label: null, grid: true, tickFormat: v => fmt(v)}, y: {label: null, domain: ult.map(d => d.territorio)}, color,
      style: {fontSize: "13px", fontFamily: "Inter, Arial, sans-serif"},
      marks: [Plot.barX(ult, {x: "valor", y: "territorio", fill: "territorio"}), Plot.ruleX([0]),
        Plot.text(ult, {x: "valor", y: "territorio", text: d => `${fmt(d.valor)} (${d.periodo})`, dx: 6, textAnchor: "start", fontSize: 12})]});
  }
  const svg = d3.create("svg").attr("xmlns", "http://www.w3.org/2000/svg").attr("width", W).attr("height", H)
    .attr("viewBox", `0 0 ${W} ${H}`).attr("font-family", "Inter, Arial, sans-serif").attr("class", "grafico-tfg");
  svg.append("rect").attr("width", W).attr("height", H).attr("fill", "#fff");
  svg.append("text").attr("x", 20).attr("y", 34).attr("font-size", 21).attr("font-weight", 700).attr("fill", "#222").text(tituloG);
  svg.append("text").attr("x", 20).attr("y", 58).attr("font-size", 14).attr("fill", "#666").text(subtituloG);
  let lx = 20;
  if (tipoG.startsWith("Líneas")) terrs.forEach((t, i) => {
    const g = svg.append("g").attr("transform", `translate(${lx},80)`);
    g.append("rect").attr("width", 14).attr("height", 14).attr("y", -11).attr("rx", 3).attr("fill", base[i % base.length]);
    g.append("text").attr("x", 20).attr("font-size", 13).attr("fill", "#333").text(t);
    lx += 34 + t.length * 7.5;
  });
  const nodo = chart.tagName.toLowerCase() === "svg" ? chart : chart.querySelector("svg");
  nodo.setAttribute("x", 0); nodo.setAttribute("y", top - 18);
  svg.node().appendChild(nodo);
  svg.append("text").attr("x", 20).attr("y", H - 26).attr("font-size", 11.5).attr("fill", "#555")
    .text(`Fuente: Eurostat (${datosG.code}), datos consultados el ${hoyG}.`);
  svg.append("text").attr("x", 20).attr("y", H - 10).attr("font-size", 11.5).attr("fill", "#555")
    .text("Elaborado con CCEEscopio, Facultad de Ciencias Económicas y Empresariales, Universidad de Granada.");
  return svg.node();
}
```

```{ojs}
//| echo: false
{
  if (!datosG.ok) return html``;
  const nombre = `grafico_${indG.id}`;
  const svgTxt = () => new XMLSerializer().serializeToString(graficoG);
  const png = () => new Promise(resolve => {
    const img = new Image();
    img.onload = () => {
      const c = document.createElement("canvas"); c.width = 1800; c.height = 1080;
      const ctx = c.getContext("2d"); ctx.fillStyle = "#fff"; ctx.fillRect(0, 0, c.width, c.height);
      ctx.drawImage(img, 0, 0, c.width, c.height); c.toBlob(resolve, "image/png");
    };
    img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svgTxt());
  });
  const terrs = selG.length ? selG : terrsG.slice(0, 1);
  const filas = datosG.rows.filter(r => terrs.includes(r.territorio) && String(r.fecha.getFullYear()) >= desdeG && String(r.fecha.getFullYear()) <= hastaG);
  return html`<div class="graf-botones">
    ${DOM.download(png, `${nombre}.png`, "⬇ Descargar PNG")}
    ${DOM.download(() => new Blob([svgTxt()], {type: "image/svg+xml"}), `${nombre}.svg`, "⬇ Descargar SVG")}
    ${DOM.download(() => new Blob([csv(filas)], {type: "text/csv;charset=utf-8"}), `${nombre}.csv`, "⬇ Datos (CSV)")}
  </div>`;
}
```

```{ojs}
//| echo: false
{
  if (!datosG.ok) return html``;
  const anio = new Date().getFullYear();
  const url = `https://ec.europa.eu/eurostat/databrowser/view/${datosG.code}/default/table?lang=es`;
  const apa = `Eurostat. (${anio}). ${indG.nombre} [Conjunto de datos ${datosG.code}]. Oficina Estadística de la Unión Europea. Recuperado el ${hoyG} de ${url}`;
  const apaWeb = `Muñoz, J.F., Álvarez, E. (2026). CCEEscopio D+I: observatorio de indicadores económicos y empresariales al servicio de la Docencia y la Investigación [Sitio web]. Facultad de Ciencias Económicas y Empresariales, Universidad de Granada. Recuperado el ${hoyG} de ${location.origin + location.pathname.replace(/[^/]*$/, "")}`;
  const caja = (t) => {
    const b = html`<button class="copiar">Copiar</button>`;
    b.onclick = async () => { try { await navigator.clipboard.writeText(t); b.textContent = "Copiado ✓"; } catch (e) { b.textContent = "Selecciona y copia"; } };
    return html`<div class="cita"><span>${t}</span>${b}</div>`;
  };
  return html`<h3>Cómo citarlo (APA 7.ª edición)</h3>
    <p><b>Fuente de los datos</b> (en la bibliografía):</p>${caja(apa)}
    <p><b>CCEEscopio</b> (la herramienta con la que has hecho el gráfico):</p>${caja(apaWeb)}
    <p class="source">Debajo del gráfico, en el trabajo, escribe: «Fuente: elaboración propia a partir de Eurostat (${datosG.code})».</p>`;
}
```

::: {.callout-note appearance="simple"}
**Consejos para el TFG.** No pongas más de seis líneas en un mismo gráfico. Usa barras para comparar territorios en un momento y líneas para ver la evolución. Explica siempre en el texto qué muestra el gráfico y cita la fuente debajo. Si vas a imprimir en blanco y negro, elige **Escala de grises**.
:::
''', ESPECS=J(unicos))

# =====================================================================================
# 3. Simulador de hipotecas y préstamos
# =====================================================================================
EUR12 = dict(id="euribor-12", nombre="Euríbor a 12 meses", code="irt_st_m", query="&int_rt=IRT_M12&geo=EA", unidad="%",
             frecuencia="Mensual", sinGeo=True, serie="Euríbor a 12 meses", desde=2000,
             alt=[dict(code="irt_st_m", query="&int_rt=IRT_M12")])
pagina("hipoteca.qmd", r'''---
title: "Simulador de hipotecas y préstamos"
subtitle: "Cuota, intereses, TAE y cuadro de amortización (sistema francés) con el euríbor real"
toc: false
---

Calcula la **cuota mensual** de una hipoteca o de un préstamo personal, cuánto pagarás en **intereses**, la **TAE** y el **cuadro de amortización**. En las hipotecas variables se usa el **euríbor a 12 meses** más reciente publicado por Eurostat, y puedes simular qué pasaría si sube o baja. Para Matemáticas Financieras, Operaciones Financieras y Finanzas personales.

__HELPERS__

```{ojs}
//| echo: false
especEur = (__EUR12__)
datosEur = cargar(especEur)
eurUlt = datosEur.ok ? d3.greatest(datosEur.rows, r => r.fecha) : null
```

```{ojs}
//| echo: false
viewof capitalH = Inputs.number([0, 1e9], {label: "Capital prestado (€)", value: 150000, step: 1000})
viewof plazoH = Inputs.range([1, 40], {label: "Plazo (años)", value: 25, step: 1})
viewof tipoH = Inputs.radio(["Fijo", "Variable (euríbor + diferencial)"], {label: "Tipo de interés", value: "Variable (euríbor + diferencial)"})
```

```{ojs}
//| echo: false
viewof fijoH = Inputs.range([0, 15], {label: "Tipo fijo (% anual)", value: 3, step: 0.05, disabled: !tipoH.startsWith("Fijo")})
viewof eurH = Inputs.range([-1, 6], {label: "Euríbor inicial (%)", value: eurUlt ? Math.round(eurUlt.valor * 100) / 100 : 2.5, step: 0.01, disabled: tipoH.startsWith("Fijo")})
viewof difH = Inputs.range([0, 5], {label: "Diferencial (puntos)", value: 0.8, step: 0.05, disabled: tipoH.startsWith("Fijo")})
viewof subidaH = Inputs.range([-3, 5], {label: "Escenario: cambio del euríbor desde el 2.º año (puntos)", value: 0, step: 0.25, disabled: tipoH.startsWith("Fijo")})
viewof comisionH = Inputs.range([0, 3], {label: "Comisión de apertura (%)", value: 0, step: 0.1})
viewof gastosH = Inputs.number([0, 1e6], {label: "Otros gastos iniciales a cargo del cliente (€)", value: 0, step: 50})
```

```{ojs}
//| echo: false
simH = {
  const n = plazoH * 12;
  const cuotaDe = (C, iAnual, m) => { const r = iAnual / 1200; return r === 0 ? C / m : C * r / (1 - Math.pow(1 + r, -m)); };
  const variable = !tipoH.startsWith("Fijo");
  const i1 = variable ? eurH + difH : fijoH;
  const i2 = variable ? Math.max(0, eurH + subidaH) + difH : fijoH;
  let pendiente = capitalH, cuota = cuotaDe(capitalH, i1, n), filas = [], i = i1;
  for (let k = 1; k <= n; k++) {
    if (variable && k === 13) { i = i2; cuota = cuotaDe(pendiente, i, n - 12); }
    const intereses = pendiente * i / 1200, amort = cuota - intereses;
    pendiente = Math.max(0, pendiente - amort);
    filas.push({mes: k, anio: Math.ceil(k / 12), tipo: i, cuota, intereses, amortizacion: amort, pendiente});
  }
  // TAE: tipo que iguala lo recibido neto de gastos con el valor actual de las cuotas
  const neto = capitalH * (1 - comisionH / 100) - gastosH;
  const va = (r) => d3.sum(filas, f => f.cuota / Math.pow(1 + r, f.mes));
  let lo = -0.0099, hi = 0.05;
  for (let k = 0; k < 100; k++) { const mid = (lo + hi) / 2; if (va(mid) > neto) lo = mid; else hi = mid; }
  const tae = (Math.pow(1 + (lo + hi) / 2, 12) - 1) * 100;
  const porAnio = d3.rollups(filas, v => ({anio: v[0].anio, tipo: v[0].tipo, cuota: v[v.length - 1].cuota, intereses: d3.sum(v, f => f.intereses), amortizacion: d3.sum(v, f => f.amortizacion), pendiente: v[v.length - 1].pendiente}), f => f.anio).map(d => d[1]);
  return {filas, porAnio, cuota1: filas[0].cuota, cuota2: filas[Math.min(12, n - 1)].cuota, i1, i2, tae, variable,
          totalInt: d3.sum(filas, f => f.intereses), totalPag: d3.sum(filas, f => f.cuota)};
}
```

```{ojs}
//| echo: false
{
  const e2 = (v) => locES.format(",.2f")(v);
  const tarjeta = (l, v, s) => html`<div class="kpi"><div class="kpi-l">${l}</div><div class="kpi-n">${v}</div><div class="kpi-s">${s}</div></div>`;
  return html`<div class="kpi-grid">
    ${tarjeta("Cuota mensual", `${e2(simH.cuota1)} €`, `Tipo del primer año: ${e2(simH.i1)} %`)}
    ${simH.variable ? tarjeta("Cuota desde el 2.º año", `${e2(simH.cuota2)} €`, `Tipo: ${e2(simH.i2)} % (${subidaH >= 0 ? "+" : ""}${e2(subidaH)} puntos de euríbor)`) : ""}
    ${tarjeta("Intereses totales", `${locES.format(",.0f")(simH.totalInt)} €`, `${e2(100 * simH.totalInt / capitalH)} % del capital`)}
    ${tarjeta("Total a pagar", `${locES.format(",.0f")(simH.totalPag)} €`, `${plazoH * 12} cuotas`)}
    ${tarjeta("TAE", `${e2(simH.tae)} %`, comisionH || gastosH ? "Incluye comisión y gastos" : "Sin comisiones ni gastos")}
  </div>
  ${eurUlt ? html`<p class="source">Euríbor a 12 meses más reciente: <b>${e2(eurUlt.valor)} %</b> (${eurUlt.periodo}), Eurostat (${datosEur.code}).</p>` : html`<p class="source">No se ha podido descargar el euríbor; ajusta su valor a mano.</p>`}`;
}
```

```{ojs}
//| echo: false
Plot.plot({
  height: 300, marginLeft: 60, x: {label: "Año", tickFormat: d => String(d), interval: 1}, y: {label: "€ pagados en el año", grid: true, tickFormat: v => locES.format(",.0f")(v)},
  color: {legend: true, domain: ["Intereses", "Amortización de capital"], range: ["#F29200", "#B5175F"]},
  marks: [
    Plot.barY(simH.porAnio.flatMap(d => [{anio: d.anio, tipo: "Intereses", v: d.intereses}, {anio: d.anio, tipo: "Amortización de capital", v: d.amortizacion}]),
      {x: "anio", y: "v", fill: "tipo", title: d => `Año ${d.anio} · ${d.tipo}: ${locES.format(",.0f")(d.v)} €`}),
    Plot.ruleY([0])
  ]
})
```

```{ojs}
//| echo: false
{
  const e2 = (v) => locES.format(",.2f")(v);
  const tabla = Inputs.table(simH.porAnio, {
    columns: ["anio", "tipo", "cuota", "intereses", "amortizacion", "pendiente"],
    header: {anio: "Año", tipo: "Tipo (%)", cuota: "Cuota mensual (€)", intereses: "Intereses del año (€)", amortizacion: "Capital amortizado (€)", pendiente: "Capital pendiente (€)"},
    format: {anio: d => d, tipo: e2, cuota: e2, intereses: e2, amortizacion: e2, pendiente: e2}, rows: 12, layout: "auto"});
  const desc = DOM.download(() => new Blob(["﻿" + d3.dsvFormat(";").format(simH.filas.map(f => ({mes: f.mes, tipo_anual: e2(f.tipo), cuota: e2(f.cuota), intereses: e2(f.intereses), amortizacion: e2(f.amortizacion), capital_pendiente: e2(f.pendiente)})))], {type: "text/csv;charset=utf-8"}), "cuadro_amortizacion.csv", "⬇ Cuadro de amortización mensual (CSV)");
  return html`<h3>Cuadro de amortización (resumen anual)</h3>${tabla}${desc}`;
}
```

```{ojs}
//| echo: false
datosEur.ok ? Plot.plot({height: 220, marginLeft: 45, x: {type: "time", label: null}, y: {label: "Euríbor a 12 meses (%)", grid: true},
  marks: [Plot.ruleY([0], {stroke: "#999"}), Plot.line(datosEur.rows, {x: "fecha", y: "valor", stroke: "#B5175F", strokeWidth: 2}),
    Plot.tip(datosEur.rows, Plot.pointerX({x: "fecha", y: "valor", title: d => `${d.periodo}: ${locES.format(",.3f")(d.valor)} %`}))]}) : html``
```

::: {.callout-note appearance="simple"}
**Cómo se calcula.** Sistema francés (cuota constante): cuota = C · i / (1 − (1 + i)^−n), con i = tipo anual / 12 y n = número de meses. En la hipoteca variable la cuota se recalcula al cumplirse el primer año con el nuevo tipo y el capital pendiente. La **TAE** es el tipo anual efectivo que iguala lo que recibes (capital menos comisión y gastos) con el valor actual de todas las cuotas. Es una simulación orientativa: los bancos revisan el tipo cada 6 o 12 meses con el euríbor del mes anterior y pueden aplicar bonificaciones.
:::
''', EUR12=J(EUR12))

# =====================================================================================
# 5. Glosario de indicadores
# =====================================================================================
CONCEPTOS = [
    ("Puntos porcentuales frente a porcentaje", "Si la tasa de paro pasa del 12 % al 10 %, baja **2 puntos porcentuales**, pero baja un **16,7 %** (2/12). Los cambios de indicadores que ya son porcentajes se expresan en puntos.", "Decir que el paro «ha bajado un 2 %» cuando ha bajado 2 puntos."),
    ("Tasa de variación interanual", "(Valor del periodo / valor del mismo periodo del año anterior − 1) × 100. Compara meses o trimestres iguales y evita el efecto de la estacionalidad.", "Comparar un mes con el anterior en series con mucha estacionalidad (turismo, empleo)."),
    ("Tasa media anual acumulativa", "[(Valor final / valor inicial)^(1/n) − 1] × 100, con n años. Es el crecimiento anual constante que lleva del valor inicial al final.", "Dividir el crecimiento total entre el número de años (media simple), que sobrestima el crecimiento."),
    ("Números índice y cambio de base", "Índice = 100 × valor / valor del año base. Para cambiar de base, se divide toda la serie entre el valor del nuevo año base y se multiplica por 100. Las tasas de variación no cambian.", "Comparar niveles de dos índices con bases distintas."),
    ("Euros corrientes y euros constantes", "Los euros corrientes son los de cada año; los constantes descuentan la inflación: valor real = valor nominal × IPC(año base) / IPC(año). Herramientas: [Conversor de unidades](conversor.qmd) y [Calculadora de inflación](calculadora.qmd).", "Comparar salarios o precios de años distintos sin deflactar."),
    ("Paridad de poder de compra (PPC)", "Tipo de conversión que iguala el poder adquisitivo entre países. El PIB per cápita en PPC compara niveles de vida eliminando las diferencias de precios.", "Comparar rentas entre países en euros sin ajustar por el nivel de precios."),
    ("Desestacionalización", "Las series corregidas de estacionalidad y calendario (SA, SCA) eliminan los movimientos que se repiten cada año. Permiten comparar un periodo con el inmediatamente anterior.", "Mezclar datos originales y desestacionalizados en el mismo análisis."),
    ("IPC frente a IPCA", "El IPC es el índice nacional del INE; el IPCA es el índice armonizado de la UE, con la misma metodología en todos los países. En España las tasas suelen ser muy parecidas, pero no iguales.", "Actualizar un contrato de alquiler con el IPCA cuando la ley o el contrato hablan del IPC."),
    ("Inflación subyacente", "Variación de los precios sin los componentes más volátiles (energía y, según la definición, alimentos no elaborados). Indica la tendencia de fondo de la inflación.", "Pensar que una inflación general baja por el abaratamiento de la energía significa que los precios ya no presionan."),
    ("Tasa de paro, de actividad y de empleo", "Paro = parados / población activa. Actividad = activos / población en edad de trabajar. Empleo = ocupados / población en edad de trabajar. El paro puede bajar porque la gente deja de buscar empleo, no solo porque encuentre trabajo.", "Usar el paro registrado en las oficinas de empleo como si fuera la tasa de paro de la EPA."),
    ("Índice de Gini", "Mide la desigualdad de la renta entre 0 (todos tienen lo mismo) y 100 (una persona lo tiene todo). Se calcula con la renta disponible equivalente de los hogares (EU-SILC).", "Interpretar diferencias pequeñas sin tener en cuenta el error de muestreo de la encuesta."),
    ("Ratio S80/S20", "Cociente entre la renta del 20 % de la población con más ingresos y la del 20 % con menos. Un valor de 5 significa que el quintil superior recibe cinco veces más que el inferior.", "Confundirlo con un porcentaje."),
    ("Tasa AROPE", "Personas en riesgo de pobreza o exclusión social: en riesgo de pobreza (renta < 60 % de la mediana), con carencia material y social severa o en hogares con baja intensidad en el empleo. Una persona se cuenta una sola vez.", "Sumar las tres componentes, que se solapan."),
    ("Umbral y tasa de riesgo de pobreza", "El umbral es el 60 % de la renta mediana equivalente del país; la tasa es el porcentaje de personas por debajo. Es una medida relativa: si la renta de todos sube igual, la tasa no cambia.", "Leerla como pobreza absoluta o comparar umbrales entre países sin ajustar por precios."),
    ("Déficit y deuda pública (% del PIB)", "El déficit es la diferencia entre ingresos y gastos públicos de un año; la deuda es el saldo acumulado. Ambos se expresan en % del PIB para comparar países.", "Confundir reducir el déficit con reducir la deuda."),
    ("Prima de riesgo", "Diferencia entre la rentabilidad del bono a 10 años de un país y la del bono alemán, normalmente en puntos básicos (1 punto porcentual = 100 puntos básicos). Ver [Mercados al día](mercados.qmd).", "Expresarla en porcentaje en lugar de en puntos básicos."),
    ("Euríbor", "Tipo de interés al que los bancos de la zona euro se prestan dinero entre sí. El euríbor a 12 meses es la referencia de la mayoría de las hipotecas variables en España. Ver el [Simulador de hipotecas](hipoteca.qmd).", "Pensar que la cuota cambia en cuanto se mueve el euríbor: se revisa cada 6 o 12 meses."),
    ("Pernoctaciones, viajeros y estancia media", "Viajeros son las llegadas a los alojamientos; pernoctaciones, las noches. Estancia media = pernoctaciones / viajeros.", "Comparar pernoctaciones entre regiones sin tener en cuenta su tamaño o su oferta de plazas."),
    ("Saldo por cuenta corriente", "Diferencia entre los ingresos y los pagos de un país con el exterior por bienes, servicios, rentas y transferencias. Un saldo positivo indica capacidad de financiación frente al resto del mundo.", "Identificarlo solo con la balanza comercial de bienes."),
    ("Productividad y costes laborales unitarios", "Productividad = producción por hora trabajada. Coste laboral unitario = coste laboral por unidad producida: sube si los salarios crecen más que la productividad.", "Comparar salarios entre países sin tener en cuenta la productividad."),
]

def slug(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")

def md_conceptos():
    out = []
    for t, d, e in sorted(CONCEPTOS, key=lambda x: slug(x[0])):
        out.append(f'::: {{.glosario-item}}\n### {t} {{#{slug(t)}}}\n\n{d}\n\n<span class="glos-error">⚠ Error frecuente:</span> {e}\n:::\n')
    return "\n".join(out)

def md_indicadores():
    out = []
    for s in sorted(unicos, key=lambda x: slug(x["nombre"])):
        url = f"https://ec.europa.eu/eurostat/databrowser/view/{s['code']}/default/table?lang=es"
        out.append(f'::: {{.glosario-item}}\n### {s["nombre"]} {{#ind-{s["id"]}}}\n\n{s.get("descripcion", "")}\n\n'
                   f'<span class="glos-meta">{s["unidad"]} · {s["frecuencia"]} · Área: [{AREAS[s["pagina"]]}]({s["pagina"]}.qmd) · '
                   f'Fuente: [Eurostat, {s["code"]}]({url}) · [Ver el gráfico]({s["pagina"]}.qmd?i={s["id"]})</span>\n:::\n')
    return "\n".join(out)

pagina("glosario.qmd", r'''---
title: "Glosario de indicadores"
subtitle: "Qué mide cada indicador, cómo se calcula, de dónde sale y los errores de interpretación más frecuentes"
toc: true
toc-depth: 2
---

```{=html}
<div class="glos-buscar"><input id="glos-q" type="search" placeholder="Buscar en el glosario (por ejemplo: paro, Gini, euríbor)…" aria-label="Buscar en el glosario"><span id="glos-n"></span></div>
<script>
document.addEventListener("DOMContentLoaded", () => {
  const q = document.getElementById("glos-q"), n = document.getElementById("glos-n");
  const items = [...document.querySelectorAll(".glosario-item")];
  const norm = s => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  q.addEventListener("input", () => {
    const t = norm(q.value.trim()); let k = 0;
    items.forEach(el => { const ok = !t || norm(el.textContent).includes(t); el.style.display = ok ? "" : "none"; if (ok) k++; });
    n.textContent = t ? `${k} resultados` : "";
  });
});
</script>
```

## Conceptos clave

__CONCEPTOS__

## Los __N__ indicadores de CCEEscopio

__INDICADORES__
''', CONCEPTOS=md_conceptos(), INDICADORES=md_indicadores(), N=str(len(unicos)), HELPERS="")

# =====================================================================================
# 6. Comparador de comunidades autónomas
# =====================================================================================
REG = [dict(s) for s in unicos if s.get("regional")]
for k, lst in SPECS.items():
    if k == "andalucia":
        for s in lst:
            if s.get("regional") and s["id"] not in {r["id"] for r in REG} and s["code"] not in {r["code"] for r in REG}:
                REG.append(dict(s, pagina="andalucia"))
MEJOR = {"pib-per-capita-en-paridad-de-poder-de-compra": 1, "tasa-de-paro-por-regiones": -1, "tasa-de-empleo-por-regiones-20-64-anos": 1,
         "gasto-en-i-d-por-regiones-del-pib": 1, "riesgo-de-pobreza-o-exclusion-social-por-regiones": -1,
         "tasa-de-riesgo-de-pobreza-por-regiones": -1}
for s in REG:
    s["mejor"] = MEJOR.get(s["id"], 0)
    n = s["nombre"].lower()
    if not s["mejor"]:
        s["mejor"] = -1 if ("paro" in n or "pobreza" in n) else (1 if ("pib" in n or "empleo" in n or "i+d" in n) else 0)

pagina("comparador.qmd", r'''---
title: "Comparador de comunidades autónomas"
subtitle: "Dos comunidades frente a frente en todos los indicadores regionales, con semáforo respecto a la media de España"
toc: false
---

Elige dos comunidades autónomas para comparar su **último dato** en todos los indicadores regionales de CCEEscopio. El semáforo indica si cada comunidad está **mejor (🟢)**, **cerca (🟡, a menos de un 5 %)** o **peor (🔴)** que el conjunto de España. Los indicadores sin una dirección clara (población, pernoctaciones) aparecen sin semáforo (⚪).

__HELPERS__

```{ojs}
//| echo: false
especCmp = __ESPECS__
ccaa = geosRegiones.filter(g => g.length > 2).map(g => nombresGeo[g]).sort((a, b) => a.localeCompare(b, "es"))
viewof ccaaA = Inputs.select(ccaa, {label: "Comunidad A", value: "Andalucía"})
viewof ccaaB = Inputs.select(ccaa, {label: "Comunidad B", value: ccaa.find(c => c.includes("Madrid")) ?? ccaa[0]})
cargasCmp = Promise.all(especCmp.map(s => cargar(s).catch(e => ({ok: false, rows: []}))))
```

```{ojs}
//| echo: false
{
  const ult = (rows, t) => rows.filter(r => r.territorio === t).sort((a, b) => b.fecha - a.fecha)[0];
  const sem = (v, es, mejor) => {
    if (!mejor || v == null || es == null || es === 0) return "⚪";
    const dif = mejor * (v - es) / Math.abs(es);
    return dif > 0.05 ? "🟢" : dif < -0.05 ? "🔴" : "🟡";
  };
  const filas = especCmp.map((s, k) => {
    const d = cargasCmp[k];
    if (!d.ok) return null;
    const a = ult(d.rows, ccaaA), b = ult(d.rows, ccaaB), es = ult(d.rows, "España");
    if (!a && !b) return null;
    return {s, a, b, es};
  }).filter(Boolean);
  const celda = (x, es, mejor) => x ? html`<td class="num">${sem(x.valor, es?.valor, mejor)} ${fmt(x.valor)}<br><span class="per">${x.periodo}</span></td>` : html`<td class="num">–</td>`;
  const tabla = html`<table class="table table-sm cmp-tabla"><thead><tr><th>Indicador</th><th>${ccaaA}</th><th>${ccaaB}</th><th>España</th></tr></thead>
    <tbody>${filas.map(f => html`<tr><td><a href="${f.s.pagina}.html?i=${f.s.id}">${f.s.nombre}</a><br><span class="per">${f.s.unidad}</span></td>
      ${celda(f.a, f.es, f.s.mejor)}${celda(f.b, f.es, f.s.mejor)}<td class="num">${f.es ? fmt(f.es.valor) : "–"}</td></tr>`)}</tbody></table>`;
  const cuenta = (x) => d3.rollup(filas.filter(f => f.s.mejor && f[x] && f.es), v => v.length, f => sem(f[x].valor, f.es.valor, f.s.mejor));
  const resumen = (t, x) => { const c = cuenta(x); return html`<span class="cmp-res"><b>${t}</b>: 🟢 ${c.get("🟢") ?? 0} · 🟡 ${c.get("🟡") ?? 0} · 🔴 ${c.get("🔴") ?? 0}</span>`; };
  const filasCsv = filas.map(f => ({indicador: f.s.nombre, unidad: f.s.unidad, [ccaaA]: f.a?.valor ?? "", [`periodo ${ccaaA}`]: f.a?.periodo ?? "", [ccaaB]: f.b?.valor ?? "", [`periodo ${ccaaB}`]: f.b?.periodo ?? "", "España": f.es?.valor ?? ""}));
  return html`<p>${resumen(ccaaA, "a")} ${resumen(ccaaB, "b")}</p>${tabla}
    ${DOM.download(() => new Blob(["﻿" + d3.csvFormat(filasCsv)], {type: "text/csv;charset=utf-8"}), "comparador_ccaa.csv", "⬇ Descargar la comparación (CSV)")}
    <p class="source">Último dato disponible de cada indicador en Eurostat (regiones NUTS 2). Los periodos pueden variar entre indicadores.</p>`;
}
```
''', ESPECS=J(REG))

# =====================================================================================
# 7. Calendario y datos recientes
# =====================================================================================
pagina("calendario.qmd", r'''---
title: "Datos recientes y calendario de publicaciones"
subtitle: "Qué indicadores ha actualizado Eurostat en los últimos días y dónde consultar los próximos datos"
toc: false
---

La tabla consulta en directo **cuándo actualizó Eurostat por última vez** cada indicador de CCEEscopio y cuál es su **último periodo** con datos. Los marcados como **Nuevo** se han actualizado en los últimos 14 días.

**Calendarios oficiales de publicación:** [INE](https://www.ine.es/daco/daco41/calen.htm) · [Eurostat (indicadores euro)](https://ec.europa.eu/eurostat/news/euro-indicators/release-calendar) · [Banco de España](https://www.bde.es/) · [Instituto de Estadística y Cartografía de Andalucía](https://www.juntadeandalucia.es/institutodeestadisticaycartografia).

```{ojs}
//| echo: false
especCal = __ESPECS__
viewof filtroCal = Inputs.radio(["Todos", "Solo los nuevos"], {label: "Mostrar", value: "Todos"})
```

```{ojs}
//| echo: false
datosCal = {
  const base = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/";
  const una = async (s) => {
    const geo = s.sinGeo ? "" : "&geo=ES";
    for (const t of [{code: s.code, query: s.query}, ...(s.alt ?? [])]) {
      try {
        const r = await fetch(`${base}${t.code}?format=JSON&lang=EN${t.query}${geo}&lastTimePeriod=1`);
        if (!r.ok) continue;
        const js = await r.json();
        const idx = js.dimension.time.category.index;
        const per = (Array.isArray(idx) ? idx : Object.keys(idx)).sort().pop();
        return {s, updated: js.updated ? new Date(js.updated) : null, periodo: per, code: t.code};
      } catch (e) {}
    }
    return {s, updated: null, periodo: "–", code: s.code};
  };
  const out = new Array(especCal.length); let i = 0;
  const w = async () => { while (i < especCal.length) { const k = i++; out[k] = await una(especCal[k]); } };
  await Promise.all(Array.from({length: 6}, w));
  return out;
}
```

```{ojs}
//| echo: false
{
  const hoy = new Date(), dias = (d) => d ? (hoy - d) / 864e5 : Infinity;
  const filas = datosCal.filter(d => filtroCal === "Todos" || dias(d.updated) <= 14).sort((a, b) => (b.updated ?? 0) - (a.updated ?? 0));
  const f = (d) => d ? d.toLocaleDateString("es-ES", {day: "numeric", month: "short", year: "numeric"}) : "–";
  const nNuevos = datosCal.filter(d => dias(d.updated) <= 14).length;
  return html`<p><b>${nNuevos}</b> de ${datosCal.length} indicadores actualizados en los últimos 14 días.</p>
  <table class="table table-sm"><thead><tr><th>Indicador</th><th>Último periodo</th><th>Actualizado por Eurostat</th><th>Frecuencia</th></tr></thead>
  <tbody>${filas.map(d => html`<tr><td><a href="${d.s.pagina}.html?i=${d.s.id}">${d.s.nombre}</a> ${dias(d.updated) <= 14 ? html`<span class="badge-nuevo">Nuevo</span>` : ""}</td>
    <td>${d.periodo}</td><td>${f(d.updated)}</td><td>${d.s.frecuencia}</td></tr>`)}</tbody></table>`;
}
```
''', ESPECS=J(unicos), HELPERS="")

# =====================================================================================
# 8. Mercados al día (datos diarios)
# =====================================================================================
pagina("mercados.qmd", r'''---
title: "Mercados al día"
subtitle: "Tipos de cambio, rentabilidad de la deuda, prima de riesgo y euríbor con los últimos datos publicados"
toc: false
---

Datos **diarios** de Eurostat (tipos de cambio de referencia del BCE y rentabilidad de la deuda pública a 10 años) y el **euríbor**. Se actualizan cada día hábil con un pequeño retraso. Cada tarjeta muestra el último dato y su variación frente al dato anterior y frente a hace un mes.

__HELPERS__

```{ojs}
//| echo: false
hace = (dias) => new Date(Date.now() - dias * 864e5).toISOString().slice(0, 10)
fechaD = (t) => /^\d{4}-\d{2}-\d{2}$/.test(t) ? new Date(t + "T00:00:00") : fecha(t)
diario = async (code, query, dias = 400) => {
  const recs = await eurostat(code, `${query}&sinceTimePeriod=${hace(dias)}`);
  return recs.map(r => ({...r, fecha: fechaD(r.time)})).filter(r => r.fecha && Number.isFinite(r.value)).sort((a, b) => a.fecha - b.fecha);
}
cambios = diario("ert_bil_eur_d", "&currency=USD&currency=GBP&currency=CHF&currency=JPY&currency=CNY&statinfo=AVG")
  .catch(() => diario("ert_bil_eur_d", "&currency=USD&currency=GBP&currency=CHF&currency=JPY&currency=CNY")).catch(e => [])
bonos = diario("irt_lt_mcby_d", "&geo=ES&geo=DE&geo=IT&geo=PT&geo=FR&int_rt=MCBY").catch(() => diario("irt_lt_mcby_d", "&geo=ES&geo=DE&geo=IT&geo=PT&geo=FR")).catch(e => [])
euribor = diario("irt_st_d", "&int_rt=IRT_M12&int_rt=IRT_M3&geo=EA")
  .catch(() => diario("irt_st_m", "&int_rt=IRT_M12&int_rt=IRT_M3&geo=EA", 1100)).catch(e => [])
```

```{ojs}
//| echo: false
tarjetaM = (titulo, serie, unidad, dec = 4) => {
  if (!serie.length) return html`<div class="kpi"><div class="kpi-l">${titulo}</div><div class="kpi-n">–</div><div class="kpi-s">Sin datos ahora mismo</div></div>`;
  const u = serie[serie.length - 1], p = serie[serie.length - 2];
  const mes = serie.filter(r => r.fecha <= new Date(u.fecha.getTime() - 30 * 864e5)).pop();
  const f = (v) => locES.format(`,.${dec}f`)(v);
  const dif = (a, b) => b ? `${a.value - b.value >= 0 ? "▲" : "▼"} ${f(Math.abs(a.value - b.value))}` : "";
  const spark = Plot.plot({height: 50, width: 220, margin: 2, axis: null, marks: [Plot.line(serie.slice(-130), {x: "fecha", y: "value", stroke: "#B5175F", strokeWidth: 1.5})]});
  return html`<div class="kpi"><div class="kpi-l">${titulo}</div><div class="kpi-n">${f(u.value)}</div>
    <div class="kpi-s">${unidad} · ${u.fecha.toLocaleDateString("es-ES")}</div>${spark}
    <div class="kpi-s">Día anterior: ${dif(u, p)} · Hace un mes: ${dif(u, mes)}</div></div>`;
}
```

## Tipos de cambio del euro

```{ojs}
//| echo: false
{
  const nombres = {USD: "Dólar estadounidense", GBP: "Libra esterlina", CHF: "Franco suizo", JPY: "Yen japonés", CNY: "Yuan chino"};
  const porDivisa = d3.group(cambios, r => r.currency);
  return html`<div class="kpi-grid">${Object.keys(nombres).map(c => tarjetaM(`Euro / ${nombres[c]}`, porDivisa.get(c) ?? [], `${c} por euro`, c === "JPY" ? 2 : 4))}</div>
  <p class="source">Tipos de cambio de referencia del Banco Central Europeo, vía Eurostat (ert_bil_eur_d).</p>`;
}
```

## Deuda pública a 10 años y prima de riesgo

```{ojs}
//| echo: false
{
  const g = d3.group(bonos, r => r.geo);
  const es = g.get("ES") ?? [], de = new Map((g.get("DE") ?? []).map(r => [r.time, r.value]));
  const prima = es.filter(r => de.has(r.time)).map(r => ({...r, value: 100 * (r.value - de.get(r.time))}));
  const nombres = {ES: "España", DE: "Alemania", IT: "Italia", PT: "Portugal", FR: "Francia"};
  const serieG = bonos.filter(r => r.fecha >= new Date(Date.now() - 365 * 864e5)).map(r => ({...r, pais: nombres[r.geo]}));
  return html`<div class="kpi-grid">${tarjetaM("Prima de riesgo de España (frente a Alemania)", prima, "puntos básicos", 0)}
    ${["ES", "DE", "IT", "PT"].map(c => tarjetaM(`Bono a 10 años: ${nombres[c]}`, g.get(c) ?? [], "% de rentabilidad", 3))}</div>
    ${serieG.length ? Plot.plot({height: 280, marginLeft: 45, x: {type: "time", label: null}, y: {label: "Rentabilidad (%)", grid: true},
      color: {legend: true, domain: ["España", "Alemania", "Italia", "Portugal", "Francia"], range: ["#B5175F", "#3C3C3B", "#4C9A2A", "#F29200", "#2A7AB0"]},
      marks: [Plot.line(serieG, {x: "fecha", y: "value", stroke: "pais", strokeWidth: 1.6}),
        Plot.tip(serieG, Plot.pointer({x: "fecha", y: "value", title: d => `${d.pais} · ${d.fecha.toLocaleDateString("es-ES")}: ${locES.format(",.3f")(d.value)} %`}))]}) : ""}
    <p class="source">Rentabilidad de la deuda pública a largo plazo (criterio de convergencia), vía Eurostat (irt_lt_mcby_d). Prima de riesgo = (rentabilidad de España − rentabilidad de Alemania) × 100.</p>`;
}
```

## Euríbor

```{ojs}
//| echo: false
{
  const g = d3.group(euribor, r => r.int_rt);
  return html`<div class="kpi-grid">${tarjetaM("Euríbor a 12 meses", g.get("IRT_M12") ?? [], "%", 3)}${tarjetaM("Euríbor a 3 meses", g.get("IRT_M3") ?? [], "%", 3)}</div>
  <p class="source">Tipos del mercado monetario de la zona euro, vía Eurostat (datos diarios si están disponibles; si no, mensuales). Calcula tu cuota con el <a href="hipoteca.qmd">simulador de hipotecas</a>.</p>`;
}
```

::: {.callout-note appearance="simple"}
**Precio de la electricidad y bolsa.** Los precios diarios del mercado eléctrico y la cotización del Ibex 35 no se publican en abierto en un formato que la web pueda descargar directamente. Consúltalos en [Red Eléctrica](https://www.ree.es/), [OMIE](https://www.omie.es/) y [BME](https://www.bolsasymercados.es/). En CCEEscopio tienes el [precio de la electricidad para los hogares](sostenibilidad.qmd) (semestral, Eurostat).
:::
''')

# =====================================================================================
# 10. Conversor de unidades económicas
# =====================================================================================
IPC_A = dict(nombre="IPCA (índice, media anual)", code="prc_hicp_aind", query="&unit=INX_A_AVG&coicop=CP00", unidad="Índice",
             frecuencia="Anual", desde=1996, alt=[dict(code="prc_hicp_aind", query="&unit=INX_A_AVG&coicop18=TOTAL")])
PLI = porid["nivel-de-precios-comparado-ue-27-100"]
POB = porid["poblacion"]
pagina("conversor.qmd", r'''---
title: "Conversor de unidades económicas"
subtitle: "Euros corrientes y constantes, paridad de poder de compra, valores per cápita y cambio de base de números índice"
toc: true
---

Cuatro conversiones que se usan constantemente en clase y en los TFG. Las tres primeras usan datos oficiales de Eurostat; la cuarta trabaja con la serie que pegues.

__HELPERS__

```{ojs}
//| echo: false
leerSerie = (txt) => txt.split(/\n/).map(l => l.trim()).filter(Boolean).map(l => {
  const p = l.includes(";") || l.includes("\t") ? l.split(/[;\t]/) : l.split(/\s+/);
  const num = (x) => { x = (x ?? "").trim(); if (x.includes(",")) x = x.replace(/\./g, "").replace(",", "."); return parseFloat(x); };
  return {periodo: (p[0] ?? "").trim(), valor: num(p[1])};
}).filter(d => d.periodo && Number.isFinite(d.valor))
e2 = (v) => locES.format(",.2f")(v)
ipcConv = cargar(__IPC__)
pliConv = cargar(__PLI__)
pobConv = cargar(__POB__)
```

## 1. Euros corrientes a euros constantes

Pega una serie en euros corrientes (una línea por año: `año;valor`) y elige el año base. Se divide cada valor por el IPCA de su año y se multiplica por el IPCA del año base.

```{ojs}
//| echo: false
paisesIpc = ipcConv.ok ? [...new Set(ipcConv.rows.map(r => r.territorio))].sort((a, b) => a.localeCompare(b, "es")) : []
viewof paisK = Inputs.select(paisesIpc, {label: "País", value: "España"})
viewof serieK = Inputs.textarea({label: "Serie en euros corrientes", value: "2015;1000\n2018;1050\n2021;1100\n2024;1250", rows: 5})
aniosK = ipcConv.ok ? ipcConv.rows.filter(r => r.territorio === paisK).map(r => r.periodo).sort() : []
viewof baseK = Inputs.select(aniosK, {label: "Año base (euros de…)", value: aniosK[aniosK.length - 1]})
```

```{ojs}
//| echo: false
{
  if (!ipcConv.ok) return html`<p class="pending">No se ha podido descargar el IPCA.</p>`;
  const ipc = new Map(ipcConv.rows.filter(r => r.territorio === paisK).map(r => [r.periodo, r.valor]));
  const filas = leerSerie(serieK).map(d => ({...d, ipc: ipc.get(d.periodo), real: ipc.get(d.periodo) ? d.valor * ipc.get(baseK) / ipc.get(d.periodo) : NaN}));
  return Inputs.table(filas, {header: {periodo: "Año", valor: "Euros corrientes", ipc: "IPCA (media anual)", real: `Euros constantes de ${baseK}`},
    format: {valor: e2, ipc: e2, real: v => Number.isFinite(v) ? e2(v) : "sin IPCA"}, layout: "auto"});
}
```

## 2. Paridad de poder de compra entre países

¿Cuánto dinero hace falta en otro país para comprar lo mismo? Se usa el **nivel de precios comparado** (UE-27 = 100): cantidad en B = cantidad en A × nivel de precios de B / nivel de precios de A.

```{ojs}
//| echo: false
paisesPli = pliConv.ok ? [...new Set(pliConv.rows.map(r => r.territorio))].sort((a, b) => a.localeCompare(b, "es")) : []
aniosPli = pliConv.ok ? [...new Set(pliConv.rows.map(r => r.periodo))].sort() : []
viewof cantP = Inputs.number([0, 1e12], {label: "Cantidad (€)", value: 1000, step: 1})
viewof paisA = Inputs.select(paisesPli, {label: "En el país", value: "España"})
viewof paisB = Inputs.select(paisesPli, {label: "Equivale en", value: "Alemania"})
viewof anioP = Inputs.select(aniosPli, {label: "Año", value: aniosPli[aniosPli.length - 1]})
```

```{ojs}
//| echo: false
{
  if (!pliConv.ok) return html`<p class="pending">No se han podido descargar los niveles de precios.</p>`;
  const v = (t) => pliConv.rows.find(r => r.territorio === t && r.periodo === anioP)?.valor;
  const a = v(paisA), b = v(paisB);
  if (!a || !b) return html`<p class="pending">No hay datos de ambos países en ${anioP}.</p>`;
  return html`<div class="calc-result"><div class="calc-big">${e2(cantP)} € en ${paisA} compran lo mismo que <b>${e2(cantP * b / a)} €</b> en ${paisB}</div>
  <div class="calc-small">Nivel de precios (UE-27 = 100) en ${anioP}: ${paisA} ${e2(a)} · ${paisB} ${e2(b)} · En estándares de poder de compra: ${e2(cantP / (a / 100))} EPC</div></div>`;
}
```

## 3. Valores per cápita

Divide una magnitud de un país entre su población a 1 de enero del año elegido.

```{ojs}
//| echo: false
paisesPob = pobConv.ok ? [...new Set(pobConv.rows.map(r => r.territorio))].sort((a, b) => a.localeCompare(b, "es")) : []
aniosPob = pobConv.ok ? [...new Set(pobConv.rows.map(r => r.periodo))].sort() : []
viewof magC = Inputs.number([0, 1e15], {label: "Magnitud total", value: 1500, step: 1})
viewof escC = Inputs.select(["euros", "miles de euros", "millones de euros", "miles de millones de euros"], {label: "Unidad", value: "miles de millones de euros"})
viewof paisPC = Inputs.select(paisesPob, {label: "País", value: "España"})
viewof anioPC = Inputs.select(aniosPob, {label: "Año", value: aniosPob[aniosPob.length - 1]})
```

```{ojs}
//| echo: false
{
  if (!pobConv.ok) return html`<p class="pending">No se ha podido descargar la población.</p>`;
  const pob = pobConv.rows.find(r => r.territorio === paisPC && r.periodo === anioPC)?.valor;
  const mult = {"euros": 1, "miles de euros": 1e3, "millones de euros": 1e6, "miles de millones de euros": 1e9}[escC];
  if (!pob) return html`<p class="pending">No hay población de ${paisPC} en ${anioPC}.</p>`;
  return html`<div class="calc-result"><div class="calc-big"><b>${e2(magC * mult / pob)} € por habitante</b></div>
  <div class="calc-small">${locES.format(",.0f")(magC * mult)} € / ${locES.format(",.0f")(pob)} habitantes (${paisPC}, 1 de enero de ${anioPC})</div></div>`;
}
```

## 4. Cambio de base de un número índice

Pega la serie del índice (`periodo;valor`) y elige el nuevo periodo base. Se muestran el índice en la nueva base y la tasa de variación respecto al periodo anterior, que no cambia con la base.

```{ojs}
//| echo: false
viewof serieI = Inputs.textarea({label: "Serie del índice", value: "2019;104,2\n2020;103,9\n2021;107,1\n2022;115,9\n2023;120,0\n2024;123,4", rows: 6})
periodosI = leerSerie(serieI).map(d => d.periodo)
viewof baseI = Inputs.select(periodosI, {label: "Nuevo periodo base (= 100)", value: periodosI[0]})
```

```{ojs}
//| echo: false
{
  const s = leerSerie(serieI), b = s.find(d => d.periodo === baseI)?.valor;
  if (!b) return html``;
  const filas = s.map((d, i) => ({periodo: d.periodo, original: d.valor, nueva: 100 * d.valor / b, tasa: i ? 100 * (d.valor / s[i - 1].valor - 1) : NaN}));
  return html`${Inputs.table(filas, {header: {periodo: "Periodo", original: "Índice original", nueva: `Base ${baseI} = 100`, tasa: "Variación (%)"},
    format: {original: e2, nueva: e2, tasa: v => Number.isFinite(v) ? e2(v) : ""}, layout: "auto"})}
  ${DOM.download(() => new Blob(["﻿" + d3.dsvFormat(";").format(filas.map(f => ({periodo: f.periodo, original: e2(f.original), nueva_base: e2(f.nueva), variacion: Number.isFinite(f.tasa) ? e2(f.tasa) : ""})))], {type: "text/csv;charset=utf-8"}), "indice_nueva_base.csv", "⬇ Descargar (CSV)")}`;
}
```
''', IPC=J(IPC_A), PLI=J(PLI), POB=J(POB))

# =====================================================================================
# 11. Turismo en Andalucía
# =====================================================================================
pagina("turismo-andalucia.qmd", r'''---
title: "Turismo en Andalucía"
subtitle: "Pernoctaciones, viajeros, estancia media y mercados nacional e internacional, comparados con España"
toc: false
---

Panel del turismo en **alojamientos turísticos** (hoteles, apartamentos turísticos y campings) de Andalucía, con datos de Eurostat para las regiones europeas (NUTS 2). Para el **turismo de la provincia y la ciudad de Granada**, consulta las fuentes oficiales del final de la página.

__HELPERS__

```{ojs}
//| echo: false
consultaT = async (code, extra, desde = 2010) => {
  const intentos = [`&geo=ES61&geo=ES&unit=NR&nace_r2=I551-I553${extra}`, `&geo=ES61&geo=ES${extra}`];
  for (const q of intentos) {
    try { const r = await eurostat(code, `${q}&sinceTimePeriod=${desde}`); if (r.length) return r; } catch (e) {}
  }
  return [];
}
nochesT = consultaT("tour_occ_nin2", "&c_resid=DOM&c_resid=FOR&c_resid=TOTAL")
llegadasT = consultaT("tour_occ_arn2", "&c_resid=TOTAL")
mensualT = consultaT("tour_occ_nin2m", "&c_resid=DOM&c_resid=FOR&c_resid=TOTAL", 2019)
regionesT = eurostat("tour_occ_nin2", "&c_resid=TOTAL&unit=NR&nace_r2=I551-I553" + geosRegiones.map(g => `&geo=${g}`).join("") + "&sinceTimePeriod=" + (new Date().getFullYear() - 3)).catch(e => [])
```

```{ojs}
//| echo: false
{
  const tot = nochesT.filter(r => r.c_resid === "TOTAL" || !r.c_resid);
  if (!tot.length) return html`<div class="callout callout-warning"><p>No se han podido descargar los datos de turismo de Eurostat. Inténtalo más tarde.</p></div>`;
  const ult = d3.max(tot.filter(r => r.geo === "ES61"), r => r.time);
  const v = (geo, res, t = ult, src = nochesT) => src.find(r => r.geo === geo && (r.c_resid ?? "TOTAL") === res && r.time === t)?.value;
  const ant = String(+ult - 1);
  const an = v("ES61", "TOTAL"), es = v("ES", "TOTAL"), anAnt = v("ES61", "TOTAL", ant);
  const lleg = llegadasT.find(r => r.geo === "ES61" && r.time === ult)?.value;
  const fmt0 = (x) => x == null ? "–" : locES.format(",.0f")(x);
  const k = (l, n, s) => html`<div class="kpi"><div class="kpi-l">${l}</div><div class="kpi-n">${n}</div><div class="kpi-s">${s}</div></div>`;
  return html`<div class="kpi-grid">
    ${k(`Pernoctaciones en ${ult}`, fmt0(an), anAnt ? `${an >= anAnt ? "▲" : "▼"} ${locES.format(",.1f")(100 * (an / anAnt - 1))} % respecto a ${ant}` : "")}
    ${k("Peso en España", es ? `${locES.format(",.1f")(100 * an / es)} %` : "–", "de las pernoctaciones de España")}
    ${k("Turismo internacional", v("ES61", "FOR") && an ? `${locES.format(",.1f")(100 * v("ES61", "FOR") / an)} %` : "–", "de las pernoctaciones son de no residentes")}
    ${k("Estancia media", lleg && an ? `${locES.format(",.2f")(an / lleg)} noches` : "–", "pernoctaciones / viajeros")}
  </div>`;
}
```

```{ojs}
//| echo: false
{
  const filas = nochesT.filter(r => r.geo === "ES61" && ["DOM", "FOR"].includes(r.c_resid)).map(r => ({...r, fecha: fecha(r.time), mercado: r.c_resid === "DOM" ? "Residentes en España" : "No residentes"}));
  if (!filas.length) return html``;
  return Plot.plot({title: "Pernoctaciones en Andalucía según la residencia del viajero", height: 300, marginLeft: 70,
    x: {type: "time", label: null}, y: {label: "Pernoctaciones", grid: true, tickFormat: v => locES.format(",.0f")(v / 1e6) + " M"},
    color: {legend: true, range: ["#B5175F", "#F29200"]},
    marks: [Plot.areaY(filas, {x: "fecha", y: "value", fill: "mercado", fillOpacity: 0.85}),
      Plot.tip(filas, Plot.pointer({x: "fecha", y: "value", title: d => `${d.mercado} · ${d.time}: ${locES.format(",.0f")(d.value)}`}))]});
}
```

```{ojs}
//| echo: false
{
  const filas = mensualT.filter(r => (r.c_resid ?? "TOTAL") === "TOTAL").map(r => ({...r, fecha: fecha(r.time)})).filter(r => r.fecha)
    .map(r => ({...r, mes: r.fecha.getMonth(), anio: String(r.fecha.getFullYear()), territorio: r.geo === "ES61" ? "Andalucía" : "España"}));
  if (!filas.length) return html`<p class="source">La serie mensual por regiones no está disponible ahora mismo en Eurostat.</p>`;
  const anios = [...new Set(filas.map(r => r.anio))].sort().slice(-4);
  const an = filas.filter(r => r.territorio === "Andalucía" && anios.includes(r.anio));
  const meses = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
  return Plot.plot({title: "Estacionalidad: pernoctaciones mensuales en Andalucía", height: 300, marginLeft: 60,
    x: {label: null, tickFormat: m => meses[m], domain: d3.range(12)}, y: {label: "Pernoctaciones", grid: true, tickFormat: v => locES.format(",.1f")(v / 1e6) + " M"},
    color: {legend: true, domain: anios, range: ["#ddd", "#c9a3b6", "#d65a92", "#B5175F"].slice(-anios.length)},
    marks: [Plot.line(an, {x: "mes", y: "value", stroke: "anio", strokeWidth: 2.2}), Plot.dot(an, {x: "mes", y: "value", fill: "anio", r: 3,
      title: d => `${meses[d.mes]} ${d.anio}: ${locES.format(",.0f")(d.value)}`})]});
}
```

```{ojs}
//| echo: false
{
  if (!regionesT.length) return html``;
  const ult = d3.max(regionesT.filter(r => r.geo.length > 2), r => r.time);
  const filas = regionesT.filter(r => r.time === ult && r.geo.length > 2).map(r => ({...r, ccaa: nombresGeo[r.geo] ?? r.geoLabel})).sort((a, b) => b.value - a.value);
  return Plot.plot({title: `Pernoctaciones por comunidad autónoma (${ult})`, height: 26 * filas.length + 40, marginLeft: 170, marginRight: 70,
    x: {label: null, grid: true, tickFormat: v => locES.format(",.0f")(v / 1e6) + " M"}, y: {label: null, domain: filas.map(d => d.ccaa)},
    marks: [Plot.barX(filas, {x: "value", y: "ccaa", fill: d => d.geo === "ES61" ? "#B5175F" : "#D9C2CC"}),
      Plot.text(filas, {x: "value", y: "ccaa", text: d => locES.format(",.1f")(d.value / 1e6) + " M", dx: 4, textAnchor: "start", fontSize: 11})]});
}
```

<p class="source">Fuente: Eurostat, alojamientos turísticos por regiones NUTS 2 (tour_occ_nin2, tour_occ_arn2 y tour_occ_nin2m). Más indicadores en <a href="turismo.qmd">Turismo</a>.</p>

### Granada y Andalucía: fuentes oficiales con más detalle

- **INE, Encuestas de ocupación en alojamientos turísticos**: viajeros, pernoctaciones, grado de ocupación y precios por provincias y por puntos turísticos (incluidas Granada y otras ciudades andaluzas). Consultar en [INEbase](https://www.ine.es/).
- **Instituto de Estadística y Cartografía de Andalucía (IECA)**: Encuesta de Coyuntura Turística de Andalucía, con gasto, origen y perfil del turista. [Web del IECA](https://www.juntadeandalucia.es/institutodeestadisticaycartografia).
- **INE, Frontur y Egatur**: llegadas y gasto de los turistas internacionales por comunidad autónoma.
''')

# =====================================================================================
# 12. Demografía empresarial
# =====================================================================================
REGQ = porid.get("registros-de-nuevas-empresas-indice")
QUIEB = next((s for s in unicos if s["id"].startswith("declaraciones-de-quiebra")), None)
pagina("empresas.qmd", r'''---
title: "Demografía empresarial"
subtitle: "Creación, cierre y supervivencia de empresas en España y en Europa"
toc: false
---

¿Se crean más empresas de las que cierran? ¿Cuántas sobreviven a los tres años? La primera parte muestra la **evolución trimestral** de los registros de nuevas empresas y de las quiebras. La segunda es un **explorador de la demografía empresarial** de Eurostat: elige el indicador, el sector y los países.

__HELPERS__

```{ojs}
//| echo: false
especEmp = __ESPECS__
cargasEmp = Promise.all(especEmp.map(s => cargar(s).catch(e => ({ok: false, rows: []}))))
```

```{ojs}
//| echo: false
html`<div class="graf-2">${especEmp.map((s, k) => {
  const d = cargasEmp[k];
  if (!d.ok) return html`<div><h4>${s.nombre}</h4><p class="pending">Sin datos ahora mismo.</p></div>`;
  const filas = d.rows.filter(r => ["España", "UE-27", "Alemania", "Francia", "Italia"].includes(r.territorio));
  return html`<div><h4><a href="${s.pagina}.html?i=${s.id}">${s.nombre}</a></h4>${Plot.plot({height: 260, width: 440, marginLeft: 45,
    x: {type: "time", label: null}, y: {label: s.unidad, grid: true}, color: {legend: true, domain: ["España", "UE-27", "Alemania", "Francia", "Italia"], range: ["#B5175F", "#3C3C3B", "#bbb", "#d8b4c6", "#F29200"]},
    marks: [Plot.ruleY([100], {stroke: "#ccc"}), Plot.line(filas, {x: "fecha", y: "valor", stroke: "territorio", strokeWidth: 1.6}),
      Plot.tip(filas, Plot.pointer({x: "fecha", y: "valor", title: d => `${d.territorio} · ${d.periodo}: ${fmt(d.valor)}`}))]})}</div>`;
})}</div>`
```

## Explorador de la demografía empresarial

```{ojs}
//| echo: false
jsonstatEtiq = (js) => {
  const ids = js.id, size = js.size, dims = js.dimension, out = [];
  const codes = ids.map(d => { const idx = dims[d].category.index; return Array.isArray(idx) ? idx : Object.keys(idx).sort((a, b) => idx[a] - idx[b]); });
  const etiq = Object.fromEntries(ids.map(d => [d, dims[d].category.label || {}]));
  const vals = js.value;
  const keys = Array.isArray(vals) ? vals.map((v, i) => i).filter(i => vals[i] != null) : Object.keys(vals).map(Number);
  for (const i of keys) { let rem = i; const rec = {}; for (let d = ids.length - 1; d >= 0; d--) { rec[ids[d]] = codes[d][rem % size[d]]; rem = Math.floor(rem / size[d]); } rec.value = +vals[i]; out.push(rec); }
  return {recs: out, etiq, ids};
}
bdEmp = {
  const base = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/";
  const geos = ["ES", "EU27_2020", "DE", "FR", "IT", "PT"].map(g => `&geo=${g}`).join("");
  const intentos = [["bd_size", "&size_emp=TOTAL"], ["bd_size", ""], ["bd_9bd_sz_cl_r2", "&sizeclas=TOTAL"], ["bd_9bd_sz_cl_r2", ""]];
  for (const [code, q] of intentos) {
    try {
      const r = await fetch(`${base}${code}?format=JSON&lang=EN${geos}${q}&sinceTimePeriod=2012`);
      if (!r.ok) continue;
      const js = await r.json(); const d = jsonstatEtiq(js);
      if (d.recs.length) return {...d, code};
    } catch (e) {}
  }
  return null;
}
dimsEmp = bdEmp ? bdEmp.ids.filter(d => !["geo", "time", "freq"].includes(d) && new Set(bdEmp.recs.map(r => r[d])).size > 1) : []
```

```{ojs}
//| echo: false
viewof selEmp = {
  if (!bdEmp) return Object.assign(html`<p class="pending">El explorador no puede descargar ahora los datos de Eurostat.</p>`, {value: {}});
  const preferido = {indic_sbs: ["V97020", "V97030", "V97043"], indic_sb: ["V97020", "V97030", "V97043"], nace_r2: ["B-S_X_K642", "B-N_X_K642"]};
  const controles = dimsEmp.map(d => {
    const cods = [...new Set(bdEmp.recs.map(r => r[d]))];
    const val = (preferido[d] ?? []).find(c => cods.includes(c)) ?? cods[0];
    return [d, Inputs.select(cods, {label: d.startsWith("indic") ? "Indicador" : d === "nace_r2" ? "Sector (NACE)" : d, format: c => bdEmp.etiq[d][c] ?? c, value: val})];
  });
  const form = html`<div>${controles.map(([, c]) => c)}</div>`;
  const leer = () => Object.fromEntries(controles.map(([d, c]) => [d, c.value]));
  form.value = leer();
  controles.forEach(([, c]) => c.addEventListener("input", () => { form.value = leer(); form.dispatchEvent(new Event("input", {bubbles: true})); }));
  return form;
}
```

```{ojs}
//| echo: false
{
  if (!bdEmp) return html``;
  const filas = bdEmp.recs.filter(r => dimsEmp.every(d => r[d] === selEmp[d])).map(r => ({...r, fecha: fecha(r.time), pais: nombresGeo[r.geo] ?? bdEmp.etiq.geo[r.geo]}));
  const ind = Object.entries(selEmp).find(([d]) => d.startsWith("indic"));
  const titulo = ind ? bdEmp.etiq[ind[0]][ind[1]] : "";
  if (!filas.length) return html`<p class="pending">No hay datos para esa combinación.</p>`;
  return html`<h4>${titulo}</h4>${Plot.plot({height: 320, marginLeft: 60, x: {type: "time", label: null}, y: {label: null, grid: true, tickFormat: v => fmt(v)},
    color: {legend: true, range: ["#B5175F", "#3C3C3B", "#bbb", "#d8b4c6", "#F29200", "#2A7AB0"]},
    marks: [Plot.line(filas, {x: "fecha", y: "value", stroke: "pais", strokeWidth: 2}), Plot.dot(filas, {x: "fecha", y: "value", fill: "pais", r: 2.5}),
      Plot.tip(filas, Plot.pointer({x: "fecha", y: "value", title: d => `${d.pais} · ${d.time}: ${fmt(d.value)}`}))]})}
  <p class="source">Fuente: Eurostat, demografía empresarial (${bdEmp.code}). Tasa de natalidad: empresas nacidas / empresas activas × 100. Tasa de mortalidad: empresas que cierran / activas × 100. Tasa de supervivencia a 3 años: empresas nacidas hace 3 años que siguen activas / nacidas ese año × 100.</p>`;
}
```
''', ESPECS=J([s for s in [REGQ, QUIEB] if s]))

# =====================================================================================
# 13. Consumo y confianza
# =====================================================================================
IDS_CONS = ["confianza-del-consumidor", "indice-de-comercio-minorista", "confianza-del-comercio-minorista", "personas-que-compran-por-internet"]
IDS_CONS += [s["id"] for s in unicos if s["id"].startswith("consumo-de-los-hogares")]
pagina("consumo.qmd", r'''---
title: "Consumo y confianza"
subtitle: "Confianza del consumidor, ventas del comercio minorista, consumo de los hogares y compra por internet"
toc: false
---

Panel para **Marketing e Investigación de Mercados** y para el análisis de coyuntura: cómo se sienten los consumidores, cuánto venden los comercios y cómo crece la compra por internet. Compara España con la UE-27 y con los grandes países europeos.

__HELPERS__

```{ojs}
//| echo: false
especCons = __ESPECS__
cargasCons = Promise.all(especCons.map(s => cargar(s).catch(e => ({ok: false, rows: []}))))
viewof compCons = Inputs.select(["UE-27", "Alemania", "Francia", "Italia", "Portugal"], {label: "Comparar España con", value: "UE-27"})
```

```{ojs}
//| echo: false
{
  const k = especCons.map((s, i) => {
    const d = cargasCons[i]; if (!d.ok) return null;
    const es = d.rows.filter(r => r.territorio === "España").sort((a, b) => a.fecha - b.fecha);
    const u = es[es.length - 1]; if (!u) return null;
    const hace = es.filter(r => r.fecha.getFullYear() === u.fecha.getFullYear() - 1 && r.fecha.getMonth() === u.fecha.getMonth()).pop();
    const pct = /%|saldo/i.test(s.unidad);
    const cambio = hace ? (pct ? `${u.valor - hace.valor >= 0 ? "▲" : "▼"} ${fmt(Math.abs(u.valor - hace.valor))} puntos en un año` : `${u.valor >= hace.valor ? "▲" : "▼"} ${locES.format(",.1f")(Math.abs(100 * (u.valor / hace.valor - 1)))} % en un año`) : "";
    return html`<div class="kpi"><div class="kpi-l"><a href="${s.pagina}.html?i=${s.id}">${s.nombre}</a></div><div class="kpi-n">${fmt(u.valor)}</div><div class="kpi-s">${s.unidad} · ${u.periodo}</div><div class="kpi-s">${cambio}</div></div>`;
  }).filter(Boolean);
  return html`<div class="kpi-grid">${k}</div>`;
}
```

```{ojs}
//| echo: false
html`<div class="graf-2">${especCons.map((s, i) => {
  const d = cargasCons[i]; if (!d.ok) return html``;
  const filas = d.rows.filter(r => ["España", compCons].includes(r.territorio) && r.fecha >= new Date(new Date().getFullYear() - 8, 0, 1));
  return html`<div><h4>${s.nombre}</h4>${Plot.plot({height: 240, width: 440, marginLeft: 45, x: {type: "time", label: null}, y: {label: s.unidad, grid: true},
    color: {legend: true, domain: ["España", compCons], range: ["#B5175F", "#3C3C3B"]},
    marks: [s.cero ? Plot.ruleY([0], {stroke: "#bbb"}) : null, Plot.line(filas, {x: "fecha", y: "valor", stroke: "territorio", strokeWidth: 1.8}),
      Plot.tip(filas, Plot.pointer({x: "fecha", y: "valor", title: d => `${d.territorio} · ${d.periodo}: ${fmt(d.valor)}`}))]})}</div>`;
})}</div>`
```

::: {.callout-tip appearance="simple"}
**Ideas para GMIM.** ¿Anticipa la confianza del consumidor las ventas del comercio minorista? Compara los dos gráficos o usa [Relaciona dos indicadores](relaciona.qmd). ¿En qué países europeos está más extendida la compra por internet y qué implica para un plan de marketing digital?
:::
''', ESPECS=J([porid[i] for i in IDS_CONS if i in porid]))

# =====================================================================================
# 15. Boletín mensual de coyuntura
# =====================================================================================
BOL = [("tasa-de-paro", "España"), ("tasa-de-paro-por-regiones", "Andalucía"), ("ipca-inflacion-general-tasa-anual", "España"),
       ("pib-crecimiento-interanual-trimestral", "España"), ("euribor-a-3-meses", None), ("confianza-del-consumidor", "España"),
       ("pernoctaciones-por-regiones", "Andalucía"), ("riesgo-de-pobreza-o-exclusion-social-por-regiones", "Andalucía")]
BOL = [dict(porid[i], terr=t) for i, t in BOL if i in porid]
pagina("boletin.qmd", r'''---
title: "Boletín de coyuntura"
subtitle: "Los datos más relevantes del mes para España y Andalucía, listos para compartir"
toc: false
---

El boletín se **genera automáticamente** con los últimos datos de Eurostat cada vez que abres la página. Copia el texto para redes sociales o la web de la Facultad, o guárdalo en PDF con el botón **Imprimir**.

__HELPERS__

```{ojs}
//| echo: false
especBol = __ESPECS__
cargasBol = Promise.all(especBol.map(s => cargar(s).catch(e => ({ok: false, rows: []}))))
mesesBol = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
periodoTxt = (r, frec) => frec === "Mensual" ? `${mesesBol[r.fecha.getMonth()]} de ${r.fecha.getFullYear()}` : frec === "Trimestral" ? `el ${Math.floor(r.fecha.getMonth() / 3) + 1}.º trimestre de ${r.fecha.getFullYear()}` : `${r.fecha.getFullYear()}`
datosBol = especBol.map((s, i) => {
  const d = cargasBol[i]; if (!d.ok) return null;
  const terr = s.terr ?? s.serie ?? s.nombre;
  const serie = d.rows.filter(r => r.territorio === terr).sort((a, b) => a.fecha - b.fecha);
  const u = serie[serie.length - 1]; if (!u) return null;
  const hace = serie.filter(r => r.fecha.getFullYear() === u.fecha.getFullYear() - 1 && r.fecha.getMonth() === u.fecha.getMonth()).pop();
  const pct = /%|saldo/i.test(s.unidad);
  let cambio = "", frase = "";
  if (hace) {
    const dif = pct ? u.valor - hace.valor : 100 * (u.valor / hace.valor - 1);
    const dir = Math.abs(dif) < 0.05 ? "igual que" : dif > 0 ? `${fmt(Math.abs(dif))} ${pct ? "puntos" : "%"} más que` : `${fmt(Math.abs(dif))} ${pct ? "puntos" : "%"} menos que`;
    cambio = `${dif >= 0 ? "▲" : "▼"} ${fmt(Math.abs(dif))} ${pct ? "puntos" : "%"} en un año`;
    frase = `${s.nombre.replace(/ por regiones/i, "")} (${terr}): ${fmt(u.valor)}${pct ? " %" : ""} en ${periodoTxt(u, s.frecuencia)}, ${dir} hace un año.`;
  } else frase = `${s.nombre.replace(/ por regiones/i, "")} (${terr}): ${fmt(u.valor)}${pct ? " %" : ""} en ${periodoTxt(u, s.frecuencia)}.`;
  return {s, terr, u, cambio, frase, serie: serie.slice(-24)};
}).filter(Boolean)
```

```{ojs}
//| echo: false
{
  const hoy = new Date();
  const titulo = `Boletín de coyuntura CCEEscopio · ${mesesBol[hoy.getMonth()]} de ${hoy.getFullYear()}`;
  const texto = `📊 ${titulo}\n\n` + datosBol.map(d => `• ${d.frase}`).join("\n") + `\n\nFuente: Eurostat. Más datos en CCEEscopio (FCCEE, Universidad de Granada).`;
  const copiar = html`<button class="copiar">📋 Copiar el texto</button>`;
  copiar.onclick = async () => { try { await navigator.clipboard.writeText(texto); copiar.textContent = "Copiado ✓"; } catch (e) { copiar.textContent = "Selecciona el texto y cópialo"; } };
  const imprimir = html`<button class="copiar">🖨 Imprimir o guardar en PDF</button>`;
  imprimir.onclick = () => window.print();
  return html`<div class="boletin">
    <h2 class="bol-t">${titulo}</h2>
    <div class="kpi-grid">${datosBol.map(d => html`<div class="kpi"><div class="kpi-l"><a href="${d.s.pagina}.html?i=${d.s.id}">${d.s.nombre.replace(/ por regiones/i, "")}</a> · ${d.terr}</div>
      <div class="kpi-n">${fmt(d.u.valor)}</div><div class="kpi-s">${d.s.unidad} · ${d.u.periodo}</div>
      ${Plot.plot({height: 46, width: 210, margin: 2, axis: null, marks: [Plot.line(d.serie, {x: "fecha", y: "valor", stroke: "#B5175F", strokeWidth: 1.6})]})}
      <div class="kpi-s">${d.cambio}</div></div>`)}</div>
    <h3>Texto para compartir</h3>
    <pre class="bol-texto">${texto}</pre>
    <div class="graf-botones no-print">${copiar}${imprimir}</div>
  </div>`;
}
```
''', ESPECS=J(BOL))

# =====================================================================================
# 16. Recursos de la Biblioteca de la UGR
# =====================================================================================
pagina("biblioteca.qmd", r'''---
title: "Bases de datos de la Biblioteca y fuentes abiertas"
subtitle: "Dónde encontrar datos de empresas, mercados y países para el TFG, el TFM y la tesis"
toc: true
---

La Universidad de Granada tiene suscritas varias bases de datos de economía y empresa. **El acceso está restringido a la comunidad universitaria**: entra desde la red de la UGR o con la **VPN** si estás fuera. La lista completa y actualizada está en el [listado de bases de datos de la Biblioteca](https://bibliotecaugr.libguides.com/az.php).

## Bases de datos suscritas por la UGR

| Base de datos | Qué contiene | Para qué sirve | Grados |
| --- | --- | --- | --- |
| **Orbis** | Información financiera y corporativa de empresas de todo el mundo | Análisis de estados financieros, sectores y competidores; muestras de empresas para el TFG | GADE, GFICO, GECO |
| **Orbis Intellectual Property** | Empresas y sus patentes | Innovación, tecnología y propiedad intelectual de las empresas | GADE, GECO |
| **Statista** | Estadísticas e informes de mercados e industrias de muchas fuentes | Datos de mercado, consumo y sectores para planes de marketing y de empresa | GMIM, GTUR, GADE |
| **Datastream** | Series financieras y macroeconómicas (cotizaciones, índices, tipos, bonos) | Finanzas, mercados de capitales y econometría financiera | GFICO, GECO |
| **CHELEM** | Comercio internacional y cuentas nacionales de todos los países | Economía internacional, especialización comercial y competitividad | GECO, GADE |
| **Harvard Business Publishing** | Casos y artículos de gestión empresarial | Casos prácticos de dirección, estrategia y marketing | GADE, GMIM |
| **Scopus y Web of Science** | Artículos científicos con sus citas | Revisión de la literatura y búsqueda de referencias | Todos |
| **ProQuest y EBSCOhost** | Revistas y bases de datos bibliográficas, incluidas las de economía y empresa | Artículos a texto completo para el marco teórico | Todos |

La Biblioteca organiza **talleres de formación** sobre estas bases de datos. Consulta las novedades en la [web de la Biblioteca](https://biblioteca.ugr.es/) y en la página de la [Facultad](https://fccee.ugr.es/).

## Fuentes abiertas (sin suscripción)

| Fuente | Qué contiene |
| --- | --- |
| [Eurostat](https://ec.europa.eu/eurostat) | Estadísticas oficiales de la UE: la fuente de casi todos los indicadores de CCEEscopio |
| [INEbase](https://www.ine.es/) | Estadísticas oficiales de España, con detalle por comunidad, provincia y municipio |
| [IECA](https://www.juntadeandalucia.es/institutodeestadisticaycartografia) | Estadísticas de Andalucía, provincias y municipios |
| [Banco de España](https://www.bde.es/) | Tipos de interés, crédito, balanza de pagos y cuentas financieras |
| [Banco Central Europeo](https://data.ecb.europa.eu/) | Política monetaria, tipos de cambio y mercados financieros de la zona euro |
| [OCDE](https://data-explorer.oecd.org/) | Comparaciones entre países desarrollados: productividad, educación, fiscalidad |
| [Banco Mundial](https://data.worldbank.org/) | Indicadores del desarrollo de todos los países del mundo |
| [FMI](https://www.imf.org/en/Data) | Previsiones y estadísticas macroeconómicas y financieras |
| [AMECO (Comisión Europea)](https://economy-finance.ec.europa.eu/) | Base macroeconómica de la Comisión Europea, con series largas y previsiones |

::: {.callout-tip appearance="simple"}
**Consejo para el TFG.** Empieza por una fuente abierta (Eurostat, INE) para el contexto y usa Orbis o Statista solo para los datos de empresas o mercados que no encuentres en abierto. Cita siempre la base de datos y la fecha de consulta. El [Generador de gráficos](graficos.qmd) te da la cita en formato APA.
:::
''', HELPERS="")
print("Recursos generados.")
