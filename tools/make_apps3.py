"""Genera la tercera tanda de recursos de CCEEscopio (noviembre de 2026):
examen (exámenes, fichas y banco de preguntas para PRADO), juegos (incluido el modo aula),
prediccion, extremos, convergencia, ciclo, desfases, prevision, desigualdad-calc, politica-fiscal y presentacion.
Uso: python3 tools/make_pages.py && python3 tools/make_apps.py && python3 tools/make_apps2.py && python3 tools/make_apps3.py"""
import json, re, glob, os

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

# Asignaturas de cada grado y sus indicadores (leídos de las páginas de docencia ya generadas)
ASIG = {}
for f in sorted(glob.glob("docencia/*.qmd")):
    g = os.path.basename(f)[:-4].upper()
    cur = None
    for l in open(f, encoding="utf-8"):
        m = re.match(r"^### (.+?) \{#", l)
        if m:
            cur = m.group(1).strip()
            continue
        if cur and l.startswith("**Indicadores recomendados:**"):
            ids = [i for i in re.findall(r"\?i=([a-z0-9-]+)", l) if i in porid]
            if ids:
                ASIG.setdefault(g, {})[cur] = ids
            cur = None

def J(x):
    return json.dumps(x, ensure_ascii=False)

def pagina(nombre, texto, **rep):
    rep.setdefault("HELPERS", HELPERS)
    rep.setdefault("PREG", PREG)
    for k, v in rep.items():
        texto = texto.replace(f"__{k}__", v)
    assert not re.search(r"__[A-Z0-9]+__", texto), f"marcador sin sustituir en {nombre}"
    open(nombre, "w", encoding="utf-8").write(texto)
    print("  ", nombre)

# =====================================================================================
# Motor de preguntas compartido (exámenes, fichas, juegos y modo aula)
# =====================================================================================
PREG = r'''```{ojs}
//| echo: false
// Generador pseudoaleatorio con semilla: la misma semilla da siempre las mismas preguntas
rngDe = (semilla) => {
  let a = typeof semilla === "number" ? semilla >>> 0 : [...String(semilla)].reduce((h, c) => Math.imul(h ^ c.charCodeAt(0), 2654435761) >>> 0, 1779033703);
  return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
}
elegir = (rng, arr) => arr[Math.floor(rng() * arr.length)]
barajar = (rng, arr) => { const a = arr.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(rng() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; }
TIPOS_PREG = ({variacion: "Cálculo: tasa de variación", puntos: "Cálculo: variación en puntos", media: "Cálculo: media aritmética",
  tmaa: "Cálculo: tasa media anual acumulativa", indice: "Cálculo: cambio de base de un índice", test: "Test: comparar territorios",
  vf: "Verdadero o falso", abierta: "Pregunta abierta de análisis"})
cacheDatos = new Map()
cargarCache = (s) => { if (!cacheDatos.has(s.id)) cacheDatos.set(s.id, cargar(s).catch(e => ({ok: false, rows: []}))); return cacheDatos.get(s.id); }
// Devuelve una pregunta del tipo pedido con los datos de un indicador, o null si los datos no lo permiten
generarPregunta = (s, rows, tipo, rng) => {
  const terrs = [...new Set(rows.map(r => r.territorio))];
  const obj = s.regional ? (terrs.includes("Andalucía") ? "Andalucía" : terrs[0]) : (terrs.includes("España") ? "España" : terrs[0]);
  const en = s.sinGeo ? "" : ` en ${obj}`;
  const serie = rows.filter(r => r.territorio === obj).sort((a, b) => a.fecha - b.fecha);
  if (serie.length < 6) return null;
  const pct = /%|puntos|saldo/i.test(s.unidad);
  const r2 = (v) => Math.round(v * 100) / 100;
  const u = serie[serie.length - 1];
  const antes = (r, n) => serie.filter(x => x.fecha.getFullYear() === r.fecha.getFullYear() - n && x.fecha.getMonth() === r.fecha.getMonth()).pop();
  const base = {tipo, s, obj};
  if (tipo === "variacion" || tipo === "puntos") {
    if ((tipo === "puntos") !== pct) return null;
    const ref = elegir(rng, serie.slice(-Math.min(serie.length, 24)));
    const h = antes(ref, 1); if (!h) return null;
    if (tipo === "puntos") {
      const sol = r2(ref.valor - h.valor);
      return {...base, enunciado: `${s.nombre}${en} fue ${fmt(h.valor)} en ${h.periodo} y ${fmt(ref.valor)} en ${ref.periodo}. ¿Cuántos **puntos** varió en ese año? (negativo si bajó)`,
        respuesta: sol, tol: 0.051, unidadResp: "puntos", solucion: `${fmt(ref.valor)} − ${fmt(h.valor)} = ${fmt(sol)} puntos. Al ser un porcentaje o un saldo, la variación se expresa en puntos.`};
    }
    const sol = r2(100 * (ref.valor / h.valor - 1));
    return {...base, enunciado: `${s.nombre}${en} fue ${fmt(h.valor)} en ${h.periodo} y ${fmt(ref.valor)} en ${ref.periodo}. Calcula la **tasa de variación interanual** (%, con dos decimales).`,
      respuesta: sol, tol: Math.max(0.11, Math.abs(sol) * 0.005), unidadResp: "%", solucion: `(${fmt(ref.valor)} / ${fmt(h.valor)} − 1) × 100 = ${fmt(sol)} %.`};
  }
  if (tipo === "media") {
    const k = Math.floor(rng() * (serie.length - 4));
    const tramo = serie.slice(k, k + 4);
    const sol = r2(d3.mean(tramo, r => r.valor));
    return {...base, enunciado: `Calcula la **media aritmética** de ${s.nombre}${en} en estos periodos (dos decimales).`,
      datos: tramo.map(r => [r.periodo, fmt(r.valor)]), respuesta: sol, tol: Math.max(0.011, Math.abs(sol) * 0.001), unidadResp: s.unidad,
      solucion: `(${tramo.map(r => fmt(r.valor)).join(" + ")}) / 4 = ${fmt(sol)}.`};
  }
  if (tipo === "tmaa") {
    if (pct || s.frecuencia !== "Anual" || !serie.every(r => r.valor > 0)) return null;
    const n = Math.min(serie.length - 1, 4 + Math.floor(rng() * 7));
    const ini = serie[serie.length - 1 - n];
    const sol = r2(100 * (Math.pow(u.valor / ini.valor, 1 / n) - 1));
    return {...base, enunciado: `${s.nombre}${en} pasó de ${fmt(ini.valor)} en ${ini.periodo} a ${fmt(u.valor)} en ${u.periodo}. Calcula la **tasa media anual acumulativa** (%, dos decimales).`,
      respuesta: sol, tol: Math.max(0.051, Math.abs(sol) * 0.01), unidadResp: "%", solucion: `[(${fmt(u.valor)} / ${fmt(ini.valor)})^(1/${n}) − 1] × 100 = ${fmt(sol)} %.`};
  }
  if (tipo === "indice") {
    if (!/índice/i.test(s.unidad)) return null;
    const b = elegir(rng, serie.slice(0, -2)), t = serie[serie.length - 1];
    const sol = r2(100 * t.valor / b.valor);
    return {...base, enunciado: `${s.nombre}${en} (${s.unidad}) vale ${fmt(b.valor)} en ${b.periodo} y ${fmt(t.valor)} en ${t.periodo}. Expresa el valor de ${t.periodo} con **base ${b.periodo} = 100** (dos decimales).`,
      respuesta: sol, tol: 0.051, unidadResp: "", solucion: `100 × ${fmt(t.valor)} / ${fmt(b.valor)} = ${fmt(sol)}.`};
  }
  // Para las preguntas entre territorios: último periodo con al menos 5 territorios
  const per = [...d3.rollup(rows, v => v.length, r => r.periodo)].filter(([, c]) => c >= 5).map(([p]) => p).sort().pop();
  const enPer = per ? rows.filter(r => r.periodo === per && !["UE-27", "Zona euro", "Zona euro (19)"].includes(r.territorio)) : [];
  if (tipo === "test") {
    if (s.sinGeo || enPer.length < 4) return null;
    const ops = barajar(rng, enPer).slice(0, 4), mayor = rng() < 0.5;
    const c = (mayor ? d3.greatest : d3.least)(ops, r => r.valor);
    return {...base, enunciado: `¿Qué territorio tenía el valor **más ${mayor ? "alto" : "bajo"}** de ${s.nombre} en ${per}?`,
      opciones: ops.map(r => r.territorio), respuesta: ops.indexOf(c),
      solucion: ops.slice().sort((a, b) => b.valor - a.valor).map(r => `${r.territorio}: ${fmt(r.valor)}`).join(" · ") + ` (${s.unidad}).`};
  }
  if (tipo === "vf") {
    if (s.sinGeo || enPer.length < 2) {
      const h = antes(u, 1); if (!h) return null;
      const sube = rng() < 0.5, ok = sube ? u.valor > h.valor : u.valor < h.valor;
      return {...base, enunciado: `Verdadero o falso: ${s.nombre}${en} fue **${sube ? "mayor" : "menor"}** en ${u.periodo} que en ${h.periodo}.`,
        opciones: ["Verdadero", "Falso"], respuesta: ok ? 0 : 1, solucion: `${h.periodo}: ${fmt(h.valor)} · ${u.periodo}: ${fmt(u.valor)}. Es ${ok ? "verdadero" : "falso"}.`};
    }
    const [a, b] = barajar(rng, enPer).slice(0, 2);
    const ok = a.valor > b.valor;
    return {...base, enunciado: `Verdadero o falso: en ${per}, ${s.nombre} fue **mayor** en ${a.territorio} que en ${b.territorio}.`,
      opciones: ["Verdadero", "Falso"], respuesta: ok ? 0 : 1, solucion: `${a.territorio}: ${fmt(a.valor)} · ${b.territorio}: ${fmt(b.valor)} (${s.unidad}). Es ${ok ? "verdadero" : "falso"}.`};
  }
  if (tipo === "abierta") {
    const anual = d3.rollups(serie, v => d3.mean(v, r => r.valor), r => r.fecha.getFullYear()).sort((x, y) => x[0] - y[0]).slice(-8);
    if (anual.length < 4) return null;
    const ref = s.sinGeo || s.regional ? null : (terrs.includes("UE-27") ? "UE-27" : null);
    const refA = ref ? new Map(d3.rollups(rows.filter(r => r.territorio === ref), v => d3.mean(v, r => r.valor), r => r.fecha.getFullYear())) : null;
    const max = d3.greatest(anual, d => d[1]), min = d3.least(anual, d => d[1]);
    return {...base, abierta: true,
      enunciado: `A partir de la tabla, comenta la evolución de ${s.nombre}${en}${ref ? " y compárala con la UE-27" : ""}. Indica el máximo, el mínimo y la variación total del periodo, y propón una posible explicación económica.`,
      datos: anual.map(([y, v]) => [String(y), fmt(v)].concat(refA ? [refA.has(y) ? fmt(refA.get(y)) : "–"] : [])),
      cabecera: ["Año", obj].concat(refA ? ["UE-27"] : []),
      solucion: `Máximo: ${fmt(max[1])} (${max[0]}). Mínimo: ${fmt(min[1])} (${min[0]}). Variación entre ${anual[0][0]} y ${anual[anual.length - 1][0]}: ${pct ? fmt(anual[anual.length - 1][1] - anual[0][1]) + " puntos" : fmt(100 * (anual[anual.length - 1][1] / anual[0][1] - 1)) + " %"}. Se valorará relacionar la evolución con el ciclo económico y con los datos de ${ref ?? "otros territorios"}. (Medias anuales; ${s.unidad}.)`};
  }
  return null;
}
// Genera n preguntas con la semilla dada, alternando los tipos pedidos
generarSerie = async (pool, tipos, n, semilla) => {
  const rng = rngDe(semilla), out = [];
  let intentos = 0;
  while (out.length < n && intentos < n * 12) {
    intentos++;
    const tipo = tipos[out.length % tipos.length];
    const s = elegir(rng, pool);
    const d = await cargarCache(s);
    if (!d.ok) continue;
    const q = generarPregunta(s, d.rows, tipo, rng);
    if (q && !out.some(p => p.enunciado === q.enunciado)) out.push(q);
  }
  return out;
}
mdNegrita = (t) => t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/\*\*(.+?)\*\*/g, "<b>$1</b>")
```'''

# =====================================================================================
# 2 + 16 + 18. Generador de exámenes, fichas de práctica y banco de preguntas para PRADO
# =====================================================================================
pagina("examen.qmd", r'''---
title: "Generador de exámenes y fichas de práctica"
subtitle: "Para el profesorado: preguntas con datos oficiales actualizados, varias versiones, soluciones y exportación a PRADO (Moodle)"
toc: false
---

Elige la **temática** (un área, o un grado y sus asignaturas), el **número y el tipo de preguntas** y los datos del encabezado. Pulsa **Generar**: las preguntas se construyen con los datos de Eurostat de hoy y quedan fijadas en el documento. Cada versión (A, B, C…) tiene los mismos tipos de pregunta con datos distintos.

__HELPERS__

__PREG__

```{ojs}
//| echo: false
especEx = __ESPECS__
asigEx = (__ASIG__)
areasEx = (__AREAS__)
viewof tipoDoc = Inputs.radio(["Examen", "Ficha de práctica", "Banco de preguntas para PRADO (Moodle)"], {label: "Documento", value: "Examen"})
viewof ambitoEx = Inputs.radio(["Áreas temáticas", "Grado y asignatura"], {label: "Temática", value: "Áreas temáticas"})
```

```{ojs}
//| echo: false
viewof areasSel = Inputs.checkbox(Object.keys(areasEx), {label: "Áreas", format: k => areasEx[k], value: ["empleo", "precios"], disabled: ambitoEx !== "Áreas temáticas"})
viewof gradoEx = Inputs.select(Object.keys(asigEx), {label: "Grado", value: "GECO", disabled: ambitoEx === "Áreas temáticas"})
```

```{ojs}
//| echo: false
viewof asigSel = Inputs.select(Object.keys(asigEx[gradoEx] ?? {}).sort((a, b) => a.localeCompare(b, "es")), {label: "Asignaturas (Ctrl o ⌘ para varias)", multiple: true, size: 6, disabled: ambitoEx === "Áreas temáticas"})
viewof tiposEx = Inputs.checkbox(Object.keys(TIPOS_PREG), {label: "Tipos de pregunta", format: k => TIPOS_PREG[k], value: ["variacion", "puntos", "test", "vf", "abierta"]})
viewof nEx = Inputs.range([1, tipoDoc.startsWith("Banco") ? 100 : 30], {label: "Número de preguntas", value: tipoDoc.startsWith("Banco") ? 30 : 8, step: 1})
viewof versEx = Inputs.range([1, 4], {label: "Versiones", value: tipoDoc === "Examen" ? 2 : 1, step: 1, disabled: tipoDoc !== "Examen"})
viewof tituloEx = Inputs.text({label: "Título", value: tipoDoc === "Ficha de práctica" ? "Ficha de práctica con datos oficiales" : "Examen", width: 520})
viewof cursoEx = Inputs.text({label: "Asignatura y grupo", placeholder: "Macroeconomía · Grupo A", width: 520})
viewof fechaEx = Inputs.date({label: "Fecha", value: new Date()})
viewof tiempoEx = Inputs.text({label: "Duración", value: "60 minutos"})
viewof instrEx = Inputs.textarea({label: "Instrucciones", value: "Responde en el espacio indicado. En los cálculos, redondea a dos decimales y escribe la fórmula utilizada.", rows: 2, width: 520})
viewof generarEx = Inputs.button("📝 Generar", {value: 0, reduce: v => v + 1})
```

```{ojs}
//| echo: false
docEx = {
  if (!generarEx) return null;
  const ids = ambitoEx === "Áreas temáticas" ? especEx.filter(s => areasSel.includes(s.pagina)).map(s => s.id)
    : [...new Set((asigSel.length ? asigSel : Object.keys(asigEx[gradoEx])).flatMap(a => asigEx[gradoEx][a]))];
  const pool = especEx.filter(s => ids.includes(s.id));
  const tipos = tiposEx.length ? tiposEx : ["variacion", "test"];
  if (!pool.length) return {error: "No hay indicadores para esa temática."};
  const semillaBase = `${tituloEx}|${cursoEx}|${fechaEx?.toISOString?.().slice(0, 10)}|${generarEx}`;
  const nv = tipoDoc === "Examen" ? versEx : 1;
  const versiones = [];
  for (let v = 0; v < nv; v++) versiones.push(await generarSerie(pool, tipos, nEx, `${semillaBase}|${v}`));
  return {versiones, pool, consultado: new Date()};
}
```

```{ojs}
//| echo: false
{
  if (!docEx) return html`<p class="pending">Configura el documento y pulsa <b>Generar</b>.</p>`;
  if (docEx.error) return html`<p class="pending">${docEx.error}</p>`;
  const letras = "ABCD", fechaTxt = fechaEx ? fechaEx.toLocaleDateString("es-ES", {day: "numeric", month: "long", year: "numeric"}) : "";
  const ficha = tipoDoc === "Ficha de práctica";
  const pts = (n) => locES.format(",.2~f")(10 / n);
  const tablaDatos = (q) => q.datos ? `<table class="ex-datos">${q.cabecera ? `<tr>${q.cabecera.map(c => `<th>${c}</th>`).join("")}</tr>` : ""}${q.datos.map(f => `<tr>${f.map(c => `<td>${c}</td>`).join("")}</tr>`).join("")}</table>` : "";
  const cuerpo = (q, i, n) => `<div class="ex-preg"><p><b>${i + 1}.</b> ${mdNegrita(q.enunciado)} <span class="ex-pts">(${pts(n)} p.)</span></p>${tablaDatos(q)}
    ${q.opciones ? `<ol class="ex-ops" type="a">${q.opciones.map(o => `<li>${o}</li>`).join("")}</ol>` : `<div class="ex-hueco ${q.abierta ? "ex-hueco-alto" : ""}"></div>`}
    <p class="ex-fuente">Fuente: Eurostat (${q.s.code}).</p></div>`;
  const solucion = (q, i) => `<li><b>${q.opciones ? `${"abcd"[q.respuesta]}) ${q.opciones[q.respuesta]}` : q.abierta ? "Respuesta orientativa" : `${fmt(q.respuesta)} ${q.unidadResp}`}</b>. ${q.solucion}</li>`;
  const cab = (letra) => `<div class="ex-cab"><h1>${tituloEx}${letra ? ` · Versión ${letra}` : ""}</h1>
    <p>${cursoEx || ""}${cursoEx ? " · " : ""}${fechaTxt}${tiempoEx ? ` · ${tiempoEx}` : ""}</p>
    ${ficha ? "" : `<p class="ex-nombre">Apellidos y nombre: ______________________________________ DNI: ____________ Grupo: ________</p>`}
    <p class="ex-instr">${instrEx}</p></div>`;
  const pie = `<p class="ex-pie">Datos de Eurostat consultados el ${docEx.consultado.toLocaleDateString("es-ES")} con CCEEscopio (FCCEE, Universidad de Granada).</p>`;
  const html1 = docEx.versiones.map((qs, v) => `<section class="ex-pagina">${cab(docEx.versiones.length > 1 ? letras[v] : "")}${qs.map((q, i) => cuerpo(q, i, qs.length)).join("")}${pie}</section>`).join("");
  const sol = docEx.versiones.map((qs, v) => `<section class="ex-pagina ex-sol"><h2>Soluciones${docEx.versiones.length > 1 ? ` · Versión ${letras[v]}` : ""}</h2><ol>${qs.map(solucion).join("")}</ol></section>`).join("");
  // GIFT (Moodle / PRADO)
  const esc = (t) => t.replace(/\*\*(.+?)\*\*/g, "$1").replace(/([~=#{}:])/g, "\\$1");
  const gift = docEx.versiones.flatMap((qs, v) => qs.map((q, i) => {
    const t = `::${tituloEx} ${docEx.versiones.length > 1 ? letras[v] : ""}${i + 1}:: ${esc(q.enunciado)}${q.datos ? " " + esc((q.cabecera ? q.cabecera.join(" | ") + " — " : "") + q.datos.map(f => f.join(": ")).join("; ")) : ""}`;
    if (q.abierta) return `${t} {}`;
    if (q.opciones && q.opciones.length === 2 && q.opciones[0] === "Verdadero") return `${t} {${q.respuesta === 0 ? "T" : "F"}#${esc(q.solucion)}}`;
    if (q.opciones) return `${t} {${q.opciones.map((o, k) => `${k === q.respuesta ? "=" : "~"}${esc(o)}`).join(" ")}}`;
    return `${t} {#${q.respuesta}:${Math.round(q.tol * 1000) / 1000}}`;
  })).join("\n\n");
  const banco = tipoDoc.startsWith("Banco");
  const contenido = banco ? `<pre class="bol-texto">${gift.replace(/&/g, "&amp;").replace(/</g, "&lt;")}</pre>` : html1 + (ficha ? sol : "") ;
  const doc = html`<div id="examen-doc" class="examen-doc">`; doc.innerHTML = contenido;
  const docSol = html`<div class="examen-doc">`; docSol.innerHTML = sol;
  const word = (h, nombre) => DOM.download(() => new Blob([`<html><head><meta charset="utf-8"><style>${estiloDoc}</style></head><body>${h}</body></html>`], {type: "application/msword"}), nombre, `⬇ ${nombre}`);
  const estiloDoc = `body{font-family:Calibri,Arial,sans-serif;font-size:11pt;max-width:780px;margin:auto} .ex-pagina{page-break-after:always} h1{font-size:16pt;margin-bottom:2px} table{border-collapse:collapse;margin:4px 0} td,th{border:1px solid #999;padding:2px 6px} .ex-hueco{height:70px;border:1px dashed #bbb;margin:4px 0} .ex-hueco-alto{height:180px} .ex-pts,.ex-fuente,.ex-pie{color:#666;font-size:9pt} .ex-preg{break-inside:avoid;margin:10px 0}`;
  const imprimir = (h, txt) => { const b = html`<button class="copiar">${txt}</button>`; b.onclick = () => { const w = window.open("", "_blank"); if (!w) return alert("Permite las ventanas emergentes para imprimir."); w.document.write(`<html><head><meta charset="utf-8"><title>${tituloEx}</title><style>${estiloDoc}</style></head><body>${h}</body></html>`); w.document.close(); w.focus(); setTimeout(() => w.print(), 300); }; return b; };
  window.cceeEvento && window.cceeEvento(`examen/${tipoDoc.split(" ")[0].toLowerCase()}`, `Generador: ${tipoDoc}`, true);
  return html`<div class="graf-botones no-print">
      ${banco ? "" : imprimir(html1 + (ficha ? sol : ""), "🖨 Imprimir o guardar en PDF")}
      ${banco ? "" : word(html1 + (ficha ? sol : ""), ficha ? "ficha_practica.doc" : "examen.doc")}
      ${tipoDoc === "Examen" ? word(sol, "soluciones.doc") : ""}
      ${tipoDoc === "Examen" ? imprimir(sol, "🖨 Soluciones en PDF") : ""}
      ${DOM.download(() => new Blob([gift], {type: "text/plain;charset=utf-8"}), "preguntas_prado.gift.txt", "⬇ Preguntas para PRADO (GIFT)")}
    </div>
    ${doc}
    ${tipoDoc === "Examen" ? html`<details class="no-print"><summary><b>Ver las soluciones</b></summary>${docSol}</details>` : ""}`;
}
```

::: {.callout-note appearance="simple"}
**Cómo importar las preguntas en PRADO (Moodle).** En el curso, abre el **Banco de preguntas → Importar**, elige el formato **GIFT** y sube el fichero descargado. Las preguntas de cálculo admiten un margen de error para el redondeo; las de verdadero o falso y las de test se corrigen solas; las abiertas quedan como «ensayo» para corregir a mano. **El documento en Word** se abre y se edita con Word o LibreOffice.
:::
''', ESPECS=J(unicos), ASIG=J(ASIG), AREAS=J(AREAS))

