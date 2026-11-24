"""Genera las páginas de Docencia por grados y asignaturas (docencia/gade.qmd, geco.qmd, gfico.qmd, gmim.qmd y gtur.qmd),
las tarjetas de docencia.qmd (_grados_cards.md) y el buscador de indicadores (indicadores.qmd).
Datos: tools/grados.py (planes de estudio), tools/asignaturas.py (fichas de uso por materia) y data/indicadores.json.
Uso (desde la carpeta del proyecto): python3 tools/make_pages.py && python3 tools/make_docencia.py"""
import json, os, re, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asignaturas import DEPTS
from grados import GR, COMPARTEN, NOTA, POSGRADO

cat = json.load(open("data/indicadores.json", encoding="utf-8"))
porid = {}
for x in sorted(cat, key=lambda x: x["pagina"] == "andalucia"):
    porid.setdefault(x["id"], x)
HERR = {"calc": ("Calculadora de inflación", "calculadora"), "ficha": ("Ficha de país o región", "ficha"),
        "rel": ("Relaciona dos indicadores", "relaciona"), "rank": ("Rankings", "rankings"), "datos": ("Datos y fuentes", "datos")}

# ---- Emparejamiento asignatura -> ficha de materia
def norm(t, keep_commas=False):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    t = re.sub(r"\([^)]*\)", " ", t)
    t = re.sub(r",", " , " if keep_commas else " ", t)
    t = re.sub(r"[^a-z0-9 ,]", " ", t)
    t = re.sub(r"\b(i|ii|iii|iv)\b", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    for _ in range(3):
        t = re.sub(r" y( ,|$| y )", r"\1", t)
    return re.sub(r"\s+", " ", t).strip()

FICHAS = [a for d in DEPTS for a in d["asig"]]
GN = [norm(a["nombre"], True) for a in FICHAS]
OVR = {"contabilidad financiera avanzada": "contabilidad financiera", "contabilidad de gestion avanzada": "contabilidad de gestion",
       "derecho mercantil estatuto juridico del empresario y sociedades mercantiles": "derecho mercantil",
       "fundamentos en direccion y administracion de empresas": "fundamentos de direccion y administracion de empresas",
       "planificacion y valoracion de empresas": "planificacion financiera y valoracion de empresas",
       "recursos territoriales turisticos de espana": "recursos territoriales turisticos",
       "recursos territoriales turisticos del mundo": "recursos territoriales turisticos",
       "sistemas informaticos de soporte a la colaboracion y decision": "sistemas de informacion basados en internet"}

def ficha(nombre):
    ns = norm(nombre); ns = OVR.get(ns, ns)
    c = [k for k, g in enumerate(GN) if g.replace(" ,", "") == ns]
    if not c:
        pat = re.compile(r"(^|, |\by |\be )" + re.escape(ns) + r"( ,| y | e |$| en )")
        c = [k for k, g in enumerate(GN) if pat.search(g)]
        if len(c) > 1:
            c = [k for k in c if re.search(r"(^|, |\by |\be )" + re.escape(ns) + r"( ,|$| en )", GN[k])] or c
    return FICHAS[c[0]] if c else None

def anchor(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:50]

CURSOS = {1: "Primer curso", 2: "Segundo curso", 3: "Tercer curso", 4: "Cuarto curso"}
os.makedirs("docencia", exist_ok=True)
resumen, faltan = [], []
for sig, (nombre, url, cursos) in GR.items():
    out = [f'---\ntitle: "{nombre} ({sig})"\nsubtitle: "Asignaturas del grado e indicadores de CCEEscopio para usar en ellas"\n---\n',
           f"Para cada asignatura del **{nombre}** se proponen los indicadores de CCEEscopio más útiles y un ejemplo de uso en clase. "
           f"Cada indicador enlaza directamente con su gráfico y su mapa interactivos, desde los que se pueden comparar países y regiones y descargar los datos en CSV. "
           f"Plan de estudios y guías docentes: [web de la Facultad]({url}).\n",
           "No se incluyen las asignaturas de idiomas, prácticas externas y Trabajo Fin de Grado. Las asignaturas optativas se marcan como *(optativa)*.\n"]
    if sig in NOTA:
        out.append(f"::: {{.callout-note}}\n## {NOTA[sig][0]}\n\n" + NOTA[sig][1].format(*[u for _, _, u in COMPARTEN[sig]]) + "\n:::\n")
    n = 0
    for c, txt in cursos.items():
        out.append(f"## {CURSOS[c]} {{#curso-{c}}}\n")
        for s in [x.strip() for x in txt.split(";") if x.strip()]:
            opt = s.endswith("*"); s = s.rstrip("*").strip()
            f = ficha(s)
            if not f:
                faltan.append(f"{sig}: {s}"); continue
            n += 1
            out.append(f'### {s}{" *(optativa)*" if opt else ""} {{#{anchor(s)}}}\n')
            out.append("**Indicadores recomendados:** " + " · ".join(
                f'[{porid[i]["nombre"]}](../{porid[i]["pagina"]}.html?i={porid[i]["id"]})' for i in f["ind"]) + "\n")
            out.append(f'::: {{.uso-box}}\n**Ejemplo de uso.** {f["uso"]}\n:::\n')
            if f["herr"]:
                out.append("**Herramientas útiles:** " + " · ".join(f'[{HERR[h][0]}](../{HERR[h][1]}.qmd)' for h in f["herr"]) + "\n")
            if s == "Técnicas Cuantitativas III":
                out.append('::: {.uso-box}\n**Para el profesorado:** [generador de exámenes de Técnicas Cuantitativas III](../examen-tc3.qmd), con muestreo y decisión, versiones aleatorias, soluciones y datos de Eurostat.\n:::\n')
    out.append('<p class="source">Asignaturas según el plan de estudios publicado en la web de la Facultad (<a href="https://fccee.ugr.es/docencia/grados">fccee.ugr.es/docencia/grados</a>), curso 2026/2027. ¿Propones otros indicadores o ejemplos para tu asignatura? Escríbenos a <a href="mailto:investiga_ccee@ugr.es">investiga_ccee@ugr.es</a>.</p>\n')
    open(f"docencia/{sig.lower()}.qmd", "w", encoding="utf-8").write("\n".join(out))
    resumen.append((sig, nombre, n))

EXTRA_CARD = {"GADE": " También para <b>GADE + Derecho</b> y <b>GADE + Ingenierías</b>.", "GECO": " También para <b>GECO bilingüe</b>.",
              "GTUR": " También para <b>Turismo + Traducción e Interpretación (TITUR)</b>."}
open("_grados_cards.md", "w", encoding="utf-8").write("::: {.cards}\n" + "\n".join(
    f'[<span class="icon">🎓</span><span class="ct">{sig}</span><span class="cd">{nombre}: {n} asignaturas con indicadores y ejemplos de uso.{EXTRA_CARD.get(sig, "")}</span>](docencia/{sig.lower()}.qmd){{.card-ccee}}\n'
    for sig, nombre, n in resumen)
    + '\n[<span class="icon">🎓</span><span class="ct">Másteres y doctorado</span><span class="cd">Recursos de CCEEscopio para los másteres universitarios y el programa de doctorado de la Facultad.</span>](docencia/posgrado.qmd){.card-ccee}\n'
    + ":::\n")

# ---- Tabla con todas las titulaciones de la Facultad (se incluye en docencia.qmd)
filas_t = []
for sig, (nombre, url, _) in GR.items():
    filas_t.append(f"| [{nombre}]({url}) | **{sig}** | [Asignaturas de {sig}](docencia/{sig.lower()}.qmd) |")
    for corta, largo, u in COMPARTEN.get(sig, []):
        filas_t.append(f"| [{largo}]({u}) | {corta} | [Asignaturas de {sig}](docencia/{sig.lower()}.qmd) (las mismas) |")
for nombre, url, _ in POSGRADO:
    filas_t.append(f"| [{nombre}]({url}) | Posgrado | [Másteres y doctorado](docencia/posgrado.qmd) |")
open("_titulaciones.md", "w", encoding="utf-8").write("| Titulación | En CCEEscopio | Dónde están sus recursos |\n|---|---|---|\n" + "\n".join(filas_t) + "\n")

# ---- Másteres y doctorado
pg = ['---\ntitle: "Másteres y doctorado"\nsubtitle: "Recursos de CCEEscopio para el posgrado de la Facultad"\n---\n',
      "Para cada máster universitario y para el programa de doctorado de la Facultad se proponen los recursos de CCEEscopio más útiles: datos descargables y citables, herramientas de análisis y actividades para clase. "
      "Oferta de posgrado: [web de la Facultad](https://fccee.ugr.es/docencia/posgrados).\n"]
for nombre, url, rec in POSGRADO:
    pg.append(f"## {nombre}\n")
    pg.append("**Recursos recomendados:** " + " · ".join(f"[{r.split('|')[1]}](../{r.split('|')[0]})" for r in rec) + "\n")
    pg.append(f'<p class="source"><a href="{url}">Información del título en la web de la Facultad</a></p>\n')
pg.append("## Para cualquier TFM o tesis\n")
pg.append("- [**Ideas para tu TFG o TFM**](../ideas-tfg.qmd): temas con pregunta, hipótesis, datos, método y estructura.\n- [**Generador de gráficos con cita de la fuente**](../graficos.qmd): gráficos listos para el trabajo, con la referencia en APA.\n"
          "- [**Datos y fuentes**](../datos.qmd): descarga en CSV, códigos de las tablas de Eurostat y ejemplos en R y Python.\n- [**Bases de datos de la Biblioteca y fuentes abiertas**](../biblioteca.qmd).\n"
          "- [**Rutas de aprendizaje**](../rutas.qmd): recorridos guiados por temas, también útiles como repaso al empezar un máster.\n")
open("docencia/posgrado.qmd", "w", encoding="utf-8").write("\n".join(pg))

# ---- Buscador de indicadores
filas = "\n".join(
    f'| [{x["nombre"]}]({x["pagina"]}.qmd) | {x["categoria"]} | {x["unidad"]} | {x["frecuencia"]} | {"Regional" if x["regional"] else "Países"} | {x["code"]} |'
    for x in cat)
js = json.dumps([dict(id=x["id"], n=x["nombre"], p=x["pagina"], c=x["categoria"], u=x["unidad"], f=x["frecuencia"],
                      r=x["regional"], code=x["code"], d=x["descripcion"]) for x in cat], ensure_ascii=False)
open("indicadores.qmd", "w", encoding="utf-8").write(f'''---
title: "Buscador de indicadores"
subtitle: "Todos los indicadores de CCEEscopio en una sola tabla"
toc: false
---

CCEEscopio reúne **{len(cat)} indicadores** de Eurostat sobre precios, empleo, actividad, empresa, turismo, sector público, desigualdad y pobreza, sostenibilidad, población, economía internacional y regiones. Escribe una palabra (por ejemplo, *pobreza*, *paro*, *energía* o *turismo*) para encontrar el indicador y abrir su gráfico.

```{{ojs}}
//| echo: false
catalogo = {js}
viewof q = Inputs.search(catalogo, {{placeholder: "Buscar indicador…", label: "Buscar", columns: ["n", "c", "d", "code"]}})
Inputs.table(q, {{
  columns: ["n", "c", "u", "f", "r", "code"],
  header: {{n: "Indicador", c: "Categoría", u: "Unidad", f: "Frecuencia", r: "Ámbito", code: "Tabla de Eurostat"}},
  format: {{n: (v, i, d) => html`<a href="${{d[i].p}}.html?i=${{d[i].id}}">${{v}}</a>`, r: v => v ? "Regiones" : "Países", code: v => html`<a href="https://ec.europa.eu/eurostat/databrowser/view/${{v}}/default/table" target="_blank" rel="noopener">${{v}}</a>`}},
  width: {{n: 330, c: 190, u: 170}}, rows: 25, layout: "auto"
}})
```

<details><summary>Lista completa de indicadores</summary>

| Indicador | Categoría | Unidad | Frecuencia | Ámbito | Tabla de Eurostat |
|---|---|---|---|---|---|
{filas}

</details>
''')
print("Grados:", ", ".join(f"{s} ({n})" for s, _, n in resumen), "| sin ficha:", faltan or "ninguna")
