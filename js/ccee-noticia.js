/* =====================================================================
   CCEEscopio · «Crea tu noticia»
   Bajo cada gráfica: el estudiante escribe un titular sobre lo que muestra y el «Periódico CCEEscopio»
   publica el suyo, generado a partir de los datos. Se puntúa el parecido por elementos (tema, territorio,
   dirección, cifra, periodo y contexto) y, en modo clase, se ordena a todos los participantes.
   No guarda nada fuera de la página: el ranking se borra al recargarla o al cambiar de gráfica.
   ===================================================================== */
(function () {
  "use strict";
  const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
  const TRIM = ["primer", "segundo", "tercer", "cuarto"];
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
  const norm = (s) => String(s ?? "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  const num = (v, d) => v.toLocaleString("es-ES", {minimumFractionDigits: d, maximumFractionDigits: d});
  const dec = (v) => Math.abs(v) >= 1000 ? 0 : Math.abs(v) >= 100 ? 0 : Math.abs(v) >= 10 ? 1 : Math.abs(v) >= 1 ? 1 : 2;
  const fmtN = (v) => {
    const a = Math.abs(v);
    if (a >= 1e9) return num(v / 1e9, 1) + " mil millones";
    if (a >= 1e6) return num(v / 1e6, a >= 1e7 ? 1 : 2) + " millones";
    return num(v, dec(v));
  };

  // ---------- periodos ----------
  function partes(p) {
    let m;
    if ((m = /^(\d{4})-?Q(\d)$/.exec(p))) return {a: +m[1], q: +m[2], tipo: "T"};
    if ((m = /^(\d{4})-?M?(\d{2})$/.exec(p))) return {a: +m[1], m: +m[2], tipo: "M"};
    if ((m = /^(\d{4})$/.exec(p))) return {a: +m[1], tipo: "A"};
    if ((m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(p))) return {a: +m[1], m: +m[2], d: +m[3], tipo: "D"};
    return {a: null, tipo: "?"};
  }
  function periodoTxt(p, conArt = true) {
    const x = partes(p);
    if (x.tipo === "M") return `${MESES[x.m - 1]} de ${x.a}`;
    if (x.tipo === "T") return `${conArt ? "el " : ""}${TRIM[x.q - 1]} trimestre de ${x.a}`;
    if (x.tipo === "D") return `${x.d} de ${MESES[x.m - 1]} de ${x.a}`;
    return String(p);
  }
  const mismoSubperiodo = (a, b) => { const x = partes(a), y = partes(b); return x.tipo === y.tipo && (x.tipo === "A" || (x.tipo === "M" && x.m === y.m) || (x.tipo === "T" && x.q === y.q)); };
  function haceUnAno(p) {
    const x = partes(p);
    if (x.tipo === "M") return `${x.a - 1}-${String(x.m).padStart(2, "0")}`;
    if (x.tipo === "T") return `${x.a - 1}-Q${x.q}`;
    if (x.tipo === "A") return String(x.a - 1);
    return null;
  }

  // ---------- tema y unidad ----------
  function temaCorto(nombre) {
    let t = String(nombre).replace(/\s*\(.*?\)\s*/g, " ").trim();
    if (t.includes(":")) t = t.split(":").slice(1).join(":").trim();
    return t.charAt(0).toUpperCase() + t.slice(1);
  }
  const esTasa = (u) => /^%|variaci|saldo/i.test(u || "");
  function conUnidad(v, unidad, corta) {
    const u = unidad || "";
    if (/^%/.test(u)) return `${fmtN(v)} %${!corta && u.length > 1 ? u.slice(1) : (/del PIB/.test(u) ? " del PIB" : "")}`;
    if (/saldo/i.test(u)) return `${fmtN(v)} puntos`;
    if (/^índice/i.test(u)) return `${fmtN(v)} puntos`;
    if (corta || !u || /^(número|personas|puntos)/i.test(u)) return fmtN(v);
    return `${fmtN(v)} (${u.charAt(0).toLowerCase() + u.slice(1)})`;
  }
  const esUE = (n) => /^(UE|Uni[oó]n Europea|Zona euro)/i.test(n);

  // ---------- análisis de los datos y titular de CCEEscopio ----------
  function analizar(o, foco) {
    const s = o.series.find(x => x.nombre === foco) || o.series[0];
    const pts = s.puntos.filter(p => Number.isFinite(p.valor)).sort((a, b) => a.fecha - b.fecha);
    if (pts.length < 2) return null;
    const u = pts.at(-1), tasa = o.modo ? o.modo === "tasa" : esTasa(o.unidad);
    let ref, cambio, refTxt;
    if (o.ventana) { ref = pts[0]; refTxt = o.ventana; }
    else if (tasa) { ref = pts.at(-2); refTxt = `frente al ${conUnidad(ref.valor, o.unidad, true)} de ${periodoTxt(ref.periodo, false)}`; }
    else {
      const pa = haceUnAno(u.periodo); ref = pts.find(p => p.periodo === pa) || pts.at(-2);
      refTxt = partes(u.periodo).tipo === "A" ? "respecto al año anterior" : "en un año";
    }
    cambio = tasa && !o.ventana ? u.valor - ref.valor : 100 * (u.valor / ref.valor - 1);
    const umbral = tasa && !o.ventana ? 0.05 : 0.3;
    const dir = Math.abs(cambio) < umbral ? 0 : Math.sign(cambio);
    // ¿máximo o mínimo desde hace años? (con datos de nivel mensuales o trimestrales, solo el mismo mes o trimestre)
    const hist = pts.slice(0, -1).filter(p => tasa || o.ventana || mismoSubperiodo(p.periodo, u.periodo));
    let record = null;
    const anoU = partes(u.periodo).a;
    if (hist.length >= 3 && anoU) {
      const mayorAnt = [...hist].reverse().find(p => p.valor >= u.valor), menorAnt = [...hist].reverse().find(p => p.valor <= u.valor);
      if (!mayorAnt) record = {tipo: "max", desde: partes(pts[0].periodo).a, serie: true};
      else if (anoU - partes(mayorAnt.periodo).a >= 2) record = {tipo: "max", desde: partes(mayorAnt.periodo).a};
      if (!record) {
        if (!menorAnt) record = {tipo: "min", desde: partes(pts[0].periodo).a, serie: true};
        else if (anoU - partes(menorAnt.periodo).a >= 2) record = {tipo: "min", desde: partes(menorAnt.periodo).a};
      }
    }
    // comparación con los demás territorios en el mismo periodo
    const otros = o.series.filter(x => x !== s).map(x => ({nombre: x.nombre, p: x.puntos.find(p => p.periodo === u.periodo)})).filter(x => x.p);
    const ue = otros.find(x => esUE(x.nombre));
    const todos = [{nombre: s.nombre, valor: u.valor}, ...otros.map(x => ({nombre: x.nombre, valor: x.p.valor}))].filter(x => !esUE(x.nombre));
    const orden = [...todos].sort((a, b) => b.valor - a.valor), puesto = orden.findIndex(x => x.nombre === s.nombre) + 1;
    return {s, u, ref, cambio, dir, tasa, refTxt, record, ue, otros, puesto, nTerr: todos.length};
  }

  function titularCCEE(o, a) {
    const tema = o.tema ? temaCorto(o.tema) : "El indicador", terr = a.s.nombre;
    const sujeto = o.ventana ? terr : `${tema} en ${terr}`;
    const per = o.ventana ? o.ventana : `en ${periodoTxt(a.u.periodo)}`;  // p. ej., «en octubre de 2025»
    let verbo;
    if (a.tasa && !o.ventana) {
      verbo = a.dir > 0 ? `sube al ${conUnidad(a.u.valor, o.unidad, true)}` : a.dir < 0 ? `baja al ${conUnidad(a.u.valor, o.unidad, true)}` : `se mantiene en el ${conUnidad(a.u.valor, o.unidad, true)}`;
    } else {
      const c = `${num(Math.abs(a.cambio), 1)} %`;
      verbo = a.dir > 0 ? `${a.cambio > 10 ? "se dispara" : "crece"} un ${c}` : a.dir < 0 ? `${a.cambio < -10 ? "se desploma" : "cae"} un ${c}` : "se mantiene estable";
      if (!o.ventana && !/^Año/.test(a.refTxt)) verbo += partes(a.u.periodo).tipo === "A" ? "" : " interanual";
    }
    let contexto = "";
    // con datos de nivel mensuales o trimestrales, el récord se refiere al mismo mes o trimestre (estacionalidad)
    const pu = partes(a.u.periodo), mismo = (!a.tasa && !o.ventana) ? (pu.tipo === "M" ? ` para un mes de ${MESES[pu.m - 1]}` : pu.tipo === "T" ? ` para un ${TRIM[pu.q - 1]} trimestre` : "") : "";
    if (a.record) contexto = (a.record.serie ? `, el ${a.record.tipo === "max" ? "más alto" : "más bajo"} de la serie` : `, su nivel más ${a.record.tipo === "max" ? "alto" : "bajo"} desde ${a.record.desde}`) + mismo;
    else if (a.ue && a.tasa) contexto = a.u.valor > a.ue.p.valor ? `, por encima de la media europea` : `, por debajo de la media europea`;
    else if (a.nTerr >= 3 && (a.puesto === 1 || a.puesto === a.nTerr)) contexto = a.puesto === 1 ? (o.ventana ? ", el mejor de los valores comparados" : ", el más alto de los territorios comparados") : (o.ventana ? ", el peor de los valores comparados" : ", el más bajo de los territorios comparados");
    const titular = `${sujeto}: ${verbo} ${per}${contexto}`;
    // entradilla
    const fr = [];
    const enP = (p) => partes(p).tipo === "D" ? `el ${periodoTxt(p)}` : `en ${periodoTxt(p)}`;
    const temaMin = tema.charAt(0).toLowerCase() + tema.slice(1);
    const valorEn = (v) => /^%/.test(o.unidad || "") ? `en el ${conUnidad(v, o.unidad, false)}` : `en ${conUnidad(v, o.unidad, false)}`;
    const masMenos = `un ${num(Math.abs(a.cambio), 1)} % ${a.cambio >= 0 ? "más" : "menos"}`;
    if (o.ventana) fr.push(`${terr} cerró en ${fmtN(a.u.valor)} ${enP(a.u.periodo)}, ${masMenos} que al inicio del periodo (${periodoTxt(a.ref.periodo)}).`);
    else if (a.tasa) fr.push(`En ${terr}, el dato de ${temaMin} se situó ${valorEn(a.u.valor)} ${enP(a.u.periodo)}, ${a.refTxt}.`);
    else fr.push(`En ${terr}, el dato de ${temaMin} alcanzó ${conUnidad(a.u.valor, o.unidad, false)} ${enP(a.u.periodo)}, ${masMenos} que ${enP(a.ref.periodo)}.`);
    if (a.record) fr.push(a.record.serie ? `Es el valor más ${a.record.tipo === "max" ? "alto" : "bajo"} de toda la serie disponible, que empieza en ${a.record.desde}.` : `No se registraba un valor tan ${a.record.tipo === "max" ? "alto" : "bajo"} desde ${a.record.desde}.`);
    if (a.ue) fr.push(`En el conjunto de la ${/zona/i.test(a.ue.nombre) ? "zona euro" : "UE"}, el dato fue ${/^%/.test(o.unidad || "") ? "del" : "de"} ${conUnidad(a.ue.p.valor, o.unidad, true)}.`);
    else if (a.nTerr >= 3) fr.push(`Ocupa el puesto ${a.puesto} de los ${a.nTerr} territorios del gráfico.`);
    fr.push(`Fuente: ${o.fuente || "Eurostat"}.`);
    return {titular: titular.replace(/\s+/g, " ").trim().replace(/^./, c => c.toUpperCase()), entradilla: fr.join(" ")};
  }

  // ---------- puntuación del titular del estudiante ----------
  const SUBE = /\b(sube|suben|subida|subir|aumenta|aumentan|aumento|crece|crecen|crecimiento|repunta|repunte|dispara|escala|alza|eleva|avanza|incrementa|incremento|record|maximo|ganancias?|gana|supera|mas alto)\b/;
  const BAJA = /\b(baja|bajan|bajada|cae|caen|caida|desciende|descenso|disminuye|disminucion|retrocede|retroceso|modera|recorta|recorte|reduce|reduccion|desploma|cede|frena|minimo|perdidas?|pierde|mas bajo|hunde)\b/;
  const ESTABLE = /\b(estable|mantiene|sin cambios|estanca|estancad[oa]|se queda|igual)\b/;
  function numeros(txt) {
    const out = [], re = /(-?\d+(?:[.,]\d+)*)\s*(mil millones|millones|millon|mil)?/g; let m;
    while ((m = re.exec(txt))) {
      let s = m[1];
      if (s.includes(",")) s = s.replace(/\./g, "").replace(",", ".");
      else if (/\.\d{3}(\D|$)/.test(s + " ")) s = s.replace(/\./g, "");
      let v = parseFloat(s); if (!Number.isFinite(v)) continue;
      const mult = m[2] === "mil millones" ? 1e9 : /^millo/.test(m[2] || "") ? 1e6 : m[2] === "mil" ? 1e3 : 1;
      out.push(v * mult);
    }
    return out;
  }
  const raiz = (w) => w.slice(0, 5);
  function puntuar(txt, o, a) {
    const t = " " + norm(txt) + " ";
    const r = [];
    // tema
    const claves = norm(temaCorto(o.tema || "")).split(/[^a-z0-9]+/).filter(w => w.length >= 4 && !["tasa", "anual", "total", "sobre", "segun"].includes(w));
    const palabrasT = t.split(/[^a-z0-9]+/).filter(Boolean).map(raiz);
    // sinónimos habituales en prensa
    const SIN = {infla: ["preci", "ipc", "ipca", "caris", "coste"], paro: ["desem", "parad"], empleo: ["traba", "ocupa", "afili"], deuda: ["endeu"],
                 perno: ["turis", "viaje", "hotel"], pib: ["econo", "creci", "activ"], expor: ["venta"], vivie: ["casas", "pisos", "inmob"]};
    const okTema = o.ventana ? true : claves.some(k => palabrasT.includes(raiz(k)) || (SIN[raiz(k)] || []).some(x => palabrasT.includes(x)));
    r.push({e: "Tema del indicador", ok: okTema, p: 15, ayuda: `${temaCorto(o.tema || "")}`});
    // territorio
    const tn = norm(a.s.nombre), alias = {espana: ["espana", "espanol", "espanola", "nacional", "pais"], "ue-27": ["ue", "union europea", "europa"]};
    const sinPar = tn.replace(/\s*\(.*?\)\s*/g, " ").trim(), dentro = (/\((.*?)\)/.exec(tn) || [])[1];
    const candidatos = [tn, sinPar, sinPar.split(" ")[0], dentro, ...(alias[tn] || [])].filter(x => x && x.length >= 2);
    const okTerr = candidatos.some(x => t.includes(" " + x) || t.includes(x + " ") || t.includes(x));
    r.push({e: "Territorio", ok: okTerr, p: 15, ayuda: a.s.nombre});
    // dirección
    const d = SUBE.test(t) && !BAJA.test(t) ? 1 : BAJA.test(t) && !SUBE.test(t) ? -1 : ESTABLE.test(t) ? 0 : null;
    r.push({e: "Dirección del cambio", ok: d !== null && d === a.dir, p: 30, ayuda: a.dir > 0 ? "sube" : a.dir < 0 ? "baja" : "se mantiene"});
    // cifra
    const objetivos = [a.u.valor, Math.abs(a.cambio)];
    const ns = numeros(t).filter(v => !(v >= 1990 && v <= 2100 && Number.isInteger(v)));
    const okNum = ns.some(v => objetivos.some(ob => Math.abs(v - ob) <= Math.max(0.15, 0.07 * Math.abs(ob))));
    r.push({e: "Cifra correcta", ok: okNum, p: 20, ayuda: `${conUnidad(a.u.valor, o.unidad, true)}${a.tasa && !o.ventana ? "" : ` o ${num(Math.abs(a.cambio), 1)} %`}`});
    // periodo
    const pu = partes(a.u.periodo);
    const okPer = o.ventana ? new RegExp(norm(o.ventana).split(" ").filter(w => w.length > 3).map(raiz).join("|")).test(t) || /ultim|semana|mes|ano/.test(t)
      : (pu.a && t.includes(String(pu.a))) || (pu.tipo === "M" && t.includes(MESES[pu.m - 1])) || (pu.tipo === "T" && t.includes(TRIM[pu.q - 1] + " trimestre"));
    r.push({e: "Periodo", ok: !!okPer, p: 10, ayuda: o.ventana || periodoTxt(a.u.periodo)});
    // contexto
    let okCtx, ayudaCtx;
    if (a.record) { okCtx = new RegExp(a.record.tipo === "max" ? "maxim|record|mas alt|desde" : "minim|mas baj|desde").test(t); ayudaCtx = a.record.serie ? `${a.record.tipo === "max" ? "máximo" : "mínimo"} de la serie` : `${a.record.tipo === "max" ? "máximo" : "mínimo"} desde ${a.record.desde}`; }
    else if (a.ue) { okCtx = /\b(ue|europ|media|zona euro)/.test(t); ayudaCtx = "comparación con la media europea"; }
    else if (a.otros.length) { okCtx = a.otros.some(x => t.includes(norm(x.nombre))) || /\b(resto|demas|otros|lider|cabeza|cola)\b/.test(t); ayudaCtx = o.ventana ? "comparación con los otros valores del gráfico" : "comparación con otros territorios"; }
    else { okCtx = true; ayudaCtx = "no aplica"; }  // sin récord ni comparación posible: el elemento no penaliza
    r.push({e: "Contexto", ok: okCtx, p: 10, ayuda: ayudaCtx});
    return {total: r.reduce((s, x) => s + (x.ok ? x.p : 0), 0), elementos: r};
  }

  // ---------- interfaz ----------
  /* opciones: {tema, unidad, fuente, seccion, series: [{nombre, puntos: [{periodo, fecha: Date, valor}]}],
                preferidos: ["España"], modo: "tasa"|"nivel" (opcional), ventana: "en el último año" (opcional, compara con el primer punto)} */
  function panel(o) {
    const raizEl = document.createElement("div"); raizEl.className = "noticia-wrap";
    const series = (o.series || []).filter(s => s.puntos && s.puntos.filter(p => Number.isFinite(p.valor)).length >= 2);
    if (!series.length) return raizEl;
    o = {...o, series};
    const nombres = series.map(s => s.nombre);
    let foco = (o.preferidos || ["España"]).find(n => nombres.includes(n)) || nombres[0];
    const participantes = [];
    raizEl.innerHTML = `<button class="noticia-btn" type="button">📰 Crea tu noticia</button><div class="noticia" hidden></div>`;
    const btn = raizEl.querySelector(".noticia-btn"), caja = raizEl.querySelector(".noticia");
    btn.onclick = () => { caja.hidden = !caja.hidden; btn.classList.toggle("on", !caja.hidden); if (!caja.hidden) escribir(); };
    const hoy = new Date().toLocaleDateString("es-ES", {weekday: "long", day: "numeric", month: "long", year: "numeric"});
    const cabecera = () => `<div class="np-cab"><div class="np-meta"><span>${hoy}</span><span>Edición digital · Facultad de CC. Económicas y Empresariales · UGR</span></div>
      <div class="np-nombre">El Periódico CCEEscopio</div><div class="np-lema">Observando la economía y la empresa</div></div>`;
    function escribir() {
      caja.innerHTML = `${cabecera()}
        <div class="np-cuerpo"><div class="np-seccion">${esc(o.seccion || "Economía")} · Redacta tu titular</div>
        <p class="np-inst">Mira la gráfica y escribe el titular que publicarías. Después, el Periódico CCEEscopio publicará el suyo con los datos y verás cuánto se parecen. Un buen titular dice <b>qué</b> indicador, <b>dónde</b>, <b>hacia dónde</b> se mueve, <b>cuánto</b>, <b>cuándo</b> y por qué es <b>noticia</b>.</p>
        ${nombres.length > 1 ? `<label class="np-campo">La noticia trata sobre <select class="np-foco">${nombres.map(n => `<option ${n === foco ? "selected" : ""}>${esc(n)}</option>`).join("")}</select></label>` : ""}
        <label class="np-campo">Seudónimo (opcional) <input class="np-nom" maxlength="30" placeholder="p. ej., Grupo 3"></label>
        <label class="np-campo np-campo-t">Tu titular <textarea class="np-tit" rows="2" maxlength="180" placeholder="Escribe aquí tu titular…"></textarea></label>
        <div class="np-botones"><button class="np-pub" type="button">🗞️ Publicar y comparar</button></div>
        ${participantes.length ? ranking() : ""}</div>`;
      const sf = caja.querySelector(".np-foco"); if (sf) sf.onchange = () => { foco = sf.value; participantes.length = 0; escribir(); };
      caja.querySelector(".np-pub").onclick = () => {
        const txt = caja.querySelector(".np-tit").value.trim();
        if (txt.length < 8) { caja.querySelector(".np-tit").focus(); caja.querySelector(".np-tit").placeholder = "Escribe un titular un poco más largo…"; return; }
        publicar(txt, caja.querySelector(".np-nom").value.trim());
      };
    }
    function publicar(txt, nom) {
      const a = analizar(o, foco); if (!a) return;
      const t = titularCCEE(o, a), p = puntuar(txt, o, a);
      participantes.push({nom: nom || `Participante ${participantes.length + 1}`, txt, puntos: p.total});
      const nota = p.total >= 85 ? "¡Titular de portada!" : p.total >= 65 ? "Muy buen titular" : p.total >= 45 ? "Buen intento" : "Revisa los datos de la gráfica";
      caja.innerHTML = `${cabecera()}
        <div class="np-cuerpo"><div class="np-seccion">${esc(o.seccion || "Economía")}</div>
        <h2 class="np-titular">${esc(t.titular)}</h2>
        <p class="np-entradilla">${esc(t.entradilla)}</p>
        <div class="np-firma">Redacción del Periódico CCEEscopio, con datos actualizados</div>
        <div class="np-tuyo"><div class="np-tuyo-l">Tu titular${nom ? ` (${esc(nom)})` : ""}</div><div class="np-tuyo-t">«${esc(txt)}»</div>
          <div class="np-punt"><span class="np-num">${p.total}</span><span>/100 · ${nota}</span></div>
          <ul class="np-elem">${p.elementos.map(e => `<li class="${e.ok ? "ok" : "no"}">${e.ok ? "✔" : "✘"} <b>${e.e}</b> <small>(${e.p} puntos${e.ok ? "" : ` · en los datos: ${esc(e.ayuda)}`})</small></li>`).join("")}</ul></div>
        ${ranking()}
        <div class="np-botones"><button class="np-otro" type="button">✍️ Otro titular (modo clase)</button>
        <button class="np-copiar" type="button">📋 Copiar el titular de CCEEscopio</button></div>
        <p class="np-nota">El titular de CCEEscopio se genera automáticamente con los últimos datos de la gráfica. La puntuación valora si tu titular recoge los mismos elementos informativos, no si está redactado igual. Nada de lo que escribes se guarda fuera de esta página.</p></div>`;
      caja.querySelector(".np-otro").onclick = escribir;
      caja.querySelector(".np-copiar").onclick = (ev) => { try { navigator.clipboard.writeText(`${t.titular}. ${t.entradilla}`); ev.target.textContent = "✅ Copiado"; } catch (e) {} };
      try { window.cceeEvento && window.cceeEvento("noticia/publicar", "Crea tu noticia", true); } catch (e) {}
    }
    function ranking() {
      if (participantes.length < 2) return "";
      const ord = [...participantes].sort((x, y) => y.puntos - x.puntos);
      return `<div class="np-rank"><div class="np-rank-t">🏆 Titulares más cercanos (${participantes.length} participantes)</div><ol>${ord.map(x => `<li><b>${esc(x.nom)}</b> · ${x.puntos} puntos<br><small>«${esc(x.txt)}»</small></li>`).join("")}</ol></div>`;
    }
    return raizEl;
  }

  window.CCEENoticia = {panel, analizar, titularCCEE, puntuar, temaCorto};
})();
