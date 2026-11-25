// Plantilla de solicitud de generador de exámenes y juego para una asignatura (CCEEscopio D+I)
// Uso, desde la raíz del proyecto: node tools/make_solicitud.js . media/solicitud_generador_examenes_CCEEscopio.docx
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType, AlignmentType,
  BorderStyle, ShadingType, Header, Footer, PageNumber, LevelFormat, VerticalAlign, HeadingLevel, TabStopType,
} = require("docx");

const RAIZ = process.argv[2];
const SALIDA = process.argv[3];
const MG = "B5175F", OR = "F29200", GR = "3C3C3B", CREMA = "FBF7F3", LINEA = "D9C7CF";
const FONT = "Arial";
const W = 9638; // ancho útil A4 con márgenes de 2 cm (11906 - 2 * 1134)

const img = (f) => fs.readFileSync(`${RAIZ}/${f}`);
const t = (text, o = {}) => new TextRun({ text, font: FONT, size: o.size ?? 21, bold: o.bold, italics: o.italics, color: o.color ?? GR });
const p = (runs, o = {}) => new Paragraph({ children: Array.isArray(runs) ? runs : [t(runs, o)], spacing: { before: o.before ?? 0, after: o.after ?? 100, line: 276 }, alignment: o.align, keepNext: o.keepNext, numbering: o.numbering, indent: o.indent });
const casilla = (text, o = {}) => p([t("☐  ", { color: MG, bold: true, size: 22 }), t(text, o)], { after: o.after ?? 60, indent: { left: 200 } });
const h = (text) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text, font: FONT, size: 25, bold: true, color: MG })],
  spacing: { before: 280, after: 120 }, keepNext: true, border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: OR, space: 4 } } });
const nota = (text) => p([t(text, { size: 18, italics: true, color: "6B6B6B" })], { after: 120 });

const borde = { style: BorderStyle.SINGLE, size: 4, color: LINEA };
const bordes = { top: borde, bottom: borde, left: borde, right: borde };
const sinBorde = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const sinBordes = { top: sinBorde, bottom: sinBorde, left: sinBorde, right: sinBorde };

// Tabla de dos columnas: etiqueta y hueco para rellenar
function campos(filas, anchoEt = 3300) {
  return new Table({
    width: { size: W, type: WidthType.DXA }, columnWidths: [anchoEt, W - anchoEt],
    rows: filas.map(([et, alto]) => new TableRow({
      height: alto ? { value: alto, rule: "atLeast" } : undefined, cantSplit: true,
      children: [
        new TableCell({ width: { size: anchoEt, type: WidthType.DXA }, borders: bordes, shading: { fill: CREMA, type: ShadingType.CLEAR, color: "auto" },
          margins: { top: 80, bottom: 80, left: 120, right: 120 }, verticalAlign: VerticalAlign.CENTER, children: [p([t(et, { bold: true, size: 20 })], { after: 0 })] }),
        new TableCell({ width: { size: W - anchoEt, type: WidthType.DXA }, borders: bordes, margins: { top: 80, bottom: 80, left: 120, right: 120 }, children: [p("", { after: 0 })] }),
      ],
    })),
  });
}

// Casillas en varias columnas (sin bordes)
function rejilla(items, cols = 3) {
  const ancho = Math.floor(W / cols), anchos = Array(cols).fill(ancho); anchos[cols - 1] = W - ancho * (cols - 1);
  const filas = [];
  for (let i = 0; i < items.length; i += cols) {
    filas.push(new TableRow({ children: anchos.map((a, j) => new TableCell({ width: { size: a, type: WidthType.DXA }, borders: sinBordes, margins: { top: 20, bottom: 20, left: 60, right: 60 },
      children: [items[i + j] ? p([t("☐  ", { color: MG, bold: true, size: 22 }), t(items[i + j], { size: 20 })], { after: 40 }) : p("", { after: 0 })] })) }));
  }
  return new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: anchos, rows: filas });
}

