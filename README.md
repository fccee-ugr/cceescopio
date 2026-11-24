# CCEEscopio

Observatorio de indicadores económicos y empresariales al servicio de la Docencia y la Investigación. Facultad de Ciencias Económicas y Empresariales de la Universidad de Granada. *Observando la economía y la empresa.*

Gestionado por el Vicedecanato de Investigación, Transferencia y Posgrado · investiga_ccee@ugr.es

## Estructura

```
_quarto.yml            configuración de la web (menú, pie, colores)
styles.scss            estilos con los colores de la Facultad
index.qmd              portada (vídeo, categorías, docencia e investigación)
precios.qmd …          páginas de indicadores (generadas, ver más abajo)
andalucia.qmd          indicadores regionales
rankings.qmd           La Facultad en los ranking: la UGR por disciplinas (data/rankings_ugr_areas.csv)
datos.qmd              descarga de datos, cómo citar, código R/Python, fuentes
docencia.qmd           usos en docencia e investigación
contacto.qmd           contacto
_helpers.qmd           funciones comunes (plantilla: make_pages.py las copia en cada página)
_panel.qmd             panel común (plantilla: make_pages.py lo copia en cada página)
_goatcounter.html      contador de visitas (opcional)
images/                logos de la UGR y la Facultad; images/brand: logo de CCEEscopio
media/                 vídeo de presentación y su portada
tools/make_pages.py    genera las páginas de indicadores a partir de una lista única
                       (y data/indicadores.json, data/indicadores_specs.json)
tools/make_apps.py     genera las herramientas: calculadora.qmd, ficha.qmd, relaciona.qmd
tools/grados.py        planes de estudio de GADE, GECO, GFICO, GMIM y GTUR por cursos
tools/asignaturas.py   fichas de uso por materia (indicadores recomendados y ejemplos de uso)
tools/make_docencia.py genera docencia/<grado>.qmd, indicadores.qmd (buscador)
                       y _grados_cards.md (tarjetas de docencia.qmd)
docencia/              páginas por grado, curso y asignatura (generadas)
tools/make_logo.py     genera el logo
tools/make_ppt.py      genera ppt.qmd (Piedra, papel o tijera) a partir de concurso.qmd
tools/make_informe.py  genera informe-coyuntura.qmd (plantilla de informe de coyuntura y rúbrica)
tools/make_muestra.py  genera tamano-muestral.qmd (calculadora de tamaño muestral);
                       las fórmulas están en tools/muestra.js (pruebas: node tools/muestra.js)
detecta-engano.qmd     «Detecta el engaño»: gráficos honestos y engañosos con datos de Eurostat
```

## Añadir o modificar indicadores

1. Edita la lista de la categoría correspondiente en `tools/make_pages.py` (nombre, código de la tabla de Eurostat, filtros, unidad, frecuencia y descripción; `regional=True` para tablas por comunidades autónomas).
2. Regenera todo, en este orden:

```
python3 tools/make_pages.py
python3 tools/make_apps.py
python3 tools/make_docencia.py
python3 tools/make_ppt.py        # después de generar concurso.qmd
python3 tools/make_informe.py
python3 tools/make_muestra.py
quarto render
```

Cada indicador tiene un identificador (se crea a partir de su nombre) que permite enlazarlo directamente: `precios.html?i=ipca-inflacion-general-tasa-anual`. Si cambias el nombre de un indicador, actualiza su alias en `tools/asignaturas.py`.

## Docencia por grados y asignaturas

Las asignaturas de cada grado y curso están en `tools/grados.py` y los indicadores recomendados y el ejemplo de uso de cada materia, en `tools/asignaturas.py`. Para añadir una asignatura o cambiar un ejemplo, edita esos ficheros y ejecuta `python3 tools/make_docencia.py`.

## Publicar

`quarto render` genera la web en `docs/`; en GitHub, *Settings → Pages → Deploy from branch → main /docs*. Cambia `site-url` en `_quarto.yml` por la dirección definitiva.

No necesita R: todos los datos se descargan en el navegador desde la API de Eurostat.

## Actualizar los rankings

Edita `data/rankings_ugr_areas.csv` con las nuevas ediciones publicadas en https://analitica.ugr.es/rankings/. Las posiciones mundiales del Ranking de Shanghái por materias pueden consultarse en la web oficial (https://www.shanghairanking.com/rankings/gras/2026); la UGR aparece en Economics (AS0501), Business Administration (AS0509), Management (AS0511) y Hospitality & Tourism Management (AS0513).
