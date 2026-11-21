# -*- coding: utf-8 -*-
"""Genera ppt.qmd (juego «Piedra, papel o tijera» con código QR).

Reutiliza de concurso.qmd las funciones comunes, el generador de preguntas con datos
de Eurostat y la conexión con el servicio de mensajería, de modo que el juego se
mantiene al día si se regenera el concurso. Ejecutar desde la raíz del proyecto,
después de generar concurso.qmd:

    python3 tools/make_ppt.py
"""
import re

src = open("concurso.qmd", encoding="utf-8").read()

# Todo lo que hay en concurso.qmd hasta el final del bloque que define especC, BROKERS y los temas
fin = src.index("temaJug = (s) =>")
fin = src.index("```", fin) + 3
comun = src[src.index("```{ojs}"):fin]
comun = comun.replace("cceescopio/concurso/", "cceescopio/ppt/")
assert "generarSerie" in comun and "conectarBroker" in comun and "CONC = {" in comun

CABECERA = '''---
title: "Piedra, papel o tijera"
subtitle: "Juego para clase con código QR: cada acierto da derecho a una partida contra la aplicación y gana quien antes supere todas las preguntas"
toc: false
---

'''

PROPIO = r'''

```{ojs}
//| echo: false
// Reglas de piedra, papel o tijera (sin dependencias del navegador, para poder probarlas)
PPT = {
  const jugadas = [{id: 0, e: "✊", n: "Piedra"}, {id: 1, e: "✋", n: "Papel"}, {id: 2, e: "✌️", n: "Tijera"}];
  // 1 = gana el estudiante, 0 = empate, -1 = gana la aplicación (el papel gana a la piedra, la tijera al papel y la piedra a la tijera)
  const resultado = (yo, app) => yo === app ? 0 : ((yo - app + 3) % 3 === 1 ? 1 : -1);
  const jugadaApp = () => crypto.getRandomValues(new Uint32Array(1))[0] % 3;
  const ordenar = (jug) => [...jug.values()].sort((a, b) => (b.superadas - a.superadas) || ((b.fin ? 1 : 0) - (a.fin ? 1 : 0)) || (a.tiempo - b.tiempo) || a.alias.localeCompare(b.alias));
  return {jugadas, resultado, jugadaApp, ordenar};
}
```

```{ojs}
//| echo: false
// ============================ PANTALLA DEL PROFESOR ============================
viewof areaP = SALA ? Object.assign(html`<span></span>`, {value: null}) : Inputs.select(new Map([["Todas las áreas", "todas"], ...Object.entries(areasC).map(([k, v]) => [v, k])]), {label: "Tema de las preguntas"})
viewof nP = SALA ? Object.assign(html`<span></span>`, {value: null}) : Inputs.range([3, 15], {label: "Número de preguntas que hay que superar", value: 5, step: 1})
viewof abrirP = SALA ? Object.assign(html`<span></span>`, {value: 0}) : Inputs.button("▶ Abrir partida", {value: 0, reduce: v => v + 1})
```

```{ojs}
//| echo: false
{
  if (SALA) return html``;
  if (!abrirP) return html`<div class="conc-intro">
    <p><b>Cómo se juega.</b> Elige el tema y el número de preguntas, pulsa «Abrir partida» y proyecta esta pantalla. Los estudiantes escanean el código QR y escriben un <b>alias</b>. Cuando estén todos, pulsa «Empezar».</p>
    <ol>
      <li>Cada estudiante empieza por la primera pregunta, con datos reales de Eurostat.</li>
      <li>Si <b>acierta</b>, juega una partida de piedra ✊, papel ✋ o tijera ✌️ contra la aplicación:
        <ul><li><b>Gana</b>: supera la pregunta y pasa a la siguiente.</li>
        <li><b>Empata</b>: juega otra partida.</li>
        <li><b>Pierde</b>: tiene que contestar otra pregunta y sigue en la misma ronda.</li></ul></li>
      <li>Si <b>falla</b> la pregunta, contesta otra y sigue en la misma ronda.</li>
    </ol>
    <p><b>Gana quien antes supere todas las preguntas.</b> En la pantalla verás el ranking en directo, ordenado por preguntas superadas y, a igualdad, por el tiempo empleado.</p>
    <p class="nota">Los resultados viajan por un servicio público de mensajería en tiempo real y no se guardan en ningún sitio. Antes de usarlo en clase por primera vez, haz una prueba con tu móvil: si la red del aula bloquea la conexión, la página lo indicará.</p></div>`;
  const caja = html`<div class="conc-panel"><p class="pending">Preparando las preguntas con los datos de Eurostat…</p></div>`;
  (async () => {
    const pool = especC.filter(s => !s.sinGeo && !s.regional && (areaP === "todas" || s.pagina === areaP));
    const sala = CONC.nuevaSala();
    // Además de las preguntas que hay que superar, una reserva para los fallos y las partidas perdidas
    const qs = await generarSerie(pool, ["test", "vf", "test"], Math.min(nP + 25, 40), `ppt-${sala}`);
    if (qs.length < nP) { caja.innerHTML = `<p class="pending">No se han podido preparar suficientes preguntas (¿hay conexión con Eurostat?). Prueba con «Todas las áreas» o inténtalo de nuevo.</p>`; return; }
    caja.innerHTML = `<p class="pending">Conectando con el servicio de mensajería…</p>`;
    let cli = null, broker = null;
    for (const b of BROKERS) { try { cli = await conectarBroker(b); broker = b; break; } catch (e) {} }
    if (!cli) { caja.innerHTML = `<p class="pending">❌ No se ha podido conectar con ningún servicio de mensajería. Es posible que la red bloquee estas conexiones: prueba con otra red (por ejemplo, los datos del móvil compartidos).</p>`; return; }
    const preguntas = qs.map((q, i) => ({e: q.enunciado, o: q.opciones, c: CONC.ofuscar(sala, i, q.respuesta, q.opciones.length), s: q.solucion}));
    const N = nP;
    const publicar = (estado) => cli.publish(temaEstado(sala), JSON.stringify(estado), {retain: true, qos: 1});
    publicar({fase: "espera", preguntas, n: N});
    const jug = new Map();
    let fase = "espera";
    cli.subscribe(temaJug(sala), {qos: 1});
    const enlace = `${location.href.split("?")[0].split("#")[0]}?sala=${sala}&b=${broker.id}`;
    caja.innerHTML = "";
    caja.append(html`<div class="conc-cab"><div class="conc-qr"></div><div><p class="asis-et">Escanea el código o entra en</p><p class="conc-url">${enlace.replace(/^https?:\/\//, "")}</p>
        <p class="conc-cuenta">0 participantes</p>
        <p class="ppt-meta">Hay que superar <b>${N}</b> preguntas · ✊ ✋ ✌️</p>
        <div class="graf-botones"><button class="asis-boton conc-empezar">▶ Empezar</button><button class="copiar conc-terminar" disabled>🏁 Terminar</button><button class="copiar conc-full">⛶ Pantalla completa</button></div></div></div>
      <div class="conc-ranking"></div>`);
    const $ = (s) => caja.querySelector(s);
    try { const qrlib = await require("qrcode-generator@1.4.4"); const qr = qrlib(0, "M"); qr.addData(enlace); qr.make(); $(".conc-qr").innerHTML = qr.createSvgTag({cellSize: 6, margin: 2, scalable: true}); } catch (e) { $(".conc-qr").textContent = "(no se ha podido crear el QR)"; }
    const pintar = () => {
      const r = PPT.ordenar(jug);
      $(".conc-cuenta").textContent = `${jug.size} participante${jug.size === 1 ? "" : "s"}`;
      if (fase === "espera") { $(".conc-ranking").innerHTML = `<div class="conc-alias">${r.map(j => `<span>${j.alias}</span>`).join("")}</div>`; return; }
      const medalla = (i) => fase === "fin" ? ["🥇", "🥈", "🥉"][i] ?? `${i + 1}.` : `${i + 1}.`;
      const barra = (j) => `<span class="ppt-barra"><span style="width:${Math.round(100 * j.superadas / N)}%"></span></span>`;
      $(".conc-ranking").innerHTML = `${fase === "fin" ? `<h2 class="conc-podio">🏆 ${r[0] ? r[0].alias : ""}</h2>` : ""}<table class="uso-tabla conc-tabla"><tr><th></th><th>Alias</th><th>Preguntas superadas</th><th>Aciertos · fallos</th><th>Partidas ✊✋✌️<br><small>ganadas · empatadas · perdidas</small></th><th>Tiempo</th></tr>` +
        r.slice(0, 15).map((j, i) => `<tr class="${i < 3 && fase === "fin" ? "conc-top" : ""}"><td>${medalla(i)}</td><td>${j.alias}</td><td><b>${j.superadas}</b> / ${N} ${j.fin ? "✔" : barra(j)}</td><td>${j.aciertos ?? 0} · ${j.fallos ?? 0}</td><td>${j.g ?? 0} · ${j.e ?? 0} · ${j.p ?? 0}</td><td>${j.tiempo ? CONC.segundos(j.tiempo) : "–"}</td></tr>`).join("") + "</table>";
    };
    cli.on("message", (t, m) => { try { const d = JSON.parse(m.toString()); if (!d.id || !d.alias) return; const prev = jug.get(d.id) ?? {superadas: 0, tiempo: 0};
      jug.set(d.id, {...prev, ...d, superadas: Math.min(N, Math.max(0, +d.superadas || 0)), alias: String(d.alias).slice(0, 20).replace(/[<>&"]/g, "")}); pintar(); } catch (e) {} });
    $(".conc-empezar").onclick = () => { fase = "juego"; publicar({fase: "juego", preguntas, n: N, inicio: Date.now()}); $(".conc-empezar").disabled = true; $(".conc-terminar").disabled = false; pintar();
      window.cceeEvento && window.cceeEvento("ppt/empezar", "Piedra, papel o tijera", true); };
    $(".conc-terminar").onclick = () => { fase = "fin"; const r = PPT.ordenar(jug).slice(0, 10).map(j => ({alias: j.alias, superadas: j.superadas, tiempo: j.tiempo}));
      publicar({fase: "fin", preguntas, n: N, ranking: r}); $(".conc-terminar").disabled = true; pintar();
      caja.append(DOM.download(() => new Blob([csv(PPT.ordenar(jug).map((j, i) => ({puesto: i + 1, alias: j.alias, preguntas_superadas: j.superadas, preguntas_objetivo: N, aciertos: j.aciertos ?? 0, fallos: j.fallos ?? 0, partidas_ganadas: j.g ?? 0, partidas_empatadas: j.e ?? 0, partidas_perdidas: j.p ?? 0, tiempo_segundos: Math.round(j.tiempo / 100) / 10, terminado: j.fin ? "sí" : "no"})))], {type: "text/csv"}), `piedra_papel_tijera_${sala}.csv`, "⬇ Descargar los resultados (CSV)")); };
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
    let id; try { id = localStorage.getItem(`ccee-ppt-${SALA}`) || crypto.randomUUID(); localStorage.setItem(`ccee-ppt-${SALA}`, id); } catch (e) { id = crypto.randomUUID(); }
    let alias = ""; try { alias = localStorage.getItem("ccee-conc-alias") || ""; } catch (e) {}
    // superadas: preguntas superadas; k: preguntas planteadas (índice en la lista común); modo: "pregunta" o "ppt"
    let estado = null, unido = false, superadas = 0, k = 0, modo = "pregunta", intento = 1, t0 = null, ocupado = false, aviso = null;
    let aciertos = 0, fallos = 0, g = 0, e = 0, p = 0;
    const N = () => estado?.n ?? 0;
    const terminado = () => N() > 0 && superadas >= N();
    const tiempo = () => t0 ? Date.now() - t0 : 0;
    const enviar = () => cli.publish(temaJug(SALA), JSON.stringify({id, alias, superadas, aciertos, fallos, g, e, p, tiempo: tiempo(), fin: terminado()}), {qos: 1});
    const cabecera = () => html`<p class="juego-ind">Pregunta ${Math.min(superadas + 1, N())} de ${N()}${intento > 1 ? ` · intento ${intento}` : ""} · ⏱ ${CONC.segundos(tiempo())}</p>`;
    const pantalla = () => {
      caja.innerHTML = "";
      if (!unido) {
        const f = html`<form class="asis-caja"><label>Tu alias para el ranking<input name="alias" required maxlength="20" autocomplete="off" placeholder="p. ej. Analista_7" value="${alias}"></label><button class="asis-boton">Entrar en la partida</button><p class="asis-nota">No escribas tu nombre real si no quieres que aparezca en la pantalla de clase.</p></form>`;
        f.onsubmit = (ev) => { ev.preventDefault(); alias = f.alias.value.trim().slice(0, 20).replace(/[<>&"]/g, ""); if (!alias) return; try { localStorage.setItem("ccee-conc-alias", alias); } catch (err) {} unido = true; enviar(); pantalla(); };
        caja.append(f); return;
      }
      if (!estado || estado.fase === "espera") { caja.append(html`<div class="asis-caja conc-espera"><p class="juego-grande">✊ ✋ ✌️</p><p>Hola, <b>${alias}</b>. Espera a que el profesor empiece la partida…</p><p class="asis-nota">Cada acierto te da una partida contra la aplicación: si ganas, pasas de pregunta; si empatas, vuelves a jugar; si pierdes, contestas otra pregunta.</p></div>`); return; }
      if (estado.fase === "fin" || terminado()) {
        const pos = estado.ranking ? estado.ranking.findIndex(r => r.alias === alias) : -1;
        caja.append(html`<div class="asis-caja conc-espera"><p class="juego-grande">${superadas} / ${N()}</p><p>Tiempo: <b>${CONC.segundos(tiempo())}</b></p>
          <p>Aciertos: ${aciertos} · Fallos: ${fallos} · Partidas: ${g} ganadas, ${e} empatadas, ${p} perdidas</p>
          ${estado.fase === "fin" ? html`<p>${pos >= 0 ? html`Has quedado en el puesto <b>${pos + 1}</b> ${["🥇", "🥈", "🥉"][pos] ?? ""}` : "Mira el ranking en la pantalla de clase."}</p>` : html`<p>🏁 ¡Has superado todas las preguntas! Mira el ranking en la pantalla de clase.</p>`}</div>`);
        return;
      }
      if (!t0) t0 = Date.now();
      if (aviso) { caja.append(html`<p class="juego-res ${aviso.bien ? "bien" : "mal"}">${aviso.texto}</p>`); }
      const P = estado.preguntas;
      if (modo === "pregunta") {
        const i = k % P.length, q = P[i], correcta = CONC.desofuscar(SALA, i, q.c, q.o.length);
        const ops = html`<div class="juego-ops juego-ops-v">`;
        q.o.forEach((o, j) => { const b = html`<button class="juego-op">${o}</button>`; b.onclick = () => {
          if (ocupado) return; ocupado = true;
          const bien = j === correcta;
          ops.querySelectorAll("button").forEach((x, m) => { x.disabled = true; if (m === correcta) x.classList.add("ok"); }); if (!bien) b.classList.add("ko");
          if (bien) { aciertos++; modo = "ppt"; aviso = {bien: true, texto: "✅ ¡Correcto! Ahora, piedra, papel o tijera contra la aplicación."}; }
          else { fallos++; k++; intento++; aviso = {bien: false, texto: `❌ No es correcta. ${q.s} Contesta otra pregunta para seguir.`}; }
          enviar();
          setTimeout(() => { ocupado = false; pantalla(); }, bien ? 900 : 2600);
        }; ops.append(b); });
        caja.append(html`<div class="juego">${cabecera()}<p class="juego-p">${q.e.split("**").map((t, j) => j % 2 ? html`<b>${t}</b>` : t)}</p></div>`, ops);
        return;
      }
      // Partida de piedra, papel o tijera
      const duelo = html`<div class="ppt-duelo"><div><small>Tú</small><span class="ppt-mano">❔</span></div><div class="vs">VS</div><div><small>Aplicación</small><span class="ppt-mano">❔</span></div></div>`;
      const msg = html`<p class="ppt-cuenta">Elige tu jugada</p>`;
      const botones = html`<div class="ppt-botones"></div>`;
      PPT.jugadas.forEach(jd => { const b = html`<button class="ppt-boton" aria-label="${jd.n}"><span>${jd.e}</span><small>${jd.n}</small></button>`; b.onclick = () => {
        if (ocupado) return; ocupado = true;
        botones.querySelectorAll("button").forEach(x => x.disabled = true); b.classList.add("elegida");
        const app = PPT.jugadaApp(), r = PPT.resultado(jd.id, app);
        const manos = duelo.querySelectorAll(".ppt-mano");
        manos[0].textContent = jd.e;
        const pasos = ["Piedra…", "papel…", "¡tijera!"];
        pasos.forEach((t, m) => setTimeout(() => { msg.textContent = t; }, m * 350));
        setTimeout(() => {
          manos[1].textContent = PPT.jugadas[app].e;
          if (r === 1) { g++; superadas++; k++; intento = 1; modo = "pregunta"; msg.textContent = "🎉 ¡Ganas!";
            aviso = {bien: true, texto: terminado() ? "🏁 ¡Última pregunta superada!" : `🎉 Ganas a ${PPT.jugadas[app].n.toLowerCase()} con ${jd.n.toLowerCase()}: pasas a la pregunta ${superadas + 1}.`}; }
          else if (r === 0) { e++; msg.textContent = "🤝 Empate"; aviso = {bien: true, texto: `🤝 Empate (${jd.n.toLowerCase()} contra ${PPT.jugadas[app].n.toLowerCase()}): juega otra partida.`}; }
          else { p++; k++; intento++; modo = "pregunta"; msg.textContent = "😬 Pierdes"; aviso = {bien: false, texto: `😬 La aplicación gana con ${PPT.jugadas[app].n.toLowerCase()} a ${jd.n.toLowerCase()}: contesta otra pregunta para seguir en la pregunta ${superadas + 1}.`}; }
          enviar();
          setTimeout(() => { ocupado = false; pantalla(); }, 1700);
        }, 1050);
      }; botones.append(b); });
      caja.append(html`<div class="juego ppt-juego">${cabecera()}${duelo}${msg}</div>`, botones);
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

open("ppt.qmd", "w", encoding="utf-8").write(CABECERA + comun + PROPIO)
print("ppt.qmd generado")