// Juegos: nombre y descripción, con casilla
const JUEGOS = [
  ["Concurso de preguntas", "Preguntas de la asignatura con ranking en directo por aciertos y tiempo."],
  ["Apuesta y acierta", "Cada estudiante apuesta 10, 20, 50 o 100 € en cada pregunta; gana quien termine con más dinero."],
  ["Piedra, papel o tijera", "Cada acierto da una partida contra la aplicación; gana quien antes supere todas las preguntas."],
  ["Escape room", "Varias salas con enigmas de la asignatura que hay que resolver para salir a tiempo."],
  ["Memoria de datos", "Memorizar una malla de resultados o conceptos y desbloquear las casillas."],
  ["Ordena la malla", "Ordenar elementos (valores, etapas, resultados) de mayor a menor o en su secuencia correcta."],
  ["¿Quién es quién?", "Adivinar un concepto, método o caso a partir de sus características."],
  ["Bingo", "Tachar en el cartón las respuestas que cumplen cada condición que se va cantando."],
];
function tablaJuegos() {
  const c = [600, 2900, W - 3500];
  const celda = (ancho, hijos, fondo) => new TableCell({ width: { size: ancho, type: WidthType.DXA }, borders: bordes, margins: { top: 60, bottom: 60, left: 100, right: 100 },
    shading: fondo ? { fill: fondo, type: ShadingType.CLEAR, color: "auto" } : undefined, verticalAlign: VerticalAlign.CENTER, children: hijos });
  return new Table({
    width: { size: W, type: WidthType.DXA }, columnWidths: c,
    rows: [new TableRow({ tableHeader: true, children: [celda(c[0], [p([t("", {})], { after: 0 })], MG), celda(c[1], [p([t("Juego", { bold: true, color: "FFFFFF", size: 20 })], { after: 0 })], MG),
      celda(c[2], [p([t("En qué consiste", { bold: true, color: "FFFFFF", size: 20 })], { after: 0 })], MG)] }),
      ...JUEGOS.map(([n, d]) => new TableRow({ cantSplit: true, children: [celda(c[0], [p([t("☐", { color: MG, bold: true, size: 24 })], { after: 0, align: AlignmentType.CENTER })]),
        celda(c[1], [p([t(n, { bold: true, size: 20 })], { after: 0 })]), celda(c[2], [p([t(d, { size: 19 })], { after: 0 })])] })),
      new TableRow({ cantSplit: true, children: [celda(c[0], [p([t("☐", { color: MG, bold: true, size: 24 })], { after: 0, align: AlignmentType.CENTER })]),
        celda(c[1], [p([t("Otro (indíquelo)", { bold: true, size: 20 })], { after: 0 })]), celda(c[2], [p("", { after: 0 })])] }),
      new TableRow({ cantSplit: true, children: [celda(c[0], [p([t("☐", { color: MG, bold: true, size: 24 })], { after: 0, align: AlignmentType.CENTER })]),
        celda(c[1], [p([t("Ninguno", { bold: true, size: 20 })], { after: 0 })]), celda(c[2], [p([t("Solo se solicita el generador de exámenes.", { size: 19 })], { after: 0 })])] }),
    ],
  });
}

// Bloque de firma
function firmas() {
  const a = Math.floor(W / 2);
  const bloque = (titulo, sub) => new TableCell({ width: { size: a, type: WidthType.DXA }, borders: bordes, margins: { top: 120, bottom: 120, left: 160, right: 160 },
    children: [p([t(titulo, { bold: true, color: MG, size: 21 })], { after: 40 }), p([t(sub, { size: 18, italics: true, color: "6B6B6B" })], { after: 900 }),
      p([t("Firma", { size: 18, color: "6B6B6B" })], { after: 60 }), p([t("Nombre y apellidos: ", { size: 19 })], { after: 60 }), p([t("Fecha: ", { size: 19 })], { after: 0 })] });
  return new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: [a, W - a], rows: [new TableRow({ cantSplit: true, children: [
    bloque("Profesor/a responsable de la asignatura", "Solicitante"),
    bloque("Director/a del Departamento", "Visto bueno (firma obligatoria)"),
  ] })] });
}

