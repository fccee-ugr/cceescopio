"""Genera el control de asistencia de CCEEscopio:
asistencia.qmd (estudiantes) y asistencia-profesor.qmd (panel del profesor: pasar lista e informe en Excel).
Los registros se guardan en una hoja de Google del profesor (tools/asistencia_apps_script.gs).
Uso: python3 tools/make_asistencia.py"""
import json, re

# Si se rellena con la URL /exec del Apps Script, los estudiantes pueden entrar sin el enlace del profesor
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
    try {
      const r = await fetch(url, {method: "POST", body: JSON.stringify(datos)});
      return await r.json();
    } catch (e) { if (i === intentos - 1) return {ok: false, error: "No se ha podido conectar. Comprueba la conexión e inténtalo de nuevo."}; await new Promise(r => setTimeout(r, 800 * (i + 1) + Math.random() * 700)); }
  }
}
```'''

# =====================================================================================
# Página de los estudiantes
# =====================================================================================
pagina("asistencia.qmd", r'''---
title: "Pasar lista"
subtitle: "Técnicas Cuantitativas III · Registra tu asistencia a clase"
toc: false
---

__COMUN__

```{ojs}
//| echo: false
{
  const q = new URLSearchParams(location.search);
  const url = q.get("u") || URL_CONFIG;
  let disp; try { disp = localStorage.getItem("ccee-dispositivo"); if (!disp) { disp = crypto.randomUUID(); localStorage.setItem("ccee-dispositivo", disp); } } catch (e) { disp = "sin-almacenamiento-" + Math.random().toString(36).slice(2); }
  let guardado = ""; try { guardado = localStorage.getItem("ccee-dni") || ""; } catch (e) {}
  if (!url) return html`<div class="asis-caja"><p>Para pasar lista, escanea el <b>código QR</b> que muestra el profesor en la pantalla o abre el enlace que te ha dado.</p></div>`;
  const f = html`<form class="asis-caja">
    <label>Código de sesión<input name="sesion" required autocomplete="off" placeholder="TC3-XXXX" value="${q.get("s") || ""}" style="text-transform:uppercase"></label>
    <label>Código que aparece ahora en la pantalla<input name="codigo" required inputmode="numeric" pattern="[0-9]{4}" maxlength="4" autocomplete="off" placeholder="0000" class="asis-codigo"></label>
    <label>Tu DNI o NIE (con letra)<input name="dni" required autocomplete="off" placeholder="12345678Z" value="${guardado}" style="text-transform:uppercase"></label>
    <label class="asis-check"><input type="checkbox" name="recordar" checked> Recordar mi DNI en este dispositivo</label>
    <button type="submit" class="asis-boton">✋ Registrar mi asistencia</button>
    <p class="asis-msg" role="status"></p>
    <p class="asis-nota">Tu DNI y la hora se guardan solo en la hoja de control de asistencia del profesor de la asignatura. Desde un mismo dispositivo solo se puede registrar un DNI por sesión.</p>
  </form>`;
  const msg = f.querySelector(".asis-msg");
  if (q.get("s")) f.codigo.focus();
  f.onsubmit = async (ev) => {
    ev.preventDefault();
    const dni = dniValido(f.dni.value);
    if (!dni) { msg.className = "asis-msg mal"; msg.textContent = "El DNI o NIE no es válido: revisa los números y la letra."; return; }
    const b = f.querySelector("button"); b.disabled = true; msg.className = "asis-msg"; msg.textContent = "Enviando…";
    const r = await llamar(url, {accion: "marcar", sesion: f.sesion.value.trim().toUpperCase(), codigo: f.codigo.value.trim(), dni, dispositivo: disp});
    b.disabled = false;
    try { if (f.recordar.checked) localStorage.setItem("ccee-dni", dni); else localStorage.removeItem("ccee-dni"); } catch (e) {}
    if (r.ok) {
      msg.className = "asis-msg bien";
      msg.innerHTML = `✅ ${r.mensaje}<br><small>${dni.slice(0, 2)}******${dni.slice(-2)} · sesión ${f.sesion.value.toUpperCase()} · ${new Date(r.hora ?? Date.now()).toLocaleTimeString("es-ES")}</small>`;
      f.codigo.value = ""; window.cceeEvento && window.cceeEvento("asistencia/registro", "Asistencia registrada", true);
    } else { msg.className = "asis-msg mal"; msg.textContent = "❌ " + r.error; f.codigo.select(); }
  };
  return f;
}
```
''', COMUN=COMUN, URL=json.dumps(ASISTENCIA_URL))

# =====================================================================================
# Panel del profesor
# =====================================================================================
pagina("asistencia-profesor.qmd", r'''---
title: "Control de asistencia (profesorado)"
subtitle: "Técnicas Cuantitativas III · Pasa lista con un código que cambia cada 20 segundos y acumula la asistencia en Excel"
toc: true
toc-depth: 2
---

**Cómo funciona.** En clase proyectas un **código de 4 cifras que cambia cada 20 segundos** y un código QR. Los estudiantes lo escanean y escriben su DNI y el código que ven en ese momento. Así, un código enviado por mensaje a quien no está en el aula caduca en menos de un minuto. Después subes tu Excel con la lista de clase y CCEEscopio añade una columna por sesión y calcula las asistencias acumuladas. Al día siguiente subes ese mismo Excel y se añade la nueva sesión.

Los registros (DNI, hora y un identificador anónimo del dispositivo) se guardan **solo en una hoja de cálculo de Google que es tuya**. CCEEscopio no guarda nada; solo envía y lee los datos de esa hoja.

__COMUN__

```{ojs}
//| echo: false
GS_CODIGO = __GS__
XLSX = { try { return await import("https://cdn.sheetjs.com/xlsx-0.20.3/package/xlsx.mjs"); } catch (e) { return require("xlsx@0.18.5/dist/xlsx.full.min.js"); } }
qrcodeLib = require("qrcode-generator@1.4.4").catch(() => null)
leerConf = () => { try { return JSON.parse(localStorage.getItem("ccee-asis-conf") ?? "{}"); } catch (e) { return {}; } }
codigoDe = async (secreto, w) => {
  const k = await crypto.subtle.importKey("raw", new TextEncoder().encode(secreto), {name: "HMAC", hash: "SHA-256"}, false, ["sign"]);
  const b = new Uint8Array(await crypto.subtle.sign("HMAC", k, new TextEncoder().encode(String(w))));
  return String((((b[0] << 24) | (b[1] << 16) | (b[2] << 8) | b[3]) >>> 0) % 10000).padStart(4, "0");
}
claveDni = (x) => { const s = String(x ?? "").toUpperCase().replace(/[^0-9A-Z]/g, ""); return /^[0-9XYZ]\d{7}[A-Z]$/.test(s) ? s.slice(0, 8) : /^\d{1,8}$/.test(s) ? s.padStart(8, "0") : s; }
```

## 1. Configuración (una sola vez) {#configuracion}

::: {.callout-note collapse="true" appearance="simple"}
## Instrucciones para crear tu hoja de asistencia (10 minutos)

1. Crea una hoja de cálculo de Google, por ejemplo «Asistencia TC3».
2. En la hoja, abre **Extensiones → Apps Script**, borra el contenido y pega el código que descargas con el botón de abajo.
3. En la primera línea, cambia `cambia-esta-clave` por una **clave de profesor** que solo sepas tú.
4. Pulsa **Implementar → Nueva implementación**, tipo **Aplicación web**. «Ejecutar como»: **Yo**. «Quién tiene acceso»: **Cualquier usuario**. Autoriza los permisos que pide Google.
5. Copia la **URL de la aplicación web** (termina en `/exec`) y pégala abajo junto con tu clave.

Si con tu cuenta de la UGR no aparece la opción «Cualquier usuario», haz la implementación con una cuenta personal de Gmail: los estudiantes tienen que poder acceder sin iniciar sesión. Si más adelante cambias el código, usa **Implementar → Gestionar implementaciones → Editar → Nueva versión** para que la URL no cambie.
:::

```{ojs}
//| echo: false
DOM.download(() => new Blob([GS_CODIGO], {type: "text/plain;charset=utf-8"}), "asistencia_apps_script.gs", "⬇ Código para Apps Script")
viewof conf = {
  const c = leerConf();
  const f = html`<form class="asis-conf">
    <label>URL de la aplicación web <input name="url" size="60" placeholder="https://script.google.com/macros/s/…/exec" value="${c.url ?? ""}"></label>
    <label>Clave de profesor <input name="clave" type="password" value="${c.clave ?? ""}"></label>
    <label class="asis-check"><input type="checkbox" name="recordar"> Recordar en este navegador</label>
    <button type="submit" class="copiar">Guardar y comprobar la conexión</button> <span class="asis-estado"></span></form>`;
  f.value = c; f.recordar.checked = !!c.url;
  f.onsubmit = async (e) => {
    e.preventDefault();
    const v = {url: f.url.value.trim(), clave: f.clave.value};
    try { if (f.recordar.checked) localStorage.setItem("ccee-asis-conf", JSON.stringify(v)); else localStorage.removeItem("ccee-asis-conf"); } catch (err) {}
    const est = f.querySelector(".asis-estado"); est.textContent = "Comprobando…";
    const r = await llamar(v.url, {accion: "sesiones", clave: v.clave}, 1);
    est.textContent = r.ok ? `✅ Conectado (${r.sesiones.length} sesiones guardadas).` : `❌ ${r.error}`;
    f.value = v; f.dispatchEvent(new Event("input", {bubbles: true}));
  };
  return f;
}
```

## 2. Pasar lista en clase {#pasar-lista}

```{ojs}
//| echo: false
viewof sesionForm = Inputs.form({
  grupo: Inputs.text({label: "Asignatura y grupo", value: "Técnicas Cuantitativas III · Grupo A", width: 360}),
  minutos: Inputs.range([2, 60], {label: "Minutos abierta", value: 10, step: 1}),
  modo: Inputs.radio(new Map([["Código que cambia cada 20 segundos (recomendado)", "rotatorio"], ["Código fijo (para decirlo en voz alta)", "fijo"]]), {label: "Tipo de código", value: "rotatorio"})
}, {submit: "▶ Abrir sesión y proyectar el código"})
```

```{ojs}
//| echo: false
{
  if (!sesionForm || !conf?.url) return html`<p class="pending">${conf?.url ? "Elige las opciones y pulsa «Abrir sesión»." : "Primero guarda la configuración (apartado 1)."}</p>`;
  const r = await llamar(conf.url, {accion: "crear", clave: conf.clave, ...sesionForm}, 2);
  if (!r.ok) return html`<p class="pending">❌ ${r.error}</p>`;
  const desfase = r.ahora - Date.now();
  let hasta = r.hasta;
  const enlace = `${location.href.replace(/asistencia-profesor\.html.*$/, "asistencia.html")}?s=${r.id}${URL_CONFIG ? "" : "&u=" + encodeURIComponent(conf.url)}`;
  const panel = html`<div class="asis-panel">
    <div class="asis-panel-cab"><span>${sesionForm.grupo}</span><span class="asis-reloj"></span></div>
    <div class="asis-panel-cuerpo">
      <div class="asis-qr"></div>
      <div><p class="asis-et">Sesión</p><p class="asis-sesion">${r.id}</p>
        <p class="asis-et">Código</p><p class="asis-grande">····</p><div class="asis-barra"><div></div></div>
        <p class="asis-cuenta">0 registros</p></div>
    </div>
    <p class="asis-url">Escanea el QR o entra en <b>${enlace.replace(/\?.*$/, "")}</b> y escribe la sesión, el código y tu DNI.</p>
    <div class="graf-botones"><button class="copiar asis-full">⛶ Pantalla completa</button><button class="copiar asis-mas">+5 minutos</button><button class="copiar asis-cerrar">⏹ Cerrar la sesión</button><button class="copiar asis-copiar">📋 Copiar enlace</button></div></div>`;
  const $ = (s) => panel.querySelector(s);
  if (qrcodeLib) { const qr = qrcodeLib(0, "M"); qr.addData(enlace); qr.make(); $(".asis-qr").innerHTML = qr.createSvgTag({cellSize: 6, margin: 2, scalable: true}); }
  else $(".asis-qr").innerHTML = `<p class="nota">No se ha podido cargar el generador de QR.</p>`;
  let cerrada = false;
  const tic = async () => {
    if (!panel.isConnected) return;
    const ahora = Date.now() + desfase, w = Math.floor(ahora / 1000 / r.ventana);
    const restante = Math.max(0, hasta - ahora);
    $(".asis-reloj").textContent = restante > 0 ? `Abierta: ${Math.floor(restante / 60000)}:${String(Math.floor(restante / 1000) % 60).padStart(2, "0")}` : "Sesión cerrada";
    if (restante <= 0 || cerrada) { $(".asis-grande").textContent = "—"; $(".asis-barra div").style.width = "0"; return; }
    $(".asis-grande").textContent = await codigoDe(r.secreto, r.modo === "fijo" ? "fijo" : w);
    $(".asis-barra div").style.width = r.modo === "fijo" ? "100%" : `${100 * (1 - ((ahora / 1000) % r.ventana) / r.ventana)}%`;
  };
  const cuenta = async () => { if (!panel.isConnected) return; const l = await llamar(conf.url, {accion: "lista", clave: conf.clave, ids: [r.id]}, 1); if (l.ok) $(".asis-cuenta").textContent = `${l.registros.length} registro${l.registros.length === 1 ? "" : "s"}`; };
  const t1 = setInterval(tic, 500), t2 = setInterval(cuenta, 10000);
  invalidation.then(() => { clearInterval(t1); clearInterval(t2); });
  tic();
  $(".asis-full").onclick = () => document.fullscreenElement ? document.exitFullscreen() : panel.requestFullscreen?.();
  $(".asis-mas").onclick = async () => { const x = await llamar(conf.url, {accion: "ampliar", clave: conf.clave, id: r.id, minutos: 5}, 2); if (x.ok) { hasta = x.hasta; cerrada = false; } };
  $(".asis-cerrar").onclick = async () => { const x = await llamar(conf.url, {accion: "cerrar", clave: conf.clave, id: r.id}, 2); if (x.ok) { hasta = x.hasta; cerrada = true; cuenta(); } };
  $(".asis-copiar").onclick = () => navigator.clipboard.writeText(enlace).then(() => $(".asis-copiar").textContent = "✔ Copiado");
  window.cceeEvento && window.cceeEvento("asistencia/sesion", "Sesión de asistencia", true);
  return panel;
}
```

## 3. Informe y asistencia acumulada en Excel {#informe}

Sube tu Excel con la lista de clase, con una columna llamada **DNI**. Los demás datos (nombre, grupo…) se conservan. Si ya has generado informes otros días, sube el **último Excel que te dio CCEEscopio**: ya tiene las sesiones anteriores, y solo se añaden las nuevas. Sin Excel, obtienes solo la lista de asistentes de las sesiones elegidas.

```{ojs}
//| echo: false
viewof refrescar = Inputs.button("↻ Actualizar la lista de sesiones", {value: 0, reduce: v => v + 1})
sesionesGuardadas = {
  refrescar;
  if (!conf?.url) return [];
  const r = await llamar(conf.url, {accion: "sesiones", clave: conf.clave}, 2);
  return r.ok ? r.sesiones.sort((a, b) => b.creada - a.creada) : [];
}
viewof excelLista = Inputs.file({label: "Excel o CSV de la lista de clase", accept: ".xlsx,.xls,.csv,.ods"})
viewof sesionesSel = Inputs.select(new Map(sesionesGuardadas.map(s => [`${new Date(s.creada).toLocaleString("es-ES", {dateStyle: "short", timeStyle: "short"})} · ${s.id} · ${s.grupo} · ${s.registros} registros`, s.id])),
  {label: "Sesiones que quieres añadir (Ctrl o ⌘ para varias)", multiple: true, size: Math.min(8, Math.max(3, sesionesGuardadas.length)), value: sesionesGuardadas.slice(0, 1).map(s => s.id)})
