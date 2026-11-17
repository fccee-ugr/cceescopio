"""Genera las páginas de Docencia por departamentos y asignaturas (carpeta docencia/) y el buscador de
indicadores (indicadores.qmd) a partir de tools/asignaturas.py y data/indicadores.json.
Uso (desde la carpeta del proyecto): python3 tools/make_pages.py && python3 tools/make_docencia.py"""
import json, os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asignaturas import DEPTS, H

cat = json.load(open("data/indicadores.json", encoding="utf-8"))
# Para cada identificador, la primera página en la que aparece (se evita la página regional duplicada)
porid = {}
for x in sorted(cat, key=lambda x: x["pagina"] == "andalucia"):
    porid.setdefault(x["id"], x)
HERR = {"calc": ("Calculadora de inflación", "calculadora"), "ficha": ("Ficha de país o región", "ficha"),
        "rel": ("Relaciona dos indicadores", "relaciona"), "rank": ("Rankings", "rankings"), "datos": ("Datos y fuentes", "datos")}

def anchor(t):
    import unicodedata
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:50]

os.makedirs("docencia", exist_ok=True)
nasig = 0
for d in DEPTS:
    out = [f'---\ntitle: "{d["nombre"]}"\nsubtitle: "Asignaturas de los grados de la Facultad e indicadores de CCEEscopio para usar en ellas"\n---\n',
           d["intro"] + "\n"]
    if d.get("web"):
        out.append(f'Web del departamento: <{d["web"]}>.\n')
    out.append("Cada indicador enlaza directamente con su gráfico interactivo, desde el que se pueden comparar países y regiones y descargar los datos en CSV.\n")
    for a in d["asig"]:
        nasig += 1
        out.append(f'## {a["nombre"]} {{#{anchor(a["nombre"])}}}\n')
        out.append(f'<p class="asig-grados">🎓 {a["grados"]}</p>\n')
        out.append("**Indicadores recomendados**\n")
        for i in a["ind"]:
            x = porid[i]
            out.append(f'- [{x["nombre"]}](../{x["pagina"]}.html?i={x["id"]}) <span class="asig-cat">{x["categoria"]}</span>')
        out.append("")
        out.append(f'::: {{.uso-box}}\n**Ejemplo de uso.** {a["uso"]}\n:::\n')
        if a["herr"]:
            hs = " · ".join(f'[{HERR[h][0]}](../{HERR[h][1]}.qmd)' for h in a["herr"])
            out.append(f"**Herramientas útiles:** {hs}\n")
    out.append('<p class="source">Asignaturas según los planes de estudio publicados en la web de la Facultad (<a href="https://fccee.ugr.es/docencia/grados">fccee.ugr.es/docencia/grados</a>), curso 2026/2027. La asignación a departamentos sigue el área de conocimiento de cada materia; consulta la guía docente para confirmarla. ¿Propones otros indicadores o ejemplos para tu asignatura? Escríbenos a <a href="mailto:investiga_ccee@ugr.es">investiga_ccee@ugr.es</a>.</p>\n')
    open(f'docencia/{d["slug"]}.qmd', "w", encoding="utf-8").write("\n".join(out))

# Bloque de tarjetas de departamentos para docencia.qmd
cards = "::: {.cards}\n" + "\n".join(
    f'[<span class="icon">🏛️</span><h3>{d["nombre"].replace("Departamento de ", "").replace("Departamentos de ", "")}</h3><p>{len(d["asig"])} asignaturas o grupos de asignaturas</p>](docencia/{d["slug"]}.qmd){{.card-ccee}}\n'
    for d in DEPTS) + ":::\n"
open("_deptos_cards.md", "w", encoding="utf-8").write(cards)

# Menú (fragmento YAML) para pegar en _quarto.yml
menu = "\n".join(f'          - href: docencia/{d["slug"]}.qmd\n            text: "{d["nombre"].replace("Departamento de ", "").replace("Departamentos de ", "")}"' for d in DEPTS)
open("tools/_menu_docencia.yml", "w", encoding="utf-8").write(menu + "\n")

# Buscador de indicadores
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

<p class="source">Si el buscador no se muestra, esta es la lista completa:</p>

<details><summary>Lista de indicadores</summary>

| Indicador | Categoría | Unidad | Frecuencia | Ámbito | Tabla de Eurostat |
|---|---|---|---|---|---|
{filas}

</details>
''')
print(f"{len(DEPTS)} páginas de departamentos, {nasig} asignaturas o grupos; buscador con {len(cat)} indicadores")
