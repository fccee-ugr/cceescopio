"""Séptima tanda de recursos de CCEEscopio (noviembre de 2026):
  bingo.qmd           Bingo de indicadores (QR)
  ordena.qmd          Ordena la malla (QR)
  quien.qmd           ¿Quién es quién? (QR)
  coyuntura.qmd       Mapa de calor de coyuntura y estructura
  numeros-indice.qmd  Laboratorio de números índice
  ideas-tfg.qmd       Generador de ideas para TFG y TFM
Uso: python3 tools/make_apps7.py   (después de make_apps5.py, del que toma el módulo de precios)"""
import json, re
from ideas_tfg import TEMAS, METODOS, AMBITOS, PERIODOS, TITULACIONES

HELPERS = open("_helpers.qmd", encoding="utf-8").read().strip()
SPECS = json.load(open("data/indicadores_specs.json", encoding="utf-8"))
PRECIOS = re.search(r"```\{ojs\}\n//\| echo: false\n// Módulo de precios.*?\n```", open("precios-productos.qmd", encoding="utf-8").read(), re.S).group(0)
AREAS = {"precios": "Precios e inflación", "empleo": "Mercado laboral", "actividad": "Actividad económica y coyuntura",
         "empresa": "Empresa, innovación y digitalización", "turismo": "Turismo", "publico": "Sector público y mercados financieros",
         "desigualdad": "Desigualdad, pobreza y condiciones de vida", "sostenibilidad": "Energía y sostenibilidad",
         "poblacion": "Población, educación y salud", "internacional": "Economía internacional y sector exterior"}


def S(area, id_, **extra):
    for i in SPECS[area]:
        if i["id"] == id_:
            return {**i, "area": area, **extra}
    raise KeyError(f"{area}/{id_}")


def J(x):
    return json.dumps(x, ensure_ascii=False)


def pagina(nombre, texto, **rep):
    rep.setdefault("HELPERS", HELPERS)
    rep.setdefault("QRJ", QRJ)
    rep.setdefault("DJ", DJ)
    for k, v in rep.items():
        texto = texto.replace(f"__{k}__", v)
    assert not re.search(r"__[A-Z0-9]+__", texto), f"marcador sin sustituir en {nombre}"
    open(nombre, "w", encoding="utf-8").write(texto)
    print("  ", nombre)


# ------------------------------------------------------------------------------------------
# Conjuntos de indicadores. corto: nombre breve; uc: unidad breve; sentido: +1 mejor alto, -1 mejor bajo, "obj2": mejor cerca del 2 %
# ------------------------------------------------------------------------------------------
JUEGO_PAISES = [
    S("internacional", "pib-per-capita-en-ppc-ue-27-100", corto="PIB per cápita (UE = 100)", uc=""),
    S("empleo", "tasa-de-paro", corto="Tasa de paro", uc="%"),
    S("empleo", "tasa-de-paro-juvenil-menores-de-25-anos", corto="Paro juvenil", uc="%"),
    S("publico", "deuda-publica-del-pib", corto="Deuda pública", uc="% del PIB"),
    S("precios", "ipca-inflacion-general-tasa-anual", corto="Inflación", uc="%"),
    S("sostenibilidad", "cuota-de-energias-renovables", corto="Energías renovables", uc="%"),
    S("poblacion", "esperanza-de-vida-al-nacer", corto="Esperanza de vida", uc="años"),
    S("desigualdad", "riesgo-de-pobreza-o-exclusion-social-arope", corto="Riesgo de pobreza o exclusión", uc="%"),
    S("empresa", "gasto-en-i-d-del-pib", corto="Gasto en I+D", uc="% del PIB"),
    S("poblacion", "tasa-de-fecundidad", corto="Hijos por mujer", uc=""),
]
JUEGO_REGIONES = [
    S("empleo", "tasa-de-paro-por-regiones", corto="Tasa de paro", uc="%"),
    S("empleo", "tasa-de-empleo-por-regiones-20-64-anos", corto="Tasa de empleo", uc="%"),
    S("actividad", "pib-per-capita-en-paridad-de-poder-de-compra", corto="PIB per cápita (PPC)", uc="PPC"),
    S("empresa", "gasto-en-i-d-por-regiones-del-pib", corto="Gasto en I+D", uc="% del PIB"),
    S("desigualdad", "riesgo-de-pobreza-o-exclusion-social-por-regiones", corto="Riesgo de pobreza o exclusión", uc="%"),
    S("desigualdad", "tasa-de-riesgo-de-pobreza-por-regiones", corto="Tasa de riesgo de pobreza", uc="%"),
    S("turismo", "pernoctaciones-por-regiones", corto="Pernoctaciones", uc=""),
    S("poblacion", "poblacion-por-regiones", corto="Población", uc="habitantes"),
]
CALOR = {
    "coyuntura": dict(titulo="Coyuntura de los países de la UE", ambito="paises", ind=[
        S("actividad", "pib-crecimiento-interanual-trimestral", corto="Crecimiento del PIB", sentido=1),
        S("empleo", "tasa-de-paro", corto="Paro", sentido=-1),
        S("empleo", "tasa-de-paro-juvenil-menores-de-25-anos", corto="Paro juvenil", sentido=-1),
        S("precios", "ipca-inflacion-general-tasa-anual", corto="Inflación", sentido="obj2"),
        S("precios", "ipca-inflacion-subyacente-sin-energia-ni-alimentos", corto="Inflación subyacente", sentido="obj2"),
        S("actividad", "indicador-de-sentimiento-economico", corto="Sentimiento económico", sentido=1),
        S("actividad", "confianza-del-consumidor", corto="Confianza consumidor", sentido=1),
        S("internacional", "exportaciones-crecimiento-interanual-trimestral", corto="Exportaciones", sentido=1),
        S("internacional", "saldo-por-cuenta-corriente-del-pib", corto="Cuenta corriente", sentido=1),
        S("publico", "deficit-o-superavit-publico-del-pib", corto="Saldo público", sentido=1),
        S("publico", "deuda-publica-del-pib", corto="Deuda pública", sentido=-1),
        S("publico", "rentabilidad-del-bono-a-10-anos", corto="Bono a 10 años", sentido=-1)]),
    "estructura": dict(titulo="Estructura económica y social de los países de la UE", ambito="paises", ind=[
        S("internacional", "pib-per-capita-en-ppc-ue-27-100", corto="PIB per cápita", sentido=1),
        S("empleo", "tasa-de-empleo-20-64-anos", corto="Tasa de empleo", sentido=1),
        S("empleo", "jovenes-que-ni-estudian-ni-trabajan-15-29-anos", corto="Ni estudian ni trabajan", sentido=-1),
        S("empleo", "brecha-salarial-de-genero", corto="Brecha salarial", sentido=-1),
        S("empresa", "gasto-en-i-d-del-pib", corto="I+D", sentido=1),
        S("desigualdad", "indice-de-gini", corto="Gini", sentido=-1),
        S("desigualdad", "riesgo-de-pobreza-o-exclusion-social-arope", corto="Pobreza o exclusión", sentido=-1),
        S("poblacion", "poblacion-de-25-34-anos-con-estudios-superiores", corto="Estudios superiores", sentido=1),
        S("poblacion", "abandono-temprano-de-la-educacion-y-la-formacion", corto="Abandono escolar", sentido=-1),
        S("poblacion", "esperanza-de-vida-al-nacer", corto="Esperanza de vida", sentido=1),
        S("sostenibilidad", "cuota-de-energias-renovables", corto="Renovables", sentido=1),
        S("sostenibilidad", "emisiones-de-gases-de-efecto-invernadero-por-habitante", corto="Emisiones por hab.", sentido=-1)]),
    "regiones": dict(titulo="Comunidades autónomas", ambito="regiones", ind=[
        S("actividad", "pib-per-capita-en-paridad-de-poder-de-compra", corto="PIB per cápita", sentido=1),
        S("empleo", "tasa-de-paro-por-regiones", corto="Paro", sentido=-1),
        S("empleo", "tasa-de-empleo-por-regiones-20-64-anos", corto="Tasa de empleo", sentido=1),
        S("empresa", "gasto-en-i-d-por-regiones-del-pib", corto="I+D", sentido=1),
        S("desigualdad", "riesgo-de-pobreza-o-exclusion-social-por-regiones", corto="Pobreza o exclusión", sentido=-1),
        S("desigualdad", "tasa-de-riesgo-de-pobreza-por-regiones", corto="Riesgo de pobreza", sentido=-1)]),
}
# Indicadores para «Ordena la malla»: todos los que tienen datos por país (salvo índices de base fija) o por región
ORDENA = {"paises": {}, "regiones": []}
_vistos = set()
for area in AREAS:
    for i in SPECS[area]:
        if i.get("sinGeo") or i["unidad"].startswith("Índice (2021"):
            continue
        if i.get("regional"):
            if i["id"] not in _vistos:
                ORDENA["regiones"].append({**i, "area": area})
        else:
            ORDENA["paises"].setdefault(area, []).append({**i, "area": area})
        _vistos.add(i["id"])

