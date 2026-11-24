# CCEEscopio D+I · Reorganización, titulaciones, inglés, recursos nuevos y vídeo (24-11-2026)

Descomprime el paquete **en la raíz del repositorio** (sobrescribe), haz *commit* y *push* a `main`.
La carpeta `docs/` ya está generada con Quarto 1.7.32: no hace falta renderizar.

## Qué cambia

| Cambio | Ficheros principales |
|---|---|
| **Menú reordenado** en seis secciones sin opciones repetidas (Indicadores, Actualidad, Herramientas, Docencia, Juegos y simuladores, Investigación) más el menú «🧭 Más» | `_quarto.yml`, `styles.scss` |
| **Portada por objetivos** («¿Qué quieres hacer?»), titulaciones y novedades resumidas | `index.qmd`, `novedades.qmd` |
| **Todos los recursos**: buscador con filtros por tipo, titulación y público | `recursos.qmd` |
| **Todas las titulaciones**: dobles grados, Economía bilingüe, másteres y doctorado | `tools/grados.py`, `tools/make_docencia.py`, `docencia.qmd`, `docencia/*.qmd`, `_titulaciones.md`, `_grados_cards.md` |
| **Recursos nuevos**: rutas de aprendizaje, escape room económico, El dato imposible, ¿Correlación o causalidad? | `rutas.qmd`, `escape-room.qmd`, `dato-imposible.qmd`, `correlacion.qmd`, `juegos.qmd` |
| **Botón EN / ES** en todas las páginas (traducción automática de Google) | `_idioma.html` |
| **Vídeo nuevo** (66 s, 1080p) y su código | `media/cceescopio_video.mp4`, `media/cceescopio_video_portada.jpg`, `tools/video/` |
| Noticias del día: se descartan sorteos, horóscopos y similares | `tools/noticias_portada.py` |

## Después de subirlo

- No hay que hacer nada más: las acciones de GitHub siguen igual. La de las noticias de portada se ejecuta sola al subir el cambio.
- Se puede borrar el CSS antiguo que quede en `docs/site_libs/bootstrap/` (solo se usa el `bootstrap-….min.css` más reciente).
- **Botón EN**: pruébalo en la web publicada. Usa el traductor de Google en la propia página y recuerda la elección al navegar. Si Google no responde, abre la página en translate.google.com.
- **Vídeo**: para regenerarlo con cotizaciones nuevas, `python tools/video/render.py datos bolsa.json` y `python tools/video/render.py todo` (necesita Playwright, Chrome, ffmpeg y las fuentes Inter y Lora).

## Para añadir una titulación o un recurso

- Titulaciones: `tools/grados.py` (diccionarios `COMPARTEN`, `NOTA` y `POSGRADO`) y después `python3 tools/make_pages.py && python3 tools/make_docencia.py`.
- Recursos del buscador: la lista `R` de `recursos.qmd` (una línea por recurso).
