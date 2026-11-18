"""Genera uso.qmd: panel con las visitas y el uso de CCEEscopio leídos de GoatCounter."""
import json, os, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

def titulo(f):
    for l in open(f, encoding="utf-8"):
        if l.startswith("title:"):
            return l.split(":", 1)[1].strip().strip('"')
    return f

paginas = []
for f in sorted(glob.glob("*.qmd")) + sorted(glob.glob("docencia/*.qmd")):
    if os.path.basename(f).startswith("_") or f in ("uso.qmd",):
        continue
    html = f[:-4] + ".html"
    clave = f[:-4].replace("docencia/", "docencia-")
    paginas.append({"html": html, "clave": clave, "titulo": titulo(f)})

ind = json.load(open("data/indicadores.json", encoding="utf-8"))
inds = [{"id": d["id"], "nombre": d["nombre"], "pagina": d["pagina"]} for d in ind]

ENC = {
    "perfil": [("estudiante-grado", "Estudiante de grado"), ("estudiante-posgrado", "Estudiante de máster o doctorado"),
               ("pdi", "Profesorado o PI"), ("ptgas", "PTGAS"), ("otro", "Otro")],
    "grado": [("gade", "GADE"), ("geco", "GECO"), ("gfico", "GFICO"), ("gmim", "GMIM"), ("gtur", "GTUR"),
              ("doble-grado", "Doble grado"), ("ninguno", "Ninguno / otro")],
    "para": [("clases", "Clases"), ("estudiar", "Estudiar"), ("tfg-tfm", "TFG o TFM"), ("investigacion", "Investigación"),
             ("curiosidad", "Curiosidad")],
    "recurso": [("graficos", "Gráficos"), ("mapas", "Mapas"), ("descarga-csv", "Descarga CSV"), ("calculadora", "Calculadora"),
                ("ficha", "Ficha"), ("relaciona", "Relaciona"), ("buscador", "Buscador"), ("docencia-grados", "Grados y asignaturas"),
                ("rankings", "Rankings"), ("ejercicios", "Ejercicios"), ("graficos-tfg", "Gráficos TFG"),
                ("hipoteca", "Hipotecas"), ("paneles", "Paneles"), ("boletin", "Boletín"), ("glosario", "Glosario")],
    "recomendaria": [("si", "Sí"), ("quiza", "Quizá"), ("no", "No")],
}