# ------------------------------------------------------------------------------------------
# Bloques comunes de JavaScript
# ------------------------------------------------------------------------------------------
QRJ = r'''```{ojs}
//| echo: false
// Salas en tiempo real con código QR (servicios públicos de mensajería MQTT; no se guarda nada)
QRJ = {
  const BROKERS = [
    {id: "h", url: "wss://broker.hivemq.com:8884/mqtt"},
    {id: "e", url: "wss://broker.emqx.io:8084/mqtt"},
    {id: "m", url: "wss://test.mosquitto.org:8081/mqtt"}];
  let lib;
  async function libreria() {
    if (lib === undefined) { try { const m = await import("https://cdn.jsdelivr.net/npm/mqtt@5.10.1/dist/mqtt.esm.js"); lib = m.default ?? m; } catch (e) { lib = null; } }
    return lib;
  }
  async function conectar(b) {
    const L = await libreria();
    if (!L) throw new Error("sin librería");
    return new Promise((ok, mal) => {
      const c = L.connect(b.url, {clientId: "ccee_" + Math.random().toString(16).slice(2, 10), connectTimeout: 6000, reconnectPeriod: 2000, clean: true});
      const t = setTimeout(() => { c.end(true); mal(new Error("tiempo agotado")); }, 7000);
      c.once("connect", () => { clearTimeout(t); ok(c); });
    });
  }
  const nuevaSala = () => Array.from(crypto.getRandomValues(new Uint8Array(8)), b => "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"[b % 32]).join("");
  const segundos = (ms) => ms == null ? "–" : `${(ms / 1000).toFixed(1).replace(".", ",")} s`;
  const limpiar = (s) => String(s ?? "").slice(0, 20).replace(/[<>&"]/g, "");
  const ERR_RED = `<p class="pending">❌ No se ha podido conectar con ningún servicio de mensajería. Es posible que la red bloquee estas conexiones: prueba con otra red (por ejemplo, los datos del móvil compartidos).</p>`;
  const ERR_MOVIL = `<p class="pending">❌ No se ha podido conectar. Comprueba la conexión a internet (si estás en la wifi de la universidad, prueba con los datos del móvil) y recarga la página.</p>`;
  // Profesor: abre una sala y recibe los mensajes de los estudiantes
  async function abrirSala(prefijo) {
    let cli = null, broker = null;
    for (const b of BROKERS) { try { cli = await conectar(b); broker = b; break; } catch (e) {} }
    if (!cli) return null;
    const sala = nuevaSala(), tE = `cceescopio/${prefijo}/${sala}/estado`, tJ = `cceescopio/${prefijo}/${sala}/jugadores`;
    const enlace = `${location.href.split("?")[0].split("#")[0]}?sala=${sala}&b=${broker.id}`;
    const jug = new Map(), oyentes = [];
    cli.subscribe(tJ, {qos: 1});
    cli.on("message", (t, m) => {
      if (t !== tJ) return;
      try { const d = JSON.parse(m.toString()); if (!d.id || !d.alias) return; d.alias = limpiar(d.alias); jug.set(d.id, {...(jug.get(d.id) ?? {}), ...d}); oyentes.forEach(f => f(jug)); } catch (e) {}
    });
    return {sala, enlace, jug, publicar: (e) => cli.publish(tE, JSON.stringify(e), {retain: true, qos: 1}),
      alCambiar: (f) => oyentes.push(f), cerrar: () => { try { cli.end(true); } catch (e) {} }};
  }
  function cabecera(enlace, botones) {
    const el = html`<div class="conc-cab"><div class="conc-qr"></div><div><p class="asis-et">Escanea el código o entra en</p><p class="conc-url">${enlace.replace(/^https?:\/\//, "")}</p><p class="conc-cuenta">0 participantes</p><div class="graf-botones"></div></div></div>`;
    const full = html`<button class="copiar">⛶ Pantalla completa</button>`;
    full.onclick = () => document.fullscreenElement ? document.exitFullscreen() : el.parentElement?.requestFullscreen?.();
    el.querySelector(".graf-botones").append(...botones, full);
    (async () => { try { const q = (await require("qrcode-generator@1.4.4"))(0, "M"); q.addData(enlace); q.make(); el.querySelector(".conc-qr").innerHTML = q.createSvgTag({cellSize: 6, margin: 2, scalable: true}); } catch (e) { el.querySelector(".conc-qr").textContent = "(no se ha podido crear el QR)"; } })();
    return el;
  }
  const cuenta = (raiz, n) => { const c = raiz.querySelector(".conc-cuenta"); if (c) c.textContent = `${n} participante${n === 1 ? "" : "s"}`; };
  // Estudiante: se une a la sala del enlace
  async function unirse(prefijo, alEstado) {
    const p = new URLSearchParams(location.search), sala = p.get("sala");
    const b = BROKERS.find(x => x.id === p.get("b")) ?? BROKERS[0];
    let cli; try { cli = await conectar(b); } catch (e) { return null; }
    const tE = `cceescopio/${prefijo}/${sala}/estado`, tJ = `cceescopio/${prefijo}/${sala}/jugadores`;
    let id; try { id = localStorage.getItem(`ccee-${prefijo}-${sala}`) || crypto.randomUUID(); localStorage.setItem(`ccee-${prefijo}-${sala}`, id); } catch (e) { id = crypto.randomUUID(); }
    cli.subscribe(tE, {qos: 1});
    cli.on("message", (t, m) => { if (t !== tE) return; try { alEstado(JSON.parse(m.toString())); } catch (e) {} });
    return {sala, id, enviar: (d) => cli.publish(tJ, JSON.stringify({id, ...d}), {qos: 1}), cerrar: () => { try { cli.end(true); } catch (e) {} }};
  }
  function formAlias(alEntrar) {
    let alias = ""; try { alias = localStorage.getItem("ccee-conc-alias") || ""; } catch (e) {}
    const f = html`<form class="asis-caja"><label class="asis-et">Tu alias para el ranking</label><input type="text" name="alias" required maxlength="20" autocomplete="off" placeholder="p. ej. Analista_7"><button class="asis-boton">Entrar</button><p class="asis-nota">No escribas tu nombre real si no quieres que aparezca en la pantalla de clase.</p></form>`;
    f.alias.value = alias;
    f.onsubmit = (e) => { e.preventDefault(); const a = limpiar(f.alias.value.trim()); if (!a) return; try { localStorage.setItem("ccee-conc-alias", a); } catch (err) {} alEntrar(a); };
    return f;
  }
  const espera = (alias, extra = "") => html`<div class="asis-caja conc-espera"><p class="juego-grande">⏳</p><p>Hola, <b>${alias}</b>. Espera a que el profesor empiece…</p>${extra}</div>`;
  const medalla = (i) => ["🥇", "🥈", "🥉"][i] ?? `${i + 1}.`;
  const hash = (s) => [...s].reduce((a, ch) => (a * 31 + ch.charCodeAt(0)) >>> 0, 7);
  return {conectar, nuevaSala, segundos, limpiar, ERR_RED, ERR_MOVIL, abrirSala, cabecera, cuenta, unirse, formAlias, espera, medalla, hash};
}
```'''

DJ = r'''```{ojs}
//| echo: false
// Datos para los juegos: territorios, último periodo común, banderas
DJ = {
  const paises = geosPaises.filter(c => /^[A-Z]{2}$/.test(c));
  const regiones = geosRegiones.filter(c => /^ES\d\d$/.test(c) && !["ES63", "ES64"].includes(c));
  // Último periodo con dato para la mayor parte de los territorios
  function ultimoComun(rows, validos, cobertura = 0.6) {
    const por = d3.group(rows.filter(r => validos.includes(r.codigo_territorio)), r => r.periodo);
    const min = Math.max(3, Math.ceil(cobertura * validos.length));
    const p = [...por.keys()].sort().reverse().find(p => new Set(por.get(p).map(r => r.codigo_territorio)).size >= min);
    return p ? {periodo: p, valores: new Map(por.get(p).map(r => [r.codigo_territorio, r.valor]))} : null;
  }
  // Carga varios indicadores a la vez; ref: valor de la UE (países) o de España (regiones) en el mismo periodo
  async function cargarVarios(specs, validos, refCode) {
    const res = await Promise.all(specs.map(async s => {
      try {
        const r = await cargar(s);
        if (!r.ok) return null;
        const u = ultimoComun(r.rows, validos);
        if (!u) return null;
        const ref = r.rows.find(x => x.periodo === u.periodo && x.codigo_territorio === refCode)?.valor;
        return {...s, ...u, ref, fuente: r.code};
      } catch (e) { return null; }
    }));
    return res.filter(Boolean);
  }
  const nombre = (c) => nombresGeo[c] ?? c;
  function bandera(c) {
    const iso = c === "EU27_2020" ? "eu" : c === "EL" ? "gr" : c === "UK" ? "gb" : (/^[A-Z]{2}$/.test(c) ? c.toLowerCase() : null);
    if (!iso) return "";
    const img = html`<img class="mem-bandera" alt="" loading="lazy">`;
    img.src = `https://flagcdn.com/w80/${iso}.png`;
    img.onerror = () => img.remove();
    return img;
  }
  function barajar(a, azar = Math.random) { const b = [...a]; for (let i = b.length - 1; i > 0; i--) { const j = Math.floor(azar() * (i + 1)); [b[i], b[j]] = [b[j], b[i]]; } return b; }
  const conUnidad = (v, uc) => uc === "%" ? `${fmt(v)} %` : uc ? `${fmt(v)} ${uc}` : fmt(v);
  return {paises, regiones, ultimoComun, cargarVarios, nombre, bandera, barajar, conUnidad};
}
```'''

INTRO_RED = '<p class="nota">Los resultados viajan por un servicio público de mensajería en tiempo real y no se guardan en ningún sitio. Antes de usarlo en clase por primera vez, haz una prueba con tu móvil.</p>'

# =====================================================================================
# 1. Ordena la malla
# =====================================================================================
pagina("ordena.qmd", r'''---
title: "Ordena la malla"
subtitle: "Juego para clase con código QR: ordena países o regiones de mayor a menor en un indicador"
toc: false
---

__HELPERS__

__QRJ__

__DJ__

```{ojs}
//| echo: false
SALA = new URLSearchParams(location.search).get("sala")
INDS_O = (__ORDENA__)
AREAS_O = (__AREAS__)
// Puntos de una ronda: porcentaje de parejas en el orden correcto (100 = orden perfecto)
puntosOrden = (orden, xs) => { let c = 0, n = 0; for (let i = 0; i < orden.length; i++) for (let j = i + 1; j < orden.length; j++) { n++; if (xs[orden[i]] > xs[orden[j]]) c++; } return n ? Math.round(100 * c / n) : 0; }
```

```{ojs}
//| echo: false
viewof ambitoO = SALA ? Object.assign(html`<span></span>`, {value: null}) : Inputs.radio(new Map([["Países de la UE", "paises"], ["Comunidades autónomas", "regiones"]]), {label: "Territorios", value: "paises"})
viewof areaO = SALA || ambitoO === "regiones" ? Object.assign(html`<span></span>`, {value: "todas"}) : Inputs.select(new Map([["Todas las áreas", "todas"], ...Object.entries(AREAS_O).map(([k, v]) => [v, k])]), {label: "Área de los indicadores", value: "todas"})
viewof rondasO = SALA ? Object.assign(html`<span></span>`, {value: null}) : Inputs.range([3, 8], {label: "Rondas (un indicador distinto en cada una)", value: 5, step: 1})
viewof nO = SALA ? Object.assign(html`<span></span>`, {value: null}) : Inputs.range([4, 7], {label: "Territorios por ronda", value: 5, step: 1})
viewof abrirO = SALA ? Object.assign(html`<span></span>`, {value: 0}) : Inputs.button("▶ Abrir el juego", {value: 0, reduce: v => v + 1})
```

```{ojs}
//| echo: false
// ============================ PANTALLA DEL PROFESOR ============================
{
  if (SALA) return html``;
  if (!abrirO) return html`<div class="conc-intro"><p><b>Cómo funciona:</b> en cada ronda aparece un indicador y varios países (o comunidades autónomas). Desde el móvil, los estudiantes los tocan <b>de mayor a menor valor</b>. Ganan más puntos cuanto más se acerque su orden al real: 100 si lo clavan. Al terminar verás el orden correcto de cada ronda, con los datos, para comentarlo en clase.</p>__INTRO_RED__</div>`;
  const ambito = (viewof ambitoO).value, area = (viewof areaO).value, rondas = (viewof rondasO).value, n = (viewof nO).value;
  const caja = html`<div class="conc-panel"><p class="pending">Descargando los datos de Eurostat…</p></div>`;
  (async () => {
    const validos = ambito === "regiones" ? DJ.regiones : DJ.paises;
    let cands = ambito === "regiones" ? INDS_O.regiones : (area === "todas" ? Object.values(INDS_O.paises).flat() : INDS_O.paises[area]);
    cands = DJ.barajar(cands).slice(0, rondas + 4);
    const datos = await DJ.cargarVarios(cands, validos, null);
    const R = [];
    for (const d of datos) {
      if (R.length >= rondas) break;
      const disp = DJ.barajar([...d.valores].filter(([, v]) => Number.isFinite(v)));
      const items = [], vistos = new Set();
      for (const [c, v] of disp) { const t = fmt(v); if (vistos.has(t)) continue; vistos.add(t); items.push({c, n: DJ.nombre(c), v: t, x: v}); if (items.length === n) break; }
      if (items.length === n) R.push({ind: d.nombre, u: d.unidad, p: d.periodo, items});
    }
    if (R.length < 2) { caja.innerHTML = `<p class="pending">❌ No se han podido descargar suficientes indicadores. Inténtalo de nuevo o elige otra área.</p>`; return; }
    const S = await QRJ.abrirSala("ordena");
    if (!S) { caja.innerHTML = QRJ.ERR_RED; return; }
    let fase = "espera";
    S.publicar({fase, rondas: R});
    const empezar = html`<button class="asis-boton">▶ Empezar</button>`, terminar = html`<button class="copiar">🏁 Terminar</button>`;
    terminar.disabled = true;
    caja.innerHTML = "";
    caja.append(QRJ.cabecera(S.enlace, [empezar, terminar]), html`<div class="conc-ranking"></div><div class="cp-soluciones"></div>`);
    const N = R.length;
    const pintar = () => {
      const r = [...S.jug.values()].sort((a, b) => (b.puntos ?? 0) - (a.puntos ?? 0) || (b.fin ? 1 : 0) - (a.fin ? 1 : 0) || (a.tiempo ?? 0) - (b.tiempo ?? 0));
      QRJ.cuenta(caja, r.length);
      const z = caja.querySelector(".conc-ranking");
      if (fase === "espera") { z.innerHTML = `<div class="conc-alias">${r.map(j => `<span>${j.alias}</span>`).join("")}</div>`; return; }
      z.innerHTML = `${fase === "fin" && r[0] ? `<h2 class="conc-podio">🏆 ${r[0].alias}</h2>` : ""}<table class="uso-tabla conc-tabla"><tr><th></th><th>Alias</th><th>Puntos</th><th>Ronda</th><th>Tiempo</th></tr>` +
        r.slice(0, 15).map((j, i) => `<tr class="${fase === "fin" && i < 3 ? "conc-top" : ""}"><td>${fase === "fin" ? QRJ.medalla(i) : i + 1 + "."}</td><td>${j.alias}</td><td><b>${j.puntos ?? 0}</b> / ${100 * N}</td><td>${j.fin ? "✔ terminado" : `${j.ronda ?? 0} / ${N}`}</td><td>${QRJ.segundos(j.tiempo)}</td></tr>`).join("") + "</table>";
    };
    S.alCambiar(pintar);
    empezar.onclick = () => { fase = "juego"; S.publicar({fase, rondas: R}); empezar.disabled = true; terminar.disabled = false; pintar(); window.cceeEvento && window.cceeEvento("ordena/empezar", "Ordena la malla", true); };
    terminar.onclick = () => {
      fase = "fin";
      const r = [...S.jug.values()].sort((a, b) => (b.puntos ?? 0) - (a.puntos ?? 0) || (a.tiempo ?? 0) - (b.tiempo ?? 0));
      S.publicar({fase, rondas: R, ranking: r.slice(0, 10).map(j => j.alias)}); terminar.disabled = true; pintar();
      caja.querySelector(".cp-soluciones").innerHTML = `<h3>Orden correcto de cada ronda</h3><div class="ord-sols">` + R.map((q, k) => `<div class="ord-sol"><p><b>${k + 1}. ${q.ind}</b><br><span class="kpi-s">${q.u} · ${q.p}</span></p><ol>${[...q.items].sort((a, b) => b.x - a.x).map(it => `<li>${it.n}: <b>${it.v}</b></li>`).join("")}</ol></div>`).join("") + "</div>";
    };
    invalidation.then(() => S.cerrar());
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
  const caja = html`<div class="conc-movil"><p class="pending">Conectando con el juego…</p></div>`;
  let estado = null, alias = null, k = 0, puntos = 0, t0 = null, orden = [], revisada = false;
  let C;
  const pantalla = () => {
    caja.innerHTML = "";
    if (!alias) { caja.append(QRJ.formAlias(a => { alias = a; C.enviar({alias, puntos: 0, ronda: 0}); pantalla(); })); return; }
    if (!estado || estado.fase === "espera") { caja.append(QRJ.espera(alias)); return; }
    const R = estado.rondas;
    if (estado.fase === "fin" || k >= R.length) {
      const pos = estado.ranking ? estado.ranking.indexOf(alias) : -1;
      caja.append(html`<div class="asis-caja conc-espera"><p class="juego-grande">${puntos} puntos</p><p>de ${100 * R.length} posibles · ${QRJ.segundos(t0 ? Date.now() - t0 : 0)}</p>${estado.fase === "fin" && pos >= 0 ? html`<p>Puesto <b>${pos + 1}</b> ${QRJ.medalla(pos)}</p>` : html`<p class="asis-nota">Mira el ranking en la pantalla de clase.</p>`}</div>`);
      return;
    }
    if (!t0) t0 = Date.now();
    const q = R[k], xs = q.items.map(it => it.x);
    const lista = html`<div class="ord-lista"></div>`;
    const comprobar = html`<button class="asis-boton">Comprobar</button>`, deshacer = html`<button type="button" class="copiar">↩ Deshacer</button>`;
    const pintarLista = () => {
      lista.innerHTML = "";
      q.items.forEach((it, i) => {
        const pos = orden.indexOf(i);
        const b = html`<button type="button" class="ord-item${pos >= 0 ? " ord-elegido" : ""}"><span class="ord-num">${pos >= 0 ? pos + 1 : ""}</span></button>`;
        const f = DJ.bandera(it.c); if (f) b.append(f);
        b.append(html`<span class="ord-nombre">${it.n}</span>`);
        if (revisada) { b.append(html`<span class="ord-valor">${it.v}</span>`); b.disabled = true; }
        else b.onclick = () => { if (pos < 0) { orden.push(i); pintarLista(); } };
        lista.append(b);
      });
      comprobar.disabled = revisada || orden.length < q.items.length;
      deshacer.disabled = revisada || !orden.length;
    };
    deshacer.onclick = () => { orden.pop(); pintarLista(); };
    const fb = html`<div></div>`;
    comprobar.onclick = () => {
      revisada = true;
      const pts = puntosOrden(orden, xs); puntos += pts; k++;
      C.enviar({alias, puntos, ronda: k, fin: k >= R.length, tiempo: Date.now() - t0});
      const correcto = [...q.items].sort((a, b) => b.x - a.x);
      fb.append(html`<div class="cp-sol ${pts === 100 ? "ok" : pts >= 60 ? "medio" : "ko"}"><p class="juego-grande">+${pts}</p><p>Orden correcto:</p><ol class="ord-correcto">${correcto.map((it, i) => html`<li>${q.items[orden[i]] === it ? "✔ " : ""}${it.n}: <b>${it.v}</b></li>`)}</ol></div>`);
      const sig = html`<button type="button" class="asis-boton">${k >= R.length ? "Ver mi resultado" : "Siguiente ronda ▶"}</button>`;
      sig.onclick = () => { orden = []; revisada = false; pantalla(); };
      fb.append(sig);
      pintarLista();
    };
    caja.append(html`<p class="juego-ind">Ronda ${k + 1} de ${R.length} · ${puntos} puntos</p>`,
      html`<p class="mem-movil-cab"><b>${q.ind}</b><br><span>${q.u} · ${q.p}</span></p>`,
      html`<p class="mem-pregunta">Tócalos de <b>mayor a menor</b></p>`, lista, html`<div class="graf-botones ord-botones">${deshacer}${comprobar}</div>`, fb);
    pintarLista();
  };
  (async () => {
    C = await QRJ.unirse("ordena", d => { const antes = estado?.fase; estado = d; if (antes !== d.fase) pantalla(); });
    if (!C) { caja.innerHTML = QRJ.ERR_MOVIL; return; }
    pantalla();
  })();
  invalidation.then(() => C?.cerrar());
  return caja;
}
```
''', ORDENA=J(ORDENA), AREAS=J(AREAS), INTRO_RED=INTRO_RED)