# =====================================================================================
# 3, 4, 5, 6, 8, 9. Juegos con datos y modo aula
# =====================================================================================
EPISODIOS = [
    {"id": "tasa-de-paro", "geo": "España", "desde": 2005, "hasta": 2016, "ok": "La Gran Recesión y la crisis del euro (2008-2013)",
     "mal": ["La pandemia de COVID-19 (2020)", "La crisis energética tras la invasión de Ucrania (2022)", "La entrada en el euro (1999-2002)"],
     "expl": "El paro en España pasó de menos del 8 % en 2007 a más del 26 % en 2013 con el estallido de la burbuja inmobiliaria y la crisis de deuda, y empezó a bajar con la recuperación."},
    {"id": "pib-crecimiento-interanual-trimestral", "geo": "España", "desde": 2018, "hasta": 2023, "ok": "La pandemia de COVID-19 y el confinamiento (2020)",
     "mal": ["La quiebra de Lehman Brothers (2008)", "El rescate bancario español (2012)", "La subida de tipos del BCE (2022-2023)"],
     "expl": "El confinamiento de la primavera de 2020 hundió el PIB más de un 20 % interanual en un solo trimestre; el rebote de 2021 es el efecto base de esa caída."},
    {"id": "ipca-inflacion-general-tasa-anual", "geo": "España", "desde": 2019, "hasta": 2024, "ok": "La crisis energética y la invasión de Ucrania (2021-2022)",
     "mal": ["La Gran Recesión (2008-2009)", "La crisis del euro (2011-2012)", "El Brexit (2016)"],
     "expl": "La subida del gas, la electricidad y los alimentos llevó la inflación a máximos de varias décadas en 2022; después bajó con la caída de la energía y la subida de tipos."},
    {"id": "rentabilidad-del-bono-a-10-anos", "geo": "España", "desde": 2008, "hasta": 2015, "ok": "La crisis de deuda soberana del euro (2010-2012)",
     "mal": ["La pandemia de COVID-19 (2020)", "La crisis de las puntocom (2001)", "La subida de tipos del BCE (2022)"],
     "expl": "La prima de riesgo española superó los 600 puntos básicos en julio de 2012; las palabras de Draghi («whatever it takes») y el programa OMT la redujeron."},
    {"id": "pernoctaciones-en-hoteles", "geo": "España", "desde": 2018, "hasta": 2023, "ok": "Las restricciones de viaje por la pandemia (2020-2021)",
     "mal": ["La Gran Recesión (2008-2009)", "La crisis energética (2022)", "Los atentados del 11-S (2001)"],
     "expl": "Con el cierre de fronteras de 2020 las pernoctaciones hoteleras cayeron casi a cero en abril y mayo; el turismo internacional no se recuperó del todo hasta 2023."},
    {"id": "euribor-a-3-meses", "geo": None, "desde": 2019, "hasta": 2025, "ok": "La subida de tipos del BCE para frenar la inflación (2022-2023)",
     "mal": ["La crisis de deuda soberana (2011)", "La pandemia de COVID-19 (2020)", "La creación del euro (1999)"],
     "expl": "El euríbor pasó de valores negativos a casi el 4 % en un año, cuando el BCE subió los tipos oficiales para frenar la inflación; desde 2024 ha bajado con los recortes."},
    {"id": "precio-de-la-vivienda-tasa-anual", "geo": "España", "desde": 2008, "hasta": 2016, "ok": "El estallido de la burbuja inmobiliaria (2008-2013)",
     "mal": ["La pandemia de COVID-19 (2020)", "La subida de tipos del BCE (2022)", "La entrada en el euro (1999)"],
     "expl": "Tras el boom inmobiliario, el precio de la vivienda cayó durante seis años seguidos, con descensos de más del 10 % anual en 2012."},
]
PERFIL = ["pib-per-capita-en-ppc-ue-27-100", "tasa-de-paro", "ipca-inflacion-general-tasa-anual", "deuda-publica-del-pib",
          "cuota-de-energias-renovables", "esperanza-de-vida-al-nacer", "indice-de-gini"]

pagina("juegos.qmd", r'''---
title: "Juegos con datos"
subtitle: "Aprende economía jugando con los datos oficiales más recientes"
toc: true
toc-depth: 2
---

Seis juegos rápidos con datos de Eurostat. Sirven para repasar en clase, para empezar una sesión o para retar a tus compañeros. Los datos se cargan en directo, así que cada día pueden cambiar.

__HELPERS__

__PREG__

```{ojs}
//| echo: false
especJ = __ESPECS__
episodios = __EPIS__
perfilIds = __PERFIL__
porId = new Map(especJ.map(s => [s.id, s]))
paisesJ = especJ.filter(s => !s.sinGeo && !s.regional)
// Último periodo con al menos 15 países (sin agregados)
corte = (rows) => {
  const agr = ["UE-27", "Zona euro", "Zona euro (19)"];
  const c = d3.rollup(rows.filter(r => !agr.includes(r.territorio)), v => v.length, r => r.periodo);
  const per = [...c].filter(([, n]) => n >= 15).map(([p]) => p).sort().pop();
  return per ? {per, filas: rows.filter(r => r.periodo === per && !agr.includes(r.territorio))} : null;
}
racha = (clave) => { try { return JSON.parse(localStorage.getItem(clave) ?? "{}"); } catch (e) { return {}; } }
guardar = (clave, v) => { try { localStorage.setItem(clave, JSON.stringify(v)); } catch (e) {} }
evento = (j) => window.cceeEvento && window.cceeEvento(`juegos/${j}`, `Juego: ${j}`, true)
```

## 📅 El dato del día {#dato-del-dia}

Una pregunta nueva cada día, la misma para todo el mundo. Acierta días seguidos para mantener la racha.

```{ojs}
//| echo: false
{
  const hoy = new Date().toISOString().slice(0, 10);
  const pool = paisesJ.filter(s => s.frecuencia !== "Semestral");
  const qs = await generarSerie(pool, [elegir(rngDe(hoy), ["test", "vf", "test"])], 1, `dia-${hoy}`);
  const q = qs[0];
  if (!q) return html`<p class="pending">Hoy no se ha podido cargar el dato. Vuelve a intentarlo más tarde.</p>`;
  const st = racha("ccee-dia");
  const caja = html`<div class="juego">`;
  const pintar = () => {
    const ya = st.ultimo === hoy;
    caja.innerHTML = "";
    caja.append(html`<p class="juego-p">${html`<span>${q.enunciado.split("**").map((t, i) => i % 2 ? html`<b>${t}</b>` : t)}</span>`}</p>`);
    const ops = html`<div class="juego-ops">`;
    q.opciones.forEach((o, k) => {
      const b = html`<button class="juego-op">${o}</button>`;
      b.disabled = ya;
      if (ya && k === q.respuesta) b.classList.add("ok");
      b.onclick = () => {
        const bien = k === q.respuesta;
        const ayer = new Date(Date.now() - 864e5).toISOString().slice(0, 10);
        st.racha = bien ? (st.ultimoBien === ayer ? (st.racha ?? 0) + 1 : 1) : 0;
        if (bien) st.ultimoBien = hoy;
        st.ultimo = hoy; st.resultado = bien; st.mejor = Math.max(st.mejor ?? 0, st.racha);
        guardar("ccee-dia", st); evento(`dato-del-dia/${bien ? "acierto" : "fallo"}`); pintar();
      };
      ops.append(b);
    });
    caja.append(ops);
    if (ya) {
      const txt = `CCEEscopio · Dato del día ${hoy}: ${st.resultado ? "✅ acertado" : "❌ fallado"} · racha ${st.racha} 🔥\n${location.href.split("#")[0]}#dato-del-dia`;
      const copia = html`<button class="copiar">📋 Copiar resultado para compartir</button>`;
      copia.onclick = () => navigator.clipboard.writeText(txt).then(() => copia.textContent = "✔ Copiado");
      caja.append(html`<p class="juego-res ${st.resultado ? "bien" : "mal"}">${st.resultado ? "¡Correcto!" : "No era esa."} ${q.solucion}</p>
        <p>Racha actual: <b>${st.racha} 🔥</b> · Mejor racha: <b>${st.mejor}</b>. Vuelve mañana para una nueva pregunta.</p>`, copia);
    }
  };
  pintar();
  return caja;
}
```

## ⬆️⬇️ ¿Más alto o más bajo? {#mas-alto}

Te damos el valor de un país. ¿El otro país está por encima o por debajo? Encadena aciertos.

```{ojs}
//| echo: false
{
  const caja = html`<div class="juego">`;
  let rng = rngDe(Date.now()), seguidos = 0, mejor = racha("ccee-mas-alto").mejor ?? 0;
  const ronda = async () => {
    caja.innerHTML = `<p class="pending">Cargando…</p>`;
    let s, c;
    for (let i = 0; i < 8 && !c; i++) { s = elegir(rng, paisesJ); const d = await cargarCache(s); c = d.ok ? corte(d.rows) : null; }
    if (!c) { caja.innerHTML = `<p class="pending">No se han podido cargar datos.</p>`; return; }
    const [a, b] = barajar(rng, c.filas.filter(r => r.valor !== undefined)).slice(0, 2);
    caja.innerHTML = "";
    const resp = (mayor) => {
      const bien = mayor ? b.valor >= a.valor : b.valor <= a.valor;
      seguidos = bien ? seguidos + 1 : 0; mejor = Math.max(mejor, seguidos); guardar("ccee-mas-alto", {mejor});
      evento(`mas-alto/${bien ? "acierto" : "fallo"}`);
      caja.querySelectorAll("button").forEach(x => x.disabled = true);
      const sig = html`<button class="juego-op">Siguiente ➜</button>`; sig.onclick = ronda;
      caja.append(html`<p class="juego-res ${bien ? "bien" : "mal"}">${bien ? "✅ ¡Bien!" : "❌ No."} ${b.territorio}: <b>${fmt(b.valor)}</b> ${s.unidad}.</p>`, sig);
    };
    const up = html`<button class="juego-op">⬆️ Más alto</button>`, dn = html`<button class="juego-op">⬇️ Más bajo</button>`;
    up.onclick = () => resp(true); dn.onclick = () => resp(false);
    caja.append(html`<p class="juego-ind">${s.nombre} · ${c.per}</p>
      <div class="juego-duelo"><div><span>${a.territorio}</span><b>${fmt(a.valor)}</b><small>${s.unidad}</small></div><div class="vs">vs</div><div><span>${b.territorio}</span><b>?</b></div></div>
      <div class="juego-ops">${up}${dn}</div><p class="juego-marcador">Aciertos seguidos: <b>${seguidos}</b> · Récord: <b>${mejor}</b></p>`);
  };
  ronda();
  return caja;
}
```

## 🌍 Adivina el país {#adivina-pais}

Mira el perfil económico y elige de qué país se trata.

```{ojs}
//| echo: false
{
  const caja = html`<div class="juego">`;
  const rng = rngDe(Date.now() + 7);
  let puntos = 0, jugadas = 0;
  const ronda = async () => {
    caja.innerHTML = `<p class="pending">Cargando el perfil…</p>`;
    const datos = (await Promise.all(perfilIds.filter(i => porId.has(i)).map(async i => { const d = await cargarCache(porId.get(i)); return d.ok ? [i, d.rows] : null; }))).filter(Boolean);
    const ult = new Map(datos.map(([i, rows]) => [i, d3.rollup(rows, v => v.sort((x, y) => x.fecha - y.fecha).at(-1), r => r.territorio)]));
    const paises = Object.values(nombresGeo).filter(p => !["UE-27", "Zona euro", "Zona euro (19)"].includes(p) && [...ult.values()].filter(m => m.has(p)).length >= 4);
    if (paises.length < 4) { caja.innerHTML = `<p class="pending">No se han podido cargar datos.</p>`; return; }
    const sol = elegir(rng, paises);
    const ops = barajar(rng, [sol, ...barajar(rng, paises.filter(p => p !== sol)).slice(0, 3)]);
    const ue = (i) => ult.get(i).get("UE-27");
    caja.innerHTML = "";
    const tabla = html`<table class="juego-perfil"><tr><th>Indicador</th><th>País misterioso</th><th>UE-27</th></tr>
      ${datos.filter(([i]) => ult.get(i).has(sol)).map(([i]) => { const r = ult.get(i).get(sol); return html`<tr><td>${porId.get(i).nombre}</td><td><b>${fmt(r.valor)}</b> <small>(${r.periodo})</small></td><td>${ue(i) ? fmt(ue(i).valor) : "–"}</td></tr>`; })}</table>`;
    const bot = html`<div class="juego-ops">`;
    ops.forEach(p => { const b = html`<button class="juego-op">${p}</button>`; b.onclick = () => {
      const bien = p === sol; jugadas++; if (bien) puntos++; evento(`adivina-pais/${bien ? "acierto" : "fallo"}`);
      bot.querySelectorAll("button").forEach(x => { x.disabled = true; if (x.textContent === sol) x.classList.add("ok"); });
      if (!bien) b.classList.add("ko");
      const sig = html`<button class="juego-op">Otro país ➜</button>`; sig.onclick = ronda;
      caja.append(html`<p class="juego-res ${bien ? "bien" : "mal"}">${bien ? "✅ ¡Correcto!" : `❌ Era ${sol}.`} Llevas ${puntos} de ${jugadas}.</p>`, sig);
    }; bot.append(b); });
    caja.append(tabla, bot);
  };
  ronda();
  return caja;
}
```

## 🕵️ ¿Qué pasó aquí? {#que-paso}

El gráfico muestra un episodio real, sin fechas. ¿Qué acontecimiento explica lo que ves?

```{ojs}
//| echo: false
{
  const caja = html`<div class="juego">`;
  let orden = barajar(rngDe(Date.now() + 3), episodios), k = 0, puntos = 0;
  const ronda = async () => {
    const e = orden[k % orden.length]; k++;
    caja.innerHTML = `<p class="pending">Cargando…</p>`;
    const d = await cargarCache(porId.get(e.id));
    const serie = d.ok ? d.rows.filter(r => (e.geo ? r.territorio === e.geo : true) && r.fecha.getFullYear() >= e.desde && r.fecha.getFullYear() <= e.hasta).sort((a, b) => a.fecha - b.fecha) : [];
    if (serie.length < 4) { if (k < orden.length * 2) return ronda(); caja.innerHTML = `<p class="pending">No se han podido cargar datos.</p>`; return; }
    const t0 = serie[0].fecha;
    const datos = serie.map((r, i) => ({x: i, valor: r.valor, r}));
    const graf = (fechas) => Plot.plot({height: 260, marginLeft: 50, x: {label: null, ticks: fechas ? 6 : 0, tickFormat: fechas ? (i => datos[Math.round(i)]?.r.periodo ?? "") : () => ""},
      y: {label: porId.get(e.id).unidad, grid: true}, marks: [Plot.ruleY([0], {stroke: "#bbb"}), Plot.lineY(datos, {x: "x", y: "valor", stroke: "#A6195E", strokeWidth: 2.5})]});
    const g = html`<div>${graf(false)}</div>`;
    caja.innerHTML = "";
    const bot = html`<div class="juego-ops juego-ops-v">`;
    const opciones = barajar(rngDe(k * 97), [e.ok, ...e.mal]);
    opciones.forEach(o => { const b = html`<button class="juego-op">${o}</button>`; b.onclick = () => {
      const bien = o === e.ok; if (bien) puntos++; evento(`que-paso/${bien ? "acierto" : "fallo"}`);
      bot.querySelectorAll("button").forEach(x => { x.disabled = true; if (x.textContent === e.ok) x.classList.add("ok"); });
      if (!bien) b.classList.add("ko");
      g.replaceChildren(graf(true));
      const sig = html`<button class="juego-op">Otro episodio ➜</button>`; sig.onclick = ronda;
      caja.append(html`<p class="juego-res ${bien ? "bien" : "mal"}">${bien ? "✅ ¡Exacto!" : "❌ No."} ${e.expl} <small>(${serie[0].periodo} a ${serie.at(-1).periodo}${e.geo ? `, ${e.geo}` : ""}.)</small></p>`, sig);
    }; bot.append(b); });
    caja.append(html`<p class="juego-ind">${porId.get(e.id).nombre}${e.geo ? ` · ${e.geo}` : ""} · Aciertos: ${puntos}</p>`, g, bot);
  };
  ronda();
  return caja;
}
```

## 🔢 Ordena de mayor a menor {#ordena}

Pulsa los países en orden, del valor más alto al más bajo.

```{ojs}
//| echo: false
{
  const caja = html`<div class="juego">`;
  const rng = rngDe(Date.now() + 11);
  const ronda = async () => {
    caja.innerHTML = `<p class="pending">Cargando…</p>`;
    let s, c;
    for (let i = 0; i < 8 && !c; i++) { s = elegir(rng, paisesJ); const d = await cargarCache(s); c = d.ok ? corte(d.rows) : null; }
    if (!c) { caja.innerHTML = `<p class="pending">No se han podido cargar datos.</p>`; return; }
    const filas = barajar(rng, c.filas).slice(0, 5);
    const correcto = filas.slice().sort((a, b) => b.valor - a.valor).map(r => r.territorio);
    const elegido = [];
    caja.innerHTML = "";
    const lista = html`<ol class="juego-orden">`;
    const bot = html`<div class="juego-ops">`;
    filas.forEach(r => { const b = html`<button class="juego-op">${r.territorio}</button>`; b.onclick = () => {
      b.disabled = true; elegido.push(r.territorio); lista.append(html`<li>${r.territorio}</li>`);
      if (elegido.length === filas.length) {
        const bien = elegido.filter((t, i) => t === correcto[i]).length;
        evento(`ordena/${bien === filas.length ? "perfecto" : bien}`);
        const sig = html`<button class="juego-op">Otra ronda ➜</button>`; sig.onclick = ronda;
        caja.append(html`<p class="juego-res ${bien === filas.length ? "bien" : "mal"}">${bien === filas.length ? "🏆 ¡Orden perfecto!" : `Has colocado bien ${bien} de ${filas.length}.`}</p>
          <ol>${correcto.map(t => { const r = filas.find(f => f.territorio === t); return html`<li>${t}: <b>${fmt(r.valor)}</b></li>`; })}</ol><p><small>${s.unidad}</small></p>`, sig);
      }
    }; bot.append(b); });
    caja.append(html`<p class="juego-ind">${s.nombre} · ${c.per}</p>`, bot, lista);
  };
  ronda();
  return caja;
}
```

## 🏫 Modo aula: competición en clase {#aula}

El profesor elige un **código de sala** y lo proyecta. Todos los estudiantes que escriban el mismo código reciben **las mismas preguntas**. Al terminar, cada estudiante ve su puntuación y su tiempo, y un código de verificación para que el profesor compruebe el resultado. No hace falta registrarse ni se guarda nada en ningún servidor.

```{ojs}
//| echo: false
viewof salaArea = Inputs.select(new Map([["Todas las áreas", "todas"], ...Object.entries(__AREAS__).map(([k, v]) => [v, k])]), {label: "Área"})
viewof salaCodigo = Inputs.text({label: "Código de sala", placeholder: "p. ej. MACRO-A", submit: "Entrar"})
```

```{ojs}
//| echo: false
{
  if (!salaCodigo) return html`<p class="pending">Escribe el código de sala que indique el profesor y pulsa <b>Entrar</b>. El profesor puede inventar cualquier código.</p>`;
  const cod = salaCodigo.trim().toUpperCase();
  const pool = paisesJ.filter(s => salaArea === "todas" || s.pagina === salaArea);
  const caja = html`<div class="juego"><p class="pending">Preparando las preguntas de la sala ${cod}…</p></div>`;
  (async () => {
    const qs = await generarSerie(pool, ["test", "vf", "test", "vf"], 10, `sala-${cod}-${salaArea}`);
    if (!qs.length) { caja.innerHTML = `<p class="pending">No se han podido cargar preguntas.</p>`; return; }
    let i = 0, puntos = 0; const t0 = Date.now(), resp = [];
    evento("aula/entrar");
    const pintar = () => {
      caja.innerHTML = "";
      if (i >= qs.length) {
        const seg = Math.round((Date.now() - t0) / 1000);
        const ver = [...`${cod}|${puntos}|${seg}|${resp.join("")}`].reduce((h, c) => Math.imul(h ^ c.charCodeAt(0), 16777619) >>> 0, 2166136261).toString(36).toUpperCase().slice(0, 5);
        evento(`aula/fin/${puntos}`);
        caja.append(html`<div class="juego-final"><p>Sala <b>${cod}</b></p><p class="juego-grande">${puntos} / ${qs.length}</p><p>Tiempo: ${Math.floor(seg / 60)} min ${seg % 60} s · Respuestas: <code>${resp.join("")}</code> · Verificación: <code>${ver}</code></p><p><small>Enséñale esta pantalla al profesor. Gana quien tenga más aciertos; en caso de empate, el menor tiempo.</small></p></div>`);
        return;
      }
      const q = qs[i];
      const bot = html`<div class="juego-ops">`;
      q.opciones.forEach((o, k) => { const b = html`<button class="juego-op">${o}</button>`; b.onclick = () => {
        const bien = k === q.respuesta; if (bien) puntos++; resp.push("abcd"[k]);
        bot.querySelectorAll("button").forEach((x, j) => { x.disabled = true; if (j === q.respuesta) x.classList.add("ok"); });
        if (!bien) b.classList.add("ko");
        setTimeout(() => { i++; pintar(); }, 1200);
      }; bot.append(b); });
      caja.append(html`<p class="juego-ind">Pregunta ${i + 1} de ${qs.length} · Aciertos: ${puntos}</p><p class="juego-p">${q.enunciado.split("**").map((t, j) => j % 2 ? html`<b>${t}</b>` : t)}</p>`, bot);
    };
    pintar();
  })();
  return caja;
}
```

::: {.callout-tip appearance="simple"}
**Para el profesorado.** Proyecta el código de sala (por ejemplo, el nombre del grupo y la fecha) y pide a los estudiantes que entren desde el móvil. Para preparar preguntas más largas o un examen, usa el [generador de exámenes](examen.qmd).
:::
''', ESPECS=J(unicos), EPIS=J(EPISODIOS), PERFIL=J(PERFIL), AREAS=J(AREAS))

