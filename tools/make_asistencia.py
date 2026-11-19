"""Genera el control de asistencia de CCEEscopio (versión sencilla):
asistencia.qmd (estudiantes: escanean el QR y escriben su DNI) y
asistencia-profesor.qmd (profesor: sube su Excel, proyecta el QR, termina y descarga el Excel acumulado).
Los registros se guardan en una hoja de Google (tools/asistencia_apps_script.gs), que se instala una sola vez.
Uso: python3 tools/make_asistencia.py"""
import json, re

# URL /exec del Apps Script (se rellena una sola vez tras instalarlo). Si se deja vacía,
# la página del profesor la pide la primera vez y la recuerda en ese navegador.
ASISTENCIA_URL = ""
GS = open("tools/asistencia_apps_script.gs", encoding="utf-8").read()

def pagina(nombre, texto, **rep):
    for k, v in rep.items():
        texto = texto.replace(f"__{k}__", v)
    assert not re.search(r"__[A-Z0-9]+__", texto), f"marcador sin sustituir en {nombre}"
    open(nombre, "w", encoding="utf-8").write(texto)
    print("  ", nombre)

COMUN = r'''```{ojs}
//| echo: false
URL_CONFIG = __URL__
dniValido = (x) => {
  const s = String(x || "").toUpperCase().replace(/[^0-9A-Z]/g, ""), L = "TRWAGMYFPDXBNJZSQVHLCKE";
  let m = s.match(/^(\d{8})([A-Z])$/); if (m) return L[+m[1] % 23] === m[2] ? s : null;
  m = s.match(/^([XYZ])(\d{7})([A-Z])$/); if (m) return L[+("XYZ".indexOf(m[1]) + m[2]) % 23] === m[3] ? s : null;
  return null;
}
llamar = async (url, datos, intentos = 4) => {
  for (let i = 0; i < intentos; i++) {
    try { const r = await fetch(url, {method: "POST", body: JSON.stringify(datos)}); return await r.json(); }
    catch (e) { if (i === intentos - 1) return {ok: false, error: "No se ha podido conectar. Comprueba la conexión e inténtalo de nuevo."}; await new Promise(r => setTimeout(r, 800 * (i + 1) + Math.random() * 700)); }
  }
}
```'''

# =====================================================================================
# Página de los estudiantes
# =====================================================================================
pagina("asistencia.qmd", r'''---
title: "Pasar lista"
subtitle: "Registra tu asistencia a clase"
toc: false
---

__COMUN__

```{ojs}
//| echo: false
{
  const q = new URLSearchParams(location.search);
  const url = q.get("u") || URL_CONFIG, sesion = q.get("s"), codigo = q.get("c");
  let disp; try { disp = localStorage.getItem("ccee-dispositivo"); if (!disp) { disp = crypto.randomUUID(); localStorage.setItem("ccee-dispositivo", disp); } } catch (e) { disp = "sin-almacenamiento-" + Math.random().toString(36).slice(2); }
  let guardado = ""; try { guardado = localStorage.getItem("ccee-dni") || ""; } catch (e) {}
  if (!url || !sesion || !codigo) return html`<div class="asis-caja"><p>📷 Para pasar lista, <b>escanea con la cámara del móvil el código QR</b> que el profesor proyecta en clase.</p></div>`;
  const f = html`<form class="asis-caja">
    <label>Tu DNI o NIE (con letra)<input name="dni" required autocomplete="off" placeholder="12345678Z" value="${guardado}" style="text-transform:uppercase"></label>
    <button type="submit" class="asis-boton">✋ Estoy en clase</button>
    <p class="asis-msg" role="status"></p>
    <p class="asis-nota">Tu DNI se guarda en este móvil para la próxima vez y se envía solo para el control de asistencia de la asignatura. Desde un mismo móvil solo se puede registrar un DNI por clase.</p>
  </form>`;
  const msg = f.querySelector(".asis-msg");
  f.onsubmit = async (ev) => {
    ev.preventDefault();
    const dni = dniValido(f.dni.value);
    if (!dni) { msg.className = "asis-msg mal"; msg.textContent = "El DNI o NIE no es válido: revisa los números y la letra."; return; }
    const b = f.querySelector("button"); b.disabled = true; msg.className = "asis-msg"; msg.textContent = "Enviando…";
    const r = await llamar(url, {accion: "marcar", sesion, codigo, dni, dispositivo: disp});
    b.disabled = false;
    if (r.ok) {
      try { localStorage.setItem("ccee-dni", dni); } catch (e) {}
      f.querySelector("label").remove(); b.remove();
      msg.className = "asis-msg bien";
      msg.innerHTML = `✅ ${r.mensaje}<br><small>DNI ${dni.slice(0, 2)}******${dni.slice(-2)} · ${new Date(r.hora ?? Date.now()).toLocaleString("es-ES", {dateStyle: "short", timeStyle: "short"})}</small>`;
      window.cceeEvento && window.cceeEvento("asistencia/registro", "Asistencia registrada", true);
    } else { msg.className = "asis-msg mal"; msg.textContent = "❌ " + r.error; }
  };
  return f;
}
```
''', COMUN=COMUN, URL=json.dumps(ASISTENCIA_URL))

