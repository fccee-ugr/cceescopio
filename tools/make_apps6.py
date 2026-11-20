"""Genera memoria.qmd: «Memoria de datos», juego para clase con código QR.
Se muestra durante unos segundos una malla 3 × 3 con el dato de un indicador para nueve países o regiones; después
se ocultan y cada estudiante, desde su móvil, tiene que recordarlos. Cada acierto descubre una casilla; un fallo
obliga a empezar de nuevo. Gana quien antes desbloquee las nueve.
Uso: python3 tools/make_apps6.py"""
import json, re

HELPERS = open("_helpers.qmd", encoding="utf-8").read().strip()
SPECS = json.load(open("data/indicadores_specs.json", encoding="utf-8"))
AREAS = {"precios": "Precios e inflación", "empleo": "Mercado laboral", "actividad": "Actividad económica y coyuntura",
         "empresa": "Empresa, innovación y digitalización", "turismo": "Turismo", "publico": "Sector público y mercados financieros",
         "desigualdad": "Desigualdad, pobreza y condiciones de vida", "sostenibilidad": "Energía y sostenibilidad",
         "poblacion": "Población, educación y salud", "internacional": "Economía internacional y sector exterior"}
POR_AREA, vistos = {}, set()
for k, lst in SPECS.items():
    if k not in AREAS:
        continue
    for i in lst:
        if i.get("sinGeo") or i["id"] in vistos:
            continue
        vistos.add(i["id"])
        POR_AREA.setdefault(k, []).append(i)


def J(x):
    return json.dumps(x, ensure_ascii=False)


def pagina(nombre, texto, **rep):
    rep.setdefault("HELPERS", HELPERS)
    for k, v in rep.items():
        texto = texto.replace(f"__{k}__", v)
    assert not re.search(r"__[A-Z0-9]+__", texto), f"marcador sin sustituir en {nombre}"
    open(nombre, "w", encoding="utf-8").write(texto)
    print("  ", nombre)