# =====================================================================================
# 2. ¿Quién es quién?
# =====================================================================================
pagina("quien.qmd", r'''---
title: "¿Quién es quién?"
subtitle: "Juego para clase con código QR: adivina el país o la comunidad autónoma a partir de sus indicadores"
toc: false
---

__HELPERS__

__QRJ__

__DJ__

```{ojs}
//| echo: false
SALA = new URLSearchParams(location.search).get("sala")
SETS_Q = ({paises: __PAISES__, regiones: __REGIONES__})
// Preguntas: un territorio oculto con su perfil y cuatro opciones (en «difícil», los tres más parecidos)
prepararQuien = (datos, pool, n, dificil, azar = Math.random) => {
  const z = datos.map(d => { const v = pool.map(c => d.valores.get(c)).filter(Number.isFinite); return {m: d3.mean(v), s: d3.deviation(v) || 1}; });
  const dist = (a, b) => d3.sum(datos, (d, i) => { const x = d.valores.get(a), y = d.valores.get(b); return Number.isFinite(x) && Number.isFinite(y) ? ((x - y) / z[i].s) ** 2 : 0; });
  return DJ.barajar(pool, azar).slice(0, n).map(c => {
    const otros = pool.filter(o => o !== c);
    const dis = dificil ? [...otros].sort((a, b) => dist(c, a) - dist(c, b)).slice(0, 3) : DJ.barajar(otros, azar).slice(0, 3);
    return {c, opciones: DJ.barajar([c, ...dis], azar),
      perfil: datos.filter(d => Number.isFinite(d.valores.get(c))).map(d => ({i: d.corto, v: DJ.conUnidad(d.valores.get(c), d.uc), r: Number.isFinite(d.ref) ? DJ.conUnidad(d.ref, d.uc) : "", p: d.periodo}))};
  });
}
```

```{ojs}
//| echo: false
viewof ambitoQ = SALA ? Object.assign(html`<span></span>`, {value: null}) : Inputs.radio(new Map([["Países de la UE", "paises"], ["Comunidades autónomas", "regiones"]]), {label: "Territorios", value: "paises"})
viewof nQ = SALA ? Object.assign(html`<span></span>`, {value: null}) : Inputs.range([4, 12], {label: "Número de preguntas", value: 6, step: 1})
viewof difQ = SALA ? Object.assign(html`<span></span>`, {value: null}) : Inputs.radio(new Map([["Normal: opciones al azar", false], ["Difícil: las opciones son territorios parecidos", true]]), {label: "Dificultad", value: false})
viewof abrirQ = SALA ? Object.assign(html`<span></span>`, {value: 0}) : Inputs.button("▶ Abrir el juego", {value: 0, reduce: v => v + 1})
```

```{ojs}
//| echo: false
// ============================ PANTALLA DEL PROFESOR ============================
{
  if (SALA) return html``;
  if (!abrirQ) return html`<div class="conc-intro"><p><b>Cómo funciona:</b> cada pregunta muestra el perfil de un país (o comunidad autónoma) oculto: su PIB per cápita, su paro, su deuda, su inflación, su esperanza de vida… junto a la media de referencia. Los estudiantes eligen en el móvil de qué territorio se trata entre cuatro opciones. Gana quien más acierte y, si hay empate, quien tarde menos.</p><p>Es una forma de practicar la lectura conjunta de indicadores: ¿qué combinación de datos delata a Irlanda, a Grecia o a Madrid?</p>__INTRO_RED__</div>`;
  const ambito = (viewof ambitoQ).value, n = (viewof nQ).value, dificil = (viewof difQ).value;
  const caja = html`<div class="conc-panel"><p class="pending">Descargando los datos de Eurostat…</p></div>`;
  (async () => {
    const validos = ambito === "regiones" ? DJ.regiones : DJ.paises;
    const datos = await DJ.cargarVarios(SETS_Q[ambito], validos, ambito === "regiones" ? "ES" : "EU27_2020");
    const pool = validos.filter(c => datos.filter(d => Number.isFinite(d.valores.get(c))).length >= Math.max(3, datos.length - 1));
    if (datos.length < 3 || pool.length < 4) { caja.innerHTML = `<p class="pending">❌ No se han podido descargar suficientes datos. Inténtalo de nuevo más tarde.</p>`; return; }
    const S = await QRJ.abrirSala("quien");
    if (!S) { caja.innerHTML = QRJ.ERR_RED; return; }
    const P = prepararQuien(datos, pool, Math.min(n, pool.length), dificil).map((q, i) => ({perfil: q.perfil, op: q.opciones.map(c => ({c, n: DJ.nombre(c)})), k: (q.opciones.indexOf(q.c) + QRJ.hash(S.sala + i)) % 4}));
    const ref = ambito === "regiones" ? "España" : "UE-27";
    let fase = "espera";
    S.publicar({fase, P, ref});
    const empezar = html`<button class="asis-boton">▶ Empezar</button>`, terminar = html`<button class="copiar">🏁 Terminar</button>`;
    terminar.disabled = true;
    caja.innerHTML = "";
    caja.append(QRJ.cabecera(S.enlace, [empezar, terminar]), html`<div class="conc-ranking"></div><div class="cp-soluciones"></div>`);
    const orden = () => [...S.jug.values()].sort((a, b) => (b.aciertos ?? 0) - (a.aciertos ?? 0) || (b.fin ? 1 : 0) - (a.fin ? 1 : 0) || (a.tiempo ?? 0) - (b.tiempo ?? 0));
    const pintar = () => {
      const r = orden(); QRJ.cuenta(caja, r.length);
      const z = caja.querySelector(".conc-ranking");
      if (fase === "espera") { z.innerHTML = `<div class="conc-alias">${r.map(j => `<span>${j.alias}</span>`).join("")}</div>`; return; }
      z.innerHTML = `${fase === "fin" && r[0] ? `<h2 class="conc-podio">🏆 ${r[0].alias}</h2>` : ""}<table class="uso-tabla conc-tabla"><tr><th></th><th>Alias</th><th>Aciertos</th><th>Pregunta</th><th>Tiempo</th></tr>` +
        r.slice(0, 15).map((j, i) => `<tr class="${fase === "fin" && i < 3 ? "conc-top" : ""}"><td>${fase === "fin" ? QRJ.medalla(i) : i + 1 + "."}</td><td>${j.alias}</td><td><b>${j.aciertos ?? 0}</b> / ${P.length}</td><td>${j.fin ? "✔ terminado" : `${j.resp ?? 0} / ${P.length}`}</td><td>${QRJ.segundos(j.tiempo)}</td></tr>`).join("") + "</table>";
    };
    S.alCambiar(pintar);
    empezar.onclick = () => { fase = "juego"; S.publicar({fase, P, ref}); empezar.disabled = true; terminar.disabled = false; pintar(); window.cceeEvento && window.cceeEvento("quien/empezar", "Quién es quién", true); };
    terminar.onclick = () => {
      fase = "fin"; S.publicar({fase, P, ref, ranking: orden().slice(0, 10).map(j => j.alias)}); terminar.disabled = true; pintar();
      caja.querySelector(".cp-soluciones").innerHTML = `<h3>Soluciones</h3><div class="ord-sols">` + P.map((q, i) => { const ok = q.op[(q.k - QRJ.hash(S.sala + i) % 4 + 4) % 4];
        return `<div class="ord-sol"><p><b>${i + 1}. ${ok.n}</b></p><ul>${q.perfil.map(f => `<li>${f.i}: <b>${f.v}</b>${f.r ? ` <span class="kpi-s">(${ref}: ${f.r})</span>` : ""}</li>`).join("")}</ul></div>`; }).join("") + "</div>";
    };
    invalidation.then(() => S.cerrar());
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
  const caja = html`<div class="conc-movil"><p class="pending">Conectando con el juego…</p></div>`;
  let estado = null, alias = null, i = 0, aciertos = 0, t0 = null, C;
  const pantalla = () => {
    caja.innerHTML = "";
    if (!alias) { caja.append(QRJ.formAlias(a => { alias = a; C.enviar({alias, aciertos: 0, resp: 0}); pantalla(); })); return; }
    if (!estado || estado.fase === "espera") { caja.append(QRJ.espera(alias)); return; }
    const P = estado.P;
    if (estado.fase === "fin" || i >= P.length) {
      const pos = estado.ranking ? estado.ranking.indexOf(alias) : -1;
      caja.append(html`<div class="asis-caja conc-espera"><p class="juego-grande">${aciertos} / ${P.length}</p><p>aciertos · ${QRJ.segundos(t0 ? Date.now() - t0 : 0)}</p>${estado.fase === "fin" && pos >= 0 ? html`<p>Puesto <b>${pos + 1}</b> ${QRJ.medalla(pos)}</p>` : html`<p class="asis-nota">Mira el ranking en la pantalla de clase.</p>`}</div>`);
      return;
    }
    if (!t0) t0 = Date.now();
    const q = P[i], ok = (q.k - QRJ.hash(C.sala + i) % 4 + 4) % 4;
    const tabla = html`<table class="uso-tabla qui-perfil"><tr><th>Indicador</th><th>Dato</th><th>${estado.ref}</th></tr>${q.perfil.map(f => html`<tr><td>${f.i} <span class="kpi-s">${f.p}</span></td><td><b>${f.v}</b></td><td class="kpi-s">${f.r}</td></tr>`)}</table>`;
    const fb = html`<div></div>`;
    const ops = html`<div class="mem-opciones qui-opciones"></div>`;
    q.op.forEach((o, j) => {
      const b = html`<button type="button" class="ord-item"></button>`;
      const f = DJ.bandera(o.c); if (f) b.append(f);
      b.append(html`<span class="ord-nombre">${o.n}</span>`);
      b.onclick = () => {
        ops.querySelectorAll("button").forEach(x => x.disabled = true);
        const bien = j === ok; if (bien) aciertos++; i++;
        b.classList.add(bien ? "qui-bien" : "qui-mal"); ops.children[ok].classList.add("qui-bien");
        C.enviar({alias, aciertos, resp: i, fin: i >= P.length, tiempo: Date.now() - t0});
        fb.append(html`<p class="${bien ? "mem-ok" : "mem-ko"}">${bien ? "✔ ¡Correcto!" : html`✘ Era <b>${q.op[ok].n}</b>`}</p>`);
        const sig = html`<button type="button" class="asis-boton">${i >= P.length ? "Ver mi resultado" : "Siguiente ▶"}</button>`;
        sig.onclick = pantalla; fb.append(sig);
      };
      ops.append(b);
    });
    caja.append(html`<p class="juego-ind">Pregunta ${i + 1} de ${P.length} · ${aciertos} aciertos</p>`, html`<p class="mem-pregunta">¿Quién es quién?</p>`, tabla, ops, fb);
  };
  (async () => {
    C = await QRJ.unirse("quien", d => { const antes = estado?.fase; estado = d; if (antes !== d.fase) pantalla(); });
    if (!C) { caja.innerHTML = QRJ.ERR_MOVIL; return; }
    pantalla();
  })();
  invalidation.then(() => C?.cerrar());
  return caja;
}
```
''', PAISES=J(JUEGO_PAISES), REGIONES=J(JUEGO_REGIONES), INTRO_RED=INTRO_RED)

