"""Planes de estudio de los grados de la Facultad (curso 2026/2027), según https://fccee.ugr.es/docencia/grados.
Asignaturas separadas por ";"; el asterisco indica optativa. Para cada asignatura, tools/make_docencia.py busca en
tools/asignaturas.py la ficha (indicadores y ejemplo de uso) de la materia correspondiente."""
GR = {
"GADE": ("Grado en Administración y Dirección de Empresas", "https://fccee.ugr.es/docencia/grados/graduadoa-administracion-y-direccion-empresas", {
 1: "Economía Política; Fundamentos de Dirección y Administración de Empresas; Introducción a las Operaciones Financieras; Introducción al Márketing; Matemáticas; Contabilidad General; Historia del Desarrollo Económico Mundial Contemporáneo; Introducción al Derecho; Matemáticas Empresariales; Microeconomía",
 2: "Contabilidad Financiera I; Dirección Comercial; Dirección y Administración de Empresas; Macroeconomía; Técnicas Cuantitativas I; Análisis de Operaciones Financieras; Contabilidad Financiera II; Economía Mundial; Organización de Empresas; Técnicas Cuantitativas II",
 3: "Contabilidad de Gestión; Derecho Fiscal; Dirección Estratégica de la Empresa I; Dirección de Operaciones I; Econometría; Análisis de Estados Financieros; Dirección Estratégica de la Empresa II; Dirección de Recursos Humanos I; Economía Española; Métodos Cuantitativos",
 4: "Auditoría de Estados Financieros*; Comercio Exterior*; Creación de Empresas; Dirección Financiera; Dirección de Operaciones II*; Distribución Comercial*; Gestión Medioambiental de la Empresa*; Gestión de Empresas en el Marco Internacional*; Gestión de la Calidad Empresarial*; Investigación de Mercados*; Organización Industrial: Evidencias Históricas*; Análisis y Control de Costes*; Comunicación Comercial*; Dirección de Recursos Humanos II*; Dirección de la Innovación y la Tecnología*; Planificación y Valoración de Empresas*; Régimen Laboral de la Empresa*"}),
"GECO": ("Grado en Economía", "https://fccee.ugr.es/docencia/grados/graduadoa-economia", {
 1: "Economía Política; Fundamentos de Dirección y Administración de Empresas; Introducción a las Operaciones Financieras; Introducción al Márketing; Matemáticas; Contabilidad General; Historia del Desarrollo Económico Mundial Contemporáneo; Introducción al Derecho; Matemáticas para la Economía I; Microeconomía I",
 2: "Instrumentos para el Análisis de la Economía Española y Mundial; Macroeconomía I; Matemáticas para la Economía II; Microeconomía II; Técnicas Cuantitativas I; Economía Española; Economía Mundial; Macroeconomía II; Microeconomía III; Técnicas Cuantitativas II",
 3: "Econometría I; Economía del Sector Público I; Macroeconomía III; Microeconomía IV; Política Económica: Objetivos e Instrumentos; Econometría II; Economía del Sector Público II; Historia del Pensamiento Económico; Macroeconomía IV; Organización Económica Internacional",
 4: "Creación de Empresas; Econometría III; Economía Monetaria y Bancaria*; Economía de la Salud*; Economía del Gasto Público*; Economía del Trabajo*; Economía y Política Regional*; Historia Económica de España*; Macroeconomía Internacional*; Política Económica de España*; Economía Experimental*; Economía Urbana*; Economía de la Unión Europea*; Economía del Medio Ambiente y de los Recursos Naturales*; Historia Económica de Andalucía*; Integración Económica Internacional*"}),
"GFICO": ("Grado en Finanzas y Contabilidad", "https://fccee.ugr.es/docencia/grados/graduadoa-finanzas-y-contabilidad", {
 1: "Economía Política; Fundamentos de Dirección y Administración de Empresas; Introducción a las Operaciones Financieras; Introducción al Márketing; Matemáticas; Contabilidad General; Economía Española y Mundial; Historia del Desarrollo Económico Mundial Contemporáneo; Introducción al Derecho; Microeconomía",
 2: "Contabilidad Financiera; Derecho Mercantil: Estatuto Jurídico del Empresario y Sociedades Mercantiles; Dirección Financiera I; Macroeconomía; Técnicas Cuantitativas I; Contabilidad Financiera Avanzada; Derecho Fiscal; Dirección Financiera II; Sistema Financiero; Técnicas Cuantitativas II",
 3: "Consolidación de Estados Financieros*; Contabilidad de Entidades Públicas*; Contabilidad de Gestión I; Econometría; Estados Financieros; Hacienda Pública*; Historia de la Empresa*; Imposición Indirecta*; Instrumentos y Mercados Financieros; Planificación Financiera y Valoración de Empresas*; Análisis Contable I; Auditoría de Estados Financieros*; Contabilidad de Gestión Avanzada*; Contabilidad de Gestión II; Dirección Estratégica de la Empresa; Finanzas Internacionales*; Imposición Directa de las Sociedades*; Informática Aplicada a la Gestión Empresarial*; Marketing Financiero*; Métodos Cuantitativos para Finanzas y Contabilidad*; Productos Financieros y Bancarios",
 4: "Análisis Contable II; Creación de Empresas; Gestión de Renta Fija; Productos Derivados"}),
"GMIM": ("Grado en Marketing e Investigación de Mercados", "https://fccee.ugr.es/docencia/grados/graduadoa-marketing-e-investigacion-mercados", {
 1: "Economía Política; Fundamentos de Dirección y Administración de Empresas; Introducción a las Operaciones Financieras; Introducción al Márketing; Matemáticas; Contabilidad General; Dirección Comercial I; Historia del Desarrollo Económico Mundial Contemporáneo; Introducción al Derecho; Microeconomía",
 2: "Dirección Comercial II; Dirección y Administración de Empresas; Economía Española y Mundial; Macroeconomía; Técnicas Cuantitativas I; Comportamiento del Consumidor; Comunicación Integrada para el Marketing I; Distribución Comercial I; Investigación de Mercados I; Técnicas Cuantitativas II",
 3: "Comercio Exterior; Comunicación Integrada para el Marketing II; Dirección de Ventas; Econometría; Investigación de Mercados II; Distribución Comercial II; Investigación de Mercados III; Marketing Internacional; Marketing Sectorial; Técnicas Cuantitativas III",
 4: "Análisis de Datos Cualitativos*; Creación de Empresas; Desarrollo de Nuevos Productos*; Historia de la Actividad Comercial y del Marketing*; Informática Aplicada a la Gestión Comercial*; Marketing Social y Político; Planificación de Medios y Soportes*; Técnicas Estadísticas Multivariantes*; Información Contable para la Gestión*; Logística y Merchandising*; Marketing Cultural y Turístico*; Marketing Electrónico*; Régimen Jurídico del Mercado*; Sistemas Informáticos de Soporte a la Colaboración y Decisión*; Sociología del Consumo*"}),
"GTUR": ("Grado en Turismo", "https://fccee.ugr.es/docencia/grados/graduadoa-turismo", {
 1: "Estadística Aplicada al Sector Turístico; Fundamentos en Dirección y Administración de Empresas; Principios de Economía I; Recursos Territoriales Turísticos del Mundo; Introducción al Derecho; Principios de Economía II; Recursos Territoriales Turísticos de España",
 2: "Derecho Mercantil; Introducción al Márketing; Contabilidad General; Dirección Comercial; Dirección de Recursos Humanos en Empresas Turísticas; Estructura Económica del Turismo",
 3: "Información Contable para la Gestión de Empresas Turísticas; Marketing de Productos Turísticos; Política Económica del Turismo; Tecnología Informática para la Empresa; Dirección Estratégica de Empresas Turísticas; Gestión Financiera; Organización Internacional del Turismo; Planificación y Gestión Territorial para el Turismo Sostenible; Turismo Sostenible y Medio Ambiente",
 4: "Creación de Empresas; Economía del Transporte; Fiscalidad de las Empresas del Sector del Turismo*; Geografía Turística de Andalucía*; Historia Económica y Social del Turismo*; Planificación y Valoración de Empresas*; Sociología del Turismo y del Ocio*; Marketing Hotelero y de Restauración*; Relaciones de Trabajo y Contratación Laboral*; Sistemas de Información Basados en Internet*"}),
}


