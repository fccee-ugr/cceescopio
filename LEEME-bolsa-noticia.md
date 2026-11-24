# CCEEscopio · Bolsa corregida y «Crea tu noticia» (24-11-2026)

Descomprime en la raíz del repositorio (sobrescribe), haz commit y push a main. La carpeta docs/ ya está regenerada.

1. Bolsa: la descarga usa ahora la librería yfinance (Yahoo bloquea las peticiones directas desde GitHub).
   Después de subirlo: Actions → «Bolsa de CCEEscopio» → Run workflow. Si termina en verde, se crea la rama «bolsa».
2. Avisos de Node 20: todas las acciones usan ya actions/checkout@v5 y actions/setup-python@v6 (Node 24).
3. «Crea tu noticia»: botón bajo la gráfica principal de las 11 páginas de indicadores (99 indicadores) y bajo la gráfica de Bolsa al día.
   Código en js/ccee-noticia.js; se añade a las páginas desde _panel.qmd y tools/make_pages.py.
   Se puede borrar sin problema docs/site_libs/bootstrap/bootstrap-bdfe3d2d08c237835f7fa3a677371bd4.min.css (ya no lo usa ninguna página).