# =====================================================================================
# 3. Bingo de indicadores
# =====================================================================================
pagina("bingo.qmd", r'''---
title: "Bingo de indicadores"
subtitle: "Juego para clase con código QR: tacha en tu cartón los países que cumplen cada condición"
toc: false
---

__HELPERS__

__QRJ__

__DJ__

```{ojs}
//| echo: false
SALA = new URLSearchParams(location.search).get("sala")
SETS_B = ({paises: __PAISES__, regiones: __REGIONES__})
BINGO = {
  // Redondeo «bonito» del umbral
  function redondo(x) {
    const m = Math.abs(x);
    const paso = m >= 1000 ? 10 ** (Math.floor(Math.log10(m)) - 1) : m >= 100 ? 5 : m >= 10 ? 1 : m >= 1 ? 0.5 : 0.1;
    return +(Math.round(x / paso) * paso).toFixed(2);
  }
  // Nueva bola: indicador, «mayor/menor que» y un umbral que cumplan entre el 25 % y el 70 % de los territorios
  function nuevaBola(inds, pool, previas, azar = Math.random) {
    for (let intento = 0; intento < 60; intento++) {
      const ind = inds[Math.floor(azar() * inds.length)];
      if (inds.length > 2 && previas.slice(-2).some(b => b.id === ind.id)) continue;
      const vals = pool.map(c => [c, ind.valores.get(c)]).filter(([, v]) => Number.isFinite(v));
      if (vals.length < 6) continue;
      const xs = vals.map(d => d[1]).sort((a, b) => a - b), mayor = azar() < 0.5;
      const umbral = redondo(d3.quantile(xs, 0.3 + azar() * 0.4));
      const ok = vals.filter(([, v]) => mayor ? v > umbral : v < umbral).map(d => d[0]);
      if (ok.length / vals.length < 0.25 || ok.length / vals.length > 0.7) continue;
      if (previas.some(b => b.id === ind.id && b.mayor === mayor && b.umbral === umbral)) continue;
      return {id: ind.id, mayor, umbral, t: `${ind.corto} ${mayor ? "mayor" : "menor"} que ${DJ.conUnidad(umbral, ind.uc)}`, ok, p: ind.periodo,
        v: Object.fromEntries(vals.map(([c, v]) => [c, DJ.conUnidad(v, ind.uc)]))};
    }
    return null;
  }
  const LINEAS = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6]];
  const hayLinea = (marcadas) => LINEAS.some(l => l.every(i => marcadas.has(i)));
  const ordenar = (jug) => [...jug.values()].sort((a, b) => (a.bingo ?? Infinity) - (b.bingo ?? Infinity) || (a.linea ?? Infinity) - (b.linea ?? Infinity) || (b.marcadas ?? 0) - (a.marcadas ?? 0) || (a.errores ?? 0) - (b.errores ?? 0));
  return {redondo, nuevaBola, LINEAS, hayLinea, ordenar};
}
```

```{ojs}
//| echo: false
viewof ambitoB = SALA ? Object.assign(html`<span></span>`, {value: null}) : Inputs.radio(new Map([["Países de la UE", "paises"], ["Comunidades autónomas", "regiones"]]), {label: "Territorios", value: "paises"})
viewof abrirB = SALA ? Object.assign(html`<span></span>`, {value: 0}) : Inputs.button("▶ Abrir el bingo", {value: 0, reduce: v => v + 1})
```

```{ojs}
//| echo: false
// ============================ PANTALLA DEL PROFESOR ============================
{
  if (SALA) return html``;
  if (!abrirB) return html`<div class="conc-intro"><p><b>Cómo funciona:</b> cada estudiante recibe en el móvil un <b>cartón de 3 × 3</b> con países (o comunidades autónomas) al azar. El profesor va sacando <b>bolas</b>, que son condiciones sobre un indicador, por ejemplo «Tasa de paro mayor que 8 %» o «Deuda pública menor que 60 % del PIB». Los estudiantes tachan en su cartón los territorios que cumplen alguna de las condiciones que han salido; si tachan uno que no las cumple, suman un error y esa casilla se bloquea unos segundos. Se canta <b>línea</b> (fila, columna o diagonal) y <b>bingo</b> (cartón completo).</p><p>Después de cada bola puedes mostrar en la pantalla qué territorios la cumplían, con un gráfico, para comentarlo.</p>__INTRO_RED__</div>`;
  const ambito = (viewof ambitoB).value;
  const caja = html`<div class="conc-panel"><p class="pending">Descargando los datos de Eurostat…</p></div>`;
  (async () => {
    const validos = ambito === "regiones" ? DJ.regiones : DJ.paises;
    const inds = await DJ.cargarVarios(SETS_B[ambito], validos, null);
    const pool = validos.filter(c => inds.filter(d => Number.isFinite(d.valores.get(c))).length >= Math.max(2, inds.length - 2));
    if (inds.length < 3 || pool.length < 9) { caja.innerHTML = `<p class="pending">❌ No se han podido descargar suficientes datos. Inténtalo de nuevo más tarde.</p>`; return; }
    const S = await QRJ.abrirSala("bingo");
    if (!S) { caja.innerHTML = QRJ.ERR_RED; return; }
    const poolN = pool.map(c => ({c, n: DJ.nombre(c)}));
    let fase = "espera", inicio = null;
    const bolas = [];
    const estado = (extra = {}) => S.publicar({fase, pool: poolN, bolas, inicio, ...extra});
    estado();
    const sacar = html`<button class="asis-boton">🎱 Sacar bola</button>`, ver = html`<button class="copiar">👁 Mostrar quién la cumple</button>`, terminar = html`<button class="copiar">🏁 Terminar</button>`;
    ver.disabled = true; terminar.disabled = true;
    caja.innerHTML = "";
    caja.append(QRJ.cabecera(S.enlace, [sacar, ver, terminar]), html`<div class="bingo-bola"></div><div class="bingo-anuncio"></div><div class="bingo-sol"></div><div class="bingo-historial"></div><div class="conc-ranking"></div>`);
    const $ = (s) => caja.querySelector(s);
    const anunciados = new Set();
    const pintar = () => {
      const r = BINGO.ordenar(S.jug); QRJ.cuenta(caja, r.length);
      for (const j of r) {
        if (j.bingo != null && !anunciados.has("b" + j.id)) { anunciados.add("b" + j.id); $(".bingo-anuncio").innerHTML = `<p class="bingo-canto">🎉 ¡BINGO! · ${j.alias}</p>`; }
        else if (j.linea != null && !anunciados.has("l" + j.id) && !r.some(x => x.bingo != null)) { anunciados.add("l" + j.id); $(".bingo-anuncio").innerHTML = `<p class="bingo-canto">📣 ¡Línea! · ${j.alias}</p>`; }
      }
      const z = $(".conc-ranking");
      if (fase === "espera") { z.innerHTML = `<div class="conc-alias">${r.map(j => `<span>${j.alias}</span>`).join("")}</div>`; return; }
      z.innerHTML = `<table class="uso-tabla conc-tabla"><tr><th></th><th>Alias</th><th>Casillas</th><th>Línea</th><th>Bingo</th><th>Errores</th></tr>` +
        r.slice(0, 15).map((j, i) => `<tr class="${j.bingo != null && i < 3 ? "conc-top" : ""}"><td>${j.bingo != null ? QRJ.medalla(i) : i + 1 + "."}</td><td>${j.alias}</td><td><span class="mem-barra"><span style="width:${100 * (j.marcadas ?? 0) / 9}%"></span></span> ${j.marcadas ?? 0} / 9</td><td>${j.linea != null ? "✔ " + QRJ.segundos(j.linea) : ""}</td><td>${j.bingo != null ? "🎉 " + QRJ.segundos(j.bingo) : ""}</td><td>${j.errores ?? 0}</td></tr>`).join("") + "</table>";
    };
    S.alCambiar(pintar);
    sacar.onclick = () => {
      const b = BINGO.nuevaBola(inds, pool, bolas);
      if (!b) { $(".bingo-bola").innerHTML = `<p class="pending">No quedan bolas distintas. Pulsa «Terminar».</p>`; return; }
      if (fase === "espera") { fase = "juego"; inicio = Date.now(); terminar.disabled = false; window.cceeEvento && window.cceeEvento("bingo/empezar", "Bingo de indicadores", true); }
      bolas.push(b); estado(); ver.disabled = false;
      $(".bingo-bola").innerHTML = `<p class="kpi-s">Bola ${bolas.length} · dato de ${b.p}</p><p class="bingo-texto">${b.t}</p>`;
      $(".bingo-sol").innerHTML = "";
      $(".bingo-historial").innerHTML = bolas.length > 1 ? `<p class="kpi-s">Bolas anteriores: ${bolas.slice(0, -1).map((x, i) => `${i + 1}. ${x.t}`).join(" · ")}</p>` : "";
      pintar();
    };
    ver.onclick = () => {
      const b = bolas.at(-1), ind = inds.find(d => d.id === b.id);
      const filas = pool.filter(c => Number.isFinite(ind.valores.get(c))).map(c => ({t: DJ.nombre(c), v: ind.valores.get(c), ok: b.ok.includes(c)}));
      $(".bingo-sol").innerHTML = "";
      $(".bingo-sol").append(Plot.plot({
        title: `${ind.nombre} (${b.p}): en color, los territorios que cumplen «${b.t}»`,
        height: Math.max(280, 18 * filas.length), marginLeft: 120, x: {label: ind.unidad, grid: true}, y: {label: null},
        marks: [Plot.barX(filas, {y: "t", x: "v", sort: {y: "-x"}, fill: d => d.ok ? "#B5175F" : "#D9D9D9"}), Plot.ruleX([b.umbral], {stroke: "#F29200", strokeWidth: 2.5}), Plot.ruleX([0])]
      }));
    };
    terminar.onclick = () => { fase = "fin"; estado({ranking: BINGO.ordenar(S.jug).slice(0, 10).map(j => j.alias)}); sacar.disabled = true; terminar.disabled = true; pintar(); };
    invalidation.then(() => S.cerrar());
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
  const caja = html`<div class="conc-movil"><p class="pending">Conectando con el bingo…</p></div>`;
  let estado = null, alias = null, carton = null, C;
  const marcadas = new Set(), bloqueadas = new Map();
  let errores = 0, linea = null, bingo = null, mensaje = "";
  const enviar = () => C.enviar({alias, marcadas: marcadas.size, errores, linea, bingo});
  const pantalla = () => {
    caja.innerHTML = "";
    if (!alias) { caja.append(QRJ.formAlias(a => { alias = a; enviar(); pantalla(); })); return; }
    if (!estado) { caja.append(QRJ.espera(alias)); return; }
    if (!carton) {
      const clave = `ccee-bingo-carton-${C.sala}`;
      try { carton = JSON.parse(localStorage.getItem(clave)); } catch (e) {}
      if (!Array.isArray(carton) || carton.length !== 9) { carton = DJ.barajar(estado.pool).slice(0, 9); try { localStorage.setItem(clave, JSON.stringify(carton)); } catch (e) {} }
    }
    const bolas = estado.bolas ?? [];
    const ultima = bolas.at(-1);
    caja.append(html`<p class="juego-ind">${estado.fase === "espera" ? "Este es tu cartón. Espera a la primera bola…" : `Bola ${bolas.length} · ${marcadas.size} / 9 · ${errores} errores`}</p>`);
    if (ultima) caja.append(html`<div class="bingo-movil-bola"><p class="kpi-s">Última bola</p><p><b>${ultima.t}</b></p></div>`);
    if (linea != null || bingo != null) caja.append(html`<p class="bingo-canto">${bingo != null ? "🎉 ¡BINGO!" : "📣 ¡Línea!"}</p>`);
    const g = html`<div class="mem-malla"></div>`;
    carton.forEach((t, i) => {
      const b = html`<button type="button" class="mem-celda${marcadas.has(i) ? " mem-ver" : ""}"></button>`;
      const f = DJ.bandera(t.c); if (f) b.append(f);
      const valor = marcadas.has(i) ? bolas.find(x => x.ok.includes(t.c))?.v?.[t.c] ?? "✔" : "";
      b.append(html`<span class="mem-nombre">${t.n}</span>`, html`<span class="mem-valor">${marcadas.has(i) ? "✔" : ""}</span>`, html`<span class="kpi-s">${valor}</span>`);
      const hasta = bloqueadas.get(i) ?? 0;
      if (marcadas.has(i) || estado.fase !== "juego" || Date.now() < hasta) { b.disabled = true; if (Date.now() < hasta) b.classList.add("bingo-bloq"); }
      b.onclick = () => {
        const cumple = bolas.find(x => x.ok.includes(t.c));
        if (cumple) {
          marcadas.add(i);
          const ms = Date.now() - (estado.inicio ?? Date.now());
          if (linea == null && BINGO.hayLinea(marcadas)) linea = ms;
          if (bingo == null && marcadas.size === 9) bingo = ms;
          mensaje = `✔ ${t.n} cumple «${cumple.t}»: ${cumple.v[t.c]}`;
        } else {
          errores++; bloqueadas.set(i, Date.now() + 5000);
          const ult = bolas.at(-1);
          mensaje = `✘ ${t.n} no cumple ninguna bola${ult?.v?.[t.c] ? ` (en la última: ${ult.v[t.c]})` : ""}. Casilla bloqueada 5 s.`;
          setTimeout(pantalla, 5100);
        }
        enviar(); pantalla();
      };
      g.append(b);
    });
    caja.append(g);
    if (mensaje) caja.append(html`<p class="${mensaje.startsWith("✔") ? "mem-ok" : "mem-ko"}">${mensaje}</p>`);
    if (bolas.length > 1) caja.append(html`<details class="bingo-movil-hist"><summary>Bolas anteriores (${bolas.length - 1})</summary><ol>${bolas.slice(0, -1).map(x => html`<li>${x.t}</li>`)}</ol></details>`);
    if (estado.fase === "fin") { const pos = estado.ranking ? estado.ranking.indexOf(alias) : -1; caja.append(html`<div class="asis-caja conc-espera"><p>Fin del bingo.${pos >= 0 ? html` Puesto <b>${pos + 1}</b> ${QRJ.medalla(pos)}` : ""}</p></div>`); }
  };
  (async () => {
    C = await QRJ.unirse("bingo", d => { const n0 = estado?.bolas?.length ?? -1, f0 = estado?.fase; estado = d; if (f0 !== d.fase || (d.bolas?.length ?? 0) !== n0) { mensaje = ""; pantalla(); } });
    if (!C) { caja.innerHTML = QRJ.ERR_MOVIL; return; }
    pantalla();
  })();
  invalidation.then(() => C?.cerrar());
  return caja;
}
```
''', PAISES=J(JUEGO_PAISES), REGIONES=J(JUEGO_REGIONES), INTRO_RED=INTRO_RED)