# Selector común: indicador y territorio
SELECTOR = r'''```{ojs}
//| echo: false
espec = __ESPECS__
viewof indSel = Inputs.select(new Map(espec.filter(__FILTRO__).map(s => [s.nombre, s])), {label: "Indicador", value: espec.find(s => s.id === "__DEF__")})
datosSel = cargar(indSel)
```'''
def selector(filtro="s => true", defecto="tasa-de-paro", lista=None):
    return SELECTOR.replace("__ESPECS__", J(lista or unicos)).replace("__FILTRO__", filtro).replace("__DEF__", defecto)

# =====================================================================================
# 7. Predice el próximo dato
# =====================================================================================
pagina("prediccion.qmd", r'''---
title: "Predice el próximo dato"
subtitle: "Apuesta por el próximo valor publicado y comprueba tu acierto cuando salga"
toc: false
---

Elige un indicador mensual o trimestral, mira su evolución y escribe tu previsión para el **próximo dato que publicará Eurostat**. Tus predicciones se guardan en este navegador; cuando vuelvas tras la publicación, verás tu error y tu puntuación. Compara tu previsión con la de tus compañeros copiando el texto para compartir.

__HELPERS__

__SELECTOR__

```{ojs}
//| echo: false
mutable predicciones = { try { return JSON.parse(localStorage.getItem("ccee-pred") ?? "[]"); } catch (e) { return []; } }
```

```{ojs}
//| echo: false
geoPred = {
  const d = await datosSel;
  const terrs = [...new Set(d.rows.map(r => r.territorio))];
  return terrs.includes("España") ? "España" : terrs[0];
}
viewof terrPred = Inputs.select([...new Set((await datosSel).rows.map(r => r.territorio))].sort((a, b) => a.localeCompare(b, "es")), {label: "Territorio", value: geoPred})
```

```{ojs}
//| echo: false
seriePred = (await datosSel).rows.filter(r => r.territorio === terrPred).sort((a, b) => a.fecha - b.fecha)
siguiente = {
  const u = seriePred.at(-1); if (!u) return null;
  const f = new Date(u.fecha); f.setMonth(f.getMonth() + (indSel.frecuencia === "Trimestral" ? 3 : 1));
  const per = indSel.frecuencia === "Trimestral" ? `${f.getFullYear()}-T${f.getMonth() / 3 + 1}` : f.toLocaleDateString("es-ES", {month: "long", year: "numeric"});
  return {fecha: f, per, ultimo: u};
}
{
  if (!seriePred.length) return html`<p class="pending">No hay datos para este territorio.</p>`;
  const u = siguiente.ultimo, tramo = seriePred.slice(-36);
  return html`<div class="kpi-grid"><div class="kpi"><div class="kpi-l">Último dato · ${u.periodo}</div><div class="kpi-n">${fmt(u.valor)}</div><div class="kpi-s">${indSel.unidad}</div></div>
    <div class="kpi"><div class="kpi-l">Media de los últimos 12</div><div class="kpi-n">${fmt(d3.mean(seriePred.slice(-12), r => r.valor))}</div></div>
    <div class="kpi"><div class="kpi-l">Próximo dato a predecir</div><div class="kpi-n" style="font-size:1.3rem">${siguiente.per}</div></div></div>
    ${Plot.plot({height: 260, marginLeft: 50, y: {grid: true, label: indSel.unidad}, x: {label: null},
      marks: [Plot.lineY(tramo, {x: "fecha", y: "valor", stroke: "#A6195E", strokeWidth: 2}), Plot.dot(tramo.slice(-1), {x: "fecha", y: "valor", fill: "#A6195E", r: 4}),
        Plot.tip(tramo, Plot.pointerX({x: "fecha", y: "valor", title: r => `${r.periodo}: ${fmt(r.valor)}`}))]})}`;
}
```

```{ojs}
//| echo: false
viewof miPred = Inputs.form({valor: Inputs.number({label: `Tu previsión para ${siguiente?.per ?? ""}`, placeholder: siguiente ? fmt(siguiente.ultimo.valor) : ""}),
  alias: Inputs.text({label: "Tu alias (opcional)", placeholder: "para compartir"})}, {submit: "Guardar mi predicción"})
```

```{ojs}
//| echo: false
{
  if (!Number.isFinite(miPred?.valor) || !siguiente) return html``;
  const lista = (mutable predicciones).filter(p => !(p.id === indSel.id && p.terr === terrPred && p.objetivo === siguiente.fecha.toISOString()));
  lista.push({id: indSel.id, nombre: indSel.nombre, terr: terrPred, objetivo: siguiente.fecha.toISOString(), per: siguiente.per, valor: miPred.valor, ultimo: siguiente.ultimo.valor, unidad: indSel.unidad, alias: miPred.alias, hecho: new Date().toISOString()});
  try { localStorage.setItem("ccee-pred", JSON.stringify(lista)); } catch (e) {}
  mutable predicciones = lista;
  window.cceeEvento && window.cceeEvento(`prediccion/${indSel.id}`, `Predicción: ${indSel.nombre}`, true);
  const txt = `${miPred.alias ? miPred.alias + " predice" : "Mi predicción"} en CCEEscopio: ${indSel.nombre} (${terrPred}) en ${siguiente.per} = ${fmt(miPred.valor)} (último dato: ${fmt(siguiente.ultimo.valor)}). ¿Y tú? ${location.href}`;
  const b = html`<button class="copiar">📋 Copiar para compartir</button>`; b.onclick = () => navigator.clipboard.writeText(txt).then(() => b.textContent = "✔ Copiado");
  return html`<p class="juego-res bien">✔ Predicción guardada: <b>${fmt(miPred.valor)}</b> para ${siguiente.per}.</p>${b}`;
}
```

## Mis predicciones

```{ojs}
//| echo: false
{
  if (!predicciones.length) return html`<p class="pending">Todavía no has guardado predicciones en este navegador.</p>`;
  const filas = await Promise.all(predicciones.map(async p => {
    const s = espec.find(x => x.id === p.id);
    const d = s ? await cargar(s) : {rows: []};
    const real = d.rows.find(r => r.territorio === p.terr && Math.abs(r.fecha - new Date(p.objetivo)) < 20 * 864e5);
    return {...p, real: real?.valor};
  }));
  const puntos = (p) => { const err = Math.abs(p.valor - p.real), escala = Math.max(Math.abs(p.real - p.ultimo), 0.1); return Math.max(0, Math.round(100 * (1 - err / (2 * escala)))); };
  const res = filas.filter(p => p.real !== undefined);
  const borrar = html`<button class="copiar">🗑 Borrar todas</button>`;
  borrar.onclick = () => { try { localStorage.removeItem("ccee-pred"); } catch (e) {} mutable predicciones = []; };
  return html`<table class="uso-tabla"><tr><th>Indicador</th><th>Territorio</th><th>Periodo</th><th>Tu previsión</th><th>Dato real</th><th>Error</th><th>Puntos</th></tr>
    ${filas.map(p => html`<tr><td>${p.nombre}</td><td>${p.terr}</td><td>${p.per}</td><td>${fmt(p.valor)}</td><td>${p.real === undefined ? html`<i>pendiente</i>` : fmt(p.real)}</td>
      <td>${p.real === undefined ? "" : fmt(p.valor - p.real)}</td><td>${p.real === undefined ? "" : html`<b>${puntos(p)}</b>`}</td></tr>`)}</table>
    ${res.length ? html`<p>Puntuación media: <b>${Math.round(d3.mean(res, puntos))}</b> de 100 en ${res.length} predicciones resueltas. Obtienes 100 puntos si aciertas exactamente y 0 si te equivocas el doble de lo que cambió el dato.</p>` : ""}${borrar}`;
}
```
''', SELECTOR=selector('s => ["Mensual", "Trimestral"].includes(s.frecuencia)', "ipca-inflacion-general-tasa-anual"))

# =====================================================================================
# 1. Detector de datos extremos e inusuales
# =====================================================================================
CLAVE = ["ipca-inflacion-general-tasa-anual", "tasa-de-paro", "tasa-de-paro-juvenil-menores-de-25-anos", "pib-crecimiento-interanual-trimestral",
         "indice-de-produccion-industrial", "indicador-de-sentimiento-economico", "confianza-del-consumidor", "rentabilidad-del-bono-a-10-anos",
         "pernoctaciones-en-hoteles", "precio-de-la-vivienda-tasa-anual", "euribor-a-3-meses", "indice-de-comercio-minorista"]
