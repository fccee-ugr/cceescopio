# Cambios en CCEEscopio (25/11/2026)

Descomprime este ZIP en la raíz del repositorio (sobrescribe los ficheros) y después:

    quarto render
    git add -A
    git commit -m "Solicitud de generador de exámenes, juego Apuesta y acierta, nuevo lema y titulaciones"
    git push

Qué cambia:
- Nuevo lema en el logo (images/brand/cceescopio_logo_di.png y .svg; se regenera con tools/make_logo_di.py) y en el vídeo (media/cceescopio_video.mp4 y su portada).
- Nombres de titulaciones: GADE · GADE + Derecho · GADE + Ingenierías; GECO · GECO Bilingüe; GTUR · TITUR (menú, tarjetas, portada, buscador, páginas y vídeo; también en tools/make_docencia.py).
- Docencia: nueva sección «Solicita un generador de exámenes y un juego para tu asignatura» (docencia.qmd#solicita) con la plantilla media/solicitud_generador_examenes_CCEEscopio.docx (se regenera con node tools/make_solicitud.js . media/solicitud_generador_examenes_CCEEscopio.docx).
- Nuevo juego «Apuesta y acierta» (apuestas.qmd, generado con python3 tools/make_apuestas.py a partir de concurso.qmd).