# =====================================================================================
# 4. Mapa de calor de coyuntura
# =====================================================================================
pagina("coyuntura.qmd", r'''---
title: "Mapa de calor de coyuntura"
subtitle: "Todos los países (o comunidades autónomas) y sus principales indicadores de un vistazo"
toc: false
---

Cada fila es un territorio y cada columna un indicador, con su último dato disponible. El color indica la **posición relativa** del territorio en ese indicador: **verde**, entre los que mejor están; **rojo**, entre los que peor. Para la inflación se considera mejor estar cerca del 2 %, el objetivo del Banco Central Europeo. La columna **Puntuación** resume la posición media en todos los indicadores.

__HELPERS__

__DJ__

```{ojs}
//| echo: false
VISTAS_C = (__CALOR__)
viewof vistaC = Inputs.radio(new Map(Object.entries(VISTAS_C).map(([k, v]) => [v.titulo, k])), {label: "Vista", value: "coyuntura"})
```

```{ojs}
//| echo: false
datosC = {
  const v = VISTAS_C[vistaC];
  const validos = v.ambito === "regiones" ? [...DJ.regiones, "ES"] : [...DJ.paises, "EU27_2020"];
  yield html`<p class="pending">Descargando ${v.ind.length} indicadores de Eurostat…</p>`;
  yield {v, validos, inds: await DJ.cargarVarios(v.ind, validos, null)};
}
```

```{ojs}
//| echo: false
// Puntuación de 0 (peor) a 1 (mejor) según la posición relativa entre los territorios (sin contar los agregados)
calor = {
  if (!datosC?.inds) return null;
  const {v, validos, inds} = datosC;
  const terr = validos.filter(c => inds.some(d => Number.isFinite(d.valores.get(c))));
  const agregado = (c) => c === "EU27_2020" || (v.ambito === "regiones" && c === "ES");
  const celdas = [];
  for (const d of inds) {
    const base = (x) => d.sentido === "obj2" ? -Math.abs(x - 2) : d.sentido * x;
    const xs = terr.filter(c => !agregado(c)).map(c => d.valores.get(c)).filter(Number.isFinite).map(base).sort((a, b) => a - b);
    for (const c of terr) {
      const x = d.valores.get(c);
      if (!Number.isFinite(x)) continue;
      const b = base(x), menores = d3.bisectLeft(xs, b), iguales = d3.bisectRight(xs, b) - menores;
      celdas.push({c, t: DJ.nombre(c), ind: d.corto, nombre: d.nombre, unidad: d.unidad, periodo: d.periodo, valor: x, punt: xs.length > 1 ? (menores + (iguales - 1) / 2) / (xs.length - 1) : 0.5, agregado: agregado(c)});
    }
  }
  const media = d3.rollup(celdas, g => d3.mean(g, d => d.punt), d => d.c);
  return {celdas, media, terr, inds, agregado};
}
viewof ordenC = calor ? Inputs.select(new Map([["Puntuación media", "media"], ["Nombre", "nombre"], ...calor.inds.map(d => [d.corto, d.corto])]), {label: "Ordenar por"}) : Object.assign(html`<span></span>`, {value: "media"})
```

```{ojs}
//| echo: false
{
  if (!calor) return html``;
  if (!calor.inds.length) return html`<p class="pending">No se han podido cargar los datos de Eurostat. Inténtalo de nuevo más tarde.</p>`;
  const {celdas, media, terr, inds} = calor;
  const valorDe = (c, ind) => celdas.find(d => d.c === c && d.ind === ind);
  const orden = [...terr].sort((a, b) => ordenC === "nombre" ? DJ.nombre(a).localeCompare(DJ.nombre(b), "es")
    : ordenC === "media" ? (media.get(b) ?? 0) - (media.get(a) ?? 0)
    : ((valorDe(b, ordenC)?.punt ?? -1) - (valorDe(a, ordenC)?.punt ?? -1))).map(DJ.nombre);
  const cols = ["Puntuación", ...inds.map(d => d.corto)];
  const filas = [...celdas, ...terr.map(c => ({c, t: DJ.nombre(c), ind: "Puntuación", punt: media.get(c), valor: 100 * media.get(c), unidad: "posición media (0-100)", periodo: "", nombre: "Puntuación media"}))];
  const periodos = Object.fromEntries(inds.map(d => [d.corto, d.periodo]));
  return Plot.plot({
    title: VISTAS_C[vistaC].titulo,
    width: Math.max(760, 92 * cols.length + 150), height: 26 * orden.length + 140, marginLeft: 130, marginTop: 120,
    x: {domain: cols, axis: "top", label: null, tickRotate: -35, tickFormat: d => periodos[d] ? `${d} (${periodos[d]})` : d},
    y: {domain: orden, label: null},
    color: {type: "linear", scheme: "RdYlGn", domain: [0, 1], legend: true, label: "Posición relativa (0 = peor, 1 = mejor)", tickFormat: d => d === 0 ? "peor" : d === 1 ? "mejor" : ""},
    marks: [
      Plot.cell(filas, {x: "ind", y: "t", fill: "punt", inset: 0.5, tip: true, title: d => `${d.t}\n${d.nombre}${d.periodo ? ` (${d.periodo})` : ""}\n${d.ind === "Puntuación" ? locES.format(",.0f")(d.valor) + " sobre 100" : fmt(d.valor) + " · " + d.unidad}`}),
      Plot.text(filas, {x: "ind", y: "t", text: d => d.ind === "Puntuación" ? locES.format(",.0f")(d.valor) : fmt(d.valor), fontSize: 10, fill: d => d.punt < 0.15 || d.punt > 0.85 ? "white" : "black", fontWeight: d => d.t === "España" || d.t === "Andalucía" || d.t === "UE-27" ? 700 : 400}),
      Plot.frame({anchor: "left", stroke: "#999"})
    ]
  });
}
```

```{ojs}
//| echo: false
calor?.celdas?.length ? html`<div class="descargas">${DOM.download(() => csv(calor.celdas.map(d => ({territorio: d.t, codigo: d.c, indicador: d.nombre, periodo: d.periodo, valor: d.valor, unidad: d.unidad, posicion_relativa: Math.round(1000 * d.punt) / 1000}))), `cceescopio_mapa_calor_${vistaC}.csv`, "⬇ Descargar los datos (CSV)")}</div>
<p class="source">Fuente: Eurostat (${calor.inds.map(d => d.fuente).join(", ")}). La posición relativa va de 0 (el peor dato entre los territorios) a 1 (el mejor), sin contar los agregados (UE-27 o España), que se sitúan respecto a los demás. Qué se considera «mejor» es una convención: un superávit exterior o una deuda baja no son siempre preferibles, y depende del momento del ciclo.</p>` : html``
```

::: {.callout-tip appearance="simple"}
**Para clase.** Proyecta el mapa y pregunta: ¿qué países están en verde en casi todo?, ¿hay alguno con buena coyuntura pero mala estructura?, ¿dónde está España? Para profundizar en un territorio, usa la [ficha de país o región](ficha.qmd); para jugar con estos mismos datos, el [¿Quién es quién?](quien.qmd) o el [Bingo de indicadores](bingo.qmd).
:::
''', CALOR=J(CALOR))

