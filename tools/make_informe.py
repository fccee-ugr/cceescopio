# -*- coding: utf-8 -*-
"""Genera informe-coyuntura.qmd (plantilla de informe de coyuntura con rúbrica).

Toma de concurso.qmd las especificaciones de los indicadores (especC), para que la
plantilla use las mismas tablas de Eurostat que el resto de CCEEscopio. Ejecutar
desde la raíz del proyecto:

    python3 tools/make_informe.py
"""
import json
import re

src = open("concurso.qmd", encoding="utf-8").read()
ESPEC = {s["id"]: s for s in json.loads(re.search(r"^especC = (\[.*\])$", src, re.M).group(1))}

SECCIONES = [
    {"t": "Resumen", "guia": "Tres a cinco frases con los mensajes principales: cómo crece la economía, qué pasa con el empleo y los precios, y cuál es el principal riesgo. Escríbelo al final.", "ids": []},
    {"t": "Actividad y demanda", "guia": "¿Crece la economía? ¿Más o menos que hace un año y que la UE? ¿Qué componentes de la demanda tiran del crecimiento? ¿Qué anticipan los indicadores de confianza?",
     "ids": ["pib-crecimiento-interanual-trimestral", "consumo-de-los-hogares-crecimiento-interanual", "inversion-formacion-bruta-de-capital-fijo-crecimiento-intera", "indice-de-produccion-industrial", "indicador-de-sentimiento-economico"]},
    {"t": "Mercado laboral", "guia": "¿Baja el paro? ¿A quién afecta más? ¿Se crea empleo? Compara con la UE y con el año anterior, en puntos porcentuales.",
     "ids": ["tasa-de-paro", "tasa-de-paro-juvenil-menores-de-25-anos", "tasa-de-empleo-20-64-anos"]},
    {"t": "Precios", "guia": "¿Sube la inflación o se modera? ¿Es un fenómeno de energía y alimentos o también de la inflación subyacente? ¿Qué ocurre con la vivienda?",
     "ids": ["ipca-inflacion-general-tasa-anual", "ipca-inflacion-subyacente-sin-energia-ni-alimentos", "precio-de-la-vivienda-tasa-anual"]},
    {"t": "Sector público y condiciones financieras", "guia": "¿Cómo están el déficit y la deuda respecto a las reglas fiscales europeas (3 % y 60 % del PIB)? ¿Cómo evolucionan los tipos de interés y qué efecto tienen en hogares y empresas?",
     "ids": ["deficit-o-superavit-publico-del-pib", "deuda-publica-del-pib", "rentabilidad-del-bono-a-10-anos", "euribor-a-3-meses"]},
    {"t": "Sector exterior", "guia": "¿Cómo evolucionan las exportaciones? ¿La economía tiene capacidad o necesidad de financiación frente al resto del mundo?",
     "ids": ["exportaciones-crecimiento-interanual-trimestral", "saldo-por-cuenta-corriente-del-pib"]},
    {"t": "Riesgos y perspectivas", "guia": "Señala dos o tres riesgos concretos (al alza o a la baja) y justifícalos con datos. ¿Qué indicadores habrá que vigilar en los próximos meses?", "ids": []},
    {"t": "Conclusión", "guia": "Valoración global en un párrafo: ¿la situación mejora, empeora o se estanca? No repitas el resumen: interpreta.", "ids": []},
]
for s in SECCIONES:
    for i in s["ids"]:
        assert i in ESPEC, i

especI = [ESPEC[i] for s in SECCIONES for i in s["ids"]]