// Cabecera con los logos
const cabecera = new Header({ children: [new Table({
  width: { size: W, type: WidthType.DXA }, columnWidths: [W / 2, W / 2],
  rows: [new TableRow({ children: [
    new TableCell({ width: { size: W / 2, type: WidthType.DXA }, borders: sinBordes, verticalAlign: VerticalAlign.CENTER,
      children: [new Paragraph({ children: [new ImageRun({ type: "jpg", data: img("images/logos_ugr_fccee.jpg"), transformation: { width: 236, height: 43 },
        altText: { title: "Universidad de Granada y Facultad", description: "Logos de la Universidad de Granada y de la Facultad de Ciencias Económicas y Empresariales", name: "logos-ugr-fccee" } })] })] }),
    new TableCell({ width: { size: W / 2, type: WidthType.DXA }, borders: sinBordes, verticalAlign: VerticalAlign.CENTER,
      children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new ImageRun({ type: "png", data: img("images/brand/cceescopio_logo_di.png"), transformation: { width: 200, height: 44 },
        altText: { title: "CCEEscopio D+I", description: "Logo de CCEEscopio D+I", name: "logo-cceescopio" } })] })] }),
  ] })],
}), new Paragraph({ spacing: { after: 0 }, border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: MG, space: 6 } }, children: [] })] });

const pie = new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
  t("CCEEscopio D+I · Vicedecanato de Investigación, Transferencia y Posgrado · Facultad de Ciencias Económicas y Empresariales · investiga_ccee@ugr.es · Página ", { size: 16, color: "808080" }),
  new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 16, color: "808080" })] })] });