# =====================================================================================
# 5. Laboratorio de números índice
# =====================================================================================
NI_SERIES = {
    "ipc": {"nombre": "IPC general (IPCA)", "tipo": "ipc", "patron": None},
    "alimentos": {"nombre": "IPCA: alimentos y bebidas no alcohólicas", "tipo": "ipc", "patron": "^food and non-alcoholic beverages$"},
    "energia": {"nombre": "IPCA: energía", "tipo": "ipc", "patron": "^energy$"},
    "servicios": {"nombre": "IPCA: servicios", "tipo": "ipc", "patron": "^services( \\(overall index excluding goods\\))?$"},
    "industria": {"nombre": "Índice de producción industrial", "tipo": "spec", "spec": S("actividad", "indice-de-produccion-industrial")},
    "comercio": {"nombre": "Índice de comercio minorista", "tipo": "spec", "spec": S("actividad", "indice-de-comercio-minorista")},
    "construccion": {"nombre": "Producción en la construcción", "tipo": "spec", "spec": S("actividad", "produccion-en-la-construccion")},
}
NI_NOMINALES = {
    "renta": S("desigualdad", "renta-mediana-equivalente"),
    "smi": S("empleo", "salario-minimo-mensual"),
    "coste": S("empleo", "coste-laboral-por-hora"),
    "umbral": S("desigualdad", "umbral-de-pobreza-hogar-de-una-persona"),
}
pagina("numeros-indice.qmd", r'''---
title: "Laboratorio de números índice"
subtitle: "Cambio de base, tasas de variación, enlace de series, deflactación e índices de Laspeyres, Paasche y Fisher, con datos reales"
toc: true
---

Los números índice resumen cómo cambia una magnitud respecto a un periodo de referencia (la **base**, que vale 100). Este laboratorio aplica, paso a paso y con las fórmulas a la vista, las operaciones más habituales a series reales de Eurostat. Al final puedes ponerte a prueba con ejercicios que se corrigen solos.

__HELPERS__

__PRECIOS__

```{ojs}
//| echo: false
SERIES_NI = (__SERIES__)
NOMINALES_NI = (__NOMINALES__)
f2 = (v) => Number.isFinite(v) ? locES.format(",.2f")(v) : "–"
f1 = (v) => Number.isFinite(v) ? locES.format(",.1f")(v) : "–"
mediaAnio = (s, a) => d3.mean(s.filter(d => d.fecha.getFullYear() === a), d => d.valor)
anuales = (s) => [...d3.rollup(s, v => ({valor: d3.mean(v, d => d.valor), n: v.length}), d => d.fecha.getFullYear())].filter(([, v]) => v.n >= 12).map(([a, v]) => ({anio: a, valor: v.valor})).sort((a, b) => a.anio - b.anio)
viewof serieNI = Inputs.select(new Map(Object.entries(SERIES_NI).map(([k, v]) => [v.nombre, k])), {label: "Serie", value: "ipc"})
viewof geoNI = Inputs.select(new Map(geosPaises.map(c => [nombresGeo[c] ?? c, c])), {label: "Territorio", value: "ES"})
```

```{ojs}
//| echo: false
catNI = PRECIOS.catalogoIPC()
datosNI = {
  const s = SERIES_NI[serieNI];
  if (s.tipo === "ipc") {
    if (!catNI) return null;
    let code = catNI.total;
    if (s.patron) { const re = new RegExp(s.patron, "i"); code = [...catNI.codigos].find(([k, l]) => re.test(l))?.[0]; if (!code) return null; }
    const m = await PRECIOS.seriesIPC(catNI, geoNI, [code], 1996);
    return {serie: m.get(code), base: `${catNI.base} = 100`, fuente: `Eurostat (${catNI.tabla})`};
  }
  const r = await cargar(s.spec);
  if (!r.ok) return null;
  return {serie: r.rows.filter(d => d.codigo_territorio === geoNI && /^\d{4}-\d{2}$/.test(d.periodo)).sort((a, b) => a.fecha - b.fecha), base: s.spec.unidad.replace(/^Índice \((.*)\)$/, "$1"), fuente: `Eurostat (${r.code})`};
}
serieN = datosNI?.serie?.length ? datosNI.serie : null
aniosN = serieN ? anuales(serieN).map(d => d.anio) : []
```

```{ojs}
//| echo: false
serieN ? html`<p class="source">${SERIES_NI[serieNI].nombre} en ${nombresGeo[geoNI] ?? geoNI}: ${serieN.length} datos mensuales, de ${PRECIOS.mesTexto(serieN[0].periodo)} a ${PRECIOS.mesTexto(serieN.at(-1).periodo)}. Base original: ${datosNI.base}. Fuente: ${datosNI.fuente}.</p>` : html`<p class="pending">${datosNI === undefined ? "Descargando la serie…" : "No hay datos de esta serie para este territorio. Prueba con otra."}</p>`
```

## 1. Cambio de base

Para expresar un índice con otra base se divide cada valor entre el valor (o la media) del nuevo periodo base y se multiplica por 100:

$$I_t^{(\text{nueva base})} = 100 \cdot \frac{I_t}{\bar I_{\text{nueva base}}}$$

El cambio de base no altera las tasas de variación: solo cambia el periodo que vale 100.

```{ojs}
//| echo: false
viewof baseNI = aniosN.length ? Inputs.select(aniosN, {label: "Nueva base (media del año = 100)", value: aniosN.includes(2015) ? 2015 : aniosN[0]}) : Object.assign(html`<span></span>`, {value: null})
```

```{ojs}
//| echo: false
{
  if (!serieN || !baseNI) return html``;
  const mb = mediaAnio(serieN, baseNI), ult = serieN.at(-1);
  const nueva = serieN.map(d => ({...d, nuevo: 100 * d.valor / mb}));
  const filas = nueva.flatMap(d => [{fecha: d.fecha, s: `Base original (${datosNI.base})`, v: d.valor}, {fecha: d.fecha, s: `Nueva base (${baseNI} = 100)`, v: d.nuevo}]);
  const tabla = anuales(serieN).filter(d => d.anio >= baseNI - 2).slice(-12);
  return html`<div class="calc-result"><p class="calc-big">Ejemplo con el último dato (${PRECIOS.mesTexto(ult.periodo)}): ${f2(ult.valor)} en la base original; la media de ${baseNI} fue ${f2(mb)}. En base ${baseNI}: 100 × ${f2(ult.valor)} / ${f2(mb)} = <b>${f2(100 * ult.valor / mb)}</b>.</p>
    <p class="calc-small">Interpretación: en ${PRECIOS.mesTexto(ult.periodo)} el índice está un ${PRECIOS.pct(100 * ult.valor / mb - 100)} por encima (o por debajo) de su nivel medio de ${baseNI}.</p></div>
  ${Plot.plot({title: `${SERIES_NI[serieNI].nombre}: base original y base ${baseNI}`, height: 340, marginLeft: 50, x: {type: "time", label: null}, y: {label: "Índice", grid: true},
    color: {legend: true, range: ["#3C3C3B", "#B5175F"]},
    marks: [Plot.ruleY([100], {stroke: "#bbb"}), Plot.line(filas, {x: "fecha", y: "v", stroke: "s", strokeWidth: 2}), Plot.tip(filas, Plot.pointer({x: "fecha", y: "v", title: d => `${d.s}\n${d.fecha.toLocaleDateString("es-ES", {month: "long", year: "numeric"})}: ${f2(d.v)}`}))]})}
  ${Inputs.table(tabla.map(d => ({Año: String(d.anio), "Base original": f2(d.valor), [`Base ${baseNI}`]: f2(100 * d.valor / mb)})), {layout: "auto", rows: 13})}`;
}
```

## 2. Tasas de variación

```{ojs}
//| echo: false
viewof tasaNI = Inputs.radio(new Map([["Mensual", "m"], ["Interanual", "a"], ["Acumulada en el año", "c"], ["Media anual", "ma"]]), {label: "Tasa", value: "a"})
```

```{ojs}
//| echo: false
{
  if (!serieN) return html``;
  const idx = new Map(serieN.map(d => [d.periodo.slice(0, 7), d.valor]));
  const prev = (p, k) => { const [a, m] = p.split("-").map(Number), t = a * 12 + m - 1 - k; return `${Math.floor(t / 12)}-${String(t % 12 + 1).padStart(2, "0")}`; };
  let filas, formula, ejemplo;
  if (tasaNI === "ma") {
    const an = anuales(serieN);
    filas = an.slice(1).map((d, i) => ({fecha: new Date(d.anio, 6, 1), et: String(d.anio), v: 100 * (d.valor / an[i].valor - 1)}));
    const u = an.at(-1), p = an.at(-2);
    formula = String.raw`T_{\text{media}} = 100\left(\frac{\bar I_{a}}{\bar I_{a-1}} - 1\right)`;
    ejemplo = u && p ? `Media de ${u.anio}: ${f2(u.valor)}; media de ${p.anio}: ${f2(p.valor)}. Tasa = 100 × (${f2(u.valor)} / ${f2(p.valor)} − 1) = ${f2(100 * (u.valor / p.valor - 1))} %.` : "";
  } else {
    const k = tasaNI === "m" ? 1 : tasaNI === "a" ? 12 : null;
    filas = serieN.map(d => { const p = d.periodo.slice(0, 7); const ref = k ? prev(p, k) : `${+p.slice(0, 4) - 1}-12`; const b = idx.get(ref); return b ? {fecha: d.fecha, et: p, v: 100 * (d.valor / b - 1), ref, b, I: d.valor} : null; }).filter(Boolean);
    const u = filas.at(-1);
    formula = tasaNI === "m" ? String.raw`T_{t,t-1} = 100\left(\frac{I_t}{I_{t-1}} - 1\right)` : tasaNI === "a" ? String.raw`T_{t,t-12} = 100\left(\frac{I_t}{I_{t-12}} - 1\right)` : String.raw`T_{\text{acum}} = 100\left(\frac{I_t}{I_{\text{dic. año anterior}}} - 1\right)`;
    ejemplo = u ? `${PRECIOS.mesTexto(u.et)}: ${f2(u.I)}; ${PRECIOS.mesTexto(u.ref)}: ${f2(u.b)}. Tasa = 100 × (${f2(u.I)} / ${f2(u.b)} − 1) = ${f2(u.v)} %.` : "";
  }
  const ult = filas.slice(tasaNI === "ma" ? -25 : -61);
  let formulaEl; try { formulaEl = tex.block`${formula}`; } catch (e) { formulaEl = html`<code>${formula}</code>`; }
  return html`<div class="calc-result">${formulaEl}<p class="calc-small">${ejemplo}</p></div>
  ${Plot.plot({title: `Tasa de variación ${{m: "mensual", a: "interanual", c: "acumulada en el año", ma: "media anual"}[tasaNI]} (%)`, height: 320, marginLeft: 45, x: {type: tasaNI === "ma" ? "band" : "time", label: null, ...(tasaNI === "ma" ? {tickFormat: d => d.getFullYear(), tickRotate: -45} : {})}, y: {label: "%", grid: true},
    marks: [Plot.ruleY([0]), Plot.rectY(ult, tasaNI === "ma" ? {x: "fecha", y: "v", fill: d => d.v >= 0 ? "#B5175F" : "#3C3C3B"} : {x: "fecha", y: "v", interval: "month", fill: d => d.v >= 0 ? "#B5175F" : "#3C3C3B"}),
      Plot.tip(ult, Plot.pointerX({x: "fecha", y: "v", title: d => `${d.et}: ${f2(d.v)} %`}))]})}`;
}
```

## 3. Enlace (empalme) de series

Cuando un índice cambia de base, la serie antigua y la nueva solo coinciden en el periodo de **solapamiento**. Para tener una serie larga y homogénea se **enlazan**: la serie antigua se multiplica por el **coeficiente de enlace**, el cociente entre las dos series en el periodo común.

$$k = \frac{\bar I^{\text{nueva}}_{\text{solape}}}{\bar I^{\text{antigua}}_{\text{solape}}}, \qquad I^{\text{enlazada}}_t = k \cdot I^{\text{antigua}}_t$$

Aquí se simula: la serie «antigua» tiene base en el año que elijas y termina en el año de solapamiento; la «nueva» empieza ese año con base 100 en él.

```{ojs}
//| echo: false
viewof solapeNI = aniosN.length > 4 ? Inputs.select(aniosN.slice(2, -1), {label: "Año de solapamiento (base de la serie nueva)", value: aniosN.includes(2015) ? 2015 : aniosN[Math.floor(aniosN.length / 2)]}) : Object.assign(html`<span></span>`, {value: null})
viewof baseViejaNI = aniosN.length > 4 ? Inputs.select(aniosN.filter(a => a < (solapeNI ?? 0)), {label: "Base de la serie antigua", value: aniosN.filter(a => a < (solapeNI ?? 0))[0]}) : Object.assign(html`<span></span>`, {value: null})
```

```{ojs}
//| echo: false
{
  if (!serieN || !solapeNI || !baseViejaNI) return html``;
  const mV = mediaAnio(serieN, baseViejaNI), mN = mediaAnio(serieN, solapeNI);
  const vieja = serieN.filter(d => d.fecha.getFullYear() <= solapeNI).map(d => ({...d, v: 100 * d.valor / mV}));
  const nueva = serieN.filter(d => d.fecha.getFullYear() >= solapeNI).map(d => ({...d, v: 100 * d.valor / mN}));
  const solV = d3.mean(vieja.filter(d => d.fecha.getFullYear() === solapeNI), d => d.v), solN = 100;
  const k = solN / solV;
  const filas = [...vieja.map(d => ({fecha: d.fecha, s: `Serie antigua (base ${baseViejaNI})`, v: d.v})), ...nueva.map(d => ({fecha: d.fecha, s: `Serie nueva (base ${solapeNI})`, v: d.v})),
    ...vieja.filter(d => d.fecha.getFullYear() < solapeNI).map(d => ({fecha: d.fecha, s: "Serie antigua enlazada", v: k * d.v}))];
  return html`<div class="calc-result"><p class="calc-big">Media de ${solapeNI} en la serie antigua: ${f2(solV)}; en la nueva: 100. Coeficiente de enlace: k = 100 / ${f2(solV)} = <b>${locES.format(",.4f")(k)}</b>.</p>
    <p class="calc-small">Comprobación: la serie enlazada coincide con la que se obtiene cambiando directamente la base a ${solapeNI}, porque aquí las dos series proceden de los mismos datos. En la práctica, cuando cambia la cesta o el método, el enlace introduce una pequeña discontinuidad.</p></div>
  ${Plot.plot({title: "Enlace de una serie antigua y una nueva", height: 340, marginLeft: 50, x: {type: "time", label: null}, y: {label: "Índice", grid: true},
    color: {legend: true, domain: [`Serie antigua (base ${baseViejaNI})`, `Serie nueva (base ${solapeNI})`, "Serie antigua enlazada"], range: ["#9E9E9E", "#B5175F", "#F29200"]},
    marks: [Plot.ruleY([100], {stroke: "#ddd"}), Plot.line(filas, {x: "fecha", y: "v", stroke: "s", strokeWidth: 2, strokeDasharray: d => d.s === "Serie antigua enlazada" ? "5,3" : null}), Plot.ruleX([new Date(solapeNI, 0, 1), new Date(solapeNI, 11, 31)], {stroke: "#999", strokeDasharray: "2,2"})]})}`;
}
```

## 4. Deflactar: de euros corrientes a euros constantes

Una magnitud en euros corrientes (**nominal**) mezcla el cambio de su valor real con el de los precios. Para expresarla en euros de un año concreto (**real**) se divide entre el índice de precios:

$$X^{\text{real}}_t = X^{\text{nominal}}_t \cdot \frac{\text{IPC}_{\text{base}}}{\text{IPC}_t}$$

```{ojs}
//| echo: false
viewof nomNI = Inputs.select(new Map([...Object.entries(NOMINALES_NI).map(([k, v]) => [v.nombre, k]), ["Mis datos (año;valor)", "propios"]]), {label: "Magnitud nominal", value: "renta"})
viewof propiosNI = nomNI === "propios" ? Inputs.textarea({label: "Tus datos: una línea por año, «año;valor»", value: "2010;1200\n2015;1300\n2020;1450\n2024;1700", rows: 5}) : Object.assign(html`<span></span>`, {value: ""})
```

```{ojs}
//| echo: false
nominalNI = {
  if (nomNI === "propios") return {nombre: "Tus datos", unidad: "€", filas: propiosNI.split(/\n/).map(l => l.split(/[;\t]/)).map(([a, v]) => ({anio: +a, valor: +String(v ?? "").replace(/\./g, "").replace(",", ".")})).filter(d => d.anio > 1990 && Number.isFinite(d.valor))};
  const s = NOMINALES_NI[nomNI], r = await cargar(s);
  if (!r.ok) return null;
  const f = [...d3.rollup(r.rows.filter(d => d.codigo_territorio === geoNI), v => d3.mean(v, d => d.valor), d => d.fecha.getFullYear())].map(([anio, valor]) => ({anio, valor})).sort((a, b) => a.anio - b.anio);
  return {nombre: s.nombre, unidad: s.unidad, filas: f};
}
ipcAnualNI = {
  if (!catNI) return null;
  const m = await PRECIOS.seriesIPC(catNI, geoNI, [catNI.total], 1996);
  return new Map(anuales(m.get(catNI.total)).map(d => [d.anio, d.valor]));
}
```

```{ojs}
//| echo: false
{
  if (!nominalNI || !ipcAnualNI) return html`<p class="pending">Cargando los datos…</p>`;
  const f = nominalNI.filas.filter(d => ipcAnualNI.has(d.anio));
  if (f.length < 2) return html`<p class="pending">No hay datos suficientes de esta magnitud para ${nombresGeo[geoNI] ?? geoNI}.</p>`;
  const base = f.at(-1).anio, ib = ipcAnualNI.get(base);
  const t = f.map(d => ({...d, real: d.valor * ib / ipcAnualNI.get(d.anio), ipc: ipcAnualNI.get(d.anio)}));
  const a = t[0], b = t.at(-1);
  const filas = t.flatMap(d => [{anio: d.anio, s: "Nominal (euros de cada año)", v: d.valor}, {anio: d.anio, s: `Real (euros de ${base})`, v: d.real}]);
  return html`<div class="calc-result"><p class="calc-big">Entre ${a.anio} y ${b.anio}, ${nominalNI.nombre.toLowerCase()} creció un <b>${PRECIOS.pct(100 * (b.valor / a.valor - 1))}</b> en euros corrientes, pero solo un <b>${PRECIOS.pct(100 * (b.real / a.real - 1))}</b> en términos reales: los precios subieron un ${PRECIOS.pct(100 * (b.ipc / a.ipc - 1))}.</p>
    <p class="calc-small">Ejemplo para ${a.anio}: ${f2(a.valor)} × ${f2(ib)} / ${f2(a.ipc)} = ${f2(a.real)} euros de ${base}. IPC: media anual del IPCA de ${nombresGeo[geoNI] ?? geoNI}.</p></div>
  ${Plot.plot({title: `${nominalNI.nombre}: nominal y real`, height: 320, marginLeft: 60, x: {label: null, tickFormat: d => String(d)}, y: {label: nominalNI.unidad, grid: true},
    color: {legend: true, range: ["#3C3C3B", "#B5175F"]}, marks: [Plot.line(filas, {x: "anio", y: "v", stroke: "s", strokeWidth: 2, marker: "circle"}), Plot.tip(filas, Plot.pointer({x: "anio", y: "v", title: d => `${d.s}\n${d.anio}: ${f2(d.v)}`}))]})}`;
}
```

## 5. Índices de Laspeyres, Paasche y Fisher

Un índice de precios **compuesto** resume la evolución de varios productos ponderándolos por las cantidades. **Laspeyres** usa las cantidades del periodo base, **Paasche** las del periodo actual y **Fisher** es la media geométrica de ambos. El IPC es, en esencia, un índice de tipo Laspeyres encadenado. Cambia la cesta para ver cómo varían.

```{ojs}
//| echo: false
viewof cestaNI = Inputs.textarea({label: "Cesta: producto;p0;q0;p1;q1 (precio y cantidad en el periodo base, 0, y en el actual, 1)", rows: 6,
  value: "Pan;1,00;60;1,20;55\nLeche;0,80;100;1,05;95\nGasolina;1,30;500;1,55;420\nCine;7,00;8;9,00;10\nCafé en el bar;1,20;150;1,50;160"})
```

```{ojs}
//| echo: false
{
  const num = (x) => +String(x ?? "").trim().replace(",", ".");
  const c = cestaNI.split(/\n/).map(l => l.split(/[;\t]/)).filter(x => x.length >= 5).map(([n, p0, q0, p1, q1]) => ({n: n.trim(), p0: num(p0), q0: num(q0), p1: num(p1), q1: num(q1)})).filter(d => [d.p0, d.q0, d.p1, d.q1].every(x => Number.isFinite(x) && x >= 0));
  if (!c.length) return html`<p class="pending">Escribe al menos un producto con sus cuatro números.</p>`;
  const S = (f) => d3.sum(c, f);
  const p0q0 = S(d => d.p0 * d.q0), p1q0 = S(d => d.p1 * d.q0), p0q1 = S(d => d.p0 * d.q1), p1q1 = S(d => d.p1 * d.q1);
  const L = 100 * p1q0 / p0q0, P = 100 * p1q1 / p0q1, F = Math.sqrt(L * P), V = 100 * p1q1 / p0q0, Lq = 100 * p0q1 / p0q0, Pq = 100 * p1q1 / p1q0;
  return html`${Inputs.table([...c.map(d => ({Producto: d.n, "p0·q0": f2(d.p0 * d.q0), "p1·q0": f2(d.p1 * d.q0), "p0·q1": f2(d.p0 * d.q1), "p1·q1": f2(d.p1 * d.q1), "Variación del precio": PRECIOS.pct(100 * (d.p1 / d.p0 - 1))})),
      {Producto: "Total", "p0·q0": f2(p0q0), "p1·q0": f2(p1q0), "p0·q1": f2(p0q1), "p1·q1": f2(p1q1), "Variación del precio": ""}], {layout: "auto"})}
  <div class="kpi-grid">
    <div class="kpi"><div class="kpi-l">Laspeyres de precios</div><div class="kpi-n">${f2(L)}</div><div class="kpi-s">100 · Σp1q0 / Σp0q0</div></div>
    <div class="kpi"><div class="kpi-l">Paasche de precios</div><div class="kpi-n">${f2(P)}</div><div class="kpi-s">100 · Σp1q1 / Σp0q1</div></div>
    <div class="kpi"><div class="kpi-l">Fisher de precios</div><div class="kpi-n">${f2(F)}</div><div class="kpi-s">√(Laspeyres · Paasche)</div></div>
    <div class="kpi"><div class="kpi-l">Índice de valor</div><div class="kpi-n">${f2(V)}</div><div class="kpi-s">100 · Σp1q1 / Σp0q0</div></div>
  </div>
  <p class="calc-small">Comprobación: índice de valor = Laspeyres de precios × Paasche de cantidades / 100 = ${f2(L)} × ${f2(Pq)} / 100 = ${f2(L * Pq / 100)}; y también = Paasche de precios × Laspeyres de cantidades / 100 = ${f2(P)} × ${f2(Lq)} / 100 = ${f2(P * Lq / 100)}. ${L > P ? "Laspeyres supera a Paasche: los consumidores han sustituido los productos que más se encarecen por otros, y Laspeyres, al mantener la cesta fija, sobrestima la subida del coste de la vida." : L < P ? "Paasche supera a Laspeyres: la cantidad consumida ha crecido más en los productos que más se encarecen." : ""}</p>`;
}
```

## 6. Ponte a prueba

```{ojs}
//| echo: false
viewof nuevoEj = Inputs.button("🎲 Nuevo ejercicio", {value: 0, reduce: v => v + 1})
```

```{ojs}
//| echo: false
{
  nuevoEj;
  if (!serieN || serieN.length < 30) return html`<p class="pending">Elige una serie con datos para generar ejercicios.</p>`;
  const r = () => Math.random();
  const i = 13 + Math.floor(r() * (serieN.length - 13)), d = serieN[i], d12 = serieN[i - 12], d1 = serieN[i - 1];
  const an = anuales(serieN), ab = an[Math.floor(r() * an.length)];
  const tipos = [
    {t: `El índice ${SERIES_NI[serieNI].nombre} de ${nombresGeo[geoNI] ?? geoNI} valía <b>${f2(d.valor)}</b> en ${PRECIOS.mesTexto(d.periodo)} y <b>${f2(d12.valor)}</b> doce meses antes. ¿Cuál es la tasa de variación interanual (en %)?`, sol: 100 * (d.valor / d12.valor - 1), exp: `100 × (${f2(d.valor)} / ${f2(d12.valor)} − 1)`},
    {t: `El índice valía <b>${f2(d.valor)}</b> en ${PRECIOS.mesTexto(d.periodo)} y <b>${f2(d1.valor)}</b> el mes anterior. ¿Cuál es la tasa de variación mensual (en %)?`, sol: 100 * (d.valor / d1.valor - 1), exp: `100 × (${f2(d.valor)} / ${f2(d1.valor)} − 1)`},
    {t: `El índice valía <b>${f2(d.valor)}</b> en ${PRECIOS.mesTexto(d.periodo)}, y su media de ${ab.anio} fue <b>${f2(ab.valor)}</b>. ¿Cuánto vale en ${PRECIOS.mesTexto(d.periodo)} con base ${ab.anio} = 100?`, sol: 100 * d.valor / ab.valor, exp: `100 × ${f2(d.valor)} / ${f2(ab.valor)}`},
    {t: `Un salario era de <b>${locES.format(",.0f")(1000 + 50 * Math.round(r() * 20))} €</b> cuando el índice de precios valía <b>${f2(d12.valor)}</b>. Si hoy el índice vale <b>${f2(d.valor)}</b>, ¿qué salario nominal mantendría el mismo poder adquisitivo (en €)?`, sol: null, exp: ""}
  ];
  const k = Math.floor(r() * tipos.length), q = tipos[k];
  if (q.sol === null) { const s = +q.t.match(/<b>([\d.]+) €<\/b>/)[1].replace(/\./g, ""); q.sol = s * d.valor / d12.valor; q.exp = `${locES.format(",.0f")(s)} × ${f2(d.valor)} / ${f2(d12.valor)}`; }
  const inp = html`<input type="text" inputmode="decimal" placeholder="Tu respuesta" style="width:9rem;font-size:1.1rem;padding:.3rem .5rem">`;
  const fb = html`<div></div>`, b = html`<button class="asis-boton">Comprobar</button>`;
  b.onclick = () => {
    const v = +inp.value.replace(/\s|%|€/g, "").replace(/\.(?=\d{3}\b)/g, "").replace(",", ".");
    const ok = Number.isFinite(v) && Math.abs(v - q.sol) <= Math.max(0.06, Math.abs(q.sol) * 0.002);
    fb.innerHTML = `<p class="${ok ? "mem-ok" : "mem-ko"}">${ok ? "✔ ¡Correcto!" : "✘ No es correcto."} Solución: ${q.exp} = <b>${f2(q.sol)}</b>.</p>`;
  };
  return html`<div class="calc-result"><p>${html`<span>${Object.assign(document.createElement("span"), {innerHTML: q.t})}</span>`}</p><div class="graf-botones">${inp}${b}</div>${fb}<p class="calc-small">Redondea a dos decimales. Se acepta un margen pequeño de redondeo.</p></div>`;
}
```

::: {.callout-tip appearance="simple"}
**Para clase.** Todo lo que se ve aquí puede comprobarse en una hoja de cálculo: descarga la serie desde la [calculadora de inflación](calculadora.qmd) o el [comparador](comparador.qmd) y repite las cuentas. Para practicar con el IPC por productos, usa [Precios de productos](precios-productos.qmd).
:::
''', SERIES=J(NI_SERIES), NOMINALES=J(NI_NOMINALES), PRECIOS=PRECIOS)

