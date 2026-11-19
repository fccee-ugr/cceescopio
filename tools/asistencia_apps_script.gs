/**
 * Control de asistencia de CCEEscopio · servidor en Google Apps Script
 * ---------------------------------------------------------------------
 * Los registros se guardan SOLO en esta hoja de cálculo, que es del profesor.
 * Instalación (una sola vez):
 *  1. Crea una hoja de cálculo de Google (por ejemplo, «Asistencia TC3»).
 *  2. Menú Extensiones → Apps Script. Borra lo que haya y pega este código.
 *  3. Cambia CLAVE_PROFESOR por una clave tuya (no la compartas con los estudiantes).
 *  4. Implementar → Nueva implementación → Tipo: Aplicación web.
 *     Ejecutar como: «Yo». Quién tiene acceso: «Cualquier usuario».
 *  5. Autoriza los permisos y copia la URL que termina en /exec.
 *     Pégala en la página «Control de asistencia (profesorado)» de CCEEscopio.
 */
const CLAVE_PROFESOR = "cambia-esta-clave";
const VENTANA_SEG = 20;      // el código del proyector cambia cada 20 segundos
const VENTANAS_VALIDAS = 4;  // se acepta el código actual y los 3 anteriores (≈ 1 minuto para escribirlo)
const MAX_INTENTOS = 6;      // intentos fallidos por dispositivo y sesión

function hoja_(nombre, cabecera) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let h = ss.getSheetByName(nombre);
  if (!h) { h = ss.insertSheet(nombre); h.appendRow(cabecera); h.setFrozenRows(1); }
  return h;
}
const sesiones_ = () => hoja_("Sesiones", ["Sesión", "Secreto", "Asignatura y grupo", "Modo", "Creada", "Abierta hasta"]);
const registros_ = () => hoja_("Registros", ["Fecha y hora", "Sesión", "DNI", "Dispositivo"]);
const json_ = (o) => ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);

function codigo_(secreto, w) {
  const b = Utilities.computeHmacSha256Signature(String(w), secreto);
  const n = (((b[0] & 255) << 24) | ((b[1] & 255) << 16) | ((b[2] & 255) << 8) | (b[3] & 255)) >>> 0;
  return String(n % 10000).padStart(4, "0");
}
function dni_(x) {
  const s = String(x || "").toUpperCase().replace(/[^0-9A-Z]/g, "");
  const L = "TRWAGMYFPDXBNJZSQVHLCKE";
  let m = s.match(/^(\d{8})([A-Z])$/);
  if (m) return L[+m[1] % 23] === m[2] ? s : null;
  m = s.match(/^([XYZ])(\d{7})([A-Z])$/);
  if (m) return L[+("XYZ".indexOf(m[1]) + m[2]) % 23] === m[3] ? s : null;
  return null;
}
function buscarSesion_(id) {
  const v = sesiones_().getDataRange().getValues();
  for (let i = 1; i < v.length; i++) if (v[i][0] === id) return {fila: i + 1, id: v[i][0], secreto: v[i][1], grupo: v[i][2], modo: v[i][3], creada: new Date(v[i][4]), hasta: new Date(v[i][5])};
  return null;
}
function nuevoId_() {
  const a = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  let s = ""; for (let i = 0; i < 4; i++) s += a[Math.floor(Math.random() * a.length)];
  return "TC3-" + s;
}

function doGet() { return json_({ok: true, servicio: "asistencia CCEEscopio", hora: Date.now()}); }