pagina("memoria.qmd", r'''---
title: "Memoria de datos"
subtitle: "Juego para clase con código QR: memoriza la malla de datos y desbloquea las nueve casillas"
toc: false
---

__HELPERS__

```{ojs}
//| echo: false
paramsM = new URLSearchParams(location.search)
SALA = paramsM.get("sala")
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
temaEstado = (s) => `cceescopio/memoria/${s}/estado`
temaJug = (s) => `cceescopio/memoria/${s}/jugadores`
```

```{ojs}
//| echo: false
// Lógica del juego (sin dependencias del navegador, para poder probarla)
MEM = {
  // Último periodo con dato para al menos 9 territorios
  function periodoMalla(rows, validos) {
    const por = d3.group(rows.filter(r => validos.includes(r.codigo_territorio)), r => r.periodo);
    return [...por.keys()].sort().reverse().find(p => new Set(por.get(p).map(r => r.codigo_territorio)).size >= 9) ?? null;
  }
  // Nueve territorios al azar (España siempre, si se pide y tiene dato)
  function elegir(rows, periodo, validos, conEspana, azar = Math.random) {
    const datos = new Map(rows.filter(r => r.periodo === periodo && validos.includes(r.codigo_territorio)).map(r => [r.codigo_territorio, r]));
    let cods = [...datos.keys()].sort(() => azar() - 0.5);
    if (conEspana && datos.has("ES")) cods = ["ES", ...cods.filter(c => c !== "ES")];
    return cods.slice(0, 9).sort(() => azar() - 0.5).map(c => datos.get(c));
  }
  const orden = (n = 9, azar = Math.random) => Array.from({length: n}, (_, i) => i).sort(() => azar() - 0.5);
  // Una respuesta es correcta si el texto del valor coincide (dos casillas pueden mostrar el mismo valor)
  const correcta = (celdas, pedida, elegida) => celdas[elegida]?.v === celdas[pedida]?.v;
  // Opciones para «¿Qué dato tenía…?»: el correcto y tres valores distintos de la malla
  function opciones(celdas, pedida, azar = Math.random) {
    const otros = [...new Set(celdas.map(c => c.v))].filter(v => v !== celdas[pedida].v).sort(() => azar() - 0.5).slice(0, 3);
    return [celdas[pedida].v, ...otros].sort(() => azar() - 0.5);
  }
  // Ranking: primero quien ha terminado (por tiempo); después, más casillas seguidas y menos fallos
  const ordenar = (jug) => [...jug.values()].sort((a, b) => ((b.fin ? 1 : 0) - (a.fin ? 1 : 0)) || (a.fin && b.fin ? a.tiempo - b.tiempo : 0) ||
    (b.mejor - a.mejor) || (b.actual - a.actual) || (a.fallos - b.fallos) || (a.tiempo - b.tiempo) || a.alias.localeCompare(b.alias));
  const nuevaSala = () => Array.from(crypto.getRandomValues(new Uint8Array(8)), b => "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"[b % 32]).join("");
  const segundos = (ms) => `${(ms / 1000).toFixed(1).replace(".", ",")} s`;
  return {periodoMalla, elegir, orden, correcta, opciones, ordenar, nuevaSala, segundos};
}
```

```{ojs}
//| echo: false
// Bandera (países) y dibujo de la malla
bandera = (c) => {
  const iso = c === "EU27_2020" ? "eu" : c === "EL" ? "gr" : c === "UK" ? "gb" : (/^[A-Z]{2}$/.test(c) ? c.toLowerCase() : null);
  if (!iso) return null;
  const img = html`<img class="mem-bandera" alt="" loading="lazy">`;
  img.src = `https://flagcdn.com/w80/${iso}.png`;
  img.onerror = () => img.remove();
  return img;
}
dibujarMalla = (celdas, {visibles = null, destacar = null, alPulsar = null, grande = false} = {}) => {
  const g = html`<div class="mem-malla${grande ? " mem-grande" : ""}"></div>`;
  celdas.forEach((c, i) => {
    const ver = visibles === true || (visibles instanceof Set && visibles.has(i));
    const b = html`<button type="button" class="mem-celda${ver ? " mem-ver" : ""}${destacar === i ? " mem-destacada" : ""}"></button>`;
    const f = bandera(c.c);
    if (f) b.append(f);
    b.append(html`<span class="mem-nombre">${c.n}</span>`, html`<span class="mem-valor">${ver ? c.v : "?"}</span>`);
    if (alPulsar) b.onclick = () => alPulsar(i, b); else b.disabled = true;
    g.append(b);
  });
  return g;
}
```

```{ojs}
//| echo: false
// ============================ PANTALLA DEL PROFESOR ============================
INDS_M = (__INDS__)
AREAS_M = (__AREAS__)
viewof areaM = SALA ? Object.assign(html`<span></span>`, {value: null}) : Inputs.select(new Map(Object.entries(AREAS_M).map(([k, v]) => [v, k])), {label: "Área", value: "empleo"})
viewof indM = SALA ? Object.assign(html`<span></span>`, {value: null}) : Inputs.select(INDS_M[areaM], {label: "Indicador", format: i => `${i.nombre}${i.regional ? " (regiones)" : ""}`})
viewof segM = SALA ? Object.assign(html`<span></span>`, {value: null}) : Inputs.range([5, 40], {label: "Segundos para memorizar", value: 15, step: 1})
viewof modoM = SALA ? Object.assign(html`<span></span>`, {value: null}) : Inputs.radio(new Map([["¿Dónde estaba este dato? (se toca la casilla)", "donde"], ["¿Qué dato tenía este territorio? (se elige entre cuatro)", "cual"]]), {label: "Tipo de pregunta", value: "donde"})
viewof espanaM = SALA ? Object.assign(html`<span></span>`, {value: null}) : Inputs.toggle({label: "Incluir siempre España", value: true})
viewof abrirM = SALA ? Object.assign(html`<span></span>`, {value: 0}) : Inputs.button("▶ Abrir el juego", {value: 0, reduce: v => v + 1})
```

```{ojs}
//| echo: false
{
  if (SALA) return html``;
  if (!abrirM) return html`<div class="conc-intro">
    <p><b>Cómo funciona:</b> elige un indicador y pulsa «Abrir el juego». Proyecta esta pantalla; los estudiantes escanean el código QR con el móvil y escriben un <b>alias</b>. Al pulsar «Empezar» aparece durante unos segundos una <b>malla de 3 × 3</b> con el último dato del indicador en nueve países (o comunidades autónomas) elegidos al azar. Después los datos se ocultan y el móvil va haciendo preguntas sobre la malla: cada acierto <b>descubre una casilla</b>; un fallo enseña la respuesta correcta y obliga a <b>empezar de nuevo</b>. Gana quien antes desbloquee las nueve.</p>
    <p>Es una buena excusa para comentar después los datos: ¿qué país estaba arriba?, ¿por qué?, ¿os ha sorprendido algún valor?</p>
    <p class="nota">Los resultados viajan por un servicio público de mensajería en tiempo real y no se guardan en ningún sitio. Antes de usarlo en clase por primera vez, haz una prueba con tu móvil.</p></div>`;
  // Los ajustes se leen al pulsar el botón: cambiarlos después no reinicia el juego abierto
  const spec = (viewof indM).value, seg = (viewof segM).value, modo = (viewof modoM).value, conEspana = (viewof espanaM).value;
  const caja = html`<div class="conc-panel"><p class="pending">Descargando los datos de ${spec.nombre}…</p></div>`;
  (async () => {
    const r = await cargar(spec);
    const validos = (spec.regional ? geosRegiones.filter(c => /^ES\d\d$/.test(c)) : geosPaises.filter(c => /^[A-Z]{2}$/.test(c) || c === "EU27_2020"));
    const periodo = r.ok ? MEM.periodoMalla(r.rows, validos) : null;
    if (!periodo) { caja.innerHTML = `<p class="pending">❌ No hay datos suficientes de este indicador para nueve territorios. Elige otro y vuelve a pulsar «Abrir el juego».</p>`; return; }
    const sel = MEM.elegir(r.rows, periodo, validos, conEspana);
    const celdas = sel.map(d => ({c: d.codigo_territorio, n: d.territorio, v: fmt(d.valor)}));
    const info = {ind: spec.nombre, u: spec.unidad, p: periodo, seg, modo, celdas, fuente: `Eurostat (${r.code})`};
    caja.innerHTML = `<p class="pending">Conectando con el servicio de mensajería…</p>`;
    let cli = null, broker = null;
    for (const b of BROKERS) { try { cli = await conectarBroker(b); broker = b; break; } catch (e) {} }
    if (!cli) { caja.innerHTML = `<p class="pending">❌ No se ha podido conectar con ningún servicio de mensajería. Es posible que la red bloquee estas conexiones: prueba con otra red (por ejemplo, los datos del móvil compartidos).</p>`; return; }
    const sala = MEM.nuevaSala();
    const publicar = (estado) => cli.publish(temaEstado(sala), JSON.stringify({...info, ...estado}), {retain: true, qos: 1});
    publicar({fase: "espera"});
    const jug = new Map();
    let fase = "espera", reloj = null;
    cli.subscribe(temaJug(sala), {qos: 1});
    const enlace = `${location.href.split("?")[0].split("#")[0]}?sala=${sala}&b=${broker.id}`;
    caja.innerHTML = "";
    caja.append(html`<div class="conc-cab"><div class="conc-qr"></div><div><p class="asis-et">Escanea el código o entra en</p><p class="conc-url">${enlace.replace(/^https?:\/\//, "")}</p>
        <p class="conc-cuenta">0 participantes</p>
        <div class="graf-botones"><button class="asis-boton mem-empezar">▶ Empezar</button><button class="copiar mem-terminar" disabled>🏁 Terminar</button><button class="copiar conc-full">⛶ Pantalla completa</button></div></div></div>
      <div class="mem-titulo"><b>${spec.nombre}</b> · ${spec.unidad} · ${periodo}</div>
      <div class="mem-zona"></div><div class="conc-ranking"></div>`);
    const $ = (s) => caja.querySelector(s);
    try { const qrlib = await require("qrcode-generator@1.4.4"); const qr = qrlib(0, "M"); qr.addData(enlace); qr.make(); $(".conc-qr").innerHTML = qr.createSvgTag({cellSize: 6, margin: 2, scalable: true}); } catch (e) { $(".conc-qr").textContent = "(no se ha podido crear el QR)"; }
    const zona = (contenido) => { $(".mem-zona").innerHTML = ""; $(".mem-zona").append(contenido); };
    zona(dibujarMalla(celdas, {visibles: false, grande: true}));
    const pintar = () => {
      const r = MEM.ordenar(jug);
      $(".conc-cuenta").textContent = `${jug.size} participante${jug.size === 1 ? "" : "s"}`;
      if (fase === "espera") { $(".conc-ranking").innerHTML = `<div class="conc-alias">${r.map(j => `<span>${j.alias}</span>`).join("")}</div>`; return; }
      if (fase === "memoriza") { $(".conc-ranking").innerHTML = ""; return; }
      const ganador = r.find(j => j.fin);
      const medalla = (i, j) => j.fin ? (["🥇", "🥈", "🥉"][i] ?? "✔") : `${i + 1}.`;
      $(".conc-ranking").innerHTML = `${ganador ? `<h2 class="conc-podio">🏆 ${ganador.alias} ha desbloqueado los 9 datos</h2>` : ""}<table class="uso-tabla conc-tabla"><tr><th></th><th>Alias</th><th>Casillas</th><th>Mejor racha</th><th>Fallos</th><th>Tiempo</th></tr>` +
        r.slice(0, 15).map((j, i) => `<tr class="${j.fin && i < 3 ? "conc-top" : ""}"><td>${medalla(i, j)}</td><td>${j.alias}</td><td><span class="mem-barra"><span style="width:${100 * (j.fin ? 9 : j.actual) / 9}%"></span></span> ${j.fin ? 9 : j.actual} / 9</td><td>${j.mejor}</td><td>${j.fallos}</td><td>${j.tiempo ? MEM.segundos(j.tiempo) : "–"}</td></tr>`).join("") + "</table>";
    };
    cli.on("message", (t, m) => { try { const d = JSON.parse(m.toString()); if (!d.id || !d.alias) return; const prev = jug.get(d.id) ?? {actual: 0, mejor: 0, fallos: 0, tiempo: 0};
      jug.set(d.id, {...prev, ...d, actual: Math.min(9, Math.max(0, +d.actual || 0)), mejor: Math.min(9, Math.max(0, +d.mejor || 0)), fallos: Math.max(0, +d.fallos || 0), alias: String(d.alias).slice(0, 20).replace(/[<>&"]/g, "")}); pintar(); } catch (e) {} });
    $(".mem-empezar").onclick = () => {
      fase = "memoriza"; const inicio = Date.now();
      publicar({fase: "memoriza", inicio});
      $(".mem-empezar").disabled = true; pintar();
      zona(html`<div><p class="mem-cuenta">⏱ <span>${seg}</span> s</p>${dibujarMalla(celdas, {visibles: true, grande: true})}</div>`);
      reloj = setInterval(() => {
        const quedan = Math.max(0, seg - Math.floor((Date.now() - inicio) / 1000));
        const s = $(".mem-cuenta span"); if (s) s.textContent = quedan;
        if (quedan > 0) return;
        clearInterval(reloj); fase = "juego"; publicar({fase: "juego", inicio});
        $(".mem-terminar").disabled = false;
        zona(dibujarMalla(celdas, {visibles: false, grande: true})); pintar();
      }, 250);
      window.cceeEvento && window.cceeEvento("memoria/empezar", "Memoria de datos", true);
    };
    $(".mem-terminar").onclick = () => {
      fase = "fin"; publicar({fase: "fin", ranking: MEM.ordenar(jug).slice(0, 10).map(j => ({alias: j.alias, fin: !!j.fin, tiempo: j.tiempo}))});
      $(".mem-terminar").disabled = true; pintar();
      zona(html`<div>${dibujarMalla(celdas, {visibles: true, grande: true})}<p class="source">Fuente: ${info.fuente}. Último periodo con dato para los nueve territorios: ${periodo}.</p></div>`);
      caja.append(DOM.download(() => new Blob([csv(MEM.ordenar(jug).map((j, i) => ({puesto: i + 1, alias: j.alias, terminado: j.fin ? "sí" : "no", casillas: j.fin ? 9 : j.actual, mejor_racha: j.mejor, fallos: j.fallos, tiempo_segundos: Math.round(j.tiempo / 100) / 10})))], {type: "text/csv"}), `memoria_${sala}.csv`, "⬇ Descargar los resultados (CSV)"));
    };
    $(".conc-full").onclick = () => document.fullscreenElement ? document.exitFullscreen() : caja.requestFullscreen?.();
    invalidation.then(() => { clearInterval(reloj); try { cli.end(true); } catch (e) {} });
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
  const broker = BROKERS.find(b => b.id === paramsM.get("b")) ?? BROKERS[0];
  const caja = html`<div class="conc-movil"><p class="pending">Conectando con el juego…</p></div>`;
  (async () => {
    let cli;
    try { cli = await conectarBroker(broker); } catch (e) { caja.innerHTML = `<p class="pending">❌ No se ha podido conectar. Comprueba la conexión a internet (si estás en la wifi de la universidad, prueba con los datos del móvil) y recarga la página.</p>`; return; }
    let id; try { id = localStorage.getItem(`ccee-mem-${SALA}`) || crypto.randomUUID(); localStorage.setItem(`ccee-mem-${SALA}`, id); } catch (e) { id = crypto.randomUUID(); }
    let alias = ""; try { alias = localStorage.getItem("ccee-conc-alias") || ""; } catch (e) {}
    let estado = null, unido = false, reloj = null;
    // Partida: orden de las preguntas, casillas descubiertas, racha actual y mejor racha
    let orden = [], k = 0, vistas = new Set(), mejor = 0, fallos = 0, fin = false, t0 = null, bloqueado = false;
    const enviar = () => cli.publish(temaJug(SALA), JSON.stringify({id, alias, actual: vistas.size, mejor, fallos, fin, tiempo: t0 ? Date.now() - t0 : 0}), {qos: 1});
    const reiniciar = () => { orden = MEM.orden(9); k = 0; vistas = new Set(); };
    const pantalla = () => {
      clearInterval(reloj);
      caja.innerHTML = "";
      if (!unido) {
        const f = html`<form class="asis-caja"><label class="asis-et">Tu alias para el ranking</label><input type="text" name="alias" required maxlength="20" autocomplete="off" placeholder="p. ej. Analista_7"><button class="asis-boton">Entrar al juego</button><p class="asis-nota">No escribas tu nombre real si no quieres que aparezca en la pantalla de clase.</p></form>`;
        f.alias.value = alias;
        f.onsubmit = (e) => { e.preventDefault(); alias = f.alias.value.trim().slice(0, 20).replace(/[<>&"]/g, ""); if (!alias) return; try { localStorage.setItem("ccee-conc-alias", alias); } catch (err) {} unido = true; enviar(); pantalla(); };
        caja.append(f); return;
      }
      if (!estado || estado.fase === "espera") { caja.append(html`<div class="asis-caja conc-espera"><p class="juego-grande">⏳</p><p>Hola, <b>${alias}</b>. Espera a que el profesor empiece el juego…</p>${estado ? html`<p class="asis-nota">Indicador: <b>${estado.ind}</b> (${estado.u})</p>` : ""}</div>`); return; }
      const C = estado.celdas;
      const cab = html`<p class="mem-movil-cab"><b>${estado.ind}</b><br><span>${estado.u} · ${estado.p}</span></p>`;
      if (estado.fase === "memoriza") {
        const quedan = () => Math.max(0, estado.seg - Math.floor((Date.now() - estado.inicio) / 1000));
        const c = html`<p class="mem-cuenta">⏱ <span>${quedan()}</span> s · ¡Memoriza!</p>`;
        caja.append(cab, c, dibujarMalla(C, {visibles: true}));
        reloj = setInterval(() => { c.querySelector("span").textContent = quedan(); if (!quedan()) { clearInterval(reloj); estado = {...estado, fase: "juego"}; pantalla(); } }, 250);
        return;
      }
      if (estado.fase === "fin" || fin) {
        const pos = estado.ranking ? estado.ranking.findIndex(r => r.alias === alias) : -1;
        caja.append(cab, html`<div class="asis-caja conc-espera"><p class="juego-grande">${fin ? "🏆 9 / 9" : `${vistas.size} / 9`}</p>
          <p>${fin ? html`¡Has desbloqueado los nueve datos en <b>${MEM.segundos(tFin)}</b> con ${fallos} fallo${fallos === 1 ? "" : "s"}!` : html`Mejor racha: <b>${mejor}</b> · Fallos: ${fallos}`}</p>
          ${estado.fase === "fin" && pos >= 0 ? html`<p>Puesto <b>${pos + 1}</b> ${["🥇", "🥈", "🥉"][pos] ?? ""}</p>` : html`<p class="asis-nota">Mira el ranking en la pantalla de clase.</p>`}</div>`,
          dibujarMalla(C, {visibles: true}));
        return;
      }
      // Fase de juego
      if (!t0) { t0 = Date.now(); reiniciar(); }
      const pedida = orden[k];
      const aviso = html`<div class="mem-aviso"></div>`;
      const marcador = html`<p class="juego-ind">Casillas: <b>${vistas.size}</b> / 9 · Mejor racha: ${mejor} · Fallos: ${fallos}</p>`;
      const resolver = (ok, elegida) => {
        if (bloqueado) return;
        bloqueado = true;
        if (ok) {
          vistas.add(pedida); k++; mejor = Math.max(mejor, vistas.size);
          if (vistas.size === 9) { fin = true; tFin = Date.now() - t0; }
          enviar();
          aviso.innerHTML = `<p class="mem-ok">✔ ¡Bien!</p>`;
          setTimeout(() => { bloqueado = false; pantalla(); }, 450);
        } else {
          fallos++; enviar();
          aviso.innerHTML = `<p class="mem-ko">✘ Era <b>${C[pedida].v}</b> en <b>${C[pedida].n}</b>. ¡Empiezas de nuevo!</p>`;
          caja.querySelector(".mem-malla")?.replaceWith(dibujarMalla(C, {visibles: new Set([...vistas, pedida]), destacar: pedida}));
          setTimeout(() => { bloqueado = false; reiniciar(); enviar(); pantalla(); }, 2200);
        }
      };
      if (estado.modo === "cual") {
        const ops = MEM.opciones(C, pedida);
        const botones = html`<div class="mem-opciones">${ops.map(v => { const b = html`<button type="button" class="asis-boton">${v}</button>`; b.onclick = () => resolver(v === C[pedida].v, null); return b; })}</div>`;
        caja.append(cab, marcador, html`<p class="mem-pregunta">¿Qué dato tenía <b>${C[pedida].n}</b>?</p>`, botones, aviso, dibujarMalla(C, {visibles: vistas, destacar: pedida}));
      } else {
        caja.append(cab, marcador, html`<p class="mem-pregunta">¿Dónde estaba <b class="mem-dato">${C[pedida].v}</b>?</p>`, aviso,
          dibujarMalla(C, {visibles: vistas, alPulsar: (i) => { if (vistas.has(i)) return; resolver(MEM.correcta(C, pedida, i), i); }}));
      }
    };
    let tFin = 0;
    cli.subscribe(temaEstado(SALA), {qos: 1});
    cli.on("message", (t, m) => { try { const d = JSON.parse(m.toString()); const antes = estado?.fase; estado = d; if (antes !== d.fase) pantalla(); } catch (e) {} });
    invalidation.then(() => { clearInterval(reloj); try { cli.end(true); } catch (e) {} });
    pantalla();
  })();
  return caja;
}
```
''', INDS=J(POR_AREA), AREAS=J(AREAS))