# =====================================================================================
# 6. Generador de ideas para TFG y TFM
# =====================================================================================
pagina("ideas-tfg.qmd", r'''---
title: "Ideas para tu TFG o TFM"
subtitle: "Generador de temas de investigación con datos de CCEEscopio: pregunta, hipótesis, datos, método y estructura"
toc: false
---

Elige tu titulación, el nivel y, si quieres, un área o una palabra clave. El generador combina **temas**, **ámbitos territoriales**, **periodos** y **métodos** para proponer ideas de trabajo que se pueden hacer con datos públicos, la mayoría disponibles en CCEEscopio. Cada idea es un **punto de partida**.

::: {.callout-warning appearance="simple"}
**Importante.** Estas líneas de investigación son solo **propuestas orientativas**, que no tienen por qué funcionar. Antes de empezar, consulta con tu **tutor o tutora de TFG o TFM** para confirmar su viabilidad.
:::

```{ojs}
//| echo: false
IDEAS = ({temas: __TEMAS__, metodos: __METODOS__, ambitos: __AMBITOS__, periodos: __PERIODOS__, titulaciones: __TITULACIONES__})
viewof titIdea = Inputs.select(new Map([["Cualquier titulación", "todas"], ...Object.entries(IDEAS.titulaciones)]), {label: "Titulación"})
viewof nivelIdea = Inputs.radio(new Map([["TFG", "grado"], ["TFM", "master"]]), {label: "Trabajo", value: "grado"})
viewof areaIdea = Inputs.select(["Todas las áreas", ...[...new Set(IDEAS.temas.map(t => t.area))].sort()], {label: "Área"})
viewof buscaIdea = Inputs.text({label: "Palabra clave (opcional)", placeholder: "p. ej. vivienda, turismo, inflación, desigualdad"})
viewof otraIdea = Inputs.button("🎲 Generar nuevas ideas", {value: 0, reduce: v => v + 1})
```

```{ojs}
//| echo: false
temasIdea = {
  const q = buscaIdea.trim().toLowerCase().normalize("NFD").replace(/\p{Diacritic}/gu, "");
  const norm = (s) => s.toLowerCase().normalize("NFD").replace(/\p{Diacritic}/gu, "");
  return IDEAS.temas.filter(t => (titIdea === "todas" || t.tit.includes(titIdea)) && (areaIdea === "Todas las áreas" || t.area === areaIdea) &&
    (!q || norm(JSON.stringify([t.titulos, t.preguntas, t.claves, t.area, t.datos.map(d => d[0])])).includes(q)));
}
combinacionesIdea = d3.sum(temasIdea, t => t.titulos.length * t.ambitos.length * t.periodos.length * Math.max(1, t.metodos.filter(m => nivelIdea === "master" || IDEAS.metodos[m].nivel !== "master").length))
```

```{ojs}
//| echo: false
ideasGen = {
  otraIdea;
  const azar = (a) => a[Math.floor(Math.random() * a.length)];
  const pool = d3.shuffle([...temasIdea]);
  return pool.slice(0, 4).map(t => {
    const amb = azar(t.ambitos), per = azar(t.periodos);
    const A = IDEAS.ambitos[amb], P = IDEAS.periodos[per];
    let mets = t.metodos.filter(m => nivelIdea === "master" || IDEAS.metodos[m].nivel !== "master");
    if (nivelIdea === "master") { const av = mets.filter(m => IDEAS.metodos[m].nivel !== "grado"); if (av.length) mets = av; }
    const metodo = azar(mets.length ? mets : t.metodos), M = IDEAS.metodos[metodo];
    const extra = d3.shuffle(t.metodos.filter(m => m !== metodo && (nivelIdea === "master" || IDEAS.metodos[m].nivel !== "master"))).slice(0, 1);
    const rellena = (s) => s.replaceAll("{ambito}", A.texto).replaceAll("{periodo}", P.texto).replaceAll("{territorio}", A.corto);
    const i = Math.floor(Math.random() * t.titulos.length);
    return {t, titulo: rellena(t.titulos[i]), pregunta: rellena(t.preguntas[i % t.preguntas.length]), hipotesis: rellena(azar(t.hipotesis)), A, P, M, extra: extra.map(m => IDEAS.metodos[m]),
      dificultad: M.nivel === "master" ? "Alta" : M.nivel === "ambos" ? "Media" : "Asequible"};
  });
}
```

```{ojs}
//| echo: false
{
  if (!temasIdea.length) return html`<p class="pending">No hay temas con esos filtros. Prueba con otra palabra clave u otra área.</p>`;
  const tarjeta = (x) => {
    const texto = `${x.titulo}\n\nPregunta de investigación: ${x.pregunta}\nHipótesis: ${x.hipotesis}\nÁmbito: ${x.A.texto}. Periodo: ${x.P.texto} (${x.P.nota}).\nDatos: ${x.t.datos.map(d => d[0]).join("; ")}.\nMétodo: ${x.M.nombre}. ${x.M.desc}\nPalabras clave para buscar bibliografía: ${x.t.claves.join(", ")}.\nPosibles ampliaciones: ${x.t.extensiones.join(" ")}`;
    const copiar = html`<button class="copiar">📋 Copiar la idea</button>`;
    copiar.onclick = async () => { try { await navigator.clipboard.writeText(texto); copiar.textContent = "✔ Copiada"; } catch (e) { copiar.textContent = "No se ha podido copiar"; } };
    return html`<div class="idea-card">
      <p class="idea-meta"><span class="idea-tag">${x.t.area}</span><span class="idea-tag idea-dif">Dificultad: ${x.dificultad}</span></p>
      <h3>${x.titulo}</h3>
      <p><b>Pregunta de investigación.</b> ${x.pregunta}</p>
      <p><b>Hipótesis de partida.</b> ${x.hipotesis}</p>
      <p><b>Ámbito y periodo.</b> ${x.A.texto[0].toUpperCase() + x.A.texto.slice(1)}, ${x.P.texto}: ${x.P.nota}.</p>
      <p><b>Datos.</b></p><ul>${x.t.datos.map(([n, url]) => html`<li>${url ? html`<a href="${url}">${n}</a>` : n}</li>`)}</ul>
      <p><b>Método.</b> ${x.M.nombre}. ${x.M.desc}${x.M.herramienta ? html` Puedes empezar con <a href="${x.M.herramienta[1]}">${x.M.herramienta[0]}</a>.` : ""}</p>
      ${x.extra.length ? html`<p><b>Para completar el análisis.</b> ${x.extra.map(m => m.nombre).join("; ")}.</p>` : ""}
      <p><b>Estructura sugerida.</b> 1. Introducción y motivación · 2. Revisión de la literatura · 3. Datos y fuentes · 4. Metodología · 5. Resultados · 6. Conclusiones${x.t.politica ? " y recomendaciones de política" : x.t.empresa ? " e implicaciones para la empresa" : ""}.</p>
      <p><b>Para buscar bibliografía</b> (Google Scholar, Dialnet, Scopus): <i>${x.t.claves.join(" · ")}</i>.</p>
      <p><b>Posibles ampliaciones.</b> ${x.t.extensiones.join(" ")}</p>
      <div class="graf-botones">${copiar}</div></div>`;
  };
  return html`<p class="source">${temasIdea.length} temas y más de ${combinacionesIdea.toLocaleString("es-ES")} combinaciones posibles con estos filtros. Pulsa «Generar nuevas ideas» para ver otras.</p><div class="idea-grid">${ideasGen.map(tarjeta)}</div>`;
}
```

::: {.callout-note appearance="simple"}
**Consejos para elegir.** Una buena pregunta de investigación es **concreta** (un fenómeno, un ámbito y un periodo), **respondible con datos** que puedas conseguir y **relevante** (alguien querría saber la respuesta). Antes de decidirte, comprueba en CCEEscopio que los datos existen para tu ámbito y periodo, y busca dos o tres artículos recientes sobre el tema. Para citar los datos, usa el [generador de gráficos para el TFG](graficos.qmd), que da la referencia en formato APA.
:::
''', TEMAS=J(TEMAS), METODOS=J(METODOS), AMBITOS=J(AMBITOS), PERIODOS=J(PERIODOS), TITULACIONES=J(TITULACIONES))
print("Listo")
