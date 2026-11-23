# CCEEscopio D+I · Novedades (23-11-2026)

Este paquete contiene los ficheros **nuevos y modificados** del repositorio `fccee-ugr/cceescopio`, con las mismas rutas.
Descomprímelo **en la raíz del repositorio** (sobrescribe los existentes), haz *commit* y *push* a `main`.
La carpeta `docs/` ya está generada con Quarto 1.7.32, así que no hace falta volver a renderizar.

## Qué incluye

| Novedad | Ficheros |
|---|---|
| **Hoy en la economía** (portada): noticias del día de España, Europa y el mundo, seleccionadas cada mañana antes de las 9:00, y las cotizaciones de las bolsas | `index.qmd`, `tools/noticias_portada.py`, `.github/workflows/portada.yml` |
| **Bolsa al día**: 25 índices, materias primas y empresas del IBEX 35, tres veces cada día hábil | `bolsa.qmd`, `tools/bolsa.py`, `.github/workflows/bolsa.yml` |
| **Simuladores**: Gobernador del Banco Central, Gestiona una cartera, Llega a fin de mes y Gestiona tu destino turístico, más un catálogo con filtro por grados | `simuladores.qmd`, `sim-*.qmd`, `js/sim-bc.js`, `js/sim-turismo.js`, `js/ccee-sim.js` |
| **Vídeo de inicio renovado** (2 min 15 s): con las tres novedades y la misma música | `media/cceescopio_video.mp4`, `media/cceescopio_video_portada.jpg`, `tools/make_video.py` |
| Menú, estilos y enlaces | `_quarto.yml` (menú «Juegos y simuladores», «Bolsa al día» en Indicadores y Herramientas, `js/*` en recursos), `styles.scss`, `calculadoras.qmd`, `juegos.qmd` |

## Después de subirlo (una sola vez)

1. En GitHub: **Settings → Actions → General → Workflow permissions → Read and write permissions** (ya debería estar, porque lo usan las noticias).
2. En **Actions**, lanza a mano (**Run workflow**) las dos acciones nuevas para que haya datos desde el primer momento:
   - «Bolsa de CCEEscopio» → crea la rama `bolsa` (`bolsa.json` y `bolsa-resumen.json`).
   - «Noticias del día (portada)» → crea la rama `portada` (`portada.json`).
3. A partir de ahí se actualizan solas: la bolsa a las 7:12 (de lunes a sábado), 17:52 y 22:33 (de lunes a viernes; horas de Madrid en invierno, una más en verano), y las noticias cada mañana hacia las 8:25 (con guarda para el cambio de hora: nunca después de las 9:59 ni dos veces el mismo día).

Igual que las noticias actuales, los datos viven en ramas propias y la web los lee de `raw.githubusercontent.com`: **no hace falta volver a generar la web** para que se actualicen.

## Avisos

- **Fuente de la bolsa**: Yahoo Finance (API pública de gráficos, sin clave). Si algún día bloquea una descarga, se conservan los datos anteriores de ese valor y la tarjeta lo indica. Los datos se muestran con fines docentes y la página lo advierte.
- **Noticias**: Google Noticias (portadas de Economía y búsquedas por temas de las últimas 24 horas). Se eligen las noticias que publican más medios, se clasifican en España, Europa y el mundo, y se enlazan con los indicadores de CCEEscopio con las mismas reglas que «Noticias e indicadores».
- **Simuladores**: descargan de Eurostat en el navegador los datos de partida (inflación, paro y euríbor de la zona euro; inflación de España por grupos de gasto; pernoctaciones en Andalucía). Si Eurostat no responde, usan valores de referencia y lo dicen en pantalla. Cada página explica su modelo y sus supuestos.
- **Vídeo**: para regenerarlo, `python tools/make_video.py render 0 1 … 14` y unir las escenas con `ffmpeg -f concat`. La música es la del vídeo anterior, alargada.

## Probado

Las cuatro simulaciones se han jugado completas en Chrome (escritorio y móvil). Las páginas de bolsa y portada se han probado con datos simulados, porque desde el entorno de trabajo no había acceso a Yahoo, Google Noticias ni Eurostat: **la primera ejecución real de las acciones de GitHub es la prueba que falta**.