pagina("extremos.qmd", r'''---
title: "Datos extremos e inusuales"
subtitle: "Máximos, mínimos y saltos fuera de lo normal: cuándo se produjeron y dónde"
toc: true
---

Para cada indicador, esta herramienta localiza los **valores récord** de cada territorio y los **cambios inusuales**: variaciones de un periodo a otro que se alejan mucho de lo habitual (más de *k* desviaciones típicas, regla de la puntuación *z*). Debajo tienes los **récords recientes** de los indicadores clave.

__HELPERS__

__SELECTOR__

```{ojs}
//| echo: false
viewof umbralZ = Inputs.range([1.5, 4], {label: "Umbral de inusual (k desviaciones típicas)", value: 2.5, step: 0.1})
analisis = {
  const d = await datosSel;
  if (!d.ok) return null;
  return d3.groups(d.rows, r => r.territorio).map(([t, v]) => {
    v.sort((a, b) => a.fecha - b.fecha);
    const cambios = v.slice(1).map((r, i) => ({...r, cambio: r.valor - v[i].valor, previo: v[i]}));
    const m = d3.mean(cambios, c => c.cambio), sd = d3.deviation(cambios, c => c.cambio) || 1;
    cambios.forEach(c => c.z = (c.cambio - m) / sd);
    const max = d3.greatest(v, r => r.valor), min = d3.least(v, r => r.valor), u = v.at(-1);
    const pctil = d3.mean(v, r => r.valor <= u.valor ? 1 : 0) * 100;
    return {t, v, cambios, max, min, u, pctil, inusuales: cambios.filter(c => Math.abs(c.z) >= umbralZ)};
  });
}
```

## Récords de cada territorio

```{ojs}
//| echo: false
{
  if (!analisis) return html`<p class="pending">No se han podido cargar los datos.</p>`;
  const filas = analisis.slice().sort((a, b) => b.pctil - a.pctil);
  return html`<p>${indSel.nombre} (${indSel.unidad}). El <b>percentil</b> indica qué posición ocupa el último dato dentro del historial de cada territorio: 100 = máximo histórico, 0 = mínimo.</p>
  <div class="tabla-scroll"><table class="uso-tabla"><tr><th>Territorio</th><th>Máximo</th><th>Cuándo</th><th>Mínimo</th><th>Cuándo</th><th>Último</th><th>Percentil</th><th>Inusuales</th></tr>
  ${filas.map(a => html`<tr><td>${a.t}</td><td>${fmt(a.max.valor)}</td><td>${a.max.periodo}</td><td>${fmt(a.min.valor)}</td><td>${a.min.periodo}</td>
    <td>${fmt(a.u.valor)} <small>(${a.u.periodo})</small></td><td><span class="pctil" style="background:${d3.interpolateRdYlBu(1 - a.pctil / 100)}">${Math.round(a.pctil)}</span>${a.u === a.max ? " 🔺 récord" : a.u === a.min ? " 🔻 mínimo" : ""}</td><td>${a.inusuales.length}</td></tr>`)}</table></div>`;
}
```

## Cambios inusuales

```{ojs}
//| echo: false
viewof terrExt = Inputs.select(analisis ? analisis.map(a => a.t).sort((a, b) => a.localeCompare(b, "es")) : [], {label: "Territorio", value: analisis?.some(a => a.t === "España") ? "España" : analisis?.[0]?.t})
```

```{ojs}
//| echo: false
{
  const a = analisis?.find(x => x.t === terrExt);
  if (!a) return html``;
  const pct = /%|puntos|saldo/i.test(indSel.unidad) ? "puntos" : indSel.unidad;
  return html`${Plot.plot({height: 300, marginLeft: 55, y: {grid: true, label: indSel.unidad}, x: {label: null},
      marks: [Plot.lineY(a.v, {x: "fecha", y: "valor", stroke: "#888"}),
        Plot.dot(a.inusuales, {x: "fecha", y: "valor", r: 6, fill: c => c.z > 0 ? "#C0392B" : "#2C6FBB", stroke: "white"}),
        Plot.dot([a.max, a.min], {x: "fecha", y: "valor", r: 8, symbol: "star", fill: "#E6A400"}),
        Plot.tip(a.v, Plot.pointerX({x: "fecha", y: "valor", title: r => `${r.periodo}: ${fmt(r.valor)}`}))]})}
    <p class="nota">Puntos rojos: subidas inusuales; azules: bajadas inusuales; estrellas: máximo y mínimo históricos.</p>
    ${a.inusuales.length ? html`<table class="uso-tabla"><tr><th>Periodo</th><th>Valor</th><th>Cambio</th><th>z</th></tr>
      ${a.inusuales.slice().sort((x, y) => Math.abs(y.z) - Math.abs(x.z)).map(c => html`<tr><td>${c.periodo}</td><td>${fmt(c.valor)}</td><td>${c.cambio > 0 ? "+" : ""}${fmt(c.cambio)} ${pct}</td><td>${fmt(c.z)}</td></tr>`)}</table>` : html`<p>No hay cambios por encima del umbral.</p>`}`;
}
```

## Cronología: ¿cuándo se concentran los episodios inusuales?

```{ojs}
//| echo: false
{
  if (!analisis) return html``;
  const ev = analisis.flatMap(a => a.inusuales.map(c => ({t: a.t, anio: c.fecha.getFullYear(), signo: c.z > 0 ? "Subida" : "Bajada"})));
  if (!ev.length) return html`<p>Sin episodios inusuales con este umbral.</p>`;
  return Plot.plot({height: 240, marginLeft: 40, x: {label: null, tickFormat: d => String(d)}, y: {label: "Nº de cambios inusuales (todos los territorios)", grid: true},
    color: {domain: ["Subida", "Bajada"], range: ["#C0392B", "#2C6FBB"], legend: true},
    marks: [Plot.barY(ev, Plot.groupX({y: "count"}, {x: "anio", fill: "signo", tip: true})), Plot.ruleY([0])]});
}
```

## Récords recientes en los indicadores clave

Indicadores clave en los que **España** está en máximos o mínimos de la serie, o en el 10 % más alto o más bajo de su historial.

```{ojs}
//| echo: false
{
  const claves = __CLAVE__.map(i => espec.find(s => s.id === i)).filter(Boolean);
  const res = (await Promise.all(claves.map(async s => {
    const d = await cargar(s); if (!d.ok) return null;
    const terrs = new Set(d.rows.map(r => r.territorio)); const t = terrs.has("España") ? "España" : [...terrs][0];
    const v = d.rows.filter(r => r.territorio === t).sort((a, b) => a.fecha - b.fecha); if (v.length < 10) return null;
    const u = v.at(-1), p = 100 * d3.mean(v, r => r.valor <= u.valor ? 1 : 0);
    const desde = v.slice().reverse().find(r => (p >= 50 ? r.valor > u.valor : r.valor < u.valor));
    return {s, u, p, desde, primero: v[0]};
  }))).filter(r => r && (r.p >= 90 || r.p <= 10));
  if (!res.length) return html`<p>Ahora mismo ningún indicador clave está en zona de récord.</p>`;
  return html`<div class="kpi-grid">${res.map(r => html`<div class="kpi"><div class="kpi-l">${r.s.nombre}</div><div class="kpi-n">${fmt(r.u.valor)}</div>
    <div class="kpi-s">${r.u.periodo} · ${r.p >= 50 ? "🔺 alto" : "🔻 bajo"}: ${r.desde ? `el ${r.p >= 50 ? "más alto" : "más bajo"} desde ${r.desde.periodo}` : `récord desde ${r.primero.periodo}`}</div></div>`)}</div>`;
}
```
''', SELECTOR=selector(defecto="tasa-de-paro"), CLAVE=J(CLAVE))

# =====================================================================================
# 10. Convergencia sigma y beta
# =====================================================================================
pagina("convergencia.qmd", r'''---
title: "¿Convergen las economías?"
subtitle: "Convergencia sigma y beta entre países de la UE o entre regiones españolas"
toc: true
---

Dos formas clásicas de medir la convergencia:

- **Convergencia sigma (σ):** la dispersión entre territorios (coeficiente de variación) disminuye con el tiempo.
- **Convergencia beta (β):** los territorios que partían de valores más bajos crecen más deprisa. Se estima con la regresión de la tasa media de crecimiento anual sobre el logaritmo del valor inicial; una pendiente negativa indica convergencia.

__HELPERS__

__SELECTOR__

```{ojs}
//| echo: false
filasConv = { const d = await datosSel; return d.ok ? d.rows.filter(r => !["UE-27", "Zona euro", "Zona euro (19)", "España"].includes(r.territorio) || (!indSel.regional && r.territorio === "España")) : []; }
aniosConv = { const a = d3.rollups(filasConv, v => new Set(v.map(r => r.territorio)).size, r => r.fecha.getFullYear()).filter(([, n]) => n >= 8).map(([y]) => y).sort(); return a; }
viewof rangoConv = Inputs.form([Inputs.select(aniosConv, {label: "Año inicial", value: aniosConv[0]}), Inputs.select(aniosConv, {label: "Año final", value: aniosConv.at(-1)})])
```

## Convergencia sigma

```{ojs}
//| echo: false
anualConv = d3.rollups(filasConv, v => d3.mean(v, r => r.valor), r => r.territorio, r => r.fecha.getFullYear()).flatMap(([t, a]) => a.map(([y, v]) => ({t, y, v})))
sigma = d3.rollups(anualConv.filter(d => d.y >= rangoConv[0] && d.y <= rangoConv[1]), v => ({cv: 100 * d3.deviation(v, d => d.v) / Math.abs(d3.mean(v, d => d.v)), sd: d3.deviation(v, d => d.v), n: v.length}), d => d.y).map(([y, o]) => ({y, ...o})).filter(d => d.n >= 5).sort((a, b) => a.y - b.y)
{
  if (sigma.length < 2) return html`<p class="pending">No hay suficientes años con datos.</p>`;
  const cambio = sigma.at(-1).cv - sigma[0].cv;
  return html`<p>Entre ${sigma[0].y} y ${sigma.at(-1).y} el coeficiente de variación de <b>${indSel.nombre}</b> pasó de ${fmt(sigma[0].cv)} % a ${fmt(sigma.at(-1).cv)} %: ${cambio < 0 ? html`<b>hay convergencia sigma</b> (la dispersión se reduce)` : html`<b>no hay convergencia sigma</b> (la dispersión aumenta)`}.</p>
  ${Plot.plot({height: 260, marginLeft: 50, x: {label: null, tickFormat: d => String(d)}, y: {label: "Coeficiente de variación (%)", grid: true},
    marks: [Plot.lineY(sigma, {x: "y", y: "cv", stroke: "#A6195E", strokeWidth: 2.5}), Plot.dot(sigma, {x: "y", y: "cv", fill: "#A6195E", tip: true, title: d => `${d.y}: CV ${fmt(d.cv)} % (${d.n} territorios)`})]})}`;
}
```

## Convergencia beta

```{ojs}
//| echo: false
{
  const [y0, y1] = rangoConv; const n = y1 - y0;
  if (n < 2) return html`<p class="pending">Elige al menos dos años de diferencia.</p>`;
  const m = d3.group(anualConv, d => d.t);
  const pts = [...m].map(([t, v]) => { const a = v.find(d => d.y === y0), b = v.find(d => d.y === y1); return a && b && a.v > 0 && b.v > 0 ? {t, x: Math.log(a.v), ini: a.v, g: 100 * (Math.pow(b.v / a.v, 1 / n) - 1)} : null; }).filter(Boolean);
  if (pts.length < 5) return html`<p class="pending">La convergencia beta necesita valores positivos en ambos años para al menos 5 territorios. Prueba con un indicador en niveles (PIB per cápita, salarios…).</p>`;
  const mx = d3.mean(pts, p => p.x), my = d3.mean(pts, p => p.g);
  const b = d3.sum(pts, p => (p.x - mx) * (p.g - my)) / d3.sum(pts, p => (p.x - mx) ** 2), a = my - b * mx;
  const ssr = d3.sum(pts, p => (p.g - a - b * p.x) ** 2), sst = d3.sum(pts, p => (p.g - my) ** 2), r2 = 1 - ssr / sst;
  const se = Math.sqrt(ssr / (pts.length - 2) / d3.sum(pts, p => (p.x - mx) ** 2)), tb = b / se;
  const vel = b < 0 ? -Math.log(1 + b / 100 * n) / n * 100 : null;
  const xs = d3.extent(pts, p => p.x);
  return html`<p>Regresión: crecimiento medio anual (%) = ${fmt(a)} ${b < 0 ? "−" : "+"} ${fmt(Math.abs(b))} × ln(valor ${y0}). R² = ${fmt(r2)}, t = ${fmt(tb)}, ${pts.length} territorios.
    ${b < 0 ? html`La pendiente es negativa: <b>hay convergencia beta</b>${Math.abs(tb) < 2 ? " (pero no es estadísticamente significativa al 5 %)" : ""}. Velocidad de convergencia implícita ≈ ${fmt(vel)} % anual${vel > 0 ? ` (la mitad de la distancia se cerraría en unos ${Math.round(Math.log(2) / (vel / 100))} años)` : ""}.` : html`La pendiente es positiva: <b>no hay convergencia beta</b>; los que partían más arriba han crecido más.`}</p>
  ${Plot.plot({height: 360, marginLeft: 55, x: {label: `ln(${indSel.nombre}, ${y0})`}, y: {label: `Crecimiento medio anual ${y0}-${y1} (%)`, grid: true},
    marks: [Plot.ruleY([0], {stroke: "#bbb"}), Plot.line([[xs[0], a + b * xs[0]], [xs[1], a + b * xs[1]]], {stroke: "#E6A400", strokeWidth: 2, strokeDasharray: "5,4"}),
      Plot.dot(pts, {x: "x", y: "g", fill: p => p.t === "España" || p.t === "Andalucía" ? "#A6195E" : "#2C6FBB", r: 5, tip: true, title: p => `${p.t}\n${y0}: ${fmt(p.ini)}\nCrecimiento: ${fmt(p.g)} %`}),
      Plot.text(pts, {x: "x", y: "g", text: "t", dy: -9, fontSize: 9, fill: "#555"})]})}`;
}
```
''', SELECTOR=selector('s => !s.sinGeo && s.frecuencia === "Anual"', "pib-per-capita-en-paridad-de-poder-de-compra"))

# =====================================================================================
# 11. Ciclo económico y semáforo de coyuntura
# =====================================================================================
CICLO = [("pib-crecimiento-interanual-trimestral", 1), ("tasa-de-paro", -1), ("indice-de-produccion-industrial", 1),
         ("indice-de-comercio-minorista", 1), ("indicador-de-sentimiento-economico", 1), ("confianza-del-consumidor", 1),
         ("confianza-de-la-industria", 1), ("produccion-en-la-construccion", 1), ("confianza-en-los-servicios", 1),
         ("pernoctaciones-en-hoteles", 1)]
pagina("ciclo.qmd", r'''---
title: "Ciclo económico y semáforo de coyuntura"
subtitle: "¿En qué fase del ciclo está la economía? Reloj del ciclo con los últimos datos"
toc: true
---

Cada indicador se compara con su **tendencia** (media móvil de los últimos 12 meses o 4 trimestres). Su posición respecto a la tendencia (por encima o por debajo) y su dirección (mejorando o empeorando) lo sitúan en una de las cuatro fases del **reloj del ciclo**:

| | Mejorando | Empeorando |
|---|---|---|
| **Por encima de la tendencia** | 🟢 Expansión | 🟡 Desaceleración |
| **Por debajo de la tendencia** | 🔵 Recuperación | 🔴 Recesión |

En la tasa de paro se invierte el signo, porque más paro es peor.

__HELPERS__

```{ojs}
//| echo: false
especC = __ESPECS__
cicloIds = __CICLO__
viewof geoCiclo = Inputs.select(["España", "UE-27", "Alemania", "Francia", "Italia", "Portugal"], {label: "Territorio", value: "España"})
FASES = ({exp: ["Expansión", "#4C9A2A", "🟢"], des: ["Desaceleración", "#E6A400", "🟡"], rec: ["Recesión", "#C0392B", "🔴"], recu: ["Recuperación", "#2C6FBB", "🔵"]})
cicloDe = (rows, signo, trimestral) => {
  const v = rows.slice().sort((a, b) => a.fecha - b.fecha);
  const L = trimestral ? 4 : 12, h = trimestral ? 1 : 3;
  const out = [];
  for (let i = L; i < v.length; i++) {
    const tend = d3.mean(v.slice(i - L, i + 1), r => r.valor);
    out.push({...v[i], brecha: signo * (v[i].valor - tend)});
  }
  const sd = d3.deviation(out, o => o.brecha) || 1;
  out.forEach((o, i) => { o.z = o.brecha / sd; o.dz = i >= h ? o.z - out[i - h].z : 0; o.fase = o.z >= 0 ? (o.dz >= 0 ? "exp" : "des") : (o.dz >= 0 ? "recu" : "rec"); });
  return out;
}
cicloTodos = (await Promise.all(cicloIds.map(async ([id, signo]) => {
  const s = especC.find(x => x.id === id); if (!s) return null;
  const d = await cargar(s); if (!d.ok) return null;
  const rows = d.rows.filter(r => r.territorio === geoCiclo); if (rows.length < 20) return null;
  return {s, c: cicloDe(rows, signo, s.frecuencia === "Trimestral")};
}))).filter(Boolean)
```

## Semáforo de coyuntura

```{ojs}
//| echo: false
{
  if (!cicloTodos.length) return html`<p class="pending">No se han podido cargar los datos.</p>`;
  const cuenta = d3.rollup(cicloTodos, v => v.length, x => x.c.at(-1).fase);
  const dom = [...cuenta].sort((a, b) => b[1] - a[1])[0][0];
  return html`<p class="juego-grande" style="color:${FASES[dom][1]}">${FASES[dom][2]} ${FASES[dom][0]}</p>
  <p>Fase predominante en ${geoCiclo}: ${[...cuenta].map(([f, n]) => `${FASES[f][2]} ${FASES[f][0]}: ${n}`).join(" · ")} indicadores.</p>
  <table class="uso-tabla"><tr><th>Indicador</th><th>Último dato</th><th>Valor</th><th>Frente a la tendencia</th><th>Fase</th></tr>
  ${cicloTodos.map(({s, c}) => { const u = c.at(-1); return html`<tr><td>${s.nombre}</td><td>${u.periodo}</td><td>${fmt(u.valor)}</td><td>${u.z >= 0 ? "▲ por encima" : "▼ por debajo"} (${fmt(u.z)} σ)</td><td style="color:${FASES[u.fase][1]};font-weight:700">${FASES[u.fase][2]} ${FASES[u.fase][0]}</td></tr>`; })}</table>`;
}
```

## Reloj del ciclo

```{ojs}
//| echo: false
viewof indCiclo = Inputs.select(new Map(cicloTodos.map(x => [x.s.nombre, x])), {label: "Indicador"})
viewof nCiclo = Inputs.range([6, 60], {label: "Periodos a mostrar", value: 24, step: 1})
```

```{ojs}
//| echo: false
{
  if (!indCiclo) return html``;
  const tr = indCiclo.c.slice(-nCiclo);
  const m = Math.max(1.5, d3.max(tr, d => Math.max(Math.abs(d.z), Math.abs(d.dz))) * 1.1);
  const cuad = [{x1: 0, x2: m, y1: 0, y2: m, f: "exp"}, {x1: 0, x2: m, y1: -m, y2: 0, f: "des"}, {x1: -m, x2: 0, y1: -m, y2: 0, f: "rec"}, {x1: -m, x2: 0, y1: 0, y2: m, f: "recu"}];
  return Plot.plot({height: 440, width: 520, marginLeft: 50, x: {domain: [-m, m], label: "Posición frente a la tendencia (σ) →"}, y: {domain: [-m, m], label: "↑ Dirección (cambio reciente)"},
    marks: [Plot.rect(cuad, {x1: "x1", x2: "x2", y1: "y1", y2: "y2", fill: d => FASES[d.f][1], fillOpacity: 0.1}),
      Plot.text(cuad, {x: d => (d.x1 + d.x2) / 2, y: d => d.y1 > -0.01 ? m * 0.9 : -m * 0.9, text: d => FASES[d.f][0], fill: d => FASES[d.f][1], fontWeight: 700, fontSize: 13}),
      Plot.ruleX([0]), Plot.ruleY([0]),
      Plot.line(tr, {x: "z", y: "dz", stroke: "#888", curve: "catmull-rom", markerEnd: "arrow"}),
      Plot.dot(tr, {x: "z", y: "dz", r: (d, i) => i === tr.length - 1 ? 7 : 3, fill: d => FASES[d.fase][1], tip: true, title: d => `${d.periodo}: ${fmt(d.valor)}\n${FASES[d.fase][0]}`}),
      Plot.text(tr.filter((d, i) => i === 0 || i === tr.length - 1), {x: "z", y: "dz", text: "periodo", dy: -12, fontSize: 10})]});
}
```

::: {.callout-note appearance="simple"}
**Cómo se calcula.** Tendencia: media móvil de los últimos 12 meses (4 trimestres). Brecha: diferencia entre el dato y la tendencia, dividida por su desviación típica. Dirección: cambio de la brecha en los últimos 3 meses (1 trimestre). Es un método sencillo con fines docentes; los organismos oficiales (OCDE, Banco de España) usan filtros más elaborados.
:::
''', ESPECS=J(unicos), CICLO=J(CICLO))