function doPost(e) {
  let d;
  try { d = JSON.parse(e.postData.contents); } catch (err) { return json_({ok: false, error: "Petición no válida."}); }
  const ahora = new Date();
  const esProfesor = d.clave === CLAVE_PROFESOR;

  if (d.accion === "marcar") {
    const s = buscarSesion_(String(d.sesion || "").toUpperCase().trim());
    if (!s) return json_({ok: false, error: "No existe esa sesión. Revisa el código de sesión."});
    if (ahora >= s.hasta) return json_({ok: false, error: "La sesión ya está cerrada."});
    const dni = dni_(d.dni);
    if (!dni) return json_({ok: false, error: "El DNI o NIE no es válido (revisa los números y la letra)."});
    const disp = String(d.dispositivo || "").slice(0, 60);
    const cache = CacheService.getScriptCache();
    const kInt = "int_" + s.id + "_" + disp, kDni = "dni_" + s.id + "_" + dni, kDisp = "disp_" + s.id + "_" + disp;
    const fallos = +(cache.get(kInt) || 0);
    if (fallos >= MAX_INTENTOS) return json_({ok: false, error: "Demasiados intentos fallidos desde este dispositivo."});
    if (cache.get(kDni)) return json_({ok: true, repetido: true, mensaje: "Tu asistencia ya estaba registrada."});
    const otro = cache.get(kDisp);
    if (otro && otro !== dni) return json_({ok: false, error: "Desde este dispositivo ya se ha registrado otro DNI en esta sesión."});
    const cod = String(d.codigo || "").replace(/\D/g, "").padStart(4, "0");
    let valido = false;
    if (s.modo === "fijo") valido = cod === codigo_(s.secreto, "fijo");
    else {
      const w = Math.floor(ahora.getTime() / 1000 / VENTANA_SEG);
      for (let k = -1; k < VENTANAS_VALIDAS && !valido; k++) valido = cod === codigo_(s.secreto, w - k);
    }
    if (!valido) { cache.put(kInt, String(fallos + 1), 21600); return json_({ok: false, error: "El código no es correcto o ha caducado. Escribe el que aparece ahora en la pantalla."}); }
    registros_().appendRow([ahora, s.id, dni, disp]);
    cache.put(kDni, "1", 21600); cache.put(kDisp, dni, 21600);
    return json_({ok: true, mensaje: "Asistencia registrada.", hora: ahora.getTime(), grupo: s.grupo});
  }

  if (!esProfesor) return json_({ok: false, error: "Clave de profesor incorrecta."});

  if (d.accion === "crear") {
    const min = Math.max(1, Math.min(240, +d.minutos || 15));
    let id; do { id = nuevoId_(); } while (buscarSesion_(id));
    const secreto = Utilities.getUuid(), modo = d.modo === "fijo" ? "fijo" : "rotatorio";
    const hasta = new Date(ahora.getTime() + min * 60000);
    sesiones_().appendRow([id, secreto, String(d.grupo || "").slice(0, 80), modo, ahora, hasta]);
    return json_({ok: true, id, secreto, modo, hasta: hasta.getTime(), ahora: ahora.getTime(), ventana: VENTANA_SEG});
  }
  if (d.accion === "cerrar" || d.accion === "ampliar") {
    const s = buscarSesion_(d.id); if (!s) return json_({ok: false, error: "Sesión no encontrada."});
    const hasta = d.accion === "cerrar" ? ahora : new Date(Math.max(ahora.getTime(), s.hasta.getTime()) + (+d.minutos || 5) * 60000);
    sesiones_().getRange(s.fila, 6).setValue(hasta);
    return json_({ok: true, hasta: hasta.getTime()});
  }
  if (d.accion === "sesiones") {
    const v = sesiones_().getDataRange().getValues().slice(1);
    const n = {}; registros_().getDataRange().getValues().slice(1).forEach(r => n[r[1]] = (n[r[1]] || 0) + 1);
    return json_({ok: true, sesiones: v.map(r => ({id: r[0], grupo: r[2], modo: r[3], creada: new Date(r[4]).getTime(), hasta: new Date(r[5]).getTime(), registros: n[r[0]] || 0}))});
  }
  if (d.accion === "lista") {
    const ids = [].concat(d.ids || []).map(x => String(x).toUpperCase().trim());
    const ses = ids.map(buscarSesion_).filter(Boolean).map(s => ({id: s.id, grupo: s.grupo, creada: s.creada.getTime(), hasta: s.hasta.getTime()}));
    const regs = registros_().getDataRange().getValues().slice(1).filter(r => ids.indexOf(r[1]) >= 0)
      .map(r => ({hora: new Date(r[0]).getTime(), sesion: r[1], dni: r[2], dispositivo: r[3]}));
    return json_({ok: true, sesiones: ses, registros: regs});
  }
  return json_({ok: false, error: "Acción desconocida."});
}