# Resto de titulaciones de grado de la Facultad (https://fccee.ugr.es/docencia/grados, consultada el 24-11-2026).
# Comparten las asignaturas del grado indicado, de modo que usan la misma página de Docencia.
# (sigla del grado, etiqueta corta, nombre oficial, URL)
COMPARTEN = {
"GADE": [
 ("GADE + Derecho", "Doble Grado en Administración y Dirección de Empresas y en Derecho", "https://fccee.ugr.es/docencia/grados/graduadoa-administracion-y-direccion-empresas-derecho"),
 ("GADE + Edificación", "Doble Grado en Edificación y en Administración y Dirección de Empresas", "https://fccee.ugr.es/docencia/grados/graduadoa-edificacion-administ-y-direcc-empresas"),
 ("GADE + Ingeniería Civil", "Doble Grado en Ingeniería Civil y en Administración y Dirección de Empresas", "https://fccee.ugr.es/docencia/grados/grado-ingenieria-civil-y-administracion-y-dreccion-empresas"),
 ("GADE + Ingeniería Informática", "Doble Grado en Ingeniería Informática y en Administración y Dirección de Empresas", "https://fccee.ugr.es/docencia/grados/graduadoa-inga-informatica-administ-y-direcc-empresas"),
],
"GECO": [("GECO bilingüe", "Grado en Economía (Bilingüe)", "https://fccee.ugr.es/docencia/grados/grado-economia-bilingue")],
"GTUR": [("TITUR", "Doble Grado en Traducción e Interpretación y en Turismo", "https://fccee.ugr.es/docencia/grados/graduadoa-traduccion-e-interpretacion-turismo")],
}
# Texto de la nota que aparece al principio de la página de cada grado
NOTA = {
"GADE": ("También para GADE + Derecho y GADE + Ingenierías",
  "Esta página sirve igualmente para los **dobles grados con ADE**: [GADE + Derecho]({0}) y **GADE + Ingenierías** ([Edificación]({1}), [Ingeniería Civil]({2}) e [Ingeniería Informática]({3})). "
  "En ellos se cursan las mismas asignaturas de ADE que aparecen aquí, repartidas en cinco cursos, salvo algunas que se reconocen por asignaturas equivalentes de la otra titulación "
  "(por ejemplo, Matemáticas o Técnicas Cuantitativas I en las ingenierías): el curso en el que se imparte cada una figura en la guía de cada doble grado."),
"GECO": ("También para el Grado en Economía (Bilingüe)",
  "El [Grado en Economía (Bilingüe)]({0}) sigue este mismo plan de estudios, con parte de la docencia en inglés: todos los indicadores y ejemplos de esta página sirven también para él. "
  "El botón **EN** del menú muestra CCEEscopio en inglés."),
"GTUR": ("También para Turismo + Traducción e Interpretación (TITUR)",
  "Esta página sirve igualmente para el [Doble Grado en Traducción e Interpretación y en Turismo (TITUR)]({0}), en sus modalidades de alemán, francés e inglés: "
  "las asignaturas de Turismo son las de este grado; el curso en el que se imparte cada una figura en la guía del doble grado."),
}
# Másteres universitarios y doctorado (https://fccee.ugr.es/docencia/posgrados, consultada el 24-11-2026): nombre, URL y recursos de CCEEscopio recomendados
POSGRADO = [
 ("Máster Universitario en Auditoría", "https://fccee.ugr.es/docencia/posgrados/master-universitario-auditoria-1",
  ["empresas.qmd|Demografía empresarial", "publico.qmd|Sector público y mercados financieros", "mercados.qmd|Mercados al día", "hipoteca.qmd|Simulador de préstamos", "dato-imposible.qmd|El dato imposible"]),
 ("Máster Universitario en Economía / Economics", "https://fccee.ugr.es/docencia/posgrados/master-universitario-economia-economics",
  ["convergencia.qmd|Convergencia sigma y beta", "desfases.qmd|¿Qué indicador se adelanta?", "regresion.qmd|Regresión con análisis de supuestos", "desigualdad-calc.qmd|Desigualdad: Gini, Lorenz y Theil", "politica-fiscal.qmd|Simulador de política fiscal", "sim-banco-central.qmd|Gobernador del Banco Central"]),
 ("Máster Universitario en Economía y Organización de Empresas", "https://fccee.ugr.es/docencia/posgrados/master-universitario-economia-y-organizacion-empresas",
  ["empresa.qmd|Empresa, innovación y digitalización", "empresas.qmd|Demografía empresarial", "regresion.qmd|Regresión", "ideas-tfg.qmd|Ideas para tu TFM", "graficos.qmd|Generador de gráficos con cita"]),
 ("Máster Universitario en Gestión y Tecnologías de Procesos de Negocio", "https://fccee.ugr.es/docencia/posgrados/master-universitario-gestion-y-tecnologias-procesos-negocio",
  ["empresa.qmd|Digitalización e inteligencia artificial en las empresas", "estadistica.qmd|Análisis cuantitativo de datos", "prevision.qmd|Previsión sencilla", "datos.qmd|Datos y fuentes (API y descarga)"]),
 ("Máster Universitario en Marketing y Comportamiento del Consumidor", "https://fccee.ugr.es/docencia/posgrados/master-universitario-marketing-y-comportamiento-del-consumidor",
  ["consumo.qmd|Consumo y confianza", "precios-productos.qmd|Precios de productos", "estadistica.qmd|Análisis cuantitativo de datos", "correlacion.qmd|¿Correlación o causalidad?", "sim-turismo.qmd|Gestiona tu destino turístico"]),
 ("Máster Universitario en Técnicas Cuantitativas en Gestión Empresarial", "https://fccee.ugr.es/docencia/posgrados/master-universitario-tecnicas-cuantitativas-gestion-empresarial",
  ["estadistica.qmd|Análisis cuantitativo de datos", "regresion.qmd|Regresión con análisis de supuestos", "prevision.qmd|Previsión sencilla", "numeros-indice.qmd|Laboratorio de números índice", "desigualdad-calc.qmd|Desigualdad con inferencia", "sim-cartera.qmd|Gestiona una cartera"]),
 ("Programa de Doctorado en Ciencias Económicas y Empresariales", "https://fccee.ugr.es/docencia/posgrados/doctorado",
  ["datos.qmd|Datos y fuentes: descarga y reutilización", "biblioteca.qmd|Bases de datos de la Biblioteca", "graficos.qmd|Generador de gráficos con cita", "desigualdad-calc.qmd|Desigualdad con inferencia", "rankings.qmd|La Facultad en los ranking"]),
]