# =====================================================================================
# 12. Correlación con desfase
# =====================================================================================
pagina("desfases.qmd", r'''---
title: "¿Qué indicador se adelanta?"
subtitle: "Correlación con desfase entre dos indicadores: adelantados, coincidentes y retrasados"
toc: false
---

Elige dos indicadores y un territorio. Calculamos la correlación entre **X desplazado k periodos** e **Y**. Si la correlación máxima se da con *k* > 0, **X se adelanta** a Y *k* periodos; con *k* < 0, X va retrasado. Ejemplo clásico: la confianza del consumidor frente al consumo de los hogares, o la producción industrial frente al paro.

__HELPERS__

```{ojs}
//| echo: false
especD = __ESPECS__
mapaD = new Map(especD.map(s => [s.nombre, s]))
viewof dX = Inputs.select(mapaD, {label: "Indicador X", value: especD.find(s => s.id === "indicador-de-sentimiento-economico")})
viewof dY = Inputs.select(mapaD, {label: "Indicador Y", value: especD.find(s => s.id === "indice-de-produccion-industrial")})
viewof dGeo = Inputs.select(["España", "UE-27", "Alemania", "Francia", "Italia", "Portugal"], {label: "Territorio", value: "España"})
viewof dTrans = Inputs.radio(["Niveles", "Variación interanual"], {label: "Transformación", value: "Variación interanual"})
viewof dMax = Inputs.range([3, 24], {label: "Desfase máximo (periodos)", value: 12, step: 1})
```

```{ojs}
//| echo: false
{
  const [a, b] = await Promise.all([cargar(dX), cargar(dY)]);
  if (!a.ok || !b.ok) return html`<p class="pending">No se han podido cargar los datos.</p>`;
  const trim = dX.frecuencia === "Trimestral" || dY.frecuencia === "Trimestral";
  const clave = (f) => trim ? `${f.getFullYear()}-${Math.floor(f.getMonth() / 3)}` : `${f.getFullYear()}-${f.getMonth()}`;
  const serie = (d, tr) => {
    let m = d3.rollups(d.rows.filter(r => r.territorio === dGeo), v => ({valor: d3.mean(v, r => r.valor), fecha: v[0].fecha}), r => clave(r.fecha)).map(([k, o]) => ({k, ...o})).sort((x, y) => x.fecha - y.fecha);
    if (tr === "Variación interanual") { const p = trim ? 4 : 12; const ix = new Map(m.map(o => [o.k, o])); m = m.map(o => { const f = new Date(o.fecha); f.setFullYear(f.getFullYear() - 1); const ant = ix.get(clave(f)); return ant && ant.valor ? {...o, valor: /%|puntos|saldo/i.test(d.rows[0].unidad) ? o.valor - ant.valor : 100 * (o.valor / ant.valor - 1)} : null; }).filter(Boolean); }
    return m;
  };
  const sx = serie(a, dTrans), sy = serie(b, dTrans);
  const iy = new Map(sy.map((o, i) => [o.k, i]));
  const idx = sx.map(o => o.k);
  const res = d3.range(-dMax, dMax + 1).map(k => {
    const pares = [];
    sx.forEach((o, i) => { const j = i + k; if (j < 0 || j >= sx.length) return; const yi = iy.get(idx[j]); if (yi !== undefined) pares.push([o.valor, sy[yi].valor]); });
    if (pares.length < 12) return {k, r: NaN, n: pares.length};
    const mx = d3.mean(pares, p => p[0]), my = d3.mean(pares, p => p[1]);
    const r = d3.sum(pares, p => (p[0] - mx) * (p[1] - my)) / Math.sqrt(d3.sum(pares, p => (p[0] - mx) ** 2) * d3.sum(pares, p => (p[1] - my) ** 2));
    return {k, r, n: pares.length};
  }).filter(d => Number.isFinite(d.r));
  if (!res.length) return html`<p class="pending">No hay suficientes periodos en común para ${dGeo}.</p>`;
  const mejor = d3.greatest(res, d => Math.abs(d.r)), u = trim ? "trimestres" : "meses";
  const r0 = res.find(d => d.k === 0);
  window.cceeEvento && window.cceeEvento("desfases/calculo", "Correlación con desfase", true);
  const z = (s) => { const m = d3.mean(s, o => o.valor), sd = d3.deviation(s, o => o.valor) || 1; return s.map(o => ({...o, z: (o.valor - m) / sd})); };
  return html`<p>Correlación contemporánea (k = 0): <b>${r0 ? fmt(r0.r) : "–"}</b>. Correlación máxima en valor absoluto: <b>${fmt(mejor.r)}</b> con <b>k = ${mejor.k}</b> ${u}:
    ${mejor.k > 0 ? html`<b>${dX.nombre}</b> se adelanta unos ${mejor.k} ${u} a <b>${dY.nombre}</b>.` : mejor.k < 0 ? html`<b>${dX.nombre}</b> va unos ${-mejor.k} ${u} por detrás de <b>${dY.nombre}</b>.` : html`los dos indicadores son <b>coincidentes</b>.`}
    ${mejor.r < 0 ? " La relación es inversa (cuando uno sube, el otro baja)." : ""}</p>
  ${Plot.plot({height: 260, marginLeft: 45, x: {label: `Desfase k (${u}); k > 0: X se adelanta`}, y: {label: "Correlación", domain: [-1, 1], grid: true},
    marks: [Plot.ruleY([0]), Plot.barY(res, {x: "k", y: "r", fill: d => d === mejor ? "#A6195E" : "#C9B6BF", tip: true, title: d => `k = ${d.k}: r = ${fmt(d.r)} (${d.n} pares)`})]})}
  <p class="nota">Series estandarizadas (media 0, desviación 1), con X desplazada ${mejor.k} ${u}:</p>
  ${Plot.plot({height: 240, marginLeft: 40, y: {label: "Valor estandarizado", grid: true}, x: {label: null}, color: {legend: true},
    marks: [Plot.lineY(z(sy).map(o => ({...o, serie: dY.nombre})), {x: "fecha", y: "z", stroke: "serie"}),
      Plot.lineY(z(sx).map((o, i) => ({...o, fecha: sx[i + mejor.k]?.fecha, serie: `${dX.nombre} (desplazado)`})).filter(o => o.fecha), {x: "fecha", y: "z", stroke: "serie"})]})}
  <p class="nota">La correlación no implica causalidad. Con datos de ${dGeo}; ${dTrans.toLowerCase()}.</p>`;
}
```
''', ESPECS=J([s for s in unicos if s["frecuencia"] in ("Mensual", "Trimestral") and not s.get("sinGeo")]))

# =====================================================================================
# 13. Previsión sencilla
# =====================================================================================
pagina("prevision.qmd", r'''---
title: "Previsión sencilla"
subtitle: "Tendencia más estacionalidad: proyecta un indicador y mide cuánto se habría equivocado el modelo"
toc: false
---

El modelo descompone la serie en **tendencia** (recta ajustada a los últimos años) y **componente estacional** (lo que cada mes o trimestre suele estar por encima o por debajo de la tendencia) y la proyecta hacia delante con un **intervalo del 95 %**. Para saber si fiarse, hacemos una **prueba hacia atrás**: estimamos el modelo sin los últimos datos y comparamos su previsión con lo que realmente pasó.

__HELPERS__

__SELECTOR__

```{ojs}
//| echo: false
viewof geoPrev = Inputs.select([...new Set((await datosSel).rows.map(r => r.territorio))].sort((a, b) => a.localeCompare(b, "es")), {label: "Territorio", value: (await datosSel).rows.some(r => r.territorio === "España") ? "España" : undefined})
viewof hPrev = Inputs.range([1, 24], {label: "Periodos a prever", value: indSel.frecuencia === "Anual" ? 3 : 12, step: 1})
viewof aniosPrev = Inputs.range([3, 15], {label: "Años para estimar", value: 6, step: 1})
viewof estPrev = Inputs.toggle({label: "Incluir estacionalidad", value: indSel.frecuencia !== "Anual"})
```

```{ojs}
//| echo: false
modelo = (serie, h, P, conEst) => {
  const n = serie.length, xs = d3.range(n);
  const est = new Array(P).fill(0);
  let des = serie.map(r => r.valor);
  for (let it = 0; it < 2; it++) {
    const mx = d3.mean(xs), my = d3.mean(des);
    var b = d3.sum(xs, i => (i - mx) * (des[i] - my)) / d3.sum(xs, i => (i - mx) ** 2), a = my - b * mx;
    if (!conEst || P === 1) break;
    for (let p = 0; p < P; p++) est[p] = d3.mean(xs.filter(i => i % P === p), i => serie[i].valor - (a + b * i)) ?? 0;
    const me = d3.mean(est); for (let p = 0; p < P; p++) est[p] -= me;
    des = serie.map((r, i) => r.valor - est[i % P]);
  }
  const ajuste = xs.map(i => a + b * i + est[i % P]);
  const sd = d3.deviation(xs, i => serie[i].valor - ajuste[i]) || 0;
  const paso = P === 12 ? 1 : P === 4 ? 3 : 12;
  const prev = d3.range(1, h + 1).map(k => { const i = n - 1 + k, f = new Date(serie[n - 1].fecha); f.setMonth(f.getMonth() + paso * k); const m = a + b * i + est[i % P], w = 1.96 * sd * Math.sqrt(1 + k / n); return {fecha: f, valor: m, lo: m - w, hi: m + w}; });
  return {prev, pendiente: b, est, sd};
}
resPrev = {
  const v = (await datosSel).rows.filter(r => r.territorio === geoPrev).sort((a, b) => a.fecha - b.fecha);
  const P = indSel.frecuencia === "Mensual" ? 12 : indSel.frecuencia === "Trimestral" ? 4 : 1;
  const n = Math.min(v.length, aniosPrev * P);
  if (n < Math.max(2 * P, 4)) return null;
  const serie = v.slice(-n);
  const m = modelo(serie, hPrev, P, estPrev);
  const hb = Math.min(hPrev, Math.floor(n / 3));
  const back = modelo(v.slice(-n - hb, -hb), hb, P, estPrev);
  const reales = v.slice(-hb);
  const mae = d3.mean(reales, (r, i) => Math.abs(r.valor - back.prev[i].valor));
  const ingenuo = d3.mean(reales, r => Math.abs(r.valor - v.at(-hb - 1).valor));
  return {v, serie, m, back, reales, mae, ingenuo, P};
}
{
  if (!resPrev) return html`<p class="pending">No hay datos suficientes para este territorio.</p>`;
  const {v, m, back, reales, mae, ingenuo, P} = resPrev;
  const hist = v.slice(-Math.max(resPrev.serie.length, 3 * P));
  window.cceeEvento && window.cceeEvento(`prevision/${indSel.id}`, `Previsión: ${indSel.nombre}`, true);
  const ult = m.prev.at(-1);
  return html`${Plot.plot({height: 340, marginLeft: 55, y: {grid: true, label: indSel.unidad}, x: {label: null}, color: {legend: true, domain: ["Datos", "Previsión", "Prueba hacia atrás"], range: ["#444", "#A6195E", "#E6A400"]},
      marks: [Plot.areaY(m.prev, {x: "fecha", y1: "lo", y2: "hi", fill: "#A6195E", fillOpacity: 0.15}),
        Plot.lineY(hist, {x: "fecha", y: "valor", stroke: () => "Datos"}),
        Plot.lineY([{fecha: v.at(-1).fecha, valor: v.at(-1).valor}, ...m.prev], {x: "fecha", y: "valor", stroke: () => "Previsión", strokeWidth: 2.5}),
        Plot.lineY(back.prev, {x: "fecha", y: "valor", stroke: () => "Prueba hacia atrás", strokeDasharray: "4,3"}),
        Plot.tip(m.prev, Plot.pointerX({x: "fecha", y: "valor", title: d => `${d.fecha.toLocaleDateString("es-ES", {month: "short", year: "numeric"})}: ${fmt(d.valor)} [${fmt(d.lo)}; ${fmt(d.hi)}]`}))]})}
    <p>Previsión para ${ult.fecha.toLocaleDateString("es-ES", {month: "long", year: "numeric"})}: <b>${fmt(ult.valor)}</b> (intervalo del 95 %: ${fmt(ult.lo)} a ${fmt(ult.hi)}). Tendencia: ${m.pendiente >= 0 ? "+" : ""}${fmt(m.pendiente * (P === 1 ? 1 : P))} ${indSel.unidad} por año.</p>
    <p><b>Prueba hacia atrás</b> (últimos ${reales.length} periodos): error absoluto medio del modelo = <b>${fmt(mae)}</b>; si se hubiera supuesto que el dato no cambia, el error habría sido ${fmt(ingenuo)}. ${mae < ingenuo ? "✅ El modelo mejora la previsión ingenua." : "⚠️ El modelo no mejora la previsión ingenua: la serie depende de factores que una tendencia no recoge."}</p>
    ${estPrev && P > 1 ? html`<details><summary>Ver el componente estacional</summary>${Plot.plot({height: 180, x: {label: P === 12 ? "Mes" : "Trimestre", tickFormat: i => P === 12 ? "EFMAMJJASOND"[i] : `T${i + 1}`}, y: {label: "Diferencia con la tendencia", grid: true},
      marks: [Plot.barY(m.est.map((e, i) => ({i: (i + resPrev.serie[0].fecha.getMonth() / (12 / P)) % P, e})), {x: "i", y: "e", fill: "#2C6FBB"}), Plot.ruleY([0])]})}</details>` : ""}
    <p class="nota">Modelo docente: no tiene en cuenta cambios de ciclo ni noticias. Las previsiones oficiales (Banco de España, AIReF, Comisión Europea) usan modelos más completos.</p>`;
}
```
''', SELECTOR=selector("s => true", "pernoctaciones-en-hoteles"))

# =====================================================================================
# 14. Calculadora de desigualdad con tus datos
# =====================================================================================
pagina("desigualdad-calc.qmd", r'''---
title: "Calculadora de desigualdad"
subtitle: "Pega tus datos de renta, salarios o ventas y obtén el índice de Gini, la curva de Lorenz, el S80/S20 y los índices de Theil"
toc: false
---

Pega una lista de valores (uno por línea, o separados por espacios o punto y coma). Si cada valor tiene un **peso** (por ejemplo, el factor de elevación de una encuesta o el número de personas del hogar), escribe cada línea como `valor;peso`. Los cálculos se hacen en tu navegador: los datos no salen de tu ordenador.

__HELPERS__

```{ojs}
//| echo: false
ejemplos = ({"Salarios de una empresa (20 personas)": "1150\n1200\n1230\n1260\n1300\n1350\n1380\n1420\n1500\n1550\n1600\n1700\n1800\n1950\n2100\n2300\n2600\n3100\n4200\n7500",
  "Renta de hogares con pesos": "8500;1200\n12000;1800\n15500;2100\n19000;2300\n23500;2000\n29000;1600\n36000;1100\n48000;600\n75000;200",
  "Igualdad perfecta": "100\n100\n100\n100\n100"})
viewof ejemploSel = Inputs.select(["(mis datos)", ...Object.keys(ejemplos)], {label: "Cargar un ejemplo"})
viewof textoDatos = Inputs.textarea({label: "Datos", rows: 10, width: 420, value: ejemplos[ejemploSel] ?? "", placeholder: "1200\n1500\n2300\n…", submit: "Calcular"})
```

```{ojs}
//| echo: false
obs = textoDatos.split(/\n|\s{2,}|\t/).flatMap(l => l.includes(";") ? [l] : l.split(/\s+/)).map(l => l.trim()).filter(Boolean).map(l => {
  const [v, w] = l.split(";").map(x => +x.replace(/\./g, "").replace(",", ".").replace(/[^\d.eE+-]/g, ""));
  return {v, w: Number.isFinite(w) && w > 0 ? w : 1};
}).filter(o => Number.isFinite(o.v) && o.v >= 0).sort((a, b) => a.v - b.v)
medidas = (o) => {
  const W = d3.sum(o, x => x.w), mu = d3.sum(o, x => x.v * x.w) / W;
  let acW = 0, acY = 0, g = 0; const lor = [{p: 0, l: 0}];
  for (const x of o) { const pw = x.w / W, py = x.v * x.w / (mu * W); g += pw * (2 * acY + py); acW += pw; acY += py; lor.push({p: acW, l: acY}); }
  const gini = 1 - g;
  const cuota = (q) => { let acum = 0, tot = 0; for (const x of o) { const ini = acum / W, fin = (acum + x.w) / W; acum += x.w; const sol = Math.max(0, Math.min(fin, q[1]) - Math.max(ini, q[0])); tot += sol * W * x.v; } return tot / (mu * W); };
  const s80s20 = cuota([0.8, 1]) / cuota([0, 0.2]);
  const pos = o.filter(x => x.v > 0), Wp = d3.sum(pos, x => x.w);
  const t1 = d3.sum(pos, x => x.w / W * (x.v / mu) * Math.log(x.v / mu));
  const t0 = pos.length === o.length ? d3.sum(o, x => x.w / W * Math.log(mu / x.v)) : NaN;
  const cuantil = (q) => { let a = 0; for (const x of o) { a += x.w; if (a / W >= q) return x.v; } return o.at(-1).v; };
  return {n: o.length, W, mu, med: cuantil(0.5), gini, s80s20, t1, t0, p90p10: cuantil(0.9) / cuantil(0.1), lor, cuota};
}
res = obs.length >= 2 ? medidas(obs) : null
```

```{ojs}
//| echo: false
{
  if (!res) return html`<p class="pending">Introduce al menos dos valores y pulsa <b>Calcular</b>.</p>`;
  window.cceeEvento && window.cceeEvento("desigualdad-calc/calculo", "Calculadora de desigualdad", true);
  // Jackknife (sin pesos o con pesos, hasta 3000 observaciones): sesgo y error típico del Gini
  let jk = null;
  if (res.n >= 10 && res.n <= 3000) {
    const g = obs.map((_, i) => medidas(obs.filter((__, j) => j !== i)).gini);
    const gm = d3.mean(g), n = res.n;
    jk = {sesgo: (n - 1) * (gm - res.gini), se: Math.sqrt((n - 1) / n * d3.sum(g, x => (x - gm) ** 2))};
  }
  const k = (t, v, nota) => html`<div class="kpi"><div class="kpi-l">${t}</div><div class="kpi-n">${v}</div><div class="kpi-s">${nota}</div></div>`;
  const q = [0, .2, .4, .6, .8].map((a, i) => ({q: `Q${i + 1}`, c: 100 * res.cuota([a, a + .2])}));
  return html`<div class="kpi-grid">
    ${k("Índice de Gini", fmt(res.gini), "0 = igualdad · 1 = máxima desigualdad")}
    ${k("Ratio S80/S20", Number.isFinite(res.s80s20) ? fmt(res.s80s20) : "∞", "renta del 20 % más rico / 20 % más pobre")}
    ${k("Theil T (GE(1))", fmt(res.t1), "más sensible a la parte alta")}
    ${k("Theil L / desviación logarítmica media (GE(0))", Number.isFinite(res.t0) ? fmt(res.t0) : "–", res.t0 ? "más sensible a la parte baja" : "no se calcula con valores cero")}
    ${k("Media y mediana", `${fmt(res.mu)} · ${fmt(res.med)}`, `${res.n} observaciones${res.W !== res.n ? `, población ${fmt(res.W)}` : ""}`)}
    ${k("Ratio P90/P10", fmt(res.p90p10), "percentil 90 / percentil 10")}</div>
  ${jk ? html`<p><b>Inferencia (jackknife).</b> Error típico del Gini: ${fmt(jk.se)}; intervalo aproximado del 95 %: [${fmt(res.gini - 1.96 * jk.se)}; ${fmt(res.gini + 1.96 * jk.se)}]. Sesgo estimado: ${fmt(jk.sesgo)}; Gini corregido de sesgo: <b>${fmt(res.gini - jk.sesgo)}</b>. En muestras pequeñas, los índices de desigualdad tienen sesgo; los proyectos de investigación <a href="https://jfmunozrosas.github.io/ginius/" target="_blank">GiniUs</a> y <a href="https://jfmunozrosas.github.io/theilumina/" target="_blank">THEILUMINA</a> estudian cómo corregirlo.</p>` : ""}
  <div class="graf-2">
  ${Plot.plot({height: 340, width: 360, marginLeft: 45, x: {label: "Proporción acumulada de población", domain: [0, 1]}, y: {label: "Proporción acumulada de renta", domain: [0, 1], grid: true},
    marks: [Plot.line([[0, 0], [1, 1]], {stroke: "#999", strokeDasharray: "4,3"}), Plot.areaY(res.lor, {x: "p", y1: "l", y2: "p", fill: "#A6195E", fillOpacity: 0.15}),
      Plot.line(res.lor, {x: "p", y: "l", stroke: "#A6195E", strokeWidth: 2.5}), Plot.text([[0.62, 0.3]], {text: [`Gini = ${fmt(res.gini)}\n(2 × área sombreada)`], fill: "#A6195E"})]})}
  ${Plot.plot({height: 340, width: 320, marginLeft: 45, y: {label: "% de la renta total", grid: true}, x: {label: "Quintil"},
    marks: [Plot.barY(q, {x: "q", y: "c", fill: "#2C6FBB"}), Plot.ruleY([20], {stroke: "#A6195E", strokeDasharray: "4,3"}), Plot.text(q, {x: "q", y: "c", text: d => fmt(d.c) + " %", dy: -8})]})}
  </div>
  <p class="nota">Para comparar con los datos oficiales, consulta el <a href="desigualdad.html?i=indice-de-gini">índice de Gini</a> y el <a href="desigualdad.html?i=ratio-s80-s20">S80/S20</a> de Eurostat. Fórmulas: Gini a partir del área de la curva de Lorenz; Theil T = Σ wᵢ (yᵢ/μ) ln(yᵢ/μ); Theil L = Σ wᵢ ln(μ/yᵢ).</p>`;
}
```
''')

