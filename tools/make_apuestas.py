# -*- coding: utf-8 -*-
"""Genera apuestas.qmd (juego «Apuesta y acierta» con código QR).

Cada estudiante empieza con el mismo saldo y, en cada pregunta, apuesta 10, 20, 50 o 100 euros
antes de responder: si acierta gana lo apostado y si falla lo pierde. Gana quien termine con más dinero.

Reutiliza de concurso.qmd las funciones comunes, el generador de preguntas con datos de Eurostat y la
conexión con el servicio de mensajería. Ejecutar desde la raíz del proyecto, después de generar concurso.qmd:

    python3 tools/make_apuestas.py
"""

src = open("concurso.qmd", encoding="utf-8").read()

# Todo lo que hay en concurso.qmd hasta el final del bloque que define especC, BROKERS y los temas
fin = src.index("temaJug = (s) =>")
fin = src.index("```", fin) + 3
comun = src[src.index("```{ojs}"):fin]
comun = comun.replace("cceescopio/concurso/", "cceescopio/apuestas/")
assert "generarSerie" in comun and "conectarBroker" in comun and "CONC = {" in comun

CABECERA = '''---
title: "Apuesta y acierta"
subtitle: "Juego para clase con código QR: cada estudiante apuesta 10, 20, 50 o 100 euros en cada pregunta y gana quien termine con más dinero"
toc: false
---

'''

