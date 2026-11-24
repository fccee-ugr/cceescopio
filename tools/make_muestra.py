"""Genera tamano-muestral.qmd: calculadora del tamaño muestral según distintos escenarios de la literatura.
Las fórmulas están en tools/muestra.js (se prueban con: node tools/muestra.js) y usan tools/estadistica.js.
Uso: python3 tools/make_muestra.py"""

def js(fichero):
    return "\n".join("  " + l for l in open(fichero, encoding="utf-8").read().splitlines()
                     if not l.startswith("if (typeof module"))

EST = js("tools/estadistica.js")
MUE = open("tools/muestra.js", encoding="utf-8").read().split("if (typeof module")[0]
MUE = "\n".join("  " + l for l in MUE.splitlines())

PAGINA = r'''---
title: "Tamaño muestral"
subtitle: "¿Cuántas observaciones necesita tu estudio? Elige el escenario y calcula n con los criterios clásicos de la literatura"
toc: true
toc-depth: 2
---

Antes de recoger datos (una encuesta, un experimento, un estudio de mercado, un TFG o un TFM), conviene decidir **cuántas observaciones hacen falta**. La respuesta depende del objetivo del estudio:

- **Estimar** una proporción o una media con una **precisión** dada (error de muestreo máximo y nivel de confianza).
- **Contrastar una hipótesis** con una **potencia** dada (probabilidad de detectar un efecto de un tamaño determinado si existe).

Elige el escenario que se ajusta a tu estudio, introduce los valores y la calculadora te da **n**, las fórmulas paso a paso y cómo cambia n si modificas los supuestos. Escribe los decimales con coma o con punto.

```{ojs}
//| echo: false
EST = {
__EST__
  return crearEstadistica();
}
M = {
__MUE__
  return crearMuestra(EST);
}
locES = d3.formatLocale({decimal: ",", thousands: ".", grouping: [3]})
f2 = (x) => typeof x === "string" ? x : Number.isFinite(x) ? locES.format(",.4~f")(x) : "–"
fN = (x) => Number.isFinite(x) ? locES.format(",.0f")(x) : "–"
fP = (x) => Number.isFinite(x) ? locES.format(",.1~f")(100 * x) + " %" : "–"
num = (s) => { const t = String(s ?? "").trim().replace(/\s|%/g, "").replace(",", "."); return t === "" ? NaN : +t; }
ESC = new Map([
  ["Estimación · Proporción con error de muestreo máximo (p. ej., ±5 puntos)", "propAbs"],
  ["Estimación · Proporción con error relativo (p. ej., ±10 % de p)", "propRel"],
  ["Estimación · Media con error de muestreo máximo (en unidades de la variable)", "mediaAbs"],
  ["Estimación · Media con error relativo (coeficiente de variación)", "mediaRel"],
  ["Contraste · Una proporción frente a un valor de referencia", "test1p"],
  ["Contraste · Una media frente a un valor de referencia (d de Cohen)", "test1m"],
  ["Contraste · Comparar dos proporciones (dos grupos independientes)", "test2p"],
  ["Contraste · Comparar dos medias (dos grupos independientes, d de Cohen)", "test2m"],
  ["Contraste · Coeficiente de correlación de Pearson", "correl"],
  ["Contraste · Regresión lineal múltiple (F de significación conjunta, f² de Cohen)", "regresion"],
  ["Contraste · Chi-cuadrado: independencia o bondad del ajuste (w de Cohen)", "chi"]
])
esEstimacion = (e) => ["propAbs", "propRel", "mediaAbs", "mediaRel"].includes(e)
```

## Escenario

```{ojs}
//| echo: false
viewof esc = Inputs.select(ESC, {label: "¿Qué quieres hacer?", value: "propAbs", width: 620})
```

```{ojs}
//| echo: false
viewof par = {
  const t = (label, value, placeholder) => Inputs.text({label, value, placeholder, width: 140});
  const conf = Inputs.select(new Map([["90 %", .90], ["95 %", .95], ["99 %", .99]]), {label: "Nivel de confianza", value: .95});
  const alfa = Inputs.select(new Map([["0,01", .01], ["0,05", .05], ["0,10", .10]]), {label: "Nivel de significación α", value: .05});
  const colas = Inputs.radio(new Map([["Bilateral", 2], ["Unilateral", 1]]), {label: "Contraste", value: 2});
  const pot = Inputs.select(new Map([["80 %", .80], ["85 %", .85], ["90 %", .90], ["95 %", .95]]), {label: "Potencia (1 − β)", value: .80});
  const k = t("Razón de tamaños n₂/n₁ (1 = grupos iguales)", "1");
  const F = {
    propAbs: {conf, p: t("Proporción esperada p (si no se conoce: 0,5)", "0,5"), e: t("Error de muestreo máximo e (0,05 = ±5 puntos)", "0,05")},
    propRel: {conf, p: t("Proporción esperada p", "0,2"), er: t("Error relativo máximo (0,10 = ±10 % de p)", "0,10")},
    mediaAbs: {conf, sigma: t("Desviación típica σ (estudio piloto o previo)", "10"), e: t("Error de muestreo máximo e (mismas unidades)", "2")},
    mediaRel: {conf, cv: t("Coeficiente de variación CV = σ/μ (0,5 = 50 %)", "0,5"), er: t("Error relativo máximo (0,05 = ±5 % de la media)", "0,05")},
    test1p: {alfa, colas, pot, p0: t("Proporción de referencia p₀ (H₀)", "0,5"), p1: t("Proporción que quieres detectar p₁", "0,6")},
    test1m: {alfa, colas, pot, d: t("Tamaño del efecto d = (μ₁ − μ₀)/σ (0,2 pequeño · 0,5 mediano · 0,8 grande)", "0,5")},
    test2p: {alfa, colas, pot, p1: t("Proporción en el grupo 1 (p₁)", "0,5"), p2: t("Proporción en el grupo 2 (p₂)", "0,4"), k, cc: Inputs.toggle({label: "Corrección de continuidad (Fleiss, Tytun y Ury, 1980)", value: false})},
    test2m: {alfa, colas, pot, d: t("Tamaño del efecto d = (μ₁ − μ₂)/σ (0,2 · 0,5 · 0,8)", "0,5"), k},
    correl: {alfa, colas, pot, r: t("Correlación que quieres detectar r (0,1 pequeña · 0,3 mediana · 0,5 grande)", "0,3")},
    regresion: {alfa, pot, f2: t("Tamaño del efecto f² = R²/(1 − R²) (0,02 · 0,15 · 0,35)", "0,15"), kx: t("Número de variables explicativas k", "5")},
    chi: {alfa, pot, w: t("Tamaño del efecto w (0,1 pequeño · 0,3 mediano · 0,5 grande)", "0,3"), gl: t("Grados de libertad [(filas − 1)(columnas − 1) o categorías − 1]", "1")}
  }[esc];
  return Inputs.form(F);
}
```

### Ajustes del diseño

```{ojs}
//| echo: false
viewof aj = Inputs.form({
  N: esEstimacion(esc) ? Inputs.text({label: "Tamaño de la población N (vacío si es muy grande o desconocido)", value: "", placeholder: "p. ej. 12500", width: 140}) : Object.assign(html`<span></span>`, {value: ""}),
  deff: Inputs.text({label: "Efecto de diseño (1 = muestreo aleatorio simple; 1,5-2 en muestreo por conglomerados)", value: "1", width: 140}),
  resp: Inputs.text({label: "Tasa de respuesta esperada (1 = 100 %; 0,6 = 60 %)", value: "1", width: 140}),
  estr: esEstimacion(esc) ? Inputs.textarea({label: "Estratos para el reparto proporcional (opcional): nombre y tamaño en cada línea", rows: 4, width: 420, placeholder: "Hombres;5200\nMujeres;5600"}) : Object.assign(html`<span></span>`, {value: ""})
})
```

```{ojs}
//| echo: false
calc = {
  const v = Object.fromEntries(Object.entries(par).map(([k, x]) => [k, typeof x === "string" ? num(x) : x]));
  if (v.kx !== undefined) v.k = v.kx;
  const N = +String(aj.N ?? "").replace(/[.\s]/g, "").replace(",", ".") || NaN, deff = Number.isFinite(num(aj.deff)) ? num(aj.deff) : 1, resp = Number.isFinite(num(aj.resp)) ? num(aj.resp) : 1;
  const mal = (m) => ({error: m});
  if (Object.entries(v).some(([k, x]) => typeof x === "number" && !Number.isFinite(x))) return mal("Revisa los valores: hay alguna casilla vacía o que no es un número.");
  const enCero1 = (x) => x > 0 && x < 1;
  if (["p", "p0", "p1", "p2", "er", ...(esc.startsWith("prop") ? ["e"] : [])].some(k => k in v && !enCero1(v[k]))) return mal("Las proporciones y los errores deben estar entre 0 y 1 (por ejemplo, 0,05).");
  if ("p0" in v && v.p0 === v.p1) return mal("p₁ debe ser distinta de p₀.");
  if ("p2" in v && v.p1 === v.p2) return mal("Las dos proporciones deben ser distintas.");
  if (["sigma", "cv", "d", "f2", "w"].some(k => k in v && !(v[k] > 0))) return mal("El tamaño del efecto y la desviación típica deben ser positivos.");
  if ("r" in v && !(v.r > 0 && v.r < 1)) return mal("La correlación debe estar entre 0 y 1 (en valor absoluto).");
  if ("k" in v && !(v.k > 0)) return mal("La razón de tamaños y el número de variables deben ser positivos.");
  if ("gl" in v && !(Number.isInteger(v.gl) && v.gl >= 1)) return mal("Los grados de libertad deben ser un número entero positivo.");
  if (!(deff >= 1) || !(resp > 0 && resp <= 1)) return mal("El efecto de diseño debe ser ≥ 1 y la tasa de respuesta, mayor que 0 y como mucho 1.");
  if (esc === "regresion" && !Number.isInteger(v.k)) return mal("El número de variables explicativas debe ser un entero.");
  const r = M.E[esc]({...v, N: Number.isFinite(N) && N > 1 ? N : null});
  const aju = M.ajustar(r.nf, deff, resp);
  const n1 = aju.n, n2 = r.grupos === 2 ? Math.ceil(n1 * (v.k ?? 1)) : 0;
  const estratos = String(aj.estr ?? "").split(/\r?\n/).map(l => l.split(/[;\t]/)).filter(c => c.length >= 2 && num(c[1]) > 0).map(c => ({nombre: c[0].trim(), N: num(c[1])}));
  return {v, r, deff, resp, N, aju, n1, n2, total: n1 + n2, estratos: estratos.length >= 2 ? M.afijacion(n1, estratos) : null};
}
```

## Resultado

```{ojs}
//| echo: false
{
  if (calc.error) return html`<p class="pending">${calc.error}</p>`;
  window.cceeEvento && window.cceeEvento("calculadoras/tamano-muestral", "Tamaño muestral", true);
  const {v, r, deff, resp, aju, n1, n2, total, estratos} = calc, dos = r.grupos === 2;
  const nucleo = Math.ceil(r.nf - 1e-9), nucleo2 = Math.ceil(nucleo * (v.k ?? 1));
  const frase = ((n1, n2) => ({
    propAbs: `Con una muestra aleatoria de ${fN(n1)} unidades, el ${fP(v.conf)} de las veces la proporción estimada no se alejará más de ±${locES.format(",.1f")(100 * v.e)} puntos de la verdadera (si p ≈ ${f2(v.p)}).`,
    propRel: `Con ${fN(n1)} unidades, el error de muestreo será como mucho del ±${fP(v.er)} de la proporción (±${locES.format(",.2f")(100 * v.er * v.p)} puntos si p ≈ ${f2(v.p)}), con una confianza del ${fP(v.conf)}.`,
    mediaAbs: `Con ${fN(n1)} unidades, la media muestral no se alejará más de ±${f2(v.e)} unidades de la media poblacional, con una confianza del ${fP(v.conf)}.`,
    mediaRel: `Con ${fN(n1)} unidades, la media muestral no se alejará más de un ±${fP(v.er)} de la media poblacional, con una confianza del ${fP(v.conf)}.`,
    test1p: `Con ${fN(n1)} unidades, si la proporción verdadera es ${f2(v.p1)}, el contraste rechazará H₀: p = ${f2(v.p0)} con una probabilidad del ${fP(v.pot)}.`,
    test1m: `Con ${fN(n1)} unidades, si el efecto verdadero es d = ${f2(v.d)}, el contraste t lo detectará con una probabilidad del ${fP(v.pot)}.`,
    test2p: `Con ${fN(n1)} unidades en el grupo 1 y ${fN(n2)} en el grupo 2, una diferencia entre ${f2(v.p1)} y ${f2(v.p2)} se detectará con una probabilidad del ${fP(v.pot)}.`,
    test2m: `Con ${fN(n1)} unidades en el grupo 1 y ${fN(n2)} en el grupo 2, una diferencia de medias de d = ${f2(v.d)} desviaciones típicas se detectará con una probabilidad del ${fP(v.pot)}.`,
    correl: `Con ${fN(n1)} pares de observaciones, una correlación de ${f2(v.r)} en la población resultará significativa con una probabilidad del ${fP(v.pot)}.`,
    regresion: `Con ${fN(n1)} observaciones y ${v.k} variables explicativas, un efecto f² = ${f2(v.f2)} (R² ≈ ${locES.format(",.2f")(v.f2 / (1 + v.f2))}) hará significativo el modelo con una probabilidad del ${fP(v.pot)}.`,
    chi: `Con ${fN(n1)} observaciones, un efecto w = ${f2(v.w)} con ${v.gl} grado${v.gl > 1 ? "s" : ""} de libertad se detectará con una probabilidad del ${fP(v.pot)}.`
  }[esc]))(nucleo, nucleo2);
  const ajustes = [deff > 1 ? `efecto de diseño ${f2(deff)}` : "", resp < 1 ? `tasa de respuesta del ${fP(resp)}` : ""].filter(Boolean);
  return html`<div class="kpi-grid">
    <div class="kpi"><div class="kpi-l">${dos ? "Tamaño del grupo 1 (n₁)" : "Tamaño muestral necesario (n)"}</div><div class="kpi-n" style="font-size:2.4rem">${fN(n1)}</div><div class="kpi-s">${ajustes.length ? `incluye ${ajustes.join(" y ")}` : "redondeado hacia arriba"}</div></div>
    ${dos ? html`<div class="kpi"><div class="kpi-l">Tamaño del grupo 2 (n₂)</div><div class="kpi-n" style="font-size:2.4rem">${fN(n2)}</div></div>
      <div class="kpi"><div class="kpi-l">Total de las dos muestras</div><div class="kpi-n" style="font-size:2.4rem">${fN(total)}</div></div>` : ""}
    ${ajustes.length ? html`<div class="kpi"><div class="kpi-l">Sin ajustes del diseño</div><div class="kpi-n">${fN(nucleo)}</div><div class="kpi-s">muestreo aleatorio simple y respuesta completa</div></div>` : ""}
    ${r.potencia ? html`<div class="kpi"><div class="kpi-l">Potencia alcanzada con ese n</div><div class="kpi-n">${fP(r.potencia)}</div><div class="kpi-s">cálculo exacto con la distribución no central</div></div>` : ""}
  </div>
  <p>${frase}${ajustes.length ? ` Con ${ajustes.join(" y ")}, hay que seleccionar ${fN(n1)}${dos ? ` y ${fN(n2)}` : ""} unidades para conseguir ese resultado.` : ""}</p>
  <h3>Cálculo paso a paso</h3>
  <table class="uso-tabla"><tr><th>Paso</th><th>Valor</th></tr>
    ${r.pasos.map(([a, b]) => html`<tr><td>${a}</td><td><b>${f2(b)}</b></td></tr>`)}
    ${deff > 1 ? html`<tr><td>× efecto de diseño (${f2(deff)})</td><td><b>${f2(aju.nd)}</b></td></tr>` : ""}
    ${resp < 1 ? html`<tr><td>÷ tasa de respuesta (${f2(resp)}): muestra que hay que seleccionar</td><td><b>${f2(aju.nr)}</b></td></tr>` : ""}
    <tr><td><b>Tamaño muestral (redondeado hacia arriba)</b></td><td><b>${fN(n1)}${dos ? ` + ${fN(n2)}` : ""}</b></td></tr></table>
  ${estratos ? html`<h3>Reparto proporcional por estratos</h3><table class="uso-tabla"><tr><th>Estrato</th><th>Tamaño N<sub>h</sub></th><th>Peso</th><th>Muestra n<sub>h</sub></th></tr>
    ${estratos.map(e => html`<tr><td>${e.nombre}</td><td>${fN(e.N)}</td><td>${fP(e.peso)}</td><td><b>${fN(e.n)}</b></td></tr>`)}</table>
    <p class="nota">Afijación proporcional: n<sub>h</sub> = n · N<sub>h</sub>/N, redondeando por el método del mayor resto.</p>` : ""}`;
}
```

## ¿Cómo cambia n si cambio los supuestos?

```{ojs}
//| echo: false
{
  if (calc.error) return html``;
  const {v} = calc, est = esEstimacion(esc);
  const clave = est ? (v.e !== undefined ? "e" : "er") : ({test1p: "p1", test1m: "d", test2p: "p2", test2m: "d", correl: "r", regresion: "f2", chi: "w"})[esc];
  const etq = {e: "Error de muestreo máximo e", er: "Error relativo máximo", p1: "Proporción que quieres detectar p₁", p2: "Proporción del grupo 2 (p₂)", d: "Tamaño del efecto d", r: "Correlación r", f2: "Tamaño del efecto f²", w: "Tamaño del efecto w"}[clave];
  const x0 = v[clave];
  let xs = d3.range(25).map(i => x0 * (0.5 + 1.5 * i / 24));
  if (clave === "p1" || clave === "p2") { const ref = clave === "p1" ? v.p0 : v.p1, lado = x0 > ref ? 1 : -1; xs = d3.range(25).map(i => ref + lado * (0.02 + (Math.abs(x0 - ref) * 2 - 0.02) * i / 24)).filter(x => x > 0.005 && x < 0.995); }
  if (clave === "r") xs = xs.filter(x => x < 0.95);
  const N = calc.N, deff = calc.deff, resp = calc.resp;
  const n = (x) => { try { const r = M.E[esc]({...v, [clave]: x, N: Number.isFinite(N) && N > 1 ? N : null}); return M.ajustar(r.nf, deff, resp).n; } catch (e) { return NaN; } };
  const curva = xs.map(x => ({x, n: n(x)})).filter(d => Number.isFinite(d.n));
  const curvaP = est ? [] : [.5, .6, .7, .75, .8, .85, .9, .95, .99].map(p => { try { const r = M.E[esc]({...v, pot: p}); return {p, n: M.ajustar(r.nf, deff, resp).n}; } catch (e) { return null; } }).filter(d => d && Number.isFinite(d.n));
  const g1 = Plot.plot({height: 300, marginLeft: 60, x: {label: etq, grid: true}, y: {label: "n", grid: true, type: "log"},
    marks: [Plot.line(curva, {x: "x", y: "n", stroke: "#A6195E", strokeWidth: 2.5}), Plot.dot([{x: x0, n: calc.n1}], {x: "x", y: "n", r: 6, fill: "#F29200"}),
      Plot.tip(curva, Plot.pointer({x: "x", y: "n", title: d => `${etq}: ${f2(d.x)}\nn = ${fN(d.n)}`}))]});
  const g2 = est ? null : Plot.plot({height: 300, marginLeft: 60, x: {label: "Potencia (1 − β)", grid: true, tickFormat: d => locES.format(".0%")(d)}, y: {label: "n", grid: true},
    marks: [Plot.line(curvaP, {x: "p", y: "n", stroke: "#2C6FBB", strokeWidth: 2.5}), Plot.dot(curvaP, {x: "p", y: "n", fill: "#2C6FBB", r: 3}), Plot.dot([{p: v.pot, n: calc.n1}], {x: "p", y: "n", r: 6, fill: "#F29200"}),
      Plot.tip(curvaP, Plot.pointer({x: "p", y: "n", title: d => `Potencia ${fP(d.p)}: n = ${fN(d.n)}`}))]});
  return html`<div class="graf-2"><div><h4>n según ${etq.toLowerCase()} (escala logarítmica)</h4>${g1}</div>${g2 ? html`<div><h4>n según la potencia</h4>${g2}</div>` : ""}</div>
  <p class="nota">El punto naranja es tu escenario. ${est ? "Reducir el error a la mitad multiplica n aproximadamente por cuatro." : "Detectar efectos más pequeños o exigir más potencia aumenta mucho el tamaño muestral."}</p>`;
}
```

## Criterios y valores de referencia

| Escenario | Fórmula o criterio | Referencia |
|---|---|---|
| Proporción, error absoluto | $n_0 = z^2_{1-\alpha/2}\,p(1-p)/e^2$; con $p = 0{,}5$ se obtiene el tamaño más conservador | Cochran (1977) |
| Media, error absoluto | $n_0 = z^2_{1-\alpha/2}\,\sigma^2/e^2$ | Cochran (1977) |
| Error relativo | $n_0 = z^2_{1-\alpha/2}\,CV^2/e_r^2$; en proporciones, $CV^2 = (1-p)/p$ | Cochran (1977); Lohr (2022) |
| Población finita | $n = n_0 / \left(1 + (n_0 - 1)/N\right)$ | Cochran (1977) |
| Efecto de diseño | $n_{\text{diseño}} = n \cdot \text{deff}$ | Kish (1965) |
| Una proporción | $n = \left[z_{1-\alpha}\sqrt{p_0q_0} + z_{1-\beta}\sqrt{p_1q_1}\right]^2/(p_1 - p_0)^2$ | Fleiss, Levin y Paik (2003) |
| Dos proporciones | Fórmula de Fleiss, con corrección de continuidad opcional | Fleiss, Levin y Paik (2003); Fleiss, Tytun y Ury (1980) |
| Una o dos medias | t no central; tamaños del efecto d: 0,2 pequeño, 0,5 mediano, 0,8 grande | Cohen (1988) |
| Correlación | $n = \left[(z_{1-\alpha} + z_{1-\beta})/C\right]^2 + 3$, con $C = \tfrac12\ln\frac{1+r}{1-r}$; r: 0,1, 0,3, 0,5 | Cohen (1988) |
| Regresión múltiple | F no central con $\lambda = f^2 n$; f²: 0,02, 0,15, 0,35. Reglas prácticas: $n \ge 50 + 8k$ y $n \ge 104 + k$ | Cohen (1988); Green (1991) |
| Chi-cuadrado | Chi-cuadrado no central con $\lambda = w^2 n$; w: 0,1, 0,3, 0,5 | Cohen (1988) |

::: {.callout-note appearance="simple"}
**Consejos.** Si no conoces la proporción, usa **p = 0,5** (el caso más desfavorable). Para la desviación típica o el coeficiente de variación, usa un **estudio piloto**, un estudio previo o datos de CCEEscopio. En los contrastes, fija el tamaño del efecto **mínimo que tenga interés práctico**, no el que esperas encontrar. Si prevés que parte de la muestra no responderá, ajusta por la **tasa de respuesta**. Los resultados de las funciones de potencia coinciden con los de G*Power (Faul et al., 2007).
:::

## Referencias

::: {.cita}
<span>Muñoz, J.F., Álvarez, E. (2026). Calculadora de tamaño muestral. CCEEscopio D+I: observatorio de indicadores económicos y empresariales al servicio de la Docencia y la Investigación. Facultad de Ciencias Económicas y Empresariales, Universidad de Granada. https://fccee-ugr.github.io/cceescopio/tamano-muestral.html</span>
:::

- Cochran, W. G. (1977). *Sampling techniques* (3.ª ed.). Wiley.
- Cohen, J. (1988). *Statistical power analysis for the behavioral sciences* (2.ª ed.). Lawrence Erlbaum.
- Faul, F., Erdfelder, E., Lang, A.-G. y Buchner, A. (2007). G*Power 3: A flexible statistical power analysis program for the social, behavioral, and biomedical sciences. *Behavior Research Methods*, 39(2), 175-191.
- Fleiss, J. L., Levin, B. y Paik, M. C. (2003). *Statistical methods for rates and proportions* (3.ª ed.). Wiley.
- Fleiss, J. L., Tytun, A. y Ury, H. K. (1980). A simple approximation for calculating sample sizes for comparing independent proportions. *Biometrics*, 36(2), 343-346.
- Green, S. B. (1991). How many subjects does it take to do a regression analysis? *Multivariate Behavioral Research*, 26(3), 499-510.
- Kish, L. (1965). *Survey sampling*. Wiley.
- Lohr, S. L. (2022). *Sampling: Design and analysis* (3.ª ed.). CRC Press.
'''

open("tamano-muestral.qmd", "w", encoding="utf-8").write(PAGINA.replace("__EST__", EST).replace("__MUE__", MUE))
print("   tamano-muestral.qmd")