# =====================================================================================
# 15. Simulador de política fiscal (dinámica de la deuda)
# =====================================================================================
pagina("politica-fiscal.qmd", r'''---
title: "Simulador de política fiscal"
subtitle: "¿Hacia dónde va la deuda pública? Juega con el saldo primario, los tipos de interés y el crecimiento"
toc: false
---

La deuda pública (en % del PIB) evoluciona según la ecuación de la dinámica de la deuda:

$$d_{t+1} = d_t \cdot \frac{1 + i}{1 + g} - sp_{t+1}$$

donde *d* es la deuda, *i* el tipo de interés implícito de la deuda, *g* el crecimiento nominal del PIB y *sp* el saldo primario (ingresos menos gastos sin intereses). Si *i* > *g*, hace falta superávit primario para que la deuda no crezca (el **efecto bola de nieve**). Los valores de partida de España se cargan de Eurostat.

__HELPERS__

```{ojs}
//| echo: false
especF = __ESPECS__
partida = {
  const get = async (id) => { const s = especF.find(x => x.id === id); const d = s ? await cargar(s) : {ok: false}; if (!d.ok) return null; const v = d.rows.filter(r => r.territorio === "España").sort((a, b) => a.fecha - b.fecha); return v.at(-1); };
  const [deuda, saldo] = await Promise.all([get("deuda-publica-del-pib"), get("deficit-o-superavit-publico-del-pib")]);
  return {deuda: deuda?.valor ?? 101.8, anio: deuda ? deuda.fecha.getFullYear() : 2024, saldo: saldo?.valor ?? -3.2, ok: !!deuda};
}
viewof fD0 = Inputs.range([0, 200], {label: "Deuda inicial (% PIB)", value: Math.round(partida.deuda * 10) / 10, step: 0.1})
viewof fI = Inputs.range([0, 8], {label: "Tipo de interés implícito (%)", value: 2.3, step: 0.1})
viewof fG = Inputs.range([-4, 10], {label: "Crecimiento nominal del PIB (%)", value: 4, step: 0.1})
viewof fSP = Inputs.range([-8, 6], {label: "Saldo primario (% PIB)", value: Math.round((partida.saldo + partida.deuda * 0.023) * 10) / 10, step: 0.1})
viewof fAnios = Inputs.range([5, 40], {label: "Horizonte (años)", value: 15, step: 1})
```

**Escenario alternativo: una medida de política fiscal**

```{ojs}
//| echo: false
viewof fMedida = Inputs.range([-3, 3], {label: "Ajuste fiscal (% PIB; + = subir impuestos o recortar gasto)", value: 1, step: 0.1})
viewof fMult = Inputs.range([0, 2], {label: "Multiplicador fiscal", value: 0.8, step: 0.1})
viewof fShock = Inputs.toggle({label: "Añadir un shock: subida de 2 puntos de los tipos de interés", value: false})
```

```{ojs}
//| echo: false
{
  const sim = (medida, shock) => {
    const out = [{t: partida.anio, d: fD0}]; let d = fD0;
    for (let k = 1; k <= fAnios; k++) {
      const g = (fG - (k === 1 ? fMult * medida : 0)) / 100; // el ajuste resta crecimiento el primer año
      const i = (fI + (shock ? Math.min(2, 2 * k / 5) : 0)) / 100; // la subida de tipos se traslada poco a poco a la deuda
      d = d * (1 + i) / (1 + g) - (fSP + medida);
      out.push({t: partida.anio + k, d});
    }
    return out;
  };
  const base = sim(0, false).map(o => ({...o, esc: "Escenario base"}));
  const alt = sim(fMedida, fShock).map(o => ({...o, esc: "Con la medida" + (fShock ? " y el shock de tipos" : "")}));
  const spEst = fD0 * (fI - fG) / (100 + fG);
  window.cceeEvento && window.cceeEvento("politica-fiscal/simulacion", "Simulador de política fiscal", false);
  return html`${partida.ok ? html`<p class="nota">Datos de partida de Eurostat: deuda de España en ${partida.anio}: ${fmt(partida.deuda)} % del PIB; saldo público: ${fmt(partida.saldo)} % del PIB. El saldo primario inicial se aproxima sumando unos intereses de ${fmt(partida.deuda * 0.023)} % del PIB.</p>` : ""}
  <div class="kpi-grid">
    <div class="kpi"><div class="kpi-l">Deuda en ${partida.anio + fAnios} (base)</div><div class="kpi-n">${fmt(base.at(-1).d)} %</div></div>
    <div class="kpi"><div class="kpi-l">Deuda en ${partida.anio + fAnios} (con la medida)</div><div class="kpi-n">${fmt(alt.at(-1).d)} %</div></div>
    <div class="kpi"><div class="kpi-l">Saldo primario que estabiliza la deuda</div><div class="kpi-n">${fmt(spEst)} %</div><div class="kpi-s">${fI > fG ? "i > g: efecto bola de nieve" : "i < g: el crecimiento reduce la deuda"}</div></div></div>
  ${Plot.plot({height: 340, marginLeft: 50, x: {label: null, tickFormat: d => String(d)}, y: {label: "Deuda pública (% del PIB)", grid: true, zero: true},
    color: {legend: true, range: ["#2C6FBB", "#A6195E"]},
    marks: [Plot.ruleY([60], {stroke: "#E6A400", strokeDasharray: "5,4"}), Plot.text([[partida.anio + 0.5, 63]], {text: ["Referencia del 60 % (Pacto de Estabilidad)"], textAnchor: "start", fill: "#A07000", fontSize: 10}),
      Plot.lineY([...base, ...alt], {x: "t", y: "d", stroke: "esc", strokeWidth: 2.5}), Plot.tip([...base, ...alt], Plot.pointerX({x: "t", y: "d", stroke: "esc", title: o => `${o.esc}, ${o.t}: ${fmt(o.d)} %`}))]})}
  <p class="nota">Simplificación docente: supone que el tipo de interés, el crecimiento y el saldo primario son constantes; el ajuste fiscal solo resta crecimiento el primer año (multiplicador × ajuste). Para el análisis oficial, consulta los informes de la AIReF.</p>`;
}
```
''', ESPECS=J([porid[i] for i in ("deuda-publica-del-pib", "deficit-o-superavit-publico-del-pib")]))

# =====================================================================================
# 17. Modo presentación
# =====================================================================================
pagina("presentacion.qmd", r'''---
title: "Modo presentación"
subtitle: "Gráficos grandes y legibles para proyectar en clase, con pantalla completa y paso de un indicador a otro"
toc: false
---

Elige una lista de indicadores y los territorios. Pulsa **Pantalla completa** y usa las flechas **← →** del teclado (o los botones) para pasar de un gráfico a otro. Pulsa **Esc** para salir.

__HELPERS__

```{ojs}
//| echo: false
especP = __ESPECS__
areasP = (__AREAS__)
viewof listaP = Inputs.select(new Map(especP.map(s => [`${s.nombre} (${areasP[s.pagina] ?? s.pagina})`, s])), {label: "Indicadores (Ctrl o ⌘ para varios)", multiple: true, size: 8,
  value: ["ipca-inflacion-general-tasa-anual", "tasa-de-paro", "pib-crecimiento-interanual-trimestral", "deuda-publica-del-pib"].map(i => especP.find(s => s.id === i))})
viewof terrsP = Inputs.select([...new Set(Object.values(nombresGeo))], {label: "Territorios", multiple: true, size: 6, value: ["España", "UE-27", "Andalucía"]})
viewof desdeP = Inputs.range([2000, new Date().getFullYear() - 1], {label: "Desde", value: 2015, step: 1})
```

```{ojs}
//| echo: false
{
  const lista = listaP.length ? listaP : especP.slice(0, 1);
  let k = 0;
  const marco = html`<div class="presentacion"><div class="pres-cab"><span class="pres-num"></span><div class="pres-botones">
    <button class="copiar pres-ant">←</button><button class="copiar pres-sig">→</button><button class="copiar pres-full">⛶ Pantalla completa</button></div></div>
    <h2 class="pres-titulo"></h2><p class="pres-sub"></p><div class="pres-graf"></div><p class="pres-fuente"></p></div>`;
  const q = (s) => marco.querySelector(s);
  const pintar = async () => {
    const s = lista[k];
    q(".pres-num").textContent = `${k + 1} / ${lista.length}`;
    q(".pres-titulo").textContent = s.nombre; q(".pres-sub").textContent = s.unidad;
    q(".pres-graf").innerHTML = `<p class="pending">Cargando…</p>`;
    const d = await cargar(s);
    if (!d.ok) { q(".pres-graf").innerHTML = `<p class="pending">No se han podido cargar los datos.</p>`; return; }
    let rows = d.rows.filter(r => r.fecha.getFullYear() >= desdeP && (s.sinGeo || terrsP.includes(r.territorio)));
    if (!rows.length) rows = d.rows.filter(r => r.fecha.getFullYear() >= desdeP && (r.territorio === "España" || s.sinGeo));
    const full = document.fullscreenElement === marco;
    const ancho = full ? window.innerWidth - 80 : (marco.clientWidth || 900) - 20;
    const ult = d3.rollups(rows, v => v.sort((a, b) => a.fecha - b.fecha).at(-1), r => r.territorio).map(([, r]) => r);
    q(".pres-graf").replaceChildren(Plot.plot({width: ancho, height: full ? window.innerHeight - 260 : 460, marginLeft: 70, marginRight: 140, style: {fontSize: "18px"},
      x: {label: null}, y: {grid: true, label: null}, color: {domain: [...new Set(rows.map(r => r.territorio))], range: ["#A6195E", "#2C6FBB", "#E6A400", "#4C9A2A", "#7A4FA0", "#D35400", "#555"]},
      marks: [Plot.ruleY([0], {stroke: "#ccc"}), Plot.lineY(rows, {x: "fecha", y: "valor", stroke: "territorio", strokeWidth: 3.5}),
        Plot.dot(ult, {x: "fecha", y: "valor", fill: "territorio", r: 6}), Plot.text(ult, {x: "fecha", y: "valor", text: r => `${r.territorio}: ${fmt(r.valor)}`, dx: 10, textAnchor: "start", fill: "territorio", fontSize: 17, fontWeight: 700}),
        Plot.tip(rows, Plot.pointerX({x: "fecha", y: "valor", stroke: "territorio", title: r => `${r.territorio}, ${r.periodo}: ${fmt(r.valor)}`}))]}));
    q(".pres-fuente").textContent = `Fuente: Eurostat (${d.code}). Último dato: ${d3.max(rows, r => r.periodo)}. CCEEscopio · FCCEE · Universidad de Granada`;
  };
  const mover = (p) => { k = (k + p + lista.length) % lista.length; pintar(); };
  q(".pres-ant").onclick = () => mover(-1); q(".pres-sig").onclick = () => mover(1);
  q(".pres-full").onclick = () => { if (document.fullscreenElement) document.exitFullscreen(); else marco.requestFullscreen?.().then(() => pintar()); };
  const tecla = (e) => { if (!marco.isConnected) return document.removeEventListener("keydown", tecla); if (e.key === "ArrowRight") mover(1); if (e.key === "ArrowLeft") mover(-1); };
  document.addEventListener("keydown", tecla);
  marco.addEventListener("fullscreenchange", () => pintar());
  invalidation.then(() => document.removeEventListener("keydown", tecla));
  window.cceeEvento && window.cceeEvento("presentacion/abrir", "Modo presentación", false);
  setTimeout(pintar, 0);
  return marco;
}
```
''', ESPECS=J(unicos), AREAS=J(AREAS))

# =====================================================================================
# Generador de exámenes de Técnicas Cuantitativas III (GMIM)
# =====================================================================================
MOTOR = "\n".join("  " + l for l in open("tools/tc3_motor.js", encoding="utf-8").read().splitlines() if not l.startswith("if (typeof module"))
CSS_TC3 = ("body{font-family:Calibri,Arial,sans-serif;font-size:11pt;max-width:800px;margin:auto;color:#111} .tc3-titulo{font-weight:bold;text-align:center;font-size:12pt} "
           ".tc3-sub{text-align:center;font-size:9pt;color:#555} .tc3-nombre{width:100%;border:0;margin:6px 0} .tc3-nombre td{border:0;padding:4px 0 18px;text-align:left} "
           "table{border-collapse:collapse;margin:6px auto} td,th{border:1px solid #888;padding:2px 8px;text-align:center} .tc3-preg{margin:12px 0;break-inside:avoid} "
           ".tc3-ap li{margin:3px 0} .tc3-sol{background:#F3F7FB;border-left:3px solid #2C6FBB;padding:4px 10px;margin:6px 0 14px} .tc3-res{font-weight:bold;color:#A6195E} "
           ".tc3-centro{text-align:center} .tc3-tema{color:#666;font-size:9pt} .tc3-euf{border-top:2px solid #A6195E;margin-top:16px;padding-top:4px} "
           ".tc3-titulo-euf{font-weight:bold;color:#A6195E} .tc3-meta{font-size:10pt} .tc3-pie{font-size:8pt;color:#777;margin-top:16px}")