viewof sesionesTxt = Inputs.text({label: "…o escribe los códigos de sesión", placeholder: "TC3-K7QM, TC3-P2RD", width: 360})
viewof generarInf = Inputs.button("📊 Generar el informe", {value: 0, reduce: v => v + 1})
```

```{ojs}
//| echo: false
informe = {
  if (!generarInf) return null;
  if (!conf?.url) return {error: "Primero guarda la configuración (apartado 1)."};
  const ids = [...new Set([...sesionesSel, ...sesionesTxt.toUpperCase().split(/[\s,;]+/).filter(Boolean)])];
  if (!ids.length) return {error: "Elige al menos una sesión."};
  const r = await llamar(conf.url, {accion: "lista", clave: conf.clave, ids}, 3);
  if (!r.ok) return {error: r.error};
  const nombreCol = (s) => `${new Date(s.creada).toLocaleDateString("es-ES", {day: "2-digit", month: "2-digit", year: "numeric"})} (${s.id})`;
  const ses = r.sesiones.sort((a, b) => a.creada - b.creada);
  // lista de clase
  let filas = [], colDni = null, cab = [];
  if (excelLista) {
    const wb = XLSX.read(await excelLista.arrayBuffer());
    filas = XLSX.utils.sheet_to_json(wb.Sheets[wb.SheetNames[0]], {defval: ""});
    cab = filas.length ? Object.keys(filas[0]) : [];
    colDni = cab.find(c => /\b(dni|nie|nif|documento)\b/i.test(c)) ?? cab.find(c => filas.filter(f => /^[0-9XYZ]\d{7}[A-Z]?$/i.test(String(f[c]).replace(/[\s.-]/g, ""))).length > filas.length / 2);
    if (!colDni) return {error: "No encuentro la columna del DNI en el Excel. Llámala «DNI»."};
  }
  const patronSes = /^\d{2}\/\d{2}\/\d{4} \([A-Z0-9-]+\)$/;
  const presentes = new Map(ses.map(s => [s.id, new Set(r.registros.filter(x => x.sesion === s.id).map(x => claveDni(x.dni)))]));
  const nuevas = ses.filter(s => !cab.includes(nombreCol(s)));
  const enLista = new Set(filas.map(f => claveDni(f[colDni])));
  filas.forEach(f => {
    delete f["Total asistencias"]; delete f["% asistencia"];
    nuevas.forEach(s => f[nombreCol(s)] = presentes.get(s.id).has(claveDni(f[colDni])) ? 1 : 0);
    const cols = Object.keys(f).filter(c => patronSes.test(c));
    f["Total asistencias"] = cols.reduce((a, c) => a + (+f[c] || 0), 0);
    f["% asistencia"] = cols.length ? Math.round(1000 * f["Total asistencias"] / cols.length) / 10 : 0;
  });
  // incidencias
  const inc = [];
  if (excelLista) r.registros.filter(x => !enLista.has(claveDni(x.dni))).forEach(x => inc.push({Tipo: "DNI que no está en la lista de clase", Sesión: x.sesion, DNI: x.dni, Hora: new Date(x.hora).toLocaleTimeString("es-ES")}));
  d3.groups(r.registros, x => x.sesion, x => x.dispositivo).forEach(([s, g]) => g.forEach(([d, xs]) => { if (new Set(xs.map(x => x.dni)).size > 1) xs.forEach(x => inc.push({Tipo: "Varios DNI desde el mismo dispositivo", Sesión: s, DNI: x.dni, Hora: new Date(x.hora).toLocaleTimeString("es-ES")})); }));
  const asistentes = r.registros.sort((a, b) => a.hora - b.hora).map(x => {
    const f = filas.find(y => claveDni(y[colDni]) === claveDni(x.dni));
    return {Sesión: x.sesion, Fecha: new Date(x.hora).toLocaleDateString("es-ES"), Hora: new Date(x.hora).toLocaleTimeString("es-ES"), DNI: x.dni, ...(f ? Object.fromEntries(cab.filter(c => c !== colDni && !patronSes.test(c)).slice(0, 3).map(c => [c, f[c]])) : {}), "En la lista": excelLista ? (f ? "Sí" : "No") : ""};
  });
  return {filas, asistentes, inc, ses, nuevas, colDni, presentes};
}
```

```{ojs}
//| echo: false
{
  if (!informe) return html`<p class="pending">Elige las sesiones y pulsa <b>Generar el informe</b>.</p>`;
  if (informe.error) return html`<p class="pending">❌ ${informe.error}</p>`;
  const {filas, asistentes, inc, ses, nuevas} = informe;
  const hoy = new Date().toISOString().slice(0, 10);
  const excel = () => {
    const wb = XLSX.utils.book_new();
    if (filas.length) XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(filas), "Asistencia acumulada");
    XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(asistentes.length ? asistentes : [{Aviso: "Sin registros"}]), "Asistentes por sesión");
    XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(ses.map(s => ({Sesión: s.id, Grupo: s.grupo, Abierta: new Date(s.creada).toLocaleString("es-ES"), Registros: informe.presentes.get(s.id).size}))), "Sesiones");
    if (inc.length) XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(inc), "Incidencias");
    return new Blob([XLSX.write(wb, {bookType: "xlsx", type: "array"})], {type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"});
  };
  const resumen = filas.length ? html`<p>${nuevas.length ? `Se han añadido ${nuevas.length} sesión(es) nueva(s)` : "Las sesiones elegidas ya estaban en el Excel (no se duplican)"}. Estudiantes en la lista: <b>${filas.length}</b>. Asistencia media: <b>${d3.format(".1f")(d3.mean(filas, f => f["% asistencia"])).replace(".", ",")} %</b>.</p>` : html`<p>Asistentes: <b>${asistentes.length}</b> registros en ${ses.length} sesión(es).</p>`;
  return html`${resumen}
    ${inc.length ? html`<p class="juego-res mal">⚠️ ${inc.length} incidencia(s): DNI que no están en tu lista o varios DNI desde un mismo dispositivo. Revisa la hoja «Incidencias».</p>` : ""}
    <div class="graf-botones">${DOM.download(excel, `asistencia_TC3_${hoy}.xlsx`, "⬇ Descargar el Excel de asistencia")}</div>
    ${Inputs.table(filas.length ? filas : asistentes, {rows: 14, layout: "auto"})}`;
}
```

::: {.callout-tip appearance="simple"}
**Consejos.** Abre la sesión al principio de la clase, durante 5 o 10 minutos, y ciérrala después. Si hay dudas, al final del informe puedes llamar en voz alta a dos o tres estudiantes de la lista de asistentes para comprobar que están. El Excel acumulado guarda una columna por sesión (1 = asistió, 0 = no asistió), el total y el porcentaje. Puedes corregir a mano cualquier valor antes de volver a subirlo otro día.

**Protección de datos.** Conviene informar al estudiantado en la guía docente o en PRADO de que la asistencia se registra con el DNI y para qué se usa. Los registros están solo en tu hoja de Google: puedes borrarlos al terminar el curso.
:::
''', COMUN=COMUN, URL=json.dumps(ASISTENCIA_URL), GS=json.dumps(GS, ensure_ascii=False))