PROPIO = r'''

```{ojs}
//| echo: false
// Reglas del juego (sin dependencias del navegador, para poder probarlas)
APU = {
  const apuestas = [10, 20, 50, 100];
  // Saldo tras una pregunta: se gana lo apostado si se acierta y se pierde si se falla
  const saldoTras = (saldo, apuesta, bien) => saldo + (bien ? apuesta : -apuesta);
  // Solo se puede apostar lo que se tiene; con menos de 10 € el estudiante queda eliminado
  const posibles = (saldo) => apuestas.filter(a => a <= saldo);
  const eliminado = (saldo) => saldo < apuestas[0];
  // Ranking: más dinero; a igualdad, más aciertos; después, menos tiempo
  const ordenar = (jug) => [...jug.values()].sort((a, b) => (b.saldo - a.saldo) || ((b.aciertos ?? 0) - (a.aciertos ?? 0)) || (a.tiempo - b.tiempo) || a.alias.localeCompare(b.alias));
  const euros = (v) => `${Math.round(v).toLocaleString("es-ES")} €`;
  return {apuestas, saldoTras, posibles, eliminado, ordenar, euros};
}
```

```{ojs}
//| echo: false
// ============================ PANTALLA DEL PROFESOR ============================
viewof areaA = SALA ? Object.assign(html`<span></span>`, {value: null}) : Inputs.select(new Map([["Todas las áreas", "todas"], ...Object.entries(areasC).map(([k, v]) => [v, k])]), {label: "Tema de las preguntas"})
viewof nA = SALA ? Object.assign(html`<span></span>`, {value: null}) : Inputs.range([5, 20], {label: "Número de preguntas", value: 10, step: 1})
viewof saldoA = SALA ? Object.assign(html`<span></span>`, {value: null}) : Inputs.select(new Map([["100 €", 100], ["200 €", 200], ["500 €", 500], ["1.000 €", 1000]]), {label: "Dinero inicial de cada estudiante", value: 200})
viewof abrirA = SALA ? Object.assign(html`<span></span>`, {value: 0}) : Inputs.button("▶ Abrir partida", {value: 0, reduce: v => v + 1})
```

```{ojs}
//| echo: false
{
  if (SALA) return html``;
  if (!abrirA) return html`<div class="conc-intro">
    <p><b>Cómo se juega.</b> Elige el tema, el número de preguntas y el dinero inicial, pulsa «Abrir partida» y proyecta esta pantalla. Los estudiantes escanean el código QR y escriben un <b>alias</b>. Cuando estén todos, pulsa «Empezar».</p>
    <ol>
      <li>Todos empiezan con el mismo dinero y responden las mismas preguntas, con datos reales de Eurostat.</li>
      <li>En cada pregunta, el estudiante lee el enunciado y <b>apuesta 10, 20, 50 o 100 euros</b> antes de ver las opciones. Solo puede apostar el dinero que tiene.</li>
      <li>Si <b>acierta</b>, gana lo apostado; si <b>falla</b>, lo pierde.</li>
      <li>Quien se queda con menos de 10 euros queda eliminado.</li>
    </ol>
    <p><b>Gana quien tenga más dinero al final.</b> En la pantalla verás el ranking en directo, ordenado por dinero y, a igualdad, por aciertos y por el tiempo empleado. El juego premia saber y también saber cuánto se sabe: apostar fuerte solo cuando se está seguro.</p>
    <p class="nota">Los resultados viajan por un servicio público de mensajería en tiempo real y no se guardan en ningún sitio. Antes de usarlo en clase por primera vez, haz una prueba con tu móvil: si la red del aula bloquea la conexión, la página lo indicará.</p></div>`;
  const caja = html`<div class="conc-panel"><p class="pending">Preparando las preguntas con los datos de Eurostat…</p></div>`;
  (async () => {
    const pool = especC.filter(s => !s.sinGeo && !s.regional && (areaA === "todas" || s.pagina === areaA));
    const sala = CONC.nuevaSala();
    const qs = await generarSerie(pool, ["test", "vf", "test"], nA, `apuestas-${sala}`);
    if (qs.length < nA) { caja.innerHTML = `<p class="pending">No se han podido preparar suficientes preguntas (¿hay conexión con Eurostat?). Prueba con «Todas las áreas» o inténtalo de nuevo.</p>`; return; }
    caja.innerHTML = `<p class="pending">Conectando con el servicio de mensajería…</p>`;
    let cli = null, broker = null;
    for (const b of BROKERS) { try { cli = await conectarBroker(b); broker = b; break; } catch (e) {} }
    if (!cli) { caja.innerHTML = `<p class="pending">❌ No se ha podido conectar con ningún servicio de mensajería. Es posible que la red bloquee estas conexiones: prueba con otra red (por ejemplo, los datos del móvil compartidos).</p>`; return; }
    const preguntas = qs.slice(0, nA).map((q, i) => ({e: q.enunciado, o: q.opciones, c: CONC.ofuscar(sala, i, q.respuesta, q.opciones.length), s: q.solucion}));
    const N = preguntas.length, S0 = saldoA;
    const publicar = (estado) => cli.publish(temaEstado(sala), JSON.stringify(estado), {retain: true, qos: 1});
    publicar({fase: "espera", preguntas, saldo: S0});
    const jug = new Map();
    let fase = "espera";
    cli.subscribe(temaJug(sala), {qos: 1});
    const enlace = `${location.href.split("?")[0].split("#")[0]}?sala=${sala}&b=${broker.id}`;
    caja.innerHTML = "";
    caja.append(html`<div class="conc-cab"><div class="conc-qr"></div><div><p class="asis-et">Escanea el código o entra en</p><p class="conc-url">${enlace.replace(/^https?:\/\//, "")}</p>
        <p class="conc-cuenta">0 participantes</p>
        <p class="ppt-meta"><b>${N}</b> preguntas · dinero inicial: <b>${APU.euros(S0)}</b> · apuestas de 10, 20, 50 o 100 €</p>
        <div class="graf-botones"><button class="asis-boton conc-empezar">▶ Empezar</button><button class="copiar conc-terminar" disabled>🏁 Terminar</button><button class="copiar conc-full">⛶ Pantalla completa</button></div></div></div>
      <div class="conc-ranking"></div>`);
    const $ = (s) => caja.querySelector(s);
    try { const qrlib = await require("qrcode-generator@1.4.4"); const qr = qrlib(0, "M"); qr.addData(enlace); qr.make(); $(".conc-qr").innerHTML = qr.createSvgTag({cellSize: 6, margin: 2, scalable: true}); } catch (e) { $(".conc-qr").textContent = "(no se ha podido crear el QR)"; }
    const pintar = () => {
      const r = APU.ordenar(jug);
      $(".conc-cuenta").textContent = `${jug.size} participante${jug.size === 1 ? "" : "s"}`;
      if (fase === "espera") { $(".conc-ranking").innerHTML = `<div class="conc-alias">${r.map(j => `<span>${j.alias}</span>`).join("")}</div>`; return; }
      const medalla = (i) => fase === "fin" ? ["🥇", "🥈", "🥉"][i] ?? `${i + 1}.` : `${i + 1}.`;
      const dif = (j) => { const d = j.saldo - S0; return `<span class="apu-dif ${d >= 0 ? "sube" : "baja"}">${d >= 0 ? "+" : "−"}${APU.euros(Math.abs(d))}</span>`; };
      const estadoJ = (j) => j.elim ? "💸 eliminado" : j.fin ? "✔" : `${j.respondidas ?? 0} / ${N}`;
      $(".conc-ranking").innerHTML = `${fase === "fin" ? `<h2 class="conc-podio">🏆 ${r[0] ? r[0].alias : ""}</h2>` : ""}<table class="uso-tabla conc-tabla"><tr><th></th><th>Alias</th><th>Dinero</th><th>Ganancia</th><th>Aciertos · fallos</th><th>Preguntas</th><th>Tiempo</th></tr>` +
        r.slice(0, 15).map((j, i) => `<tr class="${i < 3 && fase === "fin" ? "conc-top" : ""}"><td>${medalla(i)}</td><td>${j.alias}</td><td><b>${APU.euros(j.saldo)}</b></td><td>${dif(j)}</td><td>${j.aciertos ?? 0} · ${j.fallos ?? 0}</td><td>${estadoJ(j)}</td><td>${j.tiempo ? CONC.segundos(j.tiempo) : "–"}</td></tr>`).join("") + "</table>";
    };
    cli.on("message", (t, m) => { try { const d = JSON.parse(m.toString()); if (!d.id || !d.alias) return; const prev = jug.get(d.id) ?? {saldo: S0, tiempo: 0};
      // El saldo no puede superar el máximo posible ni ser negativo
      const saldo = Math.min(S0 + 100 * N, Math.max(0, Math.round(+d.saldo)));
      jug.set(d.id, {...prev, ...d, saldo: Number.isFinite(saldo) ? saldo : prev.saldo, alias: String(d.alias).slice(0, 20).replace(/[<>&"]/g, "")}); pintar(); } catch (e) {} });
    $(".conc-empezar").onclick = () => { fase = "juego"; publicar({fase: "juego", preguntas, saldo: S0, inicio: Date.now()}); $(".conc-empezar").disabled = true; $(".conc-terminar").disabled = false; pintar();
      window.cceeEvento && window.cceeEvento("apuestas/empezar", "Apuesta y acierta", true); };
    $(".conc-terminar").onclick = () => { fase = "fin"; const r = APU.ordenar(jug).slice(0, 10).map(j => ({alias: j.alias, saldo: j.saldo}));
      publicar({fase: "fin", preguntas, saldo: S0, ranking: r}); $(".conc-terminar").disabled = true; pintar();
      caja.append(DOM.download(() => new Blob([csv(APU.ordenar(jug).map((j, i) => ({puesto: i + 1, alias: j.alias, dinero_final: j.saldo, dinero_inicial: S0, ganancia: j.saldo - S0, aciertos: j.aciertos ?? 0, fallos: j.fallos ?? 0, preguntas_respondidas: j.respondidas ?? 0, preguntas: N, eliminado: j.elim ? "sí" : "no", tiempo_segundos: Math.round(j.tiempo / 100) / 10})))], {type: "text/csv"}), `apuesta_y_acierta_${sala}.csv`, "⬇ Descargar los resultados (CSV)")); };
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
  const caja = html`<div class="conc-movil"><p class="pending">Conectando con la partida…</p></div>`;
  (async () => {
    let cli;
    try { cli = await conectarBroker(broker); } catch (e) { caja.innerHTML = `<p class="pending">❌ No se ha podido conectar. Comprueba la conexión a internet (si estás en la wifi de la universidad, prueba con los datos del móvil) y recarga la página.</p>`; return; }
    let id; try { id = localStorage.getItem(`ccee-apu-${SALA}`) || crypto.randomUUID(); localStorage.setItem(`ccee-apu-${SALA}`, id); } catch (e) { id = crypto.randomUUID(); }
    let alias = ""; try { alias = localStorage.getItem("ccee-conc-alias") || ""; } catch (e) {}
    // k: pregunta actual; apuesta: cantidad elegida en la pregunta actual (null si aún no ha apostado)
    let estado = null, unido = false, saldo = null, k = 0, apuesta = null, t0 = null, ocupado = false, aviso = null;
    let aciertos = 0, fallos = 0;
    const N = () => estado?.preguntas?.length ?? 0;
    const elim = () => saldo !== null && APU.eliminado(saldo);
    const terminado = () => (N() > 0 && k >= N()) || elim();
    const tiempo = () => t0 ? Date.now() - t0 : 0;
    const enviar = () => cli.publish(temaJug(SALA), JSON.stringify({id, alias, saldo: saldo ?? estado?.saldo ?? 0, aciertos, fallos, respondidas: k, tiempo: tiempo(), fin: terminado(), elim: elim()}), {qos: 1});
    const cabecera = () => html`<div class="apu-cab"><span>Pregunta ${Math.min(k + 1, N())} de ${N()}</span><span class="apu-saldo">💰 ${APU.euros(saldo)}</span><span>⏱ ${CONC.segundos(tiempo())}</span></div>`;
    const pantalla = () => {
      caja.innerHTML = "";
      if (!unido) {
        const f = html`<form class="asis-caja"><label>Tu alias para el ranking<input name="alias" required maxlength="20" autocomplete="off" placeholder="p. ej. Analista_7" value="${alias}"></label><button class="asis-boton">Entrar en la partida</button><p class="asis-nota">No escribas tu nombre real si no quieres que aparezca en la pantalla de clase.</p></form>`;
        f.onsubmit = (ev) => { ev.preventDefault(); alias = f.alias.value.trim().slice(0, 20).replace(/[<>&"]/g, ""); if (!alias) return; try { localStorage.setItem("ccee-conc-alias", alias); } catch (err) {} unido = true; if (estado && saldo === null) saldo = estado.saldo; enviar(); pantalla(); };
        caja.append(f); return;
      }
      if (estado && saldo === null) saldo = estado.saldo;
      if (!estado || estado.fase === "espera") { caja.append(html`<div class="asis-caja conc-espera"><p class="juego-grande">💰</p><p>Hola, <b>${alias}</b>. Empiezas con <b>${APU.euros(estado?.saldo ?? 0)}</b>. Espera a que el profesor empiece la partida…</p><p class="asis-nota">En cada pregunta apuestas 10, 20, 50 o 100 euros antes de ver las opciones: si aciertas, ganas lo apostado; si fallas, lo pierdes. Gana quien termine con más dinero.</p></div>`); return; }
      if (estado.fase === "fin" || terminado()) {
        const pos = estado.ranking ? estado.ranking.findIndex(r => r.alias === alias) : -1;
        const d = saldo - estado.saldo;
        caja.append(html`<div class="asis-caja conc-espera"><p class="juego-grande">${APU.euros(saldo)}</p>
          <p>${d >= 0 ? html`Has ganado <b>${APU.euros(d)}</b>` : html`Has perdido <b>${APU.euros(-d)}</b>`} · Aciertos: ${aciertos} · Fallos: ${fallos} · Tiempo: ${CONC.segundos(tiempo())}</p>
          ${estado.fase === "fin" ? html`<p>${pos >= 0 ? html`Has quedado en el puesto <b>${pos + 1}</b> ${["🥇", "🥈", "🥉"][pos] ?? ""}` : "Mira el ranking en la pantalla de clase."}</p>`
            : elim() ? html`<p>💸 Te has quedado sin dinero para apostar. Mira el ranking en la pantalla de clase.</p>` : html`<p>🏁 Has terminado. Mira el ranking en la pantalla de clase.</p>`}</div>`);
        return;
      }
      if (!t0) t0 = Date.now();
      if (aviso) { caja.append(html`<p class="juego-res ${aviso.bien ? "bien" : "mal"}">${aviso.texto}</p>`); }
      const q = estado.preguntas[k], correcta = CONC.desofuscar(SALA, k, q.c, q.o.length);
      const enunciado = html`<p class="juego-p">${q.e.split("**").map((t, j) => j % 2 ? html`<b>${t}</b>` : t)}</p>`;
      if (apuesta === null) {
        // Primero se apuesta, viendo solo el enunciado
        const botones = html`<div class="apu-botones"></div>`;
        APU.apuestas.forEach(a => { const b = html`<button class="apu-boton">${a} €</button>`; if (a > saldo) b.disabled = true;
          b.onclick = () => { if (ocupado) return; apuesta = a; aviso = null; pantalla(); }; botones.append(b); });
        caja.append(html`<div class="juego">${cabecera()}${enunciado}<p class="apu-pide">¿Cuánto apuestas a que aciertas?</p></div>`, botones);
        return;
      }
      // Después se responde
      const ops = html`<div class="juego-ops juego-ops-v">`;
      q.o.forEach((o, j) => { const b = html`<button class="juego-op">${o}</button>`; b.onclick = () => {
        if (ocupado) return; ocupado = true;
        const bien = j === correcta;
        ops.querySelectorAll("button").forEach((x, m) => { x.disabled = true; if (m === correcta) x.classList.add("ok"); }); if (!bien) b.classList.add("ko");
        saldo = APU.saldoTras(saldo, apuesta, bien);
        if (bien) { aciertos++; aviso = {bien: true, texto: `✅ ¡Correcto! Ganas ${APU.euros(apuesta)}. Ahora tienes ${APU.euros(saldo)}.`}; }
        else { fallos++; aviso = {bien: false, texto: `❌ No es correcta: pierdes ${APU.euros(apuesta)} y te quedan ${APU.euros(saldo)}. ${q.s}`}; }
        k++; apuesta = null;
        enviar();
        setTimeout(() => { ocupado = false; pantalla(); }, bien ? 1200 : 2800);
      }; ops.append(b); });
      caja.append(html`<div class="juego">${cabecera()}${enunciado}<p class="apu-pide">Has apostado <b>${APU.euros(apuesta)}</b>. Elige tu respuesta:</p></div>`, ops);
    };
    cli.subscribe(temaEstado(SALA), {qos: 1});
    cli.on("message", (t, m) => { try { const d = JSON.parse(m.toString()); const antes = estado?.fase; estado = d; if (antes !== d.fase && !ocupado) { aviso = null; pantalla(); } } catch (err) {} });
    invalidation.then(() => { try { cli.end(true); } catch (err) {} });
    pantalla();
  })();
  return caja;
}
```
'''

open("apuestas.qmd", "w", encoding="utf-8").write(CABECERA + comun + PROPIO)
print("apuestas.qmd generado")