# =====================================================================================
# Página del profesor
# =====================================================================================
pagina("asistencia-profesor.qmd", r'''---
title: "Control de asistencia"
subtitle: "Para el profesorado · Sube tu lista, proyecta el QR y descarga el Excel con la asistencia acumulada"
toc: false
---

**Cómo se usa, cada día de clase:**

1. **Sube tu Excel.** El primer día, tu lista de clase con una columna **DNI** (y, si quieres, el nombre y otros datos). Los demás días, **el último Excel de asistencia que te dio esta página**.
2. Pulsa **Empezar a pasar lista** y proyecta la pantalla. Los estudiantes escanean el código QR con el móvil y escriben su DNI. Verás cómo se van marcando en la lista.
3. Pulsa **Terminar y descargar el Excel**. Se añade una columna con la fecha de hoy (1 = asistió, 0 = no asistió) y se actualizan el total y el porcentaje de asistencia de cada estudiante.

El código QR cambia cada 20 segundos, así que una foto del QR enviada a quien no está en clase deja de funcionar en unos 2 minutos. Tu Excel no sale de tu ordenador: solo se envían los DNI de los estudiantes que pasan lista.

__COMUN__

```{ojs}
//| echo: false
GS_CODIGO = __GS__
XLSX = { try { return await import("https://cdn.sheetjs.com/xlsx-0.20.3/package/xlsx.mjs"); } catch (e) { return require("xlsx@0.18.5/dist/xlsx.full.min.js"); } }
qrcodeLib = require("qrcode-generator@1.4.4").catch(() => null)
urlServicio = { let u = URL_CONFIG; try { u = u || localStorage.getItem("ccee-asis-url") || ""; } catch (e) {} return u; }
codigoDe = async (secreto, w) => {
  const k = await crypto.subtle.importKey("raw", new TextEncoder().encode(secreto), {name: "HMAC", hash: "SHA-256"}, false, ["sign"]);
  const b = new Uint8Array(await crypto.subtle.sign("HMAC", k, new TextEncoder().encode(String(w))));
  return String((((b[0] << 24) | (b[1] << 16) | (b[2] << 8) | b[3]) >>> 0) % 1000000).padStart(6, "0");
}
claveDni = (x) => { const s = String(x ?? "").toUpperCase().replace(/[^0-9A-Z]/g, ""); return /^[0-9XYZ]\d{7}[A-Z]$/.test(s) ? s.slice(0, 8) : /^\d{1,8}$/.test(s) ? s.padStart(8, "0") : s; }
esColFecha = (c) => /^\d{2}\/\d{2}\/\d{4}( \(\d+\))?$/.test(c)
```

```{ojs}
//| echo: false
viewof excelLista = Inputs.file({label: "1. Tu Excel (lista de clase o último Excel de asistencia)", accept: ".xlsx,.xls,.csv,.ods"})
viewof grupoAs = Inputs.text({label: "Asignatura y grupo (opcional)", value: "Técnicas Cuantitativas III", width: 360})
```

```{ojs}
//| echo: false
lista = {
  if (!excelLista) return null;
  const wb = XLSX.read(await excelLista.arrayBuffer(), {type: "array"});
  const filas = XLSX.utils.sheet_to_json(wb.Sheets[wb.SheetNames[0]], {defval: ""});
  const cab = filas.length ? Object.keys(filas[0]) : [];
  const colDni = cab.find(c => /\b(dni|nie|nif|documento)\b/i.test(c)) ?? cab.find(c => filas.filter(f => /^[0-9XYZ]\d{7}[A-Z]?$/i.test(String(f[c]).replace(/[\s.-]/g, ""))).length > filas.length / 2);
  const colNombre = cab.filter(c => /nombre|apellido|estudiante/i.test(c));
  return {filas, cab, colDni, colNombre, sesiones: cab.filter(esColFecha).length};
}
{
  if (!lista) return html`<p class="pending">Sube tu Excel para empezar. Si aún no tienes ninguno, prepara uno con una columna <b>DNI</b> y otra con el nombre.</p>`;
  if (!lista.colDni) return html`<p class="pending">❌ No encuentro la columna del DNI en tu Excel. Ponle de título «DNI».</p>`;
  return html`<p>✅ <b>${lista.filas.length} estudiantes</b> en la lista${lista.sesiones ? `, con ${lista.sesiones} día(s) de asistencia anteriores` : ""}.</p>${urlServicio ? "" : html`<p class="pending">Falta la configuración inicial del servicio (al final de esta página).</p>`}`;
}
```

```{ojs}
//| echo: false
viewof empezar = Inputs.button("▶ 2. Empezar a pasar lista", {value: 0, reduce: v => v + 1, disabled: !lista?.colDni || !urlServicio})
```

```{ojs}
//| echo: false
{
  if (!empezar || !lista?.colDni) return html``;
  // Recupera la sesión si se ha recargado la página a mitad de clase
  let ses = null; try { ses = JSON.parse(localStorage.getItem("ccee-asis-sesion") ?? "null"); } catch (e) {}
  if (!ses || Date.now() - ses.local > 4 * 3600000) {
    const r = await llamar(urlServicio, {accion: "crear", grupo: grupoAs}, 3);
    if (!r.ok) return html`<p class="pending">❌ ${r.error}</p>`;
    ses = {...r, local: Date.now(), desfase: r.ahora - Date.now()};
    try { localStorage.setItem("ccee-asis-sesion", JSON.stringify(ses)); } catch (e) {}
  }
  const base = location.href.replace(/asistencia-profesor\.html.*$/, "asistencia.html");
  const nombre = (f) => lista.colNombre.map(c => f[c]).filter(Boolean).join(" ") || f[lista.colDni];
  const indice = new Map(lista.filas.map(f => [claveDni(f[lista.colDni]), f]));
  const panel = html`<div class="asis-panel">
    <div class="asis-panel-cab"><span>${grupoAs}</span><span class="asis-cuenta">0 de ${lista.filas.length}</span></div>
    <div class="asis-panel-cuerpo">
      <div><div class="asis-qr"></div><div class="asis-barra"><div></div></div><p class="asis-url">Escanea el código con la cámara del móvil</p></div>
      <ol class="asis-presentes"></ol>
    </div>
    <div class="graf-botones"><button class="copiar asis-full">⛶ Pantalla completa</button><button class="asis-boton asis-fin">⏹ 3. Terminar y descargar el Excel</button></div>
    <p class="asis-final"></p></div>`;
  const $ = (s) => panel.querySelector(s);
  let regs = [], terminado = false, ultimoW = null;
  const pintarQR = async () => {
    if (!panel.isConnected || terminado) return;
    const ahora = Date.now() + ses.desfase, w = Math.floor(ahora / 1000 / ses.ventana);
    $(".asis-barra div").style.width = `${100 * (1 - ((ahora / 1000) % ses.ventana) / ses.ventana)}%`;
    if (w === ultimoW) return; ultimoW = w;
    const enlace = `${base}?s=${ses.id}&c=${await codigoDe(ses.secreto, w)}${URL_CONFIG ? "" : "&u=" + encodeURIComponent(urlServicio)}`;
    if (qrcodeLib) { const qr = qrcodeLib(0, "M"); qr.addData(enlace); qr.make(); $(".asis-qr").innerHTML = qr.createSvgTag({cellSize: 6, margin: 2, scalable: true}); }
    else $(".asis-qr").innerHTML = `<p class="pending">No se ha podido cargar el generador de QR. Comprueba la conexión y recarga la página.</p>`;
  };
  const pintarLista = () => {
    const vistos = [...new Map(regs.map(x => [claveDni(x.dni), x])).values()];
    const enLista = vistos.filter(x => indice.has(claveDni(x.dni)));
    $(".asis-cuenta").textContent = `${enLista.length} de ${lista.filas.length}`;
    $(".asis-presentes").innerHTML = vistos.slice().reverse().map(x => { const f = indice.get(claveDni(x.dni)); return `<li class="${f ? "" : "fuera"}">${f ? nombre(f) : `${x.dni} (no está en la lista)`}</li>`; }).join("");
  };
  const actualizar = async () => { if (!panel.isConnected || terminado) return; const l = await llamar(urlServicio, {accion: "lista", id: ses.id, secreto: ses.secreto}, 1); if (l.ok) { regs = l.registros; pintarLista(); } };
  const t1 = setInterval(pintarQR, 500), t2 = setInterval(actualizar, 5000);
  invalidation.then(() => { clearInterval(t1); clearInterval(t2); });
  pintarQR(); actualizar();
  $(".asis-full").onclick = () => document.fullscreenElement ? document.exitFullscreen() : panel.requestFullscreen?.();
  $(".asis-fin").onclick = async () => {
    $(".asis-fin").disabled = true; $(".asis-final").textContent = "Cerrando la lista…";
    const l = await llamar(urlServicio, {accion: "cerrar", id: ses.id, secreto: ses.secreto}, 4);
    if (!l.ok) { $(".asis-fin").disabled = false; $(".asis-final").textContent = "❌ " + l.error + " Vuelve a pulsar «Terminar»."; return; }
    terminado = true; regs = l.registros; pintarLista();
    if (document.fullscreenElement) document.exitFullscreen();
    try { localStorage.removeItem("ccee-asis-sesion"); } catch (e) {}
    $(".asis-qr").innerHTML = `<p class="asis-grande">✔</p>`; $(".asis-barra").remove();
    // Excel acumulado: nueva columna con la fecha de hoy
    const fecha = new Date(l.creada).toLocaleDateString("es-ES", {day: "2-digit", month: "2-digit", year: "numeric"});
    let col = fecha, k = 2; while (lista.cab.includes(col)) col = `${fecha} (${k++})`;
    const presentes = new Set(regs.map(x => claveDni(x.dni)));
    const filas = lista.filas.map(f => {
      const g = {...f}; delete g["Total asistencias"]; delete g["% asistencia"];
      g[col] = presentes.has(claveDni(f[lista.colDni])) ? 1 : 0;
      const cols = Object.keys(g).filter(esColFecha);
      g["Total asistencias"] = cols.reduce((a, c) => a + (+g[c] || 0), 0);
      g["% asistencia"] = Math.round(1000 * g["Total asistencias"] / cols.length) / 10;
      return g;
    });
    const fuera = [...new Set(regs.map(x => x.dni))].filter(d => !lista.filas.some(f => claveDni(f[lista.colDni]) === claveDni(d)));
    const porDisp = d3.groups(regs, x => x.dispositivo).filter(([, xs]) => new Set(xs.map(x => x.dni)).size > 1);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(filas), "Asistencia");
    const inc = [...fuera.map(d => ({Aviso: "Ha pasado lista pero no está en tu Excel", DNI: d, Fecha: col})), ...porDisp.flatMap(([, xs]) => xs.map(x => ({Aviso: "Varios DNI desde el mismo móvil", DNI: x.dni, Fecha: col})))];
    if (inc.length) XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(inc), "Avisos");
    const blob = new Blob([XLSX.write(wb, {bookType: "xlsx", type: "array"})], {type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"});
    const nombreFich = `asistencia_${fecha.split("/").reverse().join("-")}.xlsx`;
    const a = DOM.download(blob, nombreFich, `⬇ Descargar de nuevo ${nombreFich}`);
    const enlaceAuto = document.createElement("a"); enlaceAuto.href = URL.createObjectURL(blob); enlaceAuto.download = nombreFich; enlaceAuto.click();
    $(".asis-final").innerHTML = `✅ Asistencia del ${fecha}: <b>${presentes.size - fuera.length}</b> de ${lista.filas.length} estudiantes. Se ha descargado <b>${nombreFich}</b>: súbelo el próximo día de clase.${inc.length ? ` ⚠️ Revisa la hoja «Avisos» (${inc.length}).` : ""} `;
    $(".asis-final").append(a);
    window.cceeEvento && window.cceeEvento("asistencia/terminar", "Asistencia terminada", true);
  };
  return panel;
}
```

::: {.callout-note collapse="true" appearance="simple"}
## Configuración (solo la primera vez, la hace quien administra la web)

Los registros se guardan en una hoja de cálculo de Google. Para crearla:

1. Crea una hoja de cálculo de Google y abre **Extensiones → Apps Script**.
2. Borra lo que haya, pega el código que descargas con el botón de abajo y guarda.
3. **Implementar → Nueva implementación**, tipo **Aplicación web**, «Ejecutar como»: **Yo**, «Quién tiene acceso»: **Cualquier usuario**. Autoriza los permisos.
4. Copia la URL que termina en `/exec` y pégala aquí. Para que nadie más tenga que hacerlo, ponla también en `tools/make_asistencia.py` (`ASISTENCIA_URL`) y vuelve a generar la web.

```{ojs}
//| echo: false
DOM.download(() => new Blob([GS_CODIGO], {type: "text/plain;charset=utf-8"}), "asistencia_apps_script.gs", "⬇ Código para Apps Script")
{
  const f = html`<form class="asis-conf"><label>URL del servicio <input name="url" size="60" placeholder="https://script.google.com/macros/s/…/exec" value="${urlServicio}"></label>
    <button class="copiar" type="submit">Guardar</button> <span></span></form>`;
  f.onsubmit = async (e) => {
    e.preventDefault(); const u = f.url.value.trim();
    try { localStorage.setItem("ccee-asis-url", u); } catch (err) {}
    f.querySelector("span").textContent = "Comprobando…";
    try { const r = await (await fetch(u)).json(); f.querySelector("span").textContent = r.ok ? "✅ Conectado. Recarga la página." : "❌ La URL no responde bien."; }
    catch (err) { f.querySelector("span").textContent = "❌ No se puede conectar con esa URL."; }
  };
  return f;
}
```
:::
''', COMUN=COMUN, URL=json.dumps(ASISTENCIA_URL), GS=json.dumps(GS, ensure_ascii=False))