RUBRICA = [
    ["Uso correcto de los datos", 2.5, "Cifras exactas, con periodo y unidad; distingue tasas, niveles y puntos porcentuales.", "Datos correctos con algún descuido de periodo o unidad.", "Errores en algunos datos o confunde tasas y puntos.", "Datos erróneos, sin fecha o sin unidad."],
    ["Interpretación económica", 2.5, "Explica causas y relaciones entre indicadores; compara con la UE y con el pasado.", "Interpreta los datos, pero con pocas relaciones o comparaciones.", "Describe los datos sin apenas interpretarlos.", "Se limita a copiar cifras."],
    ["Estructura y síntesis", 1.5, "Resumen con los mensajes clave, secciones equilibradas y extensión ajustada.", "Estructura clara, con un resumen mejorable.", "Estructura desordenada o resumen ausente.", "No sigue la estructura del informe."],
    ["Gráficos y tablas", 1.5, "Pertinentes, con título, unidad y fuente, y comentados en el texto.", "Correctos, pero alguno sin fuente o sin comentar.", "Poco pertinentes o con errores de presentación.", "Sin gráficos o gráficos engañosos."],
    ["Riesgos y perspectivas", 1.0, "Riesgos concretos, justificados con datos.", "Riesgos razonables, poco justificados.", "Riesgos genéricos.", "No identifica riesgos."],
    ["Redacción y fuentes", 1.0, "Clara, sin errores; cita las fuentes y la fecha de consulta.", "Algún error menor de redacción o de cita.", "Errores frecuentes o fuentes incompletas.", "Redacción deficiente y sin fuentes."],
]
assert abs(sum(r[1] for r in RUBRICA) - 10) < 1e-9


def tabla_rubrica_md():
    filas = ["| Criterio | Puntos | Excelente (100 %) | Adecuado (70 %) | Mejorable (40 %) | Insuficiente (0 %) |", "|---|---|---|---|---|---|"]
    for c, p, *niv in RUBRICA:
        filas.append(f"| **{c}** | {str(p).replace('.', ',')} | " + " | ".join(niv) + " |")
    filas.append("| **Total** | **10** | | | | |")
    return "\n".join(filas)


def tabla_estructura_md():
    filas = ["| Sección | Qué responder | Indicadores de CCEEscopio |", "|---|---|---|"]
    for k, s in enumerate(SECCIONES, 1):
        ind = "; ".join(ESPEC[i]["nombre"] for i in s["ids"]) or "Síntesis propia"
        filas.append(f"| {k}. {s['t']} | {s['guia']} | {ind} |")
    return "\n".join(filas)