pagina("examen-tc3.qmd", r'''---
title: "Generador de exámenes de Técnicas Cuantitativas III"
subtitle: "Grado en Marketing e Investigación de Mercados · Exámenes aleatorios con soluciones, en el formato de la asignatura"
toc: false
---

Genera un examen escrito de **Técnicas Cuantitativas III** con el formato y el formulario de la asignatura (nivel de confianza del 95 %, *z* = 2). Cada vez que pulses **Generar** cambian los temas, los enunciados y los datos. Reglas:

- Como máximo **un problema por tema**. Si hay más de una pregunta, **una es de decisión** (tema 8, 9 o 10) y el resto de **muestreo** (temas 1 a 6). El tema 7 no se incluye.
- Cada apartado lleva su **puntuación**, y la suma es la puntuación máxima elegida.
- Los enunciados son de **economía, empresa y marketing**. Una de las preguntas usa **datos reales de Eurostat** de los indicadores de CCEEscopio (compras por internet, población de las comunidades autónomas o crecimiento del PIB).
- Con **Evaluación Única Final**, se añade una pregunta adicional de un tema distinto, con su propia puntuación, dificultad y duración, y la misma fecha.

Se descargan dos ficheros: el **examen** y el **examen con las soluciones**.

__HELPERS__

```{ojs}
//| echo: false
motorTC3 = {
__MOTOR__
  return crearMotorTC3();
}
especTC3 = __ESPECS__
```

```{ojs}
//| echo: false
viewof tcConv = Inputs.radio(["Ordinaria", "Extraordinaria", "Especial"], {label: "Convocatoria", value: "Ordinaria"})
viewof tcDif = Inputs.radio(["Baja", "Media", "Alta"], {label: "Dificultad", value: "Media"})
viewof tcN = Inputs.range([1, 7], {label: "Número de preguntas", value: 5, step: 1})
viewof tcPuntos = Inputs.range([1, 10], {label: "Puntuación máxima", value: 10, step: 0.5})
viewof tcTiempo = Inputs.number([10, 300], {label: "Duración (minutos)", value: 120, step: 5})
viewof tcFecha = Inputs.date({label: "Fecha del examen", value: new Date()})
viewof tcEUF = Inputs.toggle({label: "Incluir pregunta de Evaluación Única Final", value: false})
```

```{ojs}
//| echo: false
viewof tcEufDif = Inputs.radio(["Baja", "Media", "Alta"], {label: "EUF · dificultad", value: "Media", disabled: !tcEUF})
viewof tcEufPuntos = Inputs.range([0.5, 10], {label: "EUF · puntuación", value: 2, step: 0.5, disabled: !tcEUF})
viewof tcEufTiempo = Inputs.number([5, 180], {label: "EUF · duración (minutos)", value: 30, step: 5, disabled: !tcEUF})
viewof tcCodigo = Inputs.text({label: "Código (opcional)", placeholder: "para repetir un examen ya generado", width: 260})
viewof tcGenerar = Inputs.button("🎲 Generar examen", {value: 0, reduce: v => v + 1})
```

```{ojs}
//| echo: false
// Datos de Eurostat para las preguntas con indicadores (si fallan, el examen se genera sin ellos)
indicadoresTC3 = {
  const porId = (id) => especTC3.find(s => s.id === id);
  const ult = (rows, t) => rows.filter(r => r.territorio === t).sort((a, b) => a.fecha - b.fecha).at(-1);
  const out = {};
  const [c, p, g] = await Promise.all(["personas-que-compran-por-internet", "poblacion-por-regiones", "pib-crecimiento-interanual-trimestral"].map(i => porId(i) ? cargar(porId(i)).catch(() => ({ok: false})) : {ok: false}));
  if (c.ok) { const u = ult(c.rows, "España"); if (u) out.compras = {valor: u.valor, periodo: u.periodo, nombre: "Personas que compran por internet",
    texto: "de las personas de 16 a 74 años compró bienes o servicios por internet en los últimos 12 meses", accion: "han comprado alguna vez por internet"}; }
  if (p.ok) {
    const ccaa = Object.entries(nombresGeo).filter(([k]) => /^ES\d\d$/.test(k) && !["ES63", "ES64"].includes(k)).map(([, v]) => v);
    const pob = ccaa.map(t => [t, ult(p.rows, t)]).filter(([, r]) => r);
    if (pob.length >= 3) out.poblacionTodas = pob.map(([t, r]) => ({t, v: r.valor, per: r.periodo}));
  }
  if (g.ok) {
    const v = g.rows.filter(r => r.territorio === "España").sort((a, b) => a.fecha - b.fecha).slice(-40);
    if (v.length >= 20) out.pib = {cuentas: [v.filter(r => r.valor < 1).length, v.filter(r => r.valor >= 1 && r.valor <= 3).length, v.filter(r => r.valor > 3).length],
      desde: v[0].periodo.replace("Q", "T"), hasta: v.at(-1).periodo.replace("Q", "T")};
  }
  return out;
}
```

```{ojs}
//| echo: false
examenTC3 = {
  if (!tcGenerar) return null;
  const semilla = /^\d+$/.test(tcCodigo.trim()) ? +tcCodigo.trim() : Math.floor(Math.random() * 1e9);
  // tres comunidades distintas en cada examen (elegidas con la misma semilla)
  let ind = {...indicadoresTC3};
  if (ind.poblacionTodas) {
    let s = semilla; const az = () => (s = (s * 1103515245 + 12345) % 2147483648) / 2147483648;
    const tres = ind.poblacionTodas.map(x => [az(), x]).sort((a, b) => a[0] - b[0]).slice(0, 3).map(x => x[1]);
    const tot = tres.reduce((a, x) => a + x.v, 0);
    ind.poblacion = {regiones: tres.map(x => x.t), pob: tres.map(x => x.v), periodo: tres[0].per, pesos: tres.map(x => Math.round(10000 * x.v / tot) / 10000)};
    ind.poblacion.pesos[2] = Math.round(10000 * (1 - ind.poblacion.pesos[0] - ind.poblacion.pesos[1])) / 10000;
  }
  const hay = ind.compras || ind.poblacion || ind.pib;
  const op = {convocatoria: tcConv, dificultad: tcDif, nPreg: tcN, puntos: tcPuntos, tiempo: tcTiempo, fecha: tcFecha ?? new Date(),
    euf: tcEUF ? {dificultad: tcEufDif, puntos: tcEufPuntos, tiempo: tcEufTiempo} : null, semilla};
  const ex = motorTC3.generarExamen(op, hay ? ind : null);
  window.cceeEvento && window.cceeEvento(`examen-tc3/${tcConv.toLowerCase()}`, "Generador de exámenes TC3", true);
  return {ex, op, hay, examen: motorTC3.htmlExamen(ex, op, false), solucion: motorTC3.htmlExamen(ex, op, true)};
}
```

```{ojs}
//| echo: false
{
  if (!examenTC3) return html`<p class="pending">Elige las opciones y pulsa <b>Generar examen</b>.</p>`;
  const {ex, op, hay, examen, solucion} = examenTC3;
  const css = __CSS__;
  const f = op.fecha instanceof Date ? op.fecha : new Date(op.fecha);
  const base = `TC3_${op.convocatoria}_${f.getFullYear()}-${String(f.getMonth() + 1).padStart(2, "0")}-${String(f.getDate()).padStart(2, "0")}`;
  const doc = (h) => `<html><head><meta charset="utf-8"><title>${base}</title><style>${css}</style></head><body>${h}</body></html>`;
  const word = (h, nombre, txt) => DOM.download(() => new Blob(["﻿" + doc(h)], {type: "application/msword"}), nombre, txt);
  const pdf = (h, txt) => { const b = html`<button class="copiar">${txt}</button>`; b.onclick = () => { const w = window.open("", "_blank"); if (!w) return alert("Permite las ventanas emergentes para imprimir."); w.document.write(doc(h)); w.document.close(); w.focus(); setTimeout(() => w.print(), 400); }; return b; };
  const vista = html`<div class="tc3-vista">`; vista.innerHTML = examen;
  const vistaSol = html`<div class="tc3-vista">`; vistaSol.innerHTML = solucion;
  return html`<p>Temas: ${ex.preguntas.map((q, i) => `${i + 1}) tema ${q.tema}`).join(" · ")}${ex.euf ? ` · EUF) tema ${ex.euf.tema}` : ""}. Código del examen: <b>${ex.semilla}</b> (escríbelo en «Código» para volver a generar este mismo examen).${hay ? "" : html`<br><span class="pending">No se han podido cargar los datos de Eurostat: el examen se ha generado sin la pregunta con indicadores.</span>`}</p>
    <div class="graf-botones no-print">
      ${word(examen, base + "_examen.doc", "⬇ Examen (Word)")}
      ${word(solucion, base + "_soluciones.doc", "⬇ Examen con soluciones (Word)")}
      ${pdf(examen, "🖨 Examen en PDF")}
      ${pdf(solucion, "🖨 Soluciones en PDF")}
    </div>
    ${vista}
    <details><summary><b>Ver el examen con las soluciones</b></summary>${vistaSol}</details>`;
}
```

::: {.callout-note appearance="simple"}
**Antes de usar el examen**, revísalo: los datos se generan al azar y algún enunciado puede necesitar retoques. El documento de Word se puede editar con Word o LibreOffice. Para el PDF, elige «Guardar como PDF» en la ventana de impresión. Las soluciones siguen el formulario de los apuntes de la asignatura.
:::
''', MOTOR=MOTOR, ESPECS=J([porid[i] for i in ("personas-que-compran-por-internet", "poblacion-por-regiones", "pib-crecimiento-interanual-trimestral")]), CSS=J(CSS_TC3))

# =====================================================================================
# Buscador de noticias con indicadores (las noticias las actualiza cada día .github/workflows/noticias.yml)
# =====================================================================================
pagina("noticias.qmd", r'''---
title: "Noticias e indicadores"
subtitle: "Noticias económicas de los últimos días y los indicadores de CCEEscopio con los que puedes comprobarlas"
toc: false
---

Dos veces al día se recogen noticias económicas de medios españoles, y se guardan las de los últimos 30 días. Las noticias no muestran los datos: **tu reto es buscar en CCEEscopio los indicadores relacionados** y comprobar qué dicen. Con el **modo reto**, ni siquiera te decimos qué indicador buscar: tienes que descubrirlo tú.

```{ojs}
//| echo: false
areasN = (__AREAS__)
datosN = {
  const h = location.hostname, seg = location.pathname.split("/").filter(Boolean)[0];
  const urls = [];
  if (h.endsWith("github.io") && seg) urls.push(`https://raw.githubusercontent.com/${h.split(".")[0]}/${seg}/noticias/noticias.json`);
  urls.push("noticias.json");
  for (const u of urls) { try { const r = await fetch(u, {cache: "no-store"}); if (r.ok) return await r.json(); } catch (e) {} }
  return null;
}
viewof textoN = Inputs.search(datosN?.noticias ?? [], {placeholder: "Busca en los titulares: paro, vivienda, turismo…", columns: ["t", "fuente"], label: "Buscar"})
viewof areaN = Inputs.select(new Map([["Todas", "todas"], ...Object.entries(areasN).map(([k, v]) => [v, k])]), {label: "Área"})
viewof diasN = Inputs.select(new Map([["Últimos 3 días", 3], ["Última semana", 7], ["Últimas 2 semanas", 14], ["Último mes", 31]]), {label: "Periodo", value: 14})
viewof retoN = Inputs.toggle({label: "Modo reto (ocultar los indicadores)", value: false})
```

```{ojs}
//| echo: false
{
  if (!datosN) return html`<div class="pending"><p>Todavía no hay noticias disponibles: no se ha generado el fichero de noticias.</p>
    <p><small><b>Para quien administra la web:</b> en GitHub, abre el repositorio, pestaña <b>Actions</b> → «Noticias de CCEEscopio» → <b>Run workflow</b>. Si falla al publicar, en <b>Settings → Actions → General → Workflow permissions</b> marca <b>Read and write permissions</b> y vuelve a lanzarla.</small></p></div>`;
  const ind = datosN.indicadores;
  const desde = Date.now() / 1000 - diasN * 86400;
  const lista = textoN.filter(n => (!n.ts || n.ts >= desde) && (areaN === "todas" || n.ind.some(i => ind[i]?.pagina === areaN))).slice(0, 120);
  const hash = (s) => [...s].reduce((h, c) => Math.imul(h ^ c.charCodeAt(0), 16777619) >>> 0, 2166136261);
  const pregunta = (n) => {
    const i = n.ind[0], x = ind[i], nom = `«${x.nombre}»`;
    if (x.regional) return `¿Qué posición ocupa Andalucía entre las comunidades autónomas en ${nom}? ¿Está por encima o por debajo de la media de España?`;
    if (x.sinGeo) return `Busca el último valor de ${nom}. ¿Cuánto ha cambiado en el último año? ¿Encaja con lo que cuenta la noticia?`;
    return [`Busca el último dato de ${nom} para España. ¿Ha mejorado o empeorado respecto al año anterior?`,
      `Compara el último dato de ${nom} de España con la media de la UE-27. ¿Está España por encima o por debajo?`,
      `¿Confirma el último dato de ${nom} lo que cuenta la noticia? Justifica tu respuesta con los datos.`][hash(n.t) % 3];
  };
  const fecha = (ts) => { if (!ts) return ""; const d = (Date.now() / 1000 - ts) / 86400; return d < 1 ? "hoy" : d < 2 ? "ayer" : `hace ${Math.floor(d)} días`; };
  const chips = (n) => html`<div class="not-ind">${n.ind.map(i => html`<a class="not-chip" href="${ind[i].pagina}.html?i=${i}">📊 ${ind[i].nombre}</a>`)}</div>`;
  const tarjeta = (n) => {
    const caja = html`<div class="not-tarjeta">
      <a class="not-titulo" href="${n.url}" target="_blank" rel="noopener">${n.t}</a>
      <p class="not-meta">${n.fuente}${n.ts ? ` · ${fecha(n.ts)}` : ""}</p></div>`;
    if (retoN) {
      const b = html`<button class="copiar">🔎 Ver qué indicadores buscar</button>`;
      const p = html`<p class="not-reto">🎯 <b>Reto:</b> ¿qué indicadores de CCEEscopio te ayudarían a entender esta noticia? Búscalos en el menú Indicadores antes de ver la respuesta.</p>`;
      b.onclick = () => { b.replaceWith(chips(n), html`<p class="not-reto">${pregunta(n)}</p>`); window.cceeEvento && window.cceeEvento("noticias/reto", "Noticias: reto", true); };
      caja.append(p, b);
    } else caja.append(chips(n), html`<p class="not-reto">🎯 <b>Reto:</b> ${pregunta(n)}</p>`);
    return caja;
  };
  const act = new Date(datosN.actualizado * 1000).toLocaleString("es-ES", {dateStyle: "long", timeStyle: "short"});
  return html`<p class="nota">${lista.length} noticias · actualizado el ${act}. Fuente: Google Noticias (medios españoles). Los titulares enlazan a la noticia original.</p>
    ${lista.length ? lista.map(tarjeta) : html`<p class="pending">No hay noticias con esos filtros. Prueba con un periodo más largo o con otra área.</p>`}`;
}
```
''', AREAS=J(AREAS))