qmd = f'''---
title: "Uso de CCEEscopio"
subtitle: "Visitas, uso de los recursos y resultados de la encuesta de satisfacción (datos de GoatCounter)"
toc: false
page-layout: full
---

Esta página lee en directo los contadores públicos de GoatCounter. El detalle completo (por días, países, navegadores, origen de las visitas…) está en el [panel de GoatCounter](https://cceescopio.goatcounter.com). Las cifras son acumuladas desde que se activó el contador; no incluyen las visitas desde la vista previa local.

```{{=html}}
<div id="uso-ccee">
<div class="kpi-grid" id="uso-kpis"></div>
<h2>Visitas por página</h2><div id="uso-paginas" class="uso-tabla">Cargando…</div>
<h2>Uso de los recursos</h2>
<p class="source">«Uso de controles»: visitas en las que se cambió algún selector (indicador, territorios, año…). «Mapa»: visitas en las que se pasó el ratón por el mapa.</p>
<div id="uso-recursos" class="uso-tabla">Cargando…</div>
<h2>Encuesta de satisfacción</h2><div id="uso-encuesta">Cargando…</div>
<h2>Indicadores más consultados</h2>
<p><button id="uso-btn-ind" class="enc-enviar">Cargar el ranking de los 99 indicadores</button></p>
<div id="uso-indicadores" class="uso-tabla"></div>
</div>
<script>
(function () {{
  const GC = "https://cceescopio.goatcounter.com/counter/";
  const PAGINAS = {json.dumps(paginas, ensure_ascii=False)};
  const INDS = {json.dumps(inds, ensure_ascii=False)};
  const ENC = {json.dumps(ENC, ensure_ascii=False)};
  const base = location.pathname.replace(/[^/]*$/, "");
  const fmt = n => n.toLocaleString("es-ES");
  const cache = new Map();
  function contar(path) {{
    if (!cache.has(path)) cache.set(path, fetch(GC + encodeURIComponent(path) + ".json")
      .then(r => r.ok ? r.json() : {{count: "0"}})
      .then(d => +String(d.count).replace(/[^0-9]/g, "") || 0)
      .catch(() => 0));
    return cache.get(path);
  }}
  async function lote(paths) {{  // como máximo 6 peticiones a la vez
    const out = new Array(paths.length); let i = 0;
    async function w() {{ while (i < paths.length) {{ const k = i++; out[k] = await contar(paths[k]); }} }}
    await Promise.all(Array.from({{length: 6}}, w)); return out;
  }}
  function tabla(filas, cab) {{
    const max = Math.max(1, ...filas.map(f => f[f.length - 1]));
    return `<table class="table table-sm"><thead><tr>${{cab.map(c => `<th>${{c}}</th>`).join("")}}<th></th></tr></thead><tbody>` +
      filas.map(f => `<tr>${{f.map((c, j) => `<td${{typeof c === "number" ? ' class="num"' : ""}}>${{typeof c === "number" ? fmt(c) : c}}</td>`).join("")}}` +
        `<td class="barra"><span style="width:${{100 * f[f.length - 1] / max}}%"></span></td></tr>`).join("") + `</tbody></table>`;
  }}
  const kpi = (l, n, s) => `<div class="kpi"><div class="kpi-l">${{l}}</div><div class="kpi-n">${{fmt(n)}}</div><div class="kpi-s">${{s}}</div></div>`;

  (async () => {{
    // Visitas por página
    const vis = await lote(PAGINAS.map(p => base + p.html));
    const idx = PAGINAS.findIndex(p => p.html === "index.html");
    if (idx >= 0) vis[idx] += await contar(base);
    const total = await contar("TOTAL");
    const filasP = PAGINAS.map((p, i) => [`<a href="${{p.html}}">${{p.titulo}}</a>`, vis[i]]).sort((a, b) => b[1] - a[1]);
    document.getElementById("uso-paginas").innerHTML = tabla(filasP, ["Página", "Visitas"]);

    // Recursos
    const claves = PAGINAS.map(p => p.clave);
    const [uso, desc, mapa] = await Promise.all([lote(claves.map(c => "uso/" + c)), lote(claves.map(c => "descarga/" + c)), lote(claves.map(c => "mapa/" + c))]);
    const filasR = PAGINAS.map((p, i) => [`<a href="${{p.html}}">${{p.titulo}}</a>`, uso[i], mapa[i], desc[i], uso[i] + mapa[i] + desc[i]])
      .filter(f => f[4] > 0).sort((a, b) => b[4] - a[4]);
    document.getElementById("uso-recursos").innerHTML = filasR.length ? tabla(filasR, ["Página", "Uso de controles", "Mapa", "Descargas CSV", "Total"]) : "<p>Todavía no hay datos de uso.</p>";
    const [vRep, vComp, encN] = await lote(["video/reproducir", "video/completo", "encuesta/enviada"]);
    const sum = a => a.reduce((x, y) => x + y, 0);
    document.getElementById("uso-kpis").innerHTML =
      kpi("Visitas totales", total, "todas las páginas") +
      kpi("Uso de herramientas y paneles", sum(uso), "visitas con interacción") +
      kpi("Descargas de datos", sum(desc), "ficheros CSV") +
      kpi("Uso de los mapas", sum(mapa), "visitas") +
      kpi("Vídeo", vRep, `reproducciones · ${{fmt(vComp)}} completas`) +
      kpi("Encuestas", encN, "respuestas recibidas");

    // Encuesta
    let h = "";
    for (const q of ["satisfaccion", "facilidad"]) {{
      const n = await lote([1, 2, 3, 4, 5].map(v => `encuesta/${{q}}/${{v}}`));
      const tot = sum(n), media = tot ? sum(n.map((x, i) => x * (i + 1))) / tot : 0;
      h += `<h3>${{q === "satisfaccion" ? "Valoración general" : "Facilidad de uso"}}: ${{tot ? media.toLocaleString("es-ES", {{maximumFractionDigits: 2}}) + " / 5" : "sin respuestas"}}</h3>`;
      if (tot) h += tabla([5, 4, 3, 2, 1].map(v => ["★".repeat(v), n[v - 1]]), ["Estrellas", "Respuestas"]);
    }}
    const nombresQ = {{perfil: "Perfil", grado: "Grado", para: "Para qué lo usan", recurso: "Recursos más útiles", recomendaria: "¿Lo recomendarían?"}};
    for (const [q, ops] of Object.entries(ENC)) {{
      const n = await lote(ops.map(o => `encuesta/${{q}}/${{o[0]}}`));
      if (sum(n)) h += `<h3>${{nombresQ[q]}}</h3>` + tabla(ops.map((o, i) => [o[1], n[i]]).sort((a, b) => b[1] - a[1]), ["Respuesta", "N.º"]);
    }}
    document.getElementById("uso-encuesta").innerHTML = h || "<p>Todavía no hay respuestas.</p>";
  }})();

  document.getElementById("uso-btn-ind").addEventListener("click", async ev => {{
    ev.target.disabled = true; ev.target.textContent = "Cargando…";
    const [n, l] = await Promise.all([lote(INDS.map(d => "indicador/" + d.id)), lote(INDS.map(d => "enlace-directo/" + d.id))]);
    const filas = INDS.map((d, i) => [`<a href="${{d.pagina}}.html?i=${{d.id}}">${{d.nombre}}</a>`, l[i], n[i] + l[i]])
      .filter(f => f[2] > 0).sort((a, b) => b[2] - a[2]);
    document.getElementById("uso-indicadores").innerHTML = filas.length ? tabla(filas, ["Indicador", "Por enlace directo", "Consultas"]) : "<p>Todavía no hay datos.</p>";
    ev.target.remove();
  }});
}})();
</script>
```
'''
open("uso.qmd", "w", encoding="utf-8").write(qmd)
print(len(paginas), "páginas,", len(inds), "indicadores")
