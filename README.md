# CCEEscopio

Observatorio de indicadores económicos y empresariales de la Facultad de Ciencias Económicas y Empresariales de la Universidad de Granada. *Observando la economía y la empresa.*

Gestionado por el Vicedecanato de Investigación, Transferencia y Posgrado · investiga_ccee@ugr.es

## Estructura

```
_quarto.yml            configuración de la web (menú, pie, colores)
styles.scss            estilos con los colores de la Facultad
index.qmd              portada (vídeo, categorías, docencia e investigación)
precios.qmd …          páginas de indicadores (generadas, ver más abajo)
andalucia.qmd          indicadores regionales
rankings.qmd           la UGR en los rankings por disciplinas (data/rankings_ugr_areas.csv)
datos.qmd              descarga de datos, cómo citar, código R/Python, fuentes
docencia.qmd           usos en docencia e investigación
contacto.qmd           contacto
_helpers.qmd           funciones comunes (plantilla: make_pages.py las copia en cada página)
_panel.qmd             panel común (plantilla: make_pages.py lo copia en cada página)
_goatcounter.html      contador de visitas (opcional)
images/                logos de la UGR y la Facultad; images/brand: logo de CCEEscopio
media/                 vídeo de presentación y su portada
tools/make_pages.py    genera las páginas de indicadores a partir de una lista única
tools/make_logo.py     genera el logo
```

## Añadir o modificar indicadores

1. Edita la lista de la categoría correspondiente en `tools/make_pages.py` (nombre, código de la tabla de Eurostat, filtros, unidad, frecuencia y descripción; `regional=True` para tablas por comunidades autónomas).
2. Ejecuta `python3 tools/make_pages.py` para regenerar las páginas.
3. Ejecuta `quarto render`.

Los filtros de cada tabla se pueden consultar en el navegador de datos de Eurostat (https://ec.europa.eu/eurostat/databrowser). Si una consulta falla, la web intenta alternativas (por ejemplo, la tabla anterior del IPCA) y, en último caso, muestra un aviso con el enlace a Eurostat.

## Publicar

Igual que THEILUMINA: `quarto render` genera la web en `docs/`; en GitHub, *Settings → Pages → Deploy from branch → main /docs*. Cambia `site-url` en `_quarto.yml` por la dirección definitiva.

No necesita R: todos los datos se descargan en el navegador desde la API de Eurostat.

## Actualizar los rankings

Edita `data/rankings_ugr_areas.csv` con las nuevas ediciones publicadas en https://analitica.ugr.es/rankings/.