PAGINA = f'''---
title: "Plantilla de informe de coyuntura"
subtitle: "Esqueleto, guía de redacción y rúbrica para que el estudiantado elabore su propio informe con datos reales y actualizados"
toc: true
---

Un **informe de coyuntura** describe y explica la situación económica reciente de un territorio: cómo crece la actividad, qué ocurre con el empleo y los precios, cómo están las cuentas públicas y el sector exterior, y qué riesgos hay. Es el tipo de documento que publican cada trimestre el Banco de España, los servicios de estudios y las cámaras de comercio, y un buen ejercicio para aprender a **leer, relacionar e interpretar** indicadores.

Esta página ofrece todo lo necesario para hacer uno en clase: una **plantilla generada con los últimos datos** del territorio que elijas, la **estructura** del informe, una **guía de redacción** y la **rúbrica** de evaluación. Como modelo, puedes consultar el [Boletín de coyuntura](boletin.qmd) de CCEEscopio.

## Genera tu plantilla con los últimos datos {{#generador}}

Elige el territorio y pulsa el botón. CCEEscopio descarga de Eurostat los últimos datos de {len(especI)} indicadores y prepara un documento con la estructura del informe, las preguntas que debes responder en cada sección y los **datos clave** ya escritos (último dato, el de hace un año y el de la UE-27). Puedes editar el texto aquí mismo antes de descargarlo en Word o en Markdown.

{{{{< include _helpers.qmd >}}}}

```{{ojs}}
//| echo: false
especI = {json.dumps(especI, ensure_ascii=False)}
seccionesI = {json.dumps([{"t": s["t"], "guia": s["guia"], "ids": s["ids"]} for s in SECCIONES], ensure_ascii=False)}
rubricaI = {json.dumps(RUBRICA, ensure_ascii=False)}
```

```{{ojs}}
//| echo: false
viewof terrI = Inputs.select(new Map(geosPaises.filter(g => !["EA20"].includes(g)).map(g => [nombresGeo[g] ?? g, g])), {{label: "Territorio", value: "ES"}})
viewof autorI = Inputs.text({{label: "Autoría (opcional)", placeholder: "Nombre o grupo"}})
viewof generarI = Inputs.button("📝 Generar la plantilla", {{value: 0, reduce: v => v + 1}})
```

```{{ojs}}
//| echo: false
{{
  if (!generarI) return html`<p class="nota">La plantilla tarda unos segundos en prepararse: descarga en directo los datos de Eurostat.</p>`;
  const caja = html`<div class="informe-gen"><p class="pending">Descargando los datos de Eurostat…</p></div>`;
  (async () => {{
    const T = terrI, nombreT = nombresGeo[T] ?? T, hoy = new Date().toLocaleDateString("es-ES");
    const cargados = new Map(await Promise.all(especI.map(async s => [s.id, await cargar(s).catch(() => ({{ok: false, rows: []}}))])));
    const unidad = (s) => /^%/.test(s.unidad) ? " %" : " " + s.unidad.replace(/^Índice \\((.*)\\)$/, "(índice, $1)");
    const pct = (s) => /%|saldo/i.test(s.unidad);
    const dato = (s) => {{
      const d = cargados.get(s.id);
      if (!d || !d.ok) return `${{s.nombre}}: [dato no disponible en este momento; búscalo en CCEEscopio]`;
      const serie = d.rows.filter(r => s.sinGeo || r.codigo_territorio === T).sort((a, b) => a.fecha - b.fecha);
      if (!serie.length) return `${{s.nombre}}: [sin datos para ${{nombreT}} en Eurostat]`;
      const u = serie.at(-1);
      const h = serie.filter(r => r.fecha.getFullYear() === u.fecha.getFullYear() - 1 && r.fecha.getMonth() === u.fecha.getMonth()).pop();
      const ue = s.sinGeo || T === "EU27_2020" ? null : d.rows.filter(r => r.codigo_territorio === "EU27_2020" && r.periodo === u.periodo).pop();
      const dif = h ? (pct(s) ? `${{u.valor - h.valor >= 0 ? "+" : ""}}${{fmt(u.valor - h.valor)}} puntos` : `${{u.valor / h.valor - 1 >= 0 ? "+" : ""}}${{fmt(100 * (u.valor / h.valor - 1))}} %`) : null;
      return `${{s.nombre}}: ${{fmt(u.valor)}}${{unidad(s)}} en ${{u.periodo}}` +
        (h ? ` (hace un año, ${{fmt(h.valor)}}: ${{dif}})` : "") + (ue ? `; UE-27: ${{fmt(ue.valor)}}` : "") + `. Fuente: ${{u.fuente}}.`;
    }};
    const titulo = `Informe de coyuntura: ${{nombreT}}`;
    const meta = `Autoría: ${{autorI || "[nombre o grupo]"}} · Datos consultados el ${{hoy}} · Fuente principal: Eurostat, a través de CCEEscopio D+I (Facultad de Ciencias Económicas y Empresariales, Universidad de Granada).`;
    const secs = seccionesI.map((s, k) => ({{n: k + 1, t: s.t, guia: s.guia, datos: s.ids.map(id => dato(especI.find(e => e.id === id)))}}));
    // Markdown
    let md = `# ${{titulo}}\\n\\n${{meta}}\\n\\n`;
    for (const s of secs) {{
      md += `## ${{s.n}}. ${{s.t}}\\n\\n> **Qué responder:** ${{s.guia}}\\n\\n`;
      if (s.datos.length) md += `**Datos clave** (compruébalos y elige los que vayas a usar):\\n\\n${{s.datos.map(x => `- ${{x}}`).join("\\n")}}\\n\\n`;
      md += `[Escribe aquí tu análisis${{s.datos.length ? ". Incluye al menos un gráfico con título, unidad y fuente" : ""}}.]\\n\\n`;
    }}
    md += `## Fuentes\\n\\n- Eurostat, a través de CCEEscopio D+I, observatorio de indicadores económicos y empresariales de la Facultad de Ciencias Económicas y Empresariales, Universidad de Granada. Consultado el ${{hoy}}.\\n- [Añade otras fuentes: Banco de España, INE, IECA…]\\n\\n## Autoevaluación con la rúbrica\\n\\n| Criterio | Puntos | Mi valoración |\\n|---|---|---|\\n${{rubricaI.map(r => `| ${{r[0]}} | ${{String(r[1]).replace(".", ",")}} | |`).join("\\n")}}\\n| **Total** | **10** | |\\n`;
    // HTML para Word
    const esc = (t) => String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;");
    const htmlDoc = `<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:w="urn:schemas-microsoft-com:office:word"><head><meta charset="utf-8"><title>${{esc(titulo)}}</title>
<style>body{{font-family:Calibri,Arial,sans-serif;font-size:11pt;line-height:1.4}}h1{{color:#B5175F;font-size:20pt}}h2{{color:#B5175F;font-size:14pt;margin-top:18pt}}.guia{{background:#F6EEF2;padding:6pt;font-style:italic}}.hueco{{color:#888}}table{{border-collapse:collapse}}td,th{{border:1px solid #999;padding:4pt;font-size:9.5pt;vertical-align:top}}th{{background:#F6EEF2}}</style></head><body>
<h1>${{esc(titulo)}}</h1><p>${{esc(meta)}}</p>
${{secs.map(s => `<h2>${{s.n}}. ${{esc(s.t)}}</h2><p class="guia"><b>Qué responder:</b> ${{esc(s.guia)}}</p>${{s.datos.length ? `<p><b>Datos clave</b> (compruébalos y elige los que vayas a usar):</p><ul>${{s.datos.map(x => `<li>${{esc(x)}}</li>`).join("")}}</ul>` : ""}}<p class="hueco">[Escribe aquí tu análisis${{s.datos.length ? ". Incluye al menos un gráfico con título, unidad y fuente" : ""}}.]</p>`).join("\\n")}}
<h2>Fuentes</h2><ul><li>Eurostat, a través de CCEEscopio D+I, observatorio de indicadores económicos y empresariales de la Facultad de Ciencias Económicas y Empresariales, Universidad de Granada. Consultado el ${{hoy}}.</li><li class="hueco">[Añade otras fuentes: Banco de España, INE, IECA…]</li></ul>
<h2>Rúbrica de evaluación</h2><table><tr><th>Criterio</th><th>Puntos</th><th>Excelente (100 %)</th><th>Adecuado (70 %)</th><th>Mejorable (40 %)</th><th>Insuficiente (0 %)</th><th>Mi valoración</th></tr>
${{rubricaI.map(r => `<tr><td><b>${{esc(r[0])}}</b></td><td>${{String(r[1]).replace(".", ",")}}</td>${{r.slice(2).map(x => `<td>${{esc(x)}}</td>`).join("")}}<td></td></tr>`).join("")}}
<tr><td><b>Total</b></td><td><b>10</b></td><td></td><td></td><td></td><td></td><td></td></tr></table></body></html>`;
    const area = html`<textarea class="informe-texto" spellcheck="true"></textarea>`;
    area.value = md;
    const nombreF = `informe_coyuntura_${{nombreT.toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g, "").replace(/[^a-z0-9]+/g, "_")}}`;
    caja.innerHTML = "";
    caja.append(html`<p class="juego-res bien">✅ Plantilla de <b>${{nombreT}}</b> preparada con los datos disponibles el ${{hoy}}.</p>`,
      html`<div class="descargas">
        ${{DOM.download(() => new Blob(["\\ufeff" + htmlDoc], {{type: "application/msword"}}), `${{nombreF}}.doc`, "⬇ Descargar en Word (.doc)")}}
        ${{DOM.download(() => new Blob([area.value], {{type: "text/markdown;charset=utf-8"}}), `${{nombreF}}.md`, "⬇ Descargar en Markdown (.md)")}}
      </div>`,
      html`<p class="nota">La descarga en Word usa los datos generados; la de Markdown incluye también lo que escribas o cambies en el recuadro.</p>`, area);
    window.cceeEvento && window.cceeEvento(`informe/${{T}}`, "Plantilla de informe de coyuntura", true);
  }})();
  return caja;
}}
```

## Estructura del informe

El informe tiene ocho secciones. La extensión orientativa es de **1.500 a 2.500 palabras** con **cuatro a seis gráficos o tablas**.

{tabla_estructura_md()}

## Guía de redacción

- **Dato, comparación e interpretación.** Cada afirmación necesita las tres cosas. Por ejemplo (cifras ilustrativas): «La tasa de paro bajó al 10,4 % en septiembre (dato), 0,8 puntos menos que hace un año y aún el doble que en la UE (comparación), gracias al empleo en los servicios (interpretación)».
- **Fecha y unidad siempre.** Indica el periodo de cada dato (mes, trimestre o año) y su unidad. Los indicadores se publican con retrasos distintos: no mezcles datos de periodos diferentes sin avisarlo.
- **Puntos frente a porcentajes.** Si el paro pasa del 11 % al 10 %, baja **1 punto** porcentual, no un 1 %: baja un 9,1 %. Para variables en porcentaje, usa los puntos.
- **Tasa frente a nivel.** Que la inflación baje del 3 % al 2 % no significa que los precios bajen: suben más despacio. Revisa [Detecta el engaño](detecta-engano.qmd).
- **Interanual frente a intertrimestral.** Las tasas interanuales comparan con el mismo periodo del año anterior y evitan la estacionalidad; las intertrimestrales detectan antes los cambios de tendencia.
- **Relaciona los indicadores.** El informe gana valor cuando conecta secciones: consumo y confianza, empleo y producción, tipos de interés y vivienda, inflación y salarios.
- **Gráficos honestos y citados.** Usa el [generador de gráficos](graficos.qmd), que añade la fuente, y comenta cada gráfico en el texto.
- **Escribe el resumen al final**, cuando ya sepas cuáles son los mensajes principales.

## Rúbrica de evaluación

Cada criterio se valora con uno de los cuatro niveles; la nota del criterio es su peso multiplicado por el porcentaje del nivel. Por ejemplo, «Adecuado» en un criterio de 2,5 puntos suma 1,75.

{tabla_rubrica_md()}

## Antes de entregar

- [ ] Cada dato tiene su periodo, su unidad y su fuente.
- [ ] He usado puntos porcentuales para las variaciones de tasas y porcentajes.
- [ ] He comparado con el año anterior y con la UE-27 (o con otro territorio de referencia).
- [ ] Cada gráfico tiene título, unidad y fuente, y lo comento en el texto.
- [ ] He explicado por qué cambian los indicadores, no solo cuánto.
- [ ] He identificado al menos dos riesgos concretos y los he justificado con datos.
- [ ] El resumen recoge los mensajes principales en cinco frases como máximo.
- [ ] He citado CCEEscopio y Eurostat con la fecha de consulta (véase [Datos y fuentes](datos.qmd)).

## Para el profesorado

- **Un territorio por grupo.** Asigna a cada grupo un país de la UE o una comunidad autónoma (con el [comparador de comunidades autónomas](comparador.qmd)) y dedica una sesión a comparar los diagnósticos.
- **Evaluación entre iguales.** Cada grupo evalúa el informe de otro con la rúbrica; la tabla de autoevaluación ya viene en la plantilla.
- **Seguimiento a lo largo del curso.** Repite el informe al principio y al final del cuatrimestre con el mismo territorio: los datos de Eurostat se actualizan solos y el estudiantado ve cómo cambia la coyuntura.
- **Encaje en las asignaturas.** Funciona en Macroeconomía, Economía Española y Mundial, Coyuntura Económica, Estructura Económica y en las asignaturas de Métodos Cuantitativos (números índice, tasas de variación, series temporales).
'''

open("informe-coyuntura.qmd", "w", encoding="utf-8").write(PAGINA)
print("informe-coyuntura.qmd generado con", len(especI), "indicadores")