# =====================================================================================
# Descomposiciones: qué componentes explican cada indicador
# =====================================================================================
pagina("descomposiciones.qmd", r'''---
title: "¿Qué explica cada indicador?"
subtitle: "Descomposición en contribuciones: inflación, crecimiento del PIB, cuenta corriente, población y turismo"
toc: true
toc-depth: 2
---

Muchos indicadores son la suma de varias partes. Esta herramienta calcula cuánto **aporta cada componente** (su **contribución**, en puntos) y señala **qué componentes explican la mayor parte** del dato y de sus cambios. Por ejemplo, si la inflación es del 3 % y la energía contribuye con 1,2 puntos, la energía explica el 40 % de la subida de precios.

__HELPERS__

```{ojs}
//| echo: false
DESC = new Map([
  ["Inflación por componentes (IPCA)", "inflacion"],
  ["Crecimiento del PIB por componentes de la demanda", "pib"],
  ["Saldo por cuenta corriente por componentes", "cc"],
  ["Crecimiento de la población: natural y migratorio", "poblacion"],
  ["Pernoctaciones hoteleras: residentes y no residentes", "turismo"]
])
viewof tipoDesc = Inputs.select(DESC, {label: "Indicador", value: "inflacion", width: 420})
viewof geoDesc = Inputs.select(new Map(geosPaises.map(g => [nombresGeo[g] ?? g, g])), {label: "Territorio", value: "ES"})
viewof desdeDesc = Inputs.range([2000, new Date().getFullYear() - 1], {label: "Desde el año", value: 2019, step: 1})
```

```{ojs}
//| echo: false
viewof vistaInf = tipoDesc === "inflacion"
  ? Inputs.radio(new Map([["Componentes principales (4)", "main"], ["Grupos de gasto ECOICOP (13)", "div"]]), {label: "Componentes", value: "main"})
  : Object.assign(html`<span></span>`, {value: "main"})
```

```{ojs}
//| echo: false
COMP_INF = ({
  main: [["FOOD", "Alimentos, bebidas y tabaco", "#E6A400"], ["NRG", "Energía", "#C0392B"], ["IGD_NNRG", "Bienes industriales no energéticos", "#2C6FBB"], ["SERV", "Servicios", "#4C9A2A"]],
  div: [["CP01", "Alimentos y bebidas no alcohólicas", "#E6A400"], ["CP02", "Bebidas alcohólicas y tabaco", "#B07D00"], ["CP03", "Vestido y calzado", "#9467BD"],
    ["CP04", "Vivienda, agua, electricidad y gas", "#C0392B"], ["CP05", "Muebles y artículos del hogar", "#8C564B"], ["CP06", "Sanidad", "#17BECF"],
    ["CP07", "Transporte", "#2C6FBB"], ["CP08", "Información y comunicación", "#7F7F7F"], ["CP09", "Ocio, deporte y cultura", "#E377C2"],
    ["CP10", "Educación", "#BCBD22"], ["CP11", "Restaurantes y alojamiento", "#4C9A2A"], ["CP12", "Seguros y servicios financieros", "#3C3C3B"],
    ["CP13", "Cuidado personal y otros", "#A6195E"]]
})
GRUPOS_TASAS = [["TOTAL", "Inflación general", "#000000"], ["CP01", "Alimentos", "#E6A400"], ["NRG", "Energía", "#C0392B"], ["CP04", "Vivienda", "#8C564B"], ["CP07", "Transporte", "#2C6FBB"], ["SERV", "Servicios", "#4C9A2A"]]
porClave = (recs, dim) => d3.group(recs, r => r[dim])
// Intenta varias consultas y devuelve la primera que da datos
primera = async (intentos) => { for (const [code, q] of intentos) { try { const r = await eurostat(code, q); if (r.length) return {code, recs: r}; } catch (e) {} } return null; }
desde = (y) => `&sinceTimePeriod=${y}`

cargarDesc = async (tipo, g, y0, vista) => {
  if (tipo === "inflacion") {
    const comps = COMP_INF[vista];
    const codigos = [...new Set(["TOTAL", ...comps.map(c => c[0]), ...GRUPOS_TASAS.map(c => c[0])])];
    const tasas = await primera([["prc_hicp_minr", `&unit=RCH_A&geo=${g}${desde(y0)}` + codigos.map(c => `&coicop18=${c}`).join("")]]);
    if (!tasas) return {error: "No se han podido cargar las tasas de inflación de Eurostat."};
    const pesos = await primera([
      ["prc_hicp_iw", `&geo=${g}${desde(y0 - 1)}` + comps.map(c => `&coicop18=${c[0]}`).join("")],
      ...(vista === "main" ? [["prc_hicp_inw", `&geo=${g}${desde(y0 - 1)}` + comps.map(c => `&coicop=${c[0]}`).join("")]] : [])]);
    const tas = tasas.recs.map(r => ({c: r.coicop18, periodo: r.time, fecha: fecha(r.time), v: r.value})).filter(r => r.fecha);
    const total = tas.filter(r => r.c === "TOTAL").map(r => ({periodo: r.periodo, fecha: r.fecha, valor: r.v}));
    const lineas = tas.filter(r => GRUPOS_TASAS.some(x => x[0] === r.c)).map(r => ({...r, grupo: GRUPOS_TASAS.find(x => x[0] === r.c)[1]}));
    if (!pesos) return {total, lineas, comps: [], filas: [], error: "Eurostat no ha devuelto las ponderaciones del IPCA para este territorio, así que solo se muestran las tasas de cada grupo."};
    const dim = pesos.recs[0].coicop18 !== undefined ? "coicop18" : "coicop";
    const W = d3.rollup(pesos.recs, v => v[0].value, r => r[dim], r => +r.time);
    const peso = (c, y) => { const m = W.get(c); if (!m) return null; const ys = [...m.keys()].filter(a => a <= y); return m.get(ys.length ? Math.max(...ys) : Math.min(...m.keys())); };
    const filas = [];
    for (const [per, rs] of d3.group(tas, r => r.periodo)) {
      const y = rs[0].fecha.getFullYear();
      const ws = comps.map(c => peso(c[0], y)), suma = d3.sum(ws.filter(Number.isFinite));
      comps.forEach((c, i) => { const r = rs.find(x => x.c === c[0]); if (r && Number.isFinite(ws[i]) && suma) filas.push({periodo: per, fecha: r.fecha, comp: c[1], c: ws[i] / suma * r.v, tasa: r.v, peso: ws[i] / suma}); });
    }
    const faltan = comps.filter(c => !filas.some(f => f.comp === c[1])).map(c => c[1]);
    return {comps: comps.map(c => ({k: c[1], color: c[2]})), filas, total, lineas, totalLabel: "Inflación general (tasa anual, %)",
      error: faltan.length ? `Eurostat no ha devuelto datos de: ${faltan.join(", ")}; la suma de contribuciones está incompleta.` : "", unidad: "puntos porcentuales",
      fuente: `Eurostat (prc_hicp_minr y ${pesos.code})`, nota: "Contribución de cada componente = su ponderación en la cesta del IPCA × su tasa de inflación anual. Es una aproximación: la suma de las contribuciones puede diferir unas décimas de la inflación general publicada."};
  }
  if (tipo === "pib") {
    const comps = [["P31_S14_S15", "Consumo de los hogares", "#E6A400"], ["P3_S13", "Consumo de las AA. PP.", "#9467BD"], ["P51G", "Inversión (FBCF)", "#2C6FBB"], ["P52_P53", "Variación de existencias", "#BBBBBB"], ["B11", "Saldo exterior (export. − import.)", "#4C9A2A"]];
    const base = `&s_adj=SCA&geo=${g}${desde(y0 - 1)}`;
    const con = await primera([["namq_10_gdp", `&unit=CON_PPCH_SM${base}` + comps.map(c => `&na_item=${c[0]}`).join("")]]);
    const tot = await primera([["namq_10_gdp", `&unit=CLV_PCH_SM&na_item=B1GQ${base}`]]);
    if (!tot) return {error: "No se ha podido cargar el PIB de Eurostat."};
    const total = tot.recs.map(r => ({periodo: r.time, fecha: fecha(r.time), valor: r.value})).filter(r => r.fecha && r.fecha.getFullYear() >= y0);
    let filas = [], aprox = false;
    if (con) filas = con.recs.map(r => ({periodo: r.time, fecha: fecha(r.time), comp: comps.find(c => c[0] === r.na_item)[1], c: r.value}));
    else {
      // Alternativa: contribuciones aproximadas con volúmenes encadenados
      const v = await primera([["namq_10_gdp", `&unit=CLV10_MEUR${base}` + ["B1GQ", "P31_S14_S15", "P3_S13", "P51G", "P6", "P7"].map(c => `&na_item=${c}`).join("")]]);
      if (!v) return {total, comps: [], filas: [], error: "Eurostat no ha devuelto los componentes del PIB."};
      aprox = true;
      const M = d3.rollup(v.recs, a => a[0].value, r => r.na_item, r => r.time);
      const ant = (t) => { const [y, q] = t.split("-Q"); return `${+y - 1}-Q${q}`; };
      for (const t of M.get("B1GQ").keys()) {
        const t0 = ant(t), pib0 = M.get("B1GQ").get(t0); if (!pib0) continue;
        const d = (k) => (M.get(k)?.get(t) - M.get(k)?.get(t0)) / pib0 * 100;
        const vals = {P31_S14_S15: d("P31_S14_S15"), P3_S13: d("P3_S13"), P51G: d("P51G"), B11: d("P6") - d("P7")};
        vals.P52_P53 = d("B1GQ") - d3.sum(Object.values(vals));
        for (const c of comps) if (Number.isFinite(vals[c[0]])) filas.push({periodo: t, fecha: fecha(t), comp: c[1], c: vals[c[0]]});
      }
    }
    filas = filas.filter(r => r.fecha && r.fecha.getFullYear() >= y0);
    return {comps: comps.map(c => ({k: c[1], color: c[2]})), filas, total, totalLabel: "Crecimiento del PIB (tasa interanual, %)", unidad: "puntos porcentuales",
      fuente: "Eurostat (namq_10_gdp)", nota: aprox ? "Contribuciones aproximadas a partir de volúmenes encadenados (Eurostat no ha devuelto las contribuciones oficiales); la variación de existencias recoge el resto." : "Contribuciones publicadas por Eurostat: cuántos puntos aporta cada componente de la demanda al crecimiento interanual del PIB."};
  }
  if (tipo === "cc") {
    const comps = [["G", "Bienes", "#2C6FBB"], ["S", "Servicios (incluido el turismo)", "#4C9A2A"], ["IN1", "Rentas primarias", "#E6A400"], ["IN2", "Rentas secundarias", "#9467BD"]];
    const r = await primera([["bop_gdp6_q", `&stk_flow=BAL&partner=WRL_REST&unit=PC_GDP&s_adj=NSA&geo=${g}${desde(y0)}` + [...comps.map(c => c[0]), "CA"].map(c => `&bop_item=${c}`).join("")]]);
    if (!r) return {error: "No se ha podido cargar la balanza de pagos de Eurostat."};
    const filas = r.recs.filter(x => x.bop_item !== "CA").map(x => ({periodo: x.time, fecha: fecha(x.time), comp: comps.find(c => c[0] === x.bop_item)[1], c: x.value}));
    const total = r.recs.filter(x => x.bop_item === "CA").map(x => ({periodo: x.time, fecha: fecha(x.time), valor: x.value}));
    return {comps: comps.map(c => ({k: c[1], color: c[2]})), filas, total, totalLabel: "Saldo por cuenta corriente (% del PIB)", unidad: "% del PIB", fuente: "Eurostat (bop_gdp6_q)",
      nota: "El saldo por cuenta corriente es la suma de los saldos de bienes, servicios, rentas primarias (intereses, dividendos, salarios) y rentas secundarias (transferencias)."};
  }
  if (tipo === "poblacion") {
    const comps = [["NATGROWRT", "Crecimiento natural (nacimientos − defunciones)", "#2C6FBB"], ["CNMIGRATRT", "Saldo migratorio", "#E6A400"]];
    const r = await primera([["demo_gind", `&geo=${g}${desde(y0)}` + [...comps.map(c => c[0]), "GROWRT"].map(c => `&indic_de=${c}`).join("")]]);
    if (!r) return {error: "No se han podido cargar los datos de población de Eurostat."};
    const filas = r.recs.filter(x => x.indic_de !== "GROWRT").map(x => ({periodo: x.time, fecha: fecha(x.time), comp: comps.find(c => c[0] === x.indic_de)[1], c: x.value}));
    const total = r.recs.filter(x => x.indic_de === "GROWRT").map(x => ({periodo: x.time, fecha: fecha(x.time), valor: x.value}));
    return {comps: comps.map(c => ({k: c[1], color: c[2]})), filas, total, totalLabel: "Crecimiento de la población (por 1.000 habitantes)", unidad: "por 1.000 habitantes", fuente: "Eurostat (demo_gind)",
      nota: "El crecimiento de la población es la suma del crecimiento natural y del saldo migratorio (que incluye un ajuste estadístico)."};
  }
  if (tipo === "turismo") {
    const comps = [["NAT", "Residentes en el país", "#2C6FBB"], ["FOR", "No residentes (turismo extranjero)", "#E6A400"]];
    const r = await primera([["tour_occ_nim", `&unit=NR&nace_r2=I551&geo=${g}${desde(y0 - 1)}&c_resid=NAT&c_resid=FOR&c_resid=TOTAL`]]);
    if (!r) return {error: "No se han podido cargar las pernoctaciones de Eurostat."};
    const M = d3.rollup(r.recs, a => a[0].value, x => x.c_resid, x => x.time);
    const ant = (t) => { const [y, m] = t.split("-"); return `${+y - 1}-${m}`; };
    const filas = [], total = [];
    for (const t of (M.get("TOTAL") ?? new Map()).keys()) {
      const f = fecha(t); if (!f || f.getFullYear() < y0) continue;
      const t0 = ant(t), tot0 = M.get("TOTAL").get(t0); if (!tot0) continue;
      total.push({periodo: t, fecha: f, valor: 100 * (M.get("TOTAL").get(t) / tot0 - 1)});
      for (const c of comps) { const a = M.get(c[0])?.get(t), b = M.get(c[0])?.get(t0); if (Number.isFinite(a) && Number.isFinite(b)) filas.push({periodo: t, fecha: f, comp: c[1], c: 100 * (a - b) / tot0}); }
    }
    return {comps: comps.map(c => ({k: c[1], color: c[2]})), filas, total, totalLabel: "Pernoctaciones en hoteles (tasa interanual, %)", unidad: "puntos porcentuales", fuente: "Eurostat (tour_occ_nim)",
      nota: "Contribución = variación interanual de las pernoctaciones de cada grupo dividida entre el total de pernoctaciones de hace un año."};
  }
}
datosDesc = cargarDesc(tipoDesc, geoDesc, desdeDesc, vistaInf)
```

```{ojs}
//| echo: false
{
  const d = datosDesc;
  if (!d) return html``;
  if (d.error && !d.filas?.length) return html`<p class="pending">${d.error}</p>`;
  window.cceeEvento && window.cceeEvento(`descomposicion/${tipoDesc}`, `Descomposición: ${tipoDesc}`, false);
  const pers = [...new Set([...d.filas.map(r => r.periodo), ...d.total.map(r => r.periodo)])].sort();
  const paso = Math.max(1, Math.ceil(pers.length / 12));
  const ticks = pers.filter((p, i) => i % paso === 0);
  return html`<h2 id="evolucion">Evolución de las contribuciones</h2>
    <p>${geoDesc === "ES" ? "España" : nombresGeo[geoDesc]}: barras = contribución de cada componente (${d.unidad}); línea = ${d.totalLabel.toLowerCase()}.</p>
    ${Plot.plot({height: 420, marginLeft: 50, marginBottom: 50, width: Math.max(640, width),
      x: {domain: pers, ticks, label: null, tickRotate: pers.length > 24 ? -45 : 0, padding: 0.15},
      y: {grid: true, label: d.unidad},
      color: {domain: d.comps.map(c => c.k), range: d.comps.map(c => c.color), legend: true},
      marks: [Plot.barY(d.filas, {x: "periodo", y: "c", fill: "comp", title: r => `${r.periodo} · ${r.comp}: ${fmt(r.c)}${r.tasa !== undefined ? ` (tasa ${fmt(r.tasa)} %, peso ${fmt(100 * r.peso)} %)` : ""}`}),
        Plot.ruleY([0], {stroke: "#555"}),
        Plot.line(d.total.filter(r => pers.includes(r.periodo)), {x: "periodo", y: "valor", stroke: "#111", strokeWidth: 2.2}),
        Plot.dot(d.total.filter(r => pers.includes(r.periodo)), {x: "periodo", y: "valor", fill: "#111", r: pers.length > 60 ? 1.5 : 3, title: r => `${d.totalLabel}\n${r.periodo}: ${fmt(r.valor)}`})]})}
    <p class="nota">${d.nota} Fuente: ${d.fuente}.${d.error ? ` ${d.error}` : ""}</p>`;
}
```

## ¿Qué explica el último dato? {#ultimo}

```{ojs}
//| echo: false
{
  const d = datosDesc;
  if (!d?.filas?.length) return html``;
  const ult = d3.max(d.filas, r => r.periodo);
  const fs = d.filas.filter(r => r.periodo === ult).sort((a, b) => b.c - a.c);
  const tot = d.total.find(r => r.periodo === ult)?.valor ?? d3.sum(fs, r => r.c);
  const suma = d3.sum(fs, r => r.c), principal = d3.greatest(fs, r => Math.abs(r.c));
  const share = (c) => suma !== 0 ? 100 * c / suma : NaN;
  return html`<p>En <b>${ult}</b>, ${d.totalLabel.split(" (")[0].toLowerCase()}: <b>${fmt(tot)}</b>. El componente que más aporta es <b>${principal.comp}</b>, con ${fmt(principal.c)} ${d.unidad}${Number.isFinite(share(principal.c)) && Math.sign(principal.c) === Math.sign(suma) ? ` (el ${fmt(share(principal.c))} % del total)` : ""}.</p>
  ${Plot.plot({height: 40 + 34 * fs.length, marginLeft: 260, x: {grid: true, label: `Contribución (${d.unidad})`}, y: {domain: fs.map(r => r.comp), label: null},
    color: {domain: d.comps.map(c => c.k), range: d.comps.map(c => c.color)},
    marks: [Plot.barX(fs, {y: "comp", x: "c", fill: "comp"}), Plot.ruleX([0]),
      Plot.text(fs, {y: "comp", x: "c", text: r => `${fmt(r.c)}${Number.isFinite(share(r.c)) ? ` (${fmt(share(r.c))} %)` : ""}`, dx: r => r.c >= 0 ? 6 : -6, textAnchor: r => r.c >= 0 ? "start" : "end", fontSize: 11})]})}
  <p class="nota">Entre paréntesis, el porcentaje del total que explica cada componente (los componentes con signo contrario al total restan).</p>`;
}
```

## ¿Qué explica el cambio entre dos fechas? {#cambio}

```{ojs}
//| echo: false
persDesc = datosDesc?.filas?.length ? [...new Set(datosDesc.filas.map(r => r.periodo))].sort() : []
viewof perA = Inputs.select(persDesc, {label: "Desde", value: persDesc[Math.max(0, persDesc.length - 13)]})
viewof perB = Inputs.select(persDesc, {label: "Hasta", value: persDesc.at(-1)})
```

```{ojs}
//| echo: false
{
  const d = datosDesc;
  if (!d?.filas?.length || !perA || !perB) return html``;
  const tA = d.total.find(r => r.periodo === perA)?.valor, tB = d.total.find(r => r.periodo === perB)?.valor;
  const cambios = d.comps.map(c => {
    const a = d.filas.find(r => r.periodo === perA && r.comp === c.k)?.c ?? 0, b = d.filas.find(r => r.periodo === perB && r.comp === c.k)?.c ?? 0;
    return {comp: c.k, a, b, delta: b - a};
  }).sort((x, y) => Math.abs(y.delta) - Math.abs(x.delta));
  const dTot = d3.sum(cambios, c => c.delta), top = cambios[0];
  // Gráfico en cascada: del valor inicial al final, componente a componente
  let acum = d3.sum(cambios, c => c.a);
  const pasos = [{nombre: perA, y1: 0, y2: acum, tipo: "Total"}];
  for (const c of cambios) { pasos.push({nombre: c.comp, y1: acum, y2: acum + c.delta, tipo: c.delta >= 0 ? "Sube" : "Baja", delta: c.delta}); acum += c.delta; }
  pasos.push({nombre: perB, y1: 0, y2: acum, tipo: "Total"});
  const verbo = dTot >= 0 ? "aumentó" : "disminuyó";
  return html`<p>Entre <b>${perA}</b> y <b>${perB}</b>, ${d.totalLabel.split(" (")[0].toLowerCase()} ${tA !== undefined && tB !== undefined ? html`pasó de <b>${fmt(tA)}</b> a <b>${fmt(tB)}</b>` : html`${verbo}`} (suma de contribuciones: ${dTot >= 0 ? "+" : ""}${fmt(dTot)} ${d.unidad}).
    El componente que más explica el cambio es <b>${top.comp}</b> (${top.delta >= 0 ? "+" : ""}${fmt(top.delta)}${dTot !== 0 && Math.sign(top.delta) === Math.sign(dTot) ? `, el ${fmt(100 * top.delta / dTot)} % del cambio` : ""}).</p>
  ${Plot.plot({height: 380, marginBottom: 90, marginLeft: 50, x: {domain: pasos.map(p => p.nombre), label: null, tickRotate: -30}, y: {grid: true, label: d.unidad},
    color: {domain: ["Total", "Sube", "Baja"], range: ["#3C3C3B", "#C0392B", "#2C6FBB"], legend: true},
    marks: [Plot.barY(pasos, {x: "nombre", y1: "y1", y2: "y2", fill: "tipo", title: p => p.delta !== undefined ? `${p.nombre}: ${p.delta >= 0 ? "+" : ""}${fmt(p.delta)}` : `${p.nombre}: ${fmt(p.y2)}`}),
      Plot.ruleY([0]), Plot.text(pasos, {x: "nombre", y: p => Math.max(p.y1, p.y2), text: p => p.delta !== undefined ? `${p.delta >= 0 ? "+" : ""}${fmt(p.delta)}` : fmt(p.y2), dy: -8, fontSize: 11})]})}
  ${Inputs.table(cambios.map(c => ({Componente: c.comp, [perA]: c.a, [perB]: c.b, "Cambio": c.delta})), {format: {[perA]: fmt, [perB]: fmt, Cambio: fmt}, layout: "auto"})}`;
}
```

```{ojs}
//| echo: false
{
  const d = datosDesc;
  if (tipoDesc !== "inflacion" || !d?.lineas?.length) return html``;
  const lin = d.lineas.filter(r => r.fecha.getFullYear() >= desdeDesc);
  return html`<h2 id="comparar">Comparar la inflación de alimentos, energía, vivienda, transporte y servicios</h2>
  ${Plot.plot({height: 380, marginLeft: 45, y: {grid: true, label: "Tasa de inflación anual (%)"}, x: {label: null},
    color: {domain: GRUPOS_TASAS.map(g => g[1]), range: GRUPOS_TASAS.map(g => g[2]), legend: true},
    marks: [Plot.ruleY([0]), Plot.line(lin, {x: "fecha", y: "v", stroke: "grupo", strokeWidth: g => g.grupo === "Inflación general" ? 3 : 1.8}),
      Plot.tip(lin, Plot.pointer({x: "fecha", y: "v", title: r => `${r.grupo}, ${r.periodo}: ${fmt(r.v)} %`}))]})}
  <p class="nota">Tasas de variación anual del IPCA de cada grupo (ECOICOP versión 2). Vivienda incluye alquileres, agua, electricidad, gas y otros combustibles.</p>`;
}
```

## Datos {#datos}

```{ojs}
//| echo: false
{
  const d = datosDesc;
  if (!d?.filas?.length) return html``;
  const ancho = d3.rollups(d.filas, v => Object.fromEntries(v.map(r => [r.comp, Math.round(r.c * 1000) / 1000])), r => r.periodo).sort((a, b) => b[0].localeCompare(a[0]))
    .map(([p, o]) => ({Periodo: p, ...o, [d.totalLabel]: d.total.find(r => r.periodo === p)?.valor}));
  return html`${DOM.download(() => new Blob([csv(ancho)], {type: "text/csv"}), `descomposicion_${tipoDesc}_${geoDesc}.csv`, "⬇ Descargar los datos (CSV)")}
    ${Inputs.table(ancho, {rows: 12, layout: "auto"})}`;
}
```
''')