const cuerpo = [
  new Paragraph({ spacing: { before: 120, after: 60 }, children: [new TextRun({ text: "Solicitud de generador de exámenes y juego para una asignatura", font: FONT, size: 34, bold: true, color: MG })] }),
  p([t("CCEEscopio D+I · Observatorio de indicadores económicos y empresariales al servicio de la Docencia y la Investigación", { size: 19, color: OR, bold: true })], { after: 200 }),
  p([t("Con este formulario, el profesorado de la Facultad puede solicitar que CCEEscopio D+I incorpore un "), t("generador de exámenes", { bold: true }),
    t(" propio de su asignatura, como el de Técnicas Cuantitativas III, y, si lo desea, uno de los "), t("juegos de CCEEscopio", { bold: true }),
    t(" adaptado a sus contenidos. El generador crea exámenes aleatorios en el formato de la asignatura, con su versión con soluciones, listos para descargar en Word y en PDF.")]),
  p([t("Envíe el formulario, "), t("firmado por la dirección del Departamento", { bold: true }), t(", junto con la documentación del apartado 5, a "),
    t("investiga_ccee@ugr.es", { bold: true, color: MG }), t(", con el asunto «Solicitud de generador de exámenes: [nombre de la asignatura]».")], { after: 60 }),

  h("1. Datos de la asignatura"),
  campos([["Asignatura"], ["Código"], ["Departamento"], ["Curso y semestre"], ["Carácter (básica, obligatoria u optativa)"], ["Número de grupos y de estudiantes (aprox.)"]]),
  p([t("Titulaciones en las que se imparte", { bold: true })], { before: 160, after: 60, keepNext: true }),
  rejilla(["GADE", "GADE + Derecho", "GADE + Ingenierías", "GECO", "GECO Bilingüe", "GFICO", "GMIM", "GTUR", "TITUR", "Máster (indíquelo):", "Doctorado"], 3),

  h("2. Profesorado responsable"),
  campos([["Profesor/a responsable"], ["Correo electrónico"], ["Teléfono o extensión"], ["Otros profesores o profesoras de la asignatura"]]),

  h("3. Características del generador de exámenes"),
  campos([["Temas que pueden entrar en el examen", 700], ["Número de preguntas o problemas por examen"], ["Reglas para combinarlos (p. ej., como máximo un problema por tema)", 700],
    ["Puntuación máxima y reparto por apartados"], ["Duración del examen"], ["Formulario, tablas o material permitido", 500],
    ["Otras indicaciones (formato, cabecera, normas del examen…)", 900]], 3800),
  p([t("Modalidades de evaluación que debe cubrir", { bold: true })], { before: 160, after: 60, keepNext: true }),
  casilla("Evaluación continua"),
  casilla("Evaluación Única Final (con una pregunta adicional, si procede)"),
  casilla("Convocatoria extraordinaria"),
  p([t("Soluciones que debe generar", { bold: true })], { before: 160, after: 60, keepNext: true }),
  casilla("Solo los resultados de cada apartado"),
  casilla("Soluciones completas: desarrollo, fórmulas aplicadas e interpretación o comentario de cada resultado"),
  p([t("Uso de datos reales de CCEEscopio en los enunciados", { bold: true })], { before: 160, after: 60, keepNext: true }),
  casilla("Sí, cuando el contenido lo permita (indicadores de Eurostat del observatorio)"),
  casilla("No, solo datos simulados"),

  h("4. Juego para la asignatura (opcional)"),
  p("Marque el juego de CCEEscopio que desea adaptar a la asignatura. Todos se juegan en clase desde el móvil, con código QR y ranking en directo, y usan preguntas de la propia asignatura.", { after: 120 }),
  tablaJuegos(),

  h("5. Documentación que debe adjuntar"),
  p([t("Para el generador de exámenes:", { bold: true })], { after: 60, keepNext: true }),
  casilla("Una batería de al menos 5 exámenes resueltos de la asignatura (de convocatorias anteriores o de prácticas). Si se solicitan soluciones completas, los exámenes deben incluir el desarrollo y los comentarios de cada apartado.", { after: 80 }),
  casilla("Los exámenes en un formato editable (Word, LaTeX o similar), siempre que sea posible. Se admite PDF.", { after: 80 }),
  casilla("La guía docente o el temario de la asignatura.", { after: 80 }),
  casilla("El formulario, las tablas o el material que se entrega a los estudiantes en el examen, si lo hay.", { after: 80 }),
  casilla("La plantilla o cabecera habitual del examen, si se quiere conservar el mismo formato.", { after: 140 }),
  p([t("Para el juego (si se ha elegido uno):", { bold: true })], { after: 60, keepNext: true }),
  casilla("Al menos 30 preguntas de tipo test o de verdadero o falso, con la respuesta correcta y una breve explicación. Si no se adjuntan, las preguntas se prepararán a partir de los exámenes resueltos.", { after: 80 }),

  h("6. Condiciones"),
  p([t("•  ", { color: MG, bold: true }), t("El generador y el juego se publicarán en CCEEscopio D+I, que es de acceso abierto, y se enlazarán desde la página de la asignatura. Los estudiantes podrán usarlos para practicar.")], { indent: { left: 200 } }),
  p([t("•  ", { color: MG, bold: true }), t("Los exámenes se generan al azar. El profesorado de la asignatura revisará el generador antes de su publicación y cada examen antes de usarlo.")], { indent: { left: 200 } }),
  p([t("•  ", { color: MG, bold: true }), t("La documentación aportada solo se usará para preparar el generador y el juego, y no se publicará tal como se entrega.")], { indent: { left: 200 } }),
  p([t("•  ", { color: MG, bold: true }), t("Ni el generador ni el juego guardan datos personales de los estudiantes.")], { indent: { left: 200 } }),
  p([t("•  ", { color: MG, bold: true }), t("Las solicitudes se atenderán por orden de llegada. El Vicedecanato comunicará el plazo previsto al recibir la solicitud.")], { indent: { left: 200 }, after: 160 }),

  h("7. Firmas"),
  p("El profesor o la profesora responsable solicita la incorporación del generador de exámenes y, en su caso, del juego indicado, y la dirección del Departamento da su visto bueno. Se admite firma electrónica.", { after: 160 }),
  firmas(),
  p("", { after: 120 }),
  nota("Envíe este formulario firmado y la documentación a investiga_ccee@ugr.es. Vicedecanato de Investigación, Transferencia y Posgrado, Facultad de Ciencias Económicas y Empresariales, Universidad de Granada."),
];

const doc = new Document({
  creator: "CCEEscopio D+I", title: "Solicitud de generador de exámenes y juego para una asignatura", description: "Plantilla de solicitud para el profesorado de la Facultad",
  styles: { default: { document: { run: { font: FONT, size: 21 } } },
    paragraphStyles: [{ id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 25, bold: true, color: MG }, paragraph: { spacing: { before: 280, after: 120 }, outlineLevel: 0, keepNext: true } }] },
  sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1600, bottom: 1134, left: 1134, right: 1134, header: 500, footer: 500 } } },
    headers: { default: cabecera }, footers: { default: pie }, children: cuerpo }],
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync(SALIDA, b); console.log("ok", SALIDA); });
