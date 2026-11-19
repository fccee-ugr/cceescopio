/**
 * Control de asistencia de CCEEscopio · almacén de registros en Google Apps Script
 * --------------------------------------------------------------------------------
 * Solo hace falta instalarlo UNA VEZ (lo hace quien administra CCEEscopio):
 *  1. Crea una hoja de cálculo de Google (por ejemplo, «Asistencia CCEEscopio»).
 *  2. Menú Extensiones → Apps Script. Borra lo que haya, pega este código y guarda.
 *  3. Implementar → Nueva implementación → Tipo: Aplicación web.
 *     Ejecutar como: «Yo». Quién tiene acceso: «Cualquier usuario».
 *  4. Copia la URL que termina en /exec y pégala en tools/make_asistencia.py (ASISTENCIA_URL).
 * Cada sesión tiene un secreto que solo conoce el ordenador del profesor que la abrió:
 * sin él no se puede ver la lista de asistentes.
 */
const VENTANA_SEG = 20;       // el QR del proyector cambia cada 20 segundos
const VALIDEZ_VENTANAS = 6;   // un QR sirve durante unos 2 minutos después de escanearlo
const DURACION_MAX_H = 4;     // una sesión se cierra sola a las 4 horas

function hoja_(nombre, cabecera) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let h = ss.getSheetByName(nombre);
  if (!h) { h = ss.insertSheet(nombre); h.appendRow(cabecera); h.setFrozenRows(1); }
  return h;
}
const sesiones_ = () => hoja_("Sesiones", ["Sesión", "Secreto", "Grupo", "Creada", "Abierta hasta"]);
const registros_ = () => hoja_("Registros", ["Fecha y hora", "Sesión", "DNI", "Dispositivo"]);
const json_ = (o) => ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);

function codigo_(secreto, w) {
  const b = Utilities.computeHmacSha256Signature(String(w), secreto);
  const n = (((b[0] & 255) << 24) | ((b[1] & 255) << 16) | ((b[2] & 255) << 8) | (b[3] & 255)) >>> 0;
  return String(n % 1000000).padStart(6, "0");
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
  for (let i = v.length - 1; i >= 1; i--) if (v[i][0] === id) return {fila: i + 1, id: v[i][0], secreto: v[i][1], grupo: v[i][2], creada: new Date(v[i][3]), hasta: new Date(v[i][4])};
  return null;
}
function nuevoId_() {
  const a = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  let s = ""; for (let i = 0; i < 8; i++) s += a[Math.floor(Math.random() * a.length)];
  return s;
}

function doGet() { return json_({ok: true, servicio: "asistencia CCEEscopio", hora: Date.now()}); }

function doPost(e) {
  let d;
  try { d = JSON.parse(e.postData.contents); } catch (err) { return json_({ok: false, error: "Petición no válida."}); }
  const ahora = new Date();

  if (d.accion === "marcar") {
    const s = buscarSesion_(String(d.sesion || ""));
    if (!s) return json_({ok: false, error: "Este código QR no es válido. Vuelve a escanear el de la pantalla."});
    if (ahora >= s.hasta) return json_({ok: false, error: "El profesor ya ha terminado de pasar lista."});
    const dni = dni_(d.dni);
    if (!dni) return json_({ok: false, error: "El DNI o NIE no es válido (revisa los números y la letra)."});
    const w = Math.floor(ahora.getTime() / 1000 / VENTANA_SEG), cod = String(d.codigo || "");
    let valido = false;
    for (let k = -1; k < VALIDEZ_VENTANAS && !valido; k++) valido = cod === codigo_(s.secreto, w - k);
    if (!valido) return json_({ok: false, caducado: true, error: "El código QR ha caducado. Vuelve a escanear el que aparece ahora en la pantalla."});
    const disp = String(d.dispositivo || "").slice(0, 60);
    const cache = CacheService.getScriptCache();
    if (cache.get("dni_" + s.id + "_" + dni)) return json_({ok: true, mensaje: "Tu asistencia ya estaba registrada."});
    const otro = cache.get("disp_" + s.id + "_" + disp);
    if (otro && otro !== dni) return json_({ok: false, error: "Desde este móvil ya se ha registrado otro DNI en esta clase."});
    registros_().appendRow([ahora, s.id, dni, disp]);
    cache.put("dni_" + s.id + "_" + dni, "1", 21600); cache.put("disp_" + s.id + "_" + disp, dni, 21600);
    return json_({ok: true, mensaje: "Asistencia registrada.", hora: ahora.getTime(), grupo: s.grupo});
  }

  if (d.accion === "crear") {
    let id; do { id = nuevoId_(); } while (buscarSesion_(id));
    const secreto = Utilities.getUuid(), hasta = new Date(ahora.getTime() + DURACION_MAX_H * 3600000);
    sesiones_().appendRow([id, secreto, String(d.grupo || "").slice(0, 80), ahora, hasta]);
    return json_({ok: true, id, secreto, ahora: ahora.getTime(), ventana: VENTANA_SEG});
  }

  // Ver la lista o cerrar la sesión: solo con el secreto de la sesión
  const s = buscarSesion_(String(d.id || ""));
  if (!s || s.secreto !== d.secreto) return json_({ok: false, error: "Sesión no encontrada."});
  if (d.accion === "cerrar") sesiones_().getRange(s.fila, 5).setValue(ahora);
  if (d.accion === "lista" || d.accion === "cerrar") {
    const regs = registros_().getDataRange().getValues().slice(1).filter(r => r[1] === s.id)
      .map(r => ({hora: new Date(r[0]).getTime(), dni: r[2], dispositivo: r[3]}));
    return json_({ok: true, registros: regs, creada: s.creada.getTime()});
  }
  return json_({ok: false, error: "Acción desconocida."});
}
