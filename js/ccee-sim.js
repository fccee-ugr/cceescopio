/* =====================================================================
   CCEEscopio · utilidades para los simuladores, la bolsa y la portada
   (JavaScript sin dependencias; los gráficos usan d3, que cargan las páginas que los necesitan)
   ===================================================================== */
(function () {
  "use strict";
  const C = {};
  const MG = "#B5175F", OR = "#F29200", DK = "#3C3C3B";
  C.colores = {mg: MG, or: OR, dk: DK, azul: "#2C6FBB", verde: "#2E8B57", gris: "#8A8A8A", rojo: "#C62828"};

  /* ---------- formato en español ---------- */
  C.num = (v, dec = 1) => v == null || !Number.isFinite(v) ? "—" :
    v.toLocaleString("es-ES", {minimumFractionDigits: dec, maximumFractionDigits: dec});
  C.pct = (v, dec = 1, signo = false) => v == null || !Number.isFinite(v) ? "—" : (signo && v > 0 ? "+" : "") + C.num(v, dec) + " %";
  C.eur = (v, dec = 0) => C.num(v, dec) + " €";
  C.fecha = (d, opt = {day: "numeric", month: "long", year: "numeric"}) => new Date(d).toLocaleDateString("es-ES", opt);
  C.esc = (s) => String(s ?? "").replace(/[&<>"']/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
  C.evento = (ruta, titulo) => { try { window.cceeEvento && window.cceeEvento(ruta, titulo, true); } catch (e) {} };
  C.dia = (n) => new Date(n * 86400000);  // días desde el 1-1-1970 -> fecha

  /* ---------- ficheros de datos que publican las acciones de GitHub en ramas propias ---------- */
  // En github.io se leen directamente de la rama (siempre al día, sin volver a generar la web);
  // si no, del fichero con el mismo nombre junto a la página.
  C.rama = async function (rama, fichero) {
    const h = location.hostname, seg = location.pathname.split("/").filter(Boolean)[0];
    const urls = [];
    if (h.endsWith("github.io") && seg) urls.push(`https://raw.githubusercontent.com/${h.split(".")[0]}/${seg}/${rama}/${fichero}`);
    urls.push(fichero);
    for (const u of urls) {
      try { const r = await fetch(u, {cache: "no-store"}); if (r.ok) return await r.json(); } catch (e) {}
    }
    return null;
  };

  /* ---------- Eurostat (JSON-stat 2.0) ---------- */
  C.eurostat = async function (code, query = "", timeout = 15000) {
    const url = `https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/${code}?format=JSON&lang=EN${query}`;
    const ctl = new AbortController(); const tm = setTimeout(() => ctl.abort(), timeout);
    try {
      const res = await fetch(url, {signal: ctl.signal});
      if (!res.ok) throw new Error(`Eurostat ${code}: HTTP ${res.status}`);
      const js = await res.json();
      const ids = js.id, size = js.size, dims = js.dimension, vals = js.value, out = [];
      const codes = ids.map(d => { const idx = dims[d].category.index; return Array.isArray(idx) ? idx : Object.keys(idx).sort((a, b) => idx[a] - idx[b]); });
      const keys = Array.isArray(vals) ? vals.map((v, i) => i).filter(i => vals[i] != null) : Object.keys(vals).map(Number);
      for (const i of keys) {
        let rem = i; const rec = {};
        for (let d = ids.length - 1; d >= 0; d--) { rec[ids[d]] = codes[d][rem % size[d]]; rem = Math.floor(rem / size[d]); }
        rec.value = +vals[i]; out.push(rec);
      }
      return out;
    } finally { clearTimeout(tm); }
  };
  // Serie de un único territorio ordenada en el tiempo: [{t: "2025-10", v: 2.1}, ...]
  C.serie = async function (code, query) {
    const r = await C.eurostat(code, query);
    return r.filter(x => Number.isFinite(x.value)).map(x => ({t: x.time, v: x.value})).sort((a, b) => a.t < b.t ? -1 : 1);
  };
  // Prueba varias consultas [código, consulta] y devuelve la primera serie con datos (Eurostat renueva a veces sus tablas)
  C.primera = async function (intentos) {
    for (const [code, q] of intentos) { try { const r = await C.serie(code, q); if (r.length) return Object.assign(r, {code}); } catch (e) {} }
    return null;
  };
  C.fechaPeriodo = function (t) {
    let m;
    if ((m = /^(\d{4})-(\d{2})$/.exec(t)) || (m = /^(\d{4})M(\d{2})$/.exec(t))) return new Date(+m[1], +m[2] - 1, 1);
    if ((m = /^(\d{4})-?Q(\d)$/.exec(t))) return new Date(+m[1], (+m[2] - 1) * 3, 1);
    if ((m = /^(\d{4})$/.exec(t))) return new Date(+m[1], 0, 1);
    return null;
  };
  C.periodoTexto = function (t) {
    const d = C.fechaPeriodo(t); if (!d) return t;
    if (/Q/.test(t)) return `${t.slice(-1)}.º trimestre de ${d.getFullYear()}`;
    if (/^\d{4}$/.test(t)) return t;
    return d.toLocaleDateString("es-ES", {month: "long", year: "numeric"});
  };

  /* ---------- CSV ---------- */
  C.csv = function (filas, nombre) {
    if (!filas.length) return;
    const cols = Object.keys(filas[0]);
    const q = v => { const s = v instanceof Date ? v.toISOString().slice(0, 10) : String(v ?? ""); return /[;"\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s; };
    const txt = "﻿" + [cols.join(";"), ...filas.map(f => cols.map(c => q(typeof f[c] === "number" ? String(f[c]).replace(".", ",") : f[c])).join(";"))].join("\n");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([txt], {type: "text/csv;charset=utf-8"}));
    a.download = nombre; document.body.appendChild(a); a.click(); a.remove();
  };

  /* ---------- minigráfico (SVG sin dependencias) ---------- */
  C.spark = function (vals, {w = 110, h = 30, color} = {}) {
    const v = (vals || []).filter(Number.isFinite); if (v.length < 2) return "";
    const lo = Math.min(...v), hi = Math.max(...v), k = hi > lo ? (h - 4) / (hi - lo) : 0;
    const col = color || (v.at(-1) >= v[0] ? C.colores.verde : C.colores.rojo);
    const pts = v.map((y, i) => `${(i / (v.length - 1) * (w - 2) + 1).toFixed(1)},${(h - 2 - (y - lo) * k).toFixed(1)}`).join(" ");
    return `<svg class="spark" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" aria-hidden="true"><polyline fill="none" stroke="${col}" stroke-width="1.8" stroke-linejoin="round" points="${pts}"/></svg>`;
  };

  /* ---------- gráfico de líneas con d3 (con etiqueta al pasar el ratón) ----------
     series: [{nombre, color, puntos: [{x: Date|número, y}], discontinua, ancho}]
     opciones: {alto, yEtiqueta, xTipo: "tiempo"|"lineal", yFormato, xFormato, refs: [{y, texto, color}], bandas: [{x0, x1, texto}], cero} */
  let localeES = false;
  const tiempoOLineal = (o) => (o.xTipo || "tiempo") === "tiempo";
  C.lineas = function (cont, series, o = {}) {
    const d3 = window.d3; cont.innerHTML = "";
    if (!d3) { cont.textContent = "No se ha podido cargar la librería de gráficos."; return; }
    if (!localeES) {  // fechas y números de los ejes en español
      localeES = true;
      d3.timeFormatDefaultLocale({dateTime: "%A, %e de %B de %Y, %X", date: "%d/%m/%Y", time: "%H:%M:%S", periods: ["", ""],
        days: ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado"], shortDays: ["dom", "lun", "mar", "mié", "jue", "vie", "sáb"],
        months: ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
        shortMonths: ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]});
      d3.formatDefaultLocale({decimal: ",", thousands: ".", grouping: [3], currency: ["", " €"]});
    }
    const W = Math.max(300, cont.clientWidth || 640), H = o.alto || 320;
    const m = {t: 16, r: tiempoOLineal(o) ? 18 : 30, b: 34, l: 58};
    const todos = series.flatMap(s => s.puntos.filter(p => p.y != null && Number.isFinite(p.y)));
    if (!todos.length) { cont.innerHTML = `<p class="pending">Sin datos para el gráfico.</p>`; return; }
    const tiempo = (o.xTipo || "tiempo") === "tiempo";
    const x = (tiempo ? d3.scaleUtc() : d3.scaleLinear()).domain(o.xDominio || d3.extent(todos, p => p.x)).range([m.l, W - m.r]);
    let [y0, y1] = d3.extent([...todos.map(p => p.y), ...(o.refs || []).map(r => r.y), ...(o.cero ? [0] : [])]);
    if (y0 === y1) { y0 -= 1; y1 += 1; }
    const y = d3.scaleLinear().domain([y0, y1]).nice().range([H - m.b, m.t]);
    const svg = d3.select(cont).append("svg").attr("viewBox", `0 0 ${W} ${H}`).attr("width", "100%").attr("class", "ccee-graf").attr("role", "img")
      .attr("aria-label", o.titulo || series.map(s => s.nombre).join(", "));
    (o.bandas || []).forEach(b => {
      svg.append("rect").attr("x", x(b.x0)).attr("width", Math.max(1, x(b.x1) - x(b.x0))).attr("y", m.t).attr("height", H - m.b - m.t).attr("fill", b.color || "#F6EEF2");
      if (b.texto) svg.append("text").attr("x", x(b.x0) + 4).attr("y", m.t + 12).attr("font-size", 11).attr("fill", "#8a5a70").text(b.texto);
    });
    const yf = o.yFormato || (v => C.num(v, Math.abs(y1 - y0) < 10 ? 1 : 0));
    svg.append("g").attr("transform", `translate(0,${H - m.b})`).call(tiempo ? d3.axisBottom(x).ticks(Math.min(8, W / 90)) : d3.axisBottom(x).ticks(Math.min(10, W / 70)).tickFormat(o.xFormato || (v => v)))
      .call(g => g.selectAll("text").attr("font-size", 11));
    svg.append("g").attr("transform", `translate(${m.l},0)`).call(d3.axisLeft(y).ticks(6).tickFormat(yf).tickSize(-(W - m.l - m.r)))
      .call(g => g.select(".domain").remove()).call(g => g.selectAll(".tick line").attr("stroke", "#e9e3e0"))
      .call(g => g.selectAll("text").attr("font-size", 11));
    if (o.yEtiqueta) svg.append("text").attr("x", 4).attr("y", 11).attr("font-size", 11).attr("fill", "#666").text(o.yEtiqueta);
    (o.refs || []).forEach(r => {
      svg.append("line").attr("x1", m.l).attr("x2", W - m.r).attr("y1", y(r.y)).attr("y2", y(r.y)).attr("stroke", r.color || "#E6A400").attr("stroke-dasharray", "5,4");
      if (r.texto) svg.append("text").attr("x", W - m.r - 4).attr("y", y(r.y) - 4).attr("text-anchor", "end").attr("font-size", 11).attr("fill", r.color || "#A07000").text(r.texto);
    });
    const linea = d3.line().defined(p => p.y != null && Number.isFinite(p.y)).x(p => x(p.x)).y(p => y(p.y));
    series.forEach(s => {
      svg.append("path").datum(s.puntos).attr("fill", "none").attr("stroke", s.color || MG).attr("stroke-width", s.ancho || 2.4)
        .attr("stroke-dasharray", s.discontinua ? "6,4" : null).attr("stroke-linejoin", "round").attr("d", linea);
      if (s.puntosVisibles) svg.append("g").selectAll("circle").data(s.puntos.filter(p => Number.isFinite(p.y))).join("circle")
        .attr("cx", p => x(p.x)).attr("cy", p => y(p.y)).attr("r", 3.5).attr("fill", s.color || MG);
    });
    // leyenda
    if (series.length > 1 && o.leyenda !== false) {
      const ley = document.createElement("div"); ley.className = "ccee-leyenda";
      ley.innerHTML = series.map(s => `<span><i style="background:${s.color}${s.discontinua ? ";opacity:.6" : ""}"></i>${C.esc(s.nombre)}</span>`).join("");
      cont.prepend(ley);
    }
    // etiqueta al pasar el ratón
    const tip = document.createElement("div"); tip.className = "ccee-tip"; tip.hidden = true; cont.style.position = "relative"; cont.appendChild(tip);
    const guia = svg.append("line").attr("y1", m.t).attr("y2", H - m.b).attr("stroke", "#999").attr("stroke-dasharray", "3,3").style("display", "none");
    const xs = [...new Set(todos.map(p => +p.x))].sort((a, b) => a - b);
    const xfmt = o.xTexto || (tiempo ? (v => new Date(v).toLocaleDateString("es-ES", {day: "numeric", month: "short", year: "numeric"})) : (v => v));
    svg.append("rect").attr("x", m.l).attr("y", m.t).attr("width", W - m.l - m.r).attr("height", H - m.t - m.b).attr("fill", "transparent")
      .on("pointermove", (ev) => {
        const [px] = d3.pointer(ev); const xv = +x.invert(px);
        const k = d3.bisectCenter(xs, xv); const xx = xs[k];
        guia.style("display", null).attr("x1", x(xx)).attr("x2", x(xx));
        const filas = series.map(s => { const p = s.puntos.find(q => +q.x === xx); return p && Number.isFinite(p.y) ? `<div><i style="background:${s.color}"></i>${C.esc(s.nombre)}: <b>${yf(p.y)}${o.ySufijo || ""}</b></div>` : ""; }).join("");
        tip.innerHTML = `<div class="ccee-tip-t">${xfmt(xx)}</div>${filas}`; tip.hidden = false;
        const r = cont.getBoundingClientRect(), sx = r.width / W;
        let left = x(xx) * sx + 12; if (left + tip.offsetWidth > r.width) left = x(xx) * sx - tip.offsetWidth - 12;
        tip.style.left = Math.max(0, left) + "px"; tip.style.top = (m.t * sx + 6) + "px";
      })
      .on("pointerleave", () => { tip.hidden = true; guia.style("display", "none"); });
  };

  /* ---------- controles ---------- */
  // Deslizador con su valor a la vista. Devuelve el elemento; su valor está en el.valor.
  C.deslizador = function ({etiqueta, min, max, paso = 1, valor, formato = (v => C.num(v, paso < 1 ? (paso < 0.1 ? 2 : 1) : 0)), alCambiar, ayuda}) {
    const el = document.createElement("label"); el.className = "sim-slider";
    el.innerHTML = `<span class="sim-slider-l">${etiqueta}</span><span class="sim-slider-row"><input type="range" min="${min}" max="${max}" step="${paso}" value="${valor}"><output></output></span>${ayuda ? `<small>${ayuda}</small>` : ""}`;
    const inp = el.querySelector("input"), out = el.querySelector("output");
    const pon = () => { el.valor = +inp.value; out.textContent = formato(+inp.value); };
    inp.addEventListener("input", () => { pon(); alCambiar && alCambiar(el.valor); });
    el.fijar = (v) => { inp.value = v; pon(); };
    pon(); return el;
  };

  // Generador pseudoaleatorio reproducible (para repetir una partida con la misma semilla)
  C.azar = function (semilla) {
    let s = (semilla >>> 0) || 1;
    const f = () => { s ^= s << 13; s >>>= 0; s ^= s >>> 17; s ^= s << 5; s >>>= 0; return s / 4294967296; };
    f.normal = () => { let u = 0, v = 0; while (!u) u = f(); while (!v) v = f(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); };
    f.elige = (a) => a[Math.floor(f() * a.length)];
    return f;
  };

  // Guardar el mejor resultado de cada simulador en este navegador (sin datos personales)
  C.record = function (clave, puntos) {
    try {
      const k = "ccee-record-" + clave, ant = +localStorage.getItem(k) || null;
      if (puntos != null && (ant == null || puntos > ant)) { localStorage.setItem(k, puntos); return {nuevo: true, record: puntos, anterior: ant}; }
      return {nuevo: false, record: ant};
    } catch (e) { return {nuevo: false, record: null}; }
  };

  window.CCEE = C;
})();
