// Motor del generador de exámenes de Técnicas Cuantitativas III (Grado en Marketing e Investigación de Mercados, UGR).
// Sigue el formulario y el formato de los apuntes y exámenes de la asignatura (z = 2, nivel de confianza del 95 %).
// Lo usa tools/make_apps3.py para construir examen-tc3.qmd; también se puede probar con Node.
function crearMotorTC3() {
  // ---------- utilidades ----------
  const rngDe = (s) => { let a = s >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; };
  let R = Math.random;
  const ri = (a, b) => a + Math.floor(R() * (b - a + 1));
  const rr = (a, b, paso = 1) => a + paso * Math.floor(R() * (Math.round((b - a) / paso) + 1));
  const pick = (arr) => arr[Math.floor(R() * arr.length)];
  const shuffle = (arr) => { const a = arr.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(R() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
  const sum = (a) => a.reduce((s, x) => s + x, 0);
  const red = (x, d = 4) => Math.round(x * 10 ** d) / 10 ** d;
  const miles = (s) => s.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  // Números con coma decimal; 4 decimales (o 6 cifras significativas si es muy pequeño), como en las soluciones de la asignatura
  const num = (x, dec) => {
    if (!Number.isFinite(x)) return "–";
    let s;
    if (dec !== undefined) s = x.toFixed(dec);
    else if (Number.isInteger(x)) s = String(x);
    else if (Math.abs(x) >= 0.01) s = x.toFixed(4);
    else s = x.toPrecision(6).includes("e") ? x.toFixed(10) : x.toPrecision(6);
    if (s.includes(".") && dec === undefined) s = s.replace(/0+$/, "").replace(/\.$/, "");
    const [e, d] = s.split(".");
    const ent = e.replace("-", "");
    return (x < 0 && Number(s) !== 0 ? "−" : "") + (ent.length > 4 ? miles(ent) : ent) + (d ? "," + d : "");
  };
  const pct = (x, d = 2) => num(100 * x, d) + " %";
  const techo = (x) => Math.ceil(x - 1e-9);
  const tabla = (cab, filas, cls = "tc3-tabla") => `<table class="${cls}"><tr>${cab.map(c => `<th>${c}</th>`).join("")}</tr>${filas.map(f => `<tr>${f.map(c => `<td>${c}</td>`).join("")}</tr>`).join("")}</table>`;
  const S = (x) => `<span class="tc3-res">${x}</span>`;
  const raiz = (x) => `√(${x})`;
  const DIF = {Baja: 0, Media: 1, Alta: 2};

  // ---------- tema 1: muestreo aleatorio simple ----------
  const CTX1 = [
    {pob: "clientes con tarjeta de fidelización de una cadena de perfumerías", N: [2000, 9000], v: "gasto mensual en la cadena", m: "el gasto mensual medio en la cadena", tt: "el gasto mensual total en la cadena", u: "euros", mu: [35, 90], cv: [0.3, 0.6],
     prop: "han utilizado algún cupón descuento de la aplicación móvil en el último mes"},
    {pob: "suscriptores de una plataforma de música en streaming", N: [3000, 12000], v: "tiempo semanal de escucha", m: "el tiempo semanal medio de escucha", tt: "el tiempo semanal total de escucha", u: "horas", mu: [6, 18], cv: [0.3, 0.5],
     prop: "recuerdan la última campaña publicitaria de la plataforma"},
    {pob: "clientes de una tienda online de material deportivo", N: [1500, 8000], v: "importe de su último pedido", m: "el importe medio del último pedido", tt: "el importe total de los últimos pedidos", u: "euros", mu: [40, 120], cv: [0.35, 0.6],
     prop: "volverían a comprar en la tienda en los próximos tres meses"},
    {pob: "socios de una cadena de gimnasios", N: [1200, 5000], v: "número de visitas mensuales al gimnasio", m: "el número medio de visitas mensuales", tt: "el número total de visitas mensuales al gimnasio", u: "visitas", mu: [7, 16], cv: [0.3, 0.5],
     prop: "recomendarían el gimnasio a un amigo"},
    {pob: "compradores de un nuevo modelo de patinete eléctrico", N: [1000, 6000], art: "la", v: "valoración del producto (escala de 0 a 100)", m: "la valoración media del producto", tt: null, u: "puntos", mu: [55, 80], cv: [0.15, 0.3],
     prop: "conocieron el producto a través de las redes sociales"},
  ];
  function tema1(d, ind) {
    const c = pick(CTX1), N = rr(c.N[0], c.N[1], 100), n = d === 0 ? ri(30, 60) : ri(40, 120);
    const ybar = red(rr(c.mu[0] * 10, c.mu[1] * 10) / 10, 1), Sd = red(ybar * (c.cv[0] + R() * (c.cv[1] - c.cv[0])), 1);
    const sy = red(n * ybar, 1), S2 = Sd * Sd, sy2 = red((n - 1) * S2 + sy * sy / n, 0);
    const S2c = (sy2 - sy * sy / n) / (n - 1), media = sy / n;
    const V = S2c / n * (N - n) / N, B = 2 * Math.sqrt(V);
    const intro = `Una empresa quiere conocer mejor a los ${miles(String(N))} ${c.pob}. Para ello selecciona una muestra aleatoria simple de ${n} de ellos y anota ${c.art ?? "el"} ${c.v} (en ${c.u}) de cada uno, obteniendo:`;
    const datos = `<p class="tc3-centro">n = ${n} &nbsp;&nbsp;&nbsp; Σ y<sub>i</sub> = ${num(sy)} &nbsp;&nbsp;&nbsp; Σ y<sub>i</sub><sup>2</sup> = ${num(sy2)}</p>`;
    const base = `S<sup>2</sup> = [Σy<sub>i</sub><sup>2</sup> − (Σy<sub>i</sub>)<sup>2</sup>/n]/(n − 1) = (${num(sy2)} − ${num(sy)}<sup>2</sup>/${n})/${n - 1} = ${num(S2c)}`;
    const ap = [];
    ap.push({w: 1, t: `Estime ${c.m} de los ${c.pob} y el límite para el error de estimación.`,
      s: `ȳ = Σy<sub>i</sub>/n = ${num(sy)}/${n} = ${S(num(media))} ${c.u}<br>${base}<br>V̂(ȳ) = (S<sup>2</sup>/n)·(N − n)/N = (${num(S2c)}/${n})·(${N} − ${n})/${N} = ${num(V)}<br>B = 2√V̂(ȳ) = ${S(num(B))} ${c.u}`});
    if (d >= 1) {
      const tau = N * media, Bt = N * B;
      ap.push(c.tt === null ? {w: 1, t: `Dé un intervalo de confianza para ${c.m}.`, s: `(ȳ − B ; ȳ + B) = ${S(`(${num(media - B)} ; ${num(media + B)})`)} ${c.u}`} : {w: 1, t: `Estime con un intervalo de confianza ${c.tt} del conjunto de los ${c.pob}.`,
        s: `τ̂ = N·ȳ = ${N} · ${num(media)} = ${num(tau)}<br>V̂(τ̂) = N<sup>2</sup>·V̂(ȳ) = ${num(N * N * V)} &nbsp;&nbsp; B = 2√V̂(τ̂) = N·B<sub>μ</sub> = ${num(Bt)}<br>Intervalo: (τ̂ − B ; τ̂ + B) = ${S(`(${num(tau - Bt)} ; ${num(tau + Bt)})`)} ${c.u}`});
    }
    // tamaño muestral para la media (en dificultad baja se sustituye por la pregunta con el indicador)
    if (d === 2 || (d === 0 && !ind)) {
      const B0 = red(B * (0.45 + 0.25 * R()), media > 50 ? 0 : 1) || red(B * 0.5, 2);
      if (d === 2) {
        const min = red(Math.max(0, media - 2.2 * Sd), 0), max = red(media + 2.4 * Sd, 0), sig2 = ((max - min) / 4) ** 2, D = B0 * B0 / 4;
        const nn = N * sig2 / ((N - 1) * D + sig2);
        ap.push({w: 1, t: `Antes de realizar el estudio solo se sabía que ${c.art ?? "el"} ${c.v} de cada uno está comprendid${c.art === "la" ? "a" : "o"} entre ${num(min)} y ${num(max)} ${c.u}. Con esa información, ¿qué tamaño muestral habría hecho falta para estimar ${c.m} con un error de estimación inferior a ${num(B0)} ${c.u}?`,
          s: `σ<sup>2</sup> ≈ (R/4)<sup>2</sup> = ((${num(max)} − ${num(min)})/4)<sup>2</sup> = ${num(sig2)} &nbsp;&nbsp; D = B<sup>2</sup>/4 = ${num(B0)}<sup>2</sup>/4 = ${num(D)}<br>n = Nσ<sup>2</sup>/[(N − 1)D + σ<sup>2</sup>] = ${N}·${num(sig2)}/(${N - 1}·${num(D)} + ${num(sig2)}) = ${num(nn)} → ${S(`n = ${techo(nn)}`)}`});
      } else {
        const D = B0 * B0 / 4, nn = N * S2c / ((N - 1) * D + S2c);
        ap.push({w: 1, t: `Usando la muestra anterior como muestra previa, ¿cuál debe ser el tamaño muestral para estimar ${c.m} con un error de estimación inferior a ${num(B0)} ${c.u}?`,
          s: `σ<sup>2</sup> ≈ S<sup>2</sup> = ${num(S2c)} &nbsp;&nbsp; D = B<sup>2</sup>/4 = ${num(D)}<br>n = Nσ<sup>2</sup>/[(N − 1)D + σ<sup>2</sup>] = ${N}·${num(S2c)}/(${N - 1}·${num(D)} + ${num(S2c)}) = ${num(nn)} → ${S(`n = ${techo(nn)}`)}`});
      }
    }
    // tamaño muestral para una proporción (con indicador de Eurostat si está disponible)
    if (d >= 1 || ind) {
      const Bp = pick([0.02, 0.025, 0.03, 0.04, 0.05]), D = Bp * Bp / 4;
      if (ind) {
        const p = ind.valor / 100, q = 1 - p, nn = N * p * q / ((N - 1) * D + p * q);
        ap.push({w: 1, indicador: true, t: `Según Eurostat, en ${ind.periodo} el ${num(ind.valor, 1).replace(/,0$/, "")} % ${ind.texto} en España (indicador «${ind.nombre}», disponible en CCEEscopio). La empresa quiere estimar la proporción de sus clientes que ${ind.accion} y toma ese porcentaje como información previa. ¿Cuántos clientes debe incluir en la muestra para que el error de estimación sea como máximo del ${num(100 * Bp)} %?`,
          s: `p ≈ ${num(p)} (Eurostat), q = ${num(q)} &nbsp;&nbsp; D = B<sup>2</sup>/4 = ${num(Bp)}<sup>2</sup>/4 = ${num(D)}<br>n = Npq/[(N − 1)D + pq] = ${N}·${num(p)}·${num(q)}/(${N - 1}·${num(D)} + ${num(p * q)}) = ${num(nn)} → ${S(`n = ${techo(nn)}`)}`});
      } else {
        const nn = N * 0.25 / ((N - 1) * D + 0.25);
        ap.push({w: 1, t: `También se quiere estimar la proporción de estos clientes que ${c.prop}. Sin información previa, ¿cuál debe ser el tamaño muestral para que el error de estimación sea como máximo del ${num(100 * Bp)} %?`,
          s: `Sin información previa: p = q = 1/2 &nbsp;&nbsp; D = B<sup>2</sup>/4 = ${num(D)}<br>n = Npq/[(N − 1)D + pq] = ${N}·0,25/(${N - 1}·${num(D)} + 0,25) = ${num(nn)} → ${S(`n = ${techo(nn)}`)}`});
      }
    }
    return {tema: 1, intro, datos, ap};
  }

  // ---------- tema 2: muestreo aleatorio estratificado ----------
  const CTX2P = [
    {obj: "la proporción de clientes de una cadena de electrodomésticos que han contratado la garantía ampliada", est: ["Tienda física", "Tienda online"], uds: "clientes", resp: "han contratado la garantía ampliada"},
    {obj: "la proporción de usuarios de una aplicación de comida a domicilio que han usado un código promocional", est: ["Usuarios menores de 30 años", "Usuarios de 30 años o más"], uds: "usuarios", resp: "han usado un código promocional"},
    {obj: "la proporción de visitantes de un centro comercial que recuerdan la campaña de Navidad", est: ["Visitantes entre semana", "Visitantes en fin de semana"], uds: "visitantes", resp: "recuerdan la campaña"},
    {obj: "la proporción de clientes de una aseguradora dispuestos a contratar un seguro adicional", est: ["Clientes particulares", "Pequeñas empresas", "Autónomos"], uds: "clientes", resp: "están dispuestos a contratar el seguro adicional"},
    {obj: "la proporción de compradores de una marca de cosmética que la conocieron por recomendación de influencers", est: ["Compradoras", "Compradores"], uds: "compradores", resp: "la conocieron por influencers"},
  ];
  const CTX2N = [
    {obj: "el gasto mensual en publicidad de los comercios asociados a una federación de comercio", est: ["Pequeños", "Medianos", "Grandes"], u: "euros", base: [180, 600, 2200]},
    {obj: "las ventas semanales de las franquicias de una cadena de cafeterías", est: ["Centro urbano", "Barrios", "Centros comerciales"], u: "miles de euros", base: [9, 5, 12]},
    {obj: "el número de visitas semanales a la web de las tiendas de una red de concesionarios", est: ["Concesionarios pequeños", "Concesionarios grandes"], u: "visitas", base: [350, 1400]},
  ];
  function pesos(L) { const w = Array.from({length: L}, () => rr(15, 70, 5)); const s = sum(w); let p = w.map(x => Math.round(100 * x / s)); p[p.length - 1] += 100 - sum(p); return p.map(x => x / 100); }
  function tema2(d, ind) {
    if (!ind && R() < 0.35) return tema2num(d);
    const c = ind ? {obj: `la proporción de clientes de una cadena de supermercados con tiendas en ${ind.regiones.slice(0, -1).join(", ")} y ${ind.regiones.at(-1)} que han probado su nueva línea de productos ecológicos`, est: ind.regiones, uds: "clientes", resp: "la han probado"} : pick(CTX2P);
    const L = c.est.length;
    const W = ind ? ind.pesos : pesos(L);
    const n = rr(L === 2 ? 200 : 240, 500, 10);
    // muestra NO proporcional, para que el apartado c tenga sentido
    let ni = W.map(w => Math.max(30, Math.round(n * (1 / L + (R() < 0.5 ? -1 : 1) * (0.3 + R() * 0.3) * (w - 1 / L) * 2 + 0.15 * (R() - 0.5))))); ni[L - 1] = n - sum(ni.slice(0, -1));
    if (ni.some(x => x < 25)) ni = W.map((w, i) => i < L - 1 ? Math.round(n / L) : n - Math.round(n / L) * (L - 1));
    const pi = W.map(() => rr(5, 60) / 100);
    const ai = ni.map((m, i) => Math.max(1, Math.round(m * pi[i])));
    const ph = ai.map((a, i) => a / ni[i]);
    const intro = ind
      ? `Se quiere estimar ${c.obj}. Los clientes se reparten entre las tres comunidades en proporción a su población. Según Eurostat (población a 1 de enero de ${ind.periodo}, disponible en CCEEscopio), la población de cada comunidad es: ${ind.regiones.map((r, i) => `${r}, ${miles(String(ind.pob[i]))} habitantes`).join("; ")}. Se tomó una muestra aleatoria de ${n} clientes y se obtuvo:`
      : `Se quiere estimar ${c.obj}. Se sabe que ${c.est.map((e, i) => `el ${num(100 * W[i], 0)} % corresponde al grupo «${e.toLowerCase()}»`).join(", ")}. En una muestra aleatoria de ${n} ${c.uds} se obtuvo:`;
    const datos = tabla(["Estrato", ind ? "Peso del estrato (W<sub>i</sub>)" : "Peso", `${c.uds[0].toUpperCase() + c.uds.slice(1)} en la muestra`, `Cuántos ${c.resp}`],
      c.est.map((e, i) => [e, ind ? num(W[i]) : num(100 * W[i], 0) + " %", ni[i], ai[i]]));
    const indSol = ind ? `W<sub>i</sub> = N<sub>i</sub>/N: ${ind.regiones.map((r, i) => `${r} ${miles(String(ind.pob[i]))}/${miles(String(sum(ind.pob)))} = ${num(W[i])}`).join("; ")}<br>` : "";
    const ap = [];
    const p = sum(ai) / n, Vp = p * (1 - p) / (n - 1);
    ap.push({w: 1, t: `Considerando una sola muestra aleatoria simple de ${n} ${c.uds}, estime la proporción de ${c.uds} que ${c.resp} y el límite para el error de estimación.`,
      s: `p̂ = ${ai.join(" + ")}/${n} = ${num(p)} &nbsp;&nbsp; V̂(p̂) = p̂q̂/(n − 1) = ${num(p)}·${num(1 - p)}/${n - 1} = ${num(Vp)}<br>B = 2√V̂(p̂) = ${S(num(2 * Math.sqrt(Vp)))}`});
    const pst = sum(W.map((w, i) => w * ph[i])), Vst = sum(W.map((w, i) => w * w * ph[i] * (1 - ph[i]) / (ni[i] - 1))), Bst = 2 * Math.sqrt(Vst);
    ap.push({w: 1, indicador: !!ind, t: `Estratifique la muestra ${ind ? "por comunidades autónomas, con los pesos obtenidos de los datos de Eurostat," : "en los grupos anteriores,"} estime la proporción de ${c.uds} que ${c.resp} y el límite para el error de estimación${d >= 1 ? " (dé también el intervalo de confianza)" : ""}.`,
      s: `${indSol}p̂<sub>i</sub>: ${ph.map((x, i) => `${ai[i]}/${ni[i]} = ${num(x)}`).join("; ")}<br>p̂<sub>st</sub> = Σ W<sub>i</sub> p̂<sub>i</sub> = ${W.map((w, i) => `${num(w)}·${num(ph[i])}`).join(" + ")} = ${S(num(pst))}<br>V̂(p̂<sub>st</sub>) = Σ W<sub>i</sub><sup>2</sup> p̂<sub>i</sub>q̂<sub>i</sub>/(n<sub>i</sub> − 1) = ${num(Vst)} &nbsp;&nbsp; B = 2√V̂ = ${S(num(Bst))}${d >= 1 ? `<br>Intervalo: ${S(`(${num(pst - Bst)} ; ${num(pst + Bst)})`)}` : ""}`});
    if (d >= 1) {
      const sesgo = ni.map((m, i) => m / n - W[i]);
      const mas = sesgo.findIndex(x => x === Math.max(...sesgo));
      ap.push({w: d === 2 ? 0.5 : 1, t: "¿Qué respuesta encuentra más aceptable? ¿Por qué?",
        s: `Es más aceptable la estimación estratificada. La muestra no está repartida en proporción al peso de cada estrato (el estrato «${c.est[mas]}» supone el ${num(100 * ni[mas] / n, 1)} % de la muestra frente a un peso de ${num(100 * W[mas], 1)} %), por lo que la estimación de la muestra aleatoria simple da demasiada importancia a ese estrato y está sesgada. El estimador estratificado pondera cada estrato por su peso real${Vst < Vp ? " y, además, su error de estimación es menor" : ""}.`});
    }
    if (d < 2) {
      const prop = W.map(w => n * w);
      ap.push({w: d === 0 ? 1 : 0.5, t: `Si se hubiera tomado la muestra de ${n} ${c.uds} con asignación proporcional, ¿cuántos se deberían haber observado en cada estrato?`,
        s: `n<sub>i</sub> = n·W<sub>i</sub>: ${c.est.map((e, i) => `${e}: ${n}·${num(W[i])} = ${S(num(prop[i]))}`).join("; ")}`});
    } else {
      const Bn = pick([0.02, 0.025, 0.03]), D = Bn * Bn / 4, raices = W.map((w, i) => w * Math.sqrt(ph[i] * (1 - ph[i])));
      const nn = sum(raices) ** 2 / D;
      ap.push({w: 1.5, t: `Se quiere repetir el estudio con un error de estimación inferior al ${num(100 * Bn)} % usando asignación de Neyman y la muestra anterior como información previa. ¿Cuántos ${c.uds} deben estudiarse en total y en cada estrato?`,
        s: `D = B<sup>2</sup>/4 = ${num(D)} &nbsp;&nbsp; Σ W<sub>i</sub>√(p<sub>i</sub>q<sub>i</sub>) = ${raices.map(x => num(x)).join(" + ")} = ${num(sum(raices))}<br>n = (Σ W<sub>i</sub>√(p<sub>i</sub>q<sub>i</sub>))<sup>2</sup>/D = ${num(sum(raices) ** 2)}/${num(D)} = ${num(nn)} → n = ${techo(nn)}<br>n<sub>i</sub> = n·W<sub>i</sub>√(p<sub>i</sub>q<sub>i</sub>)/Σ W<sub>j</sub>√(p<sub>j</sub>q<sub>j</sub>): ${c.est.map((e, i) => `${e}: ${S(num(techo(nn) * raices[i] / sum(raices)))}`).join("; ")}`});
    }
    return {tema: 2, intro, datos, ap};
  }
  function tema2num(d) {
    const c = pick(CTX2N), L = c.est.length;
    const Ni = c.est.map(() => rr(40, 400, 10)), N = sum(Ni);
    const ni = Ni.map(x => Math.max(5, Math.round(x * (0.06 + R() * 0.08))));
    const yb = c.base.map(b => red(b * (0.8 + 0.4 * R()), b > 100 ? 0 : 1)), Si = c.base.map(b => red(b * (0.15 + 0.25 * R()), b > 100 ? 0 : 1));
    const intro = `Se quiere estimar ${c.obj}. Los ${N} establecimientos se clasifican en ${L} estratos según su tipo. Se selecciona una muestra aleatoria estratificada y se obtienen los siguientes resultados (en ${c.u}):`;
    const datos = tabla(["Estrato", "N<sub>i</sub>", "n<sub>i</sub>", "Media muestral", "Cuasivarianza muestral"], c.est.map((e, i) => [e, Ni[i], ni[i], num(yb[i]), num(Si[i] ** 2)]));
    const yst = sum(Ni.map((x, i) => x * yb[i])) / N, comp = Ni.map((x, i) => x * x * Si[i] ** 2 / ni[i] * (x - ni[i]) / x);
    const Vt = sum(comp), Bt = 2 * Math.sqrt(Vt), tau = N * yst;
    const ap = [];
    ap.push({w: 1, t: `Estime la media por establecimiento y el límite para el error de estimación.`,
      s: `ȳ<sub>st</sub> = (1/N) Σ N<sub>i</sub>ȳ<sub>i</sub> = ${S(num(yst))}<br>V̂(ȳ<sub>st</sub>) = (1/N<sup>2</sup>) Σ N<sub>i</sub><sup>2</sup>(S<sub>i</sub><sup>2</sup>/n<sub>i</sub>)(N<sub>i</sub> − n<sub>i</sub>)/N<sub>i</sub> = ${num(Vt / N / N)} &nbsp;&nbsp; B = ${S(num(Bt / N))}`});
    if (d >= 1) ap.push({w: 1, t: `Estime el total con un intervalo de confianza.`,
      s: `τ̂<sub>st</sub> = N·ȳ<sub>st</sub> = ${num(tau)} &nbsp;&nbsp; V̂(τ̂<sub>st</sub>) = Σ N<sub>i</sub><sup>2</sup>(S<sub>i</sub><sup>2</sup>/n<sub>i</sub>)(N<sub>i</sub> − n<sub>i</sub>)/N<sub>i</sub> = ${num(Vt)} &nbsp;&nbsp; B = ${num(Bt)}<br>Intervalo: ${S(`(${num(tau - Bt)} ; ${num(tau + Bt)})`)}`});
    const B0 = red(Bt / N * (0.5 + 0.2 * R()), yst > 100 ? 0 : 2), D = B0 * B0 / 4;
    if (d !== 1 || R() < 0.5) {
      const nn = sum(Ni.map((x, i) => x * Si[i] ** 2)) / (N * D + sum(Ni.map((x, i) => x * Si[i] ** 2)) / N);
      ap.push({w: 1, t: `Con asignación proporcional, ¿qué tamaño muestral hace falta para estimar la media por establecimiento con un error inferior a ${num(B0)} ${c.u}? ¿Cuántos establecimientos de cada estrato?`,
        s: `D = B<sup>2</sup>/4 = ${num(D)} &nbsp;&nbsp; Σ N<sub>i</sub>σ<sub>i</sub><sup>2</sup> = ${num(sum(Ni.map((x, i) => x * Si[i] ** 2)))}<br>n = Σ N<sub>i</sub>σ<sub>i</sub><sup>2</sup>/[ND + (1/N)Σ N<sub>i</sub>σ<sub>i</sub><sup>2</sup>] = ${num(nn)} → n = ${techo(nn)}<br>n<sub>i</sub> = n·N<sub>i</sub>/N: ${c.est.map((e, i) => `${e}: ${S(num(techo(nn) * Ni[i] / N))}`).join("; ")}`});
    }
    if (d === 2) {
      const sNs = sum(Ni.map((x, i) => x * Si[i])), nn = sNs ** 2 / (N * N * D + sum(Ni.map((x, i) => x * Si[i] ** 2)));
      ap.push({w: 1, t: `Repita el apartado anterior con asignación de Neyman. ¿Qué asignación resulta más eficiente?`,
        s: `n = (Σ N<sub>i</sub>σ<sub>i</sub>)<sup>2</sup>/[N<sup>2</sup>D + Σ N<sub>i</sub>σ<sub>i</sub><sup>2</sup>] = ${num(sNs ** 2)}/(${num(N * N * D)} + ${num(sum(Ni.map((x, i) => x * Si[i] ** 2)))}) = ${num(nn)} → n = ${techo(nn)}<br>n<sub>i</sub> = n·N<sub>i</sub>σ<sub>i</sub>/Σ N<sub>j</sub>σ<sub>j</sub>: ${c.est.map((e, i) => `${e}: ${S(num(techo(nn) * Ni[i] * Si[i] / sNs))}`).join("; ")}<br>La asignación de Neyman necesita una muestra menor (o igual), porque tiene en cuenta la variabilidad de cada estrato.`});
    }
    return {tema: 2, intro, datos, ap};
  }

  // ---------- tema 3: estimación de razón, regresión y diferencia ----------
  const CTX3 = [
    {tipo: "razon", uni: "Tienda", unis: "tiendas", todas: "de todas las tiendas de la cadena", N: [60, 300], obj: "las tiendas de una cadena de moda", x: "Superficie de venta (m²)", y: "Ventas mensuales (miles de €)", xr: [80, 400], k: [0.08, 0.16],
     q: "las ventas mensuales por metro cuadrado de superficie de venta", ux: "metros cuadrados de superficie de venta", uy: "miles de euros"},
    {tipo: "razon", uni: "Campaña", unis: "campañas", todas: "de todas las campañas de la agencia", N: [80, 400], obj: "las campañas publicitarias en redes sociales de una agencia de marketing", x: "Inversión (€)", y: "Clics conseguidos", xr: [500, 3000], k: [0.8, 2.2],
     q: "el número de clics por euro invertido", ux: "euros invertidos", uy: "clics"},
    {tipo: "regresion", uni: "Comercio", N: [80, 300], obj: "los comercios de una asociación de comerciantes", x: "Gasto en publicidad (cientos de €)", y: "Ventas (miles de €)", xr: [5, 40], k: [1.5, 3.5], a: [10, 40],
     q: "las ventas", ux: "cientos de euros de gasto en publicidad", uy: "miles de euros"},
    {tipo: "diferencia", uni: "Punto de venta", N: [60, 250], obj: "los puntos de venta de una marca de helados", x: "Ventas del año pasado (miles de €)", y: "Ventas de este año (miles de €)", xr: [40, 160], k: [1, 1], a: [-6, 14],
     q: "las ventas de este año", ux: "miles de euros vendidos el año pasado", uy: "miles de euros"},
  ];
  function tema3(d) {
    const c = pick(CTX3), N = rr(c.N[0], c.N[1], 5), n = d === 2 ? 6 : 5;
    const k = c.k[0] + R() * (c.k[1] - c.k[0]), a = c.a ? c.a[0] + R() * (c.a[1] - c.a[0]) : 0;
    const dx = c.xr[1] > 1000 ? 100 : c.xr[1] > 100 ? 10 : 1;
    const x = Array.from({length: n}, () => rr(c.xr[0], c.xr[1], dx));
    const ruido = c.tipo === "diferencia" ? 4 : (c.xr[1] * k) * 0.08;
    const y = x.map(v => Math.max(1, Math.round((a + k * v + (R() - 0.5) * 2 * ruido) * (c.xr[1] * k > 200 ? 1 : 10)) / (c.xr[1] * k > 200 ? 1 : 10)));
    const xb = sum(x) / n, yb = sum(y) / n, Sx2 = sum(x.map(v => v * v)), Sy2 = sum(y.map(v => v * v)), Sxy = sum(x.map((v, i) => v * y[i]));
    const mux = red(xb * (0.9 + 0.2 * R()), dx >= 10 ? 0 : 1), taux = N * mux;
    const datos = tabla([c.uni, c.x, c.y], x.map((v, i) => [i + 1, num(v), num(y[i])]));
    const ap = [];
    let intro;
    if (c.tipo === "razon") {
      intro = `Se quiere estudiar ${c.q} de ${c.obj}, formada por ${N} unidades. Se seleccionan al azar ${n} de ellas y se obtienen los siguientes datos:`;
      const r = sum(y) / sum(x), Sr2 = (Sy2 + r * r * Sx2 - 2 * r * Sxy) / (n - 1), mx = d >= 1 ? mux : xb;
      const Vr = (N - n) / N * Sr2 / (n * mx * mx), Br = 2 * Math.sqrt(Vr);
      const tabC = tabla(["x<sub>i</sub>", "y<sub>i</sub>", "x<sub>i</sub><sup>2</sup>", "y<sub>i</sub><sup>2</sup>", "x<sub>i</sub>y<sub>i</sub>"], [...x.map((v, i) => [num(v), num(y[i]), num(v * v), num(y[i] * y[i]), num(v * y[i])]), [num(sum(x)), num(sum(y)), num(Sx2), num(Sy2), num(Sxy)]]);
      if (d >= 1) intro += ` Se sabe, además, que el total de ${c.ux} de toda la población es τ<sub>x</sub> = ${num(taux)}.`;
      ap.push({w: 1, t: `Estime ${c.q} y el límite del error de dicha estimación.`,
        s: `${tabC}r = Σy<sub>i</sub>/Σx<sub>i</sub> = ${num(sum(y))}/${num(sum(x))} = ${S(num(r))}<br>S<sub>r</sub><sup>2</sup> = [Σy<sub>i</sub><sup>2</sup> + r<sup>2</sup>Σx<sub>i</sub><sup>2</sup> − 2rΣx<sub>i</sub>y<sub>i</sub>]/(n − 1) = ${num(Sr2)}<br>${d >= 1 ? `μ<sub>x</sub> = τ<sub>x</sub>/N = ${num(mx)}` : `μ<sub>x</sub> ≈ x̄ = ${num(mx)}`} &nbsp;&nbsp; V̂(r) = (1/μ<sub>x</sub><sup>2</sup>)·((N − n)/N)·S<sub>r</sub><sup>2</sup>/n = ${num(Vr)} &nbsp;&nbsp; B = 2√V̂(r) = ${S(num(Br))}`});
      if (d >= 1) {
        const ty = r * taux, Bt = taux * Br;
        ap.push({w: 1, t: `Estime con un intervalo de confianza el total de ${c.y.split(" (")[0].toLowerCase()} ${c.todas}.`,
          s: `τ̂<sub>y</sub> = r·τ<sub>x</sub> = ${num(r)}·${num(taux)} = ${num(ty)} &nbsp;&nbsp; V̂(τ̂<sub>y</sub>) = τ<sub>x</sub><sup>2</sup>V̂(r) = ${num(taux * taux * Vr)} &nbsp;&nbsp; B = ${num(Bt)}<br>Intervalo: ${S(`(${num(ty - Bt)} ; ${num(ty + Bt)})`)}`});
      }
      if (d === 2) {
        const B0 = red(Br * (0.4 + 0.2 * R()), 4) || 0.0001, D = B0 * B0 * mux * mux / 4, nn = N * Sr2 / (N * D + Sr2);
        ap.push({w: 1, t: `Se quiere ampliar el estudio para estimar ${c.q} con un error inferior a ${num(B0)}. ¿Cuántas ${c.unis} deberían estudiarse?`,
          s: `D = B<sup>2</sup>μ<sub>x</sub><sup>2</sup>/4 = ${num(D)} &nbsp;&nbsp; σ<sub>r</sub><sup>2</sup> ≈ S<sub>r</sub><sup>2</sup> = ${num(Sr2)}<br>n = Nσ<sub>r</sub><sup>2</sup>/(ND + σ<sub>r</sub><sup>2</sup>) = ${num(nn)} → ${S(`n = ${techo(nn)}`)}`});
      }
    } else if (c.tipo === "regresion") {
      intro = `Se quiere estimar ${c.q} totales de ${c.obj} (${N} comercios) aprovechando su relación con el gasto en publicidad. Se conoce el gasto total en publicidad de todos los comercios: τ<sub>x</sub> = ${num(taux)} ${c.ux}. Una muestra aleatoria de ${n} comercios dio:`;
      const sx2 = Sx2 / n - xb * xb, sy2 = Sy2 / n - yb * yb, sxy = Sxy / n - xb * yb, b = sxy / sx2;
      const mu = yb + b * (mux - xb), SL2 = n / (n - 2) * (sy2 - sxy * sxy / sx2), V = (N - n) / N * SL2 / n, B = 2 * Math.sqrt(V);
      ap.push({w: d === 0 ? 2 : 1.5, t: `Usando estimación de regresión, estime con un intervalo de confianza el total de ventas de los comercios de la asociación.`,
        s: `x̄ = ${num(xb)}; ȳ = ${num(yb)}; s<sub>x</sub><sup>2</sup> = ${num(sx2)}; s<sub>y</sub><sup>2</sup> = ${num(sy2)}; s<sub>xy</sub> = ${num(sxy)} (dividiendo por n)<br>μ<sub>x</sub> = τ<sub>x</sub>/N = ${num(mux)} &nbsp;&nbsp; b = s<sub>xy</sub>/s<sub>x</sub><sup>2</sup> = ${num(b)}<br>μ̂<sub>yL</sub> = ȳ + b(μ<sub>x</sub> − x̄) = ${num(mu)} &nbsp;&nbsp; τ̂<sub>yL</sub> = N·μ̂<sub>yL</sub> = ${num(N * mu)}<br>S<sub>L</sub><sup>2</sup> = (n/(n − 2))·(s<sub>y</sub><sup>2</sup> − s<sub>xy</sub><sup>2</sup>/s<sub>x</sub><sup>2</sup>) = ${num(SL2)}<br>V̂(τ̂<sub>yL</sub>) = N<sup>2</sup>·((N − n)/N)·S<sub>L</sub><sup>2</sup>/n = ${num(N * N * V)} &nbsp;&nbsp; B = ${num(N * B)}<br>Intervalo: ${S(`(${num(N * (mu - B))} ; ${num(N * (mu + B))})`)}`});
      if (d >= 1) {
        const B0 = red(N * B * (0.4 + 0.2 * R()), 0) || 1, D = B0 * B0 / (4 * N * N), nn = N * SL2 / (N * D + SL2);
        ap.push({w: 1.5, t: `Se quiere ampliar el estudio de forma que la estimación del total tenga un error inferior a ${num(B0)} ${c.uy}. ¿Cuántos comercios deberían estudiarse?`,
          s: `D = B<sup>2</sup>/(4N<sup>2</sup>) = ${num(D)} &nbsp;&nbsp; σ<sub>L</sub><sup>2</sup> ≈ S<sub>L</sub><sup>2</sup> = ${num(SL2)}<br>n = Nσ<sub>L</sub><sup>2</sup>/(ND + σ<sub>L</sub><sup>2</sup>) = ${num(nn)} → ${S(`n = ${techo(nn)}`)}`});
      }
      if (d === 2) {
        const r2 = sxy * sxy / (sx2 * sy2);
        ap.push({w: 0.5, t: `¿Está justificado el uso de la estimación de regresión? Razone la respuesta con el coeficiente de determinación.`,
          s: `r<sub>xy</sub><sup>2</sup> = s<sub>xy</sub><sup>2</sup>/(s<sub>x</sub><sup>2</sup>s<sub>y</sub><sup>2</sup>) = ${S(num(r2))}. ${r2 > 0.6 ? "La relación lineal entre gasto en publicidad y ventas es fuerte, por lo que la estimación de regresión reduce mucho la varianza frente al muestreo aleatorio simple." : "La relación lineal es débil, por lo que la ganancia de precisión frente al muestreo aleatorio simple es pequeña."}`});
      }
    } else {
      intro = `Se quiere estimar ${c.q} de ${c.obj} (${N} puntos de venta). Se conocen las ventas del año pasado de todos ellos: en total, τ<sub>x</sub> = ${num(taux)} ${c.ux}. Una muestra aleatoria de ${n} puntos de venta dio:`;
      const di = y.map((v, i) => v - x[i]), db = sum(di) / n, SD2 = (sum(di.map(v => v * v)) - sum(di) ** 2 / n) / (n - 1);
      const mu = mux + db, V = (N - n) / N * SD2 / n, B = 2 * Math.sqrt(V);
      ap.push({w: d === 0 ? 2 : 1.5, t: `Usando estimación de diferencia, estime con un intervalo de confianza las ventas medias por punto de venta de este año.`,
        s: `d<sub>i</sub> = y<sub>i</sub> − x<sub>i</sub>: ${di.map(v => num(red(v, 2))).join("; ")} &nbsp;&nbsp; d̄ = ${num(db)}<br>μ<sub>x</sub> = τ<sub>x</sub>/N = ${num(mux)} &nbsp;&nbsp; μ̂<sub>yD</sub> = μ<sub>x</sub> + d̄ = ${num(mu)}<br>S<sub>D</sub><sup>2</sup> = [Σd<sub>i</sub><sup>2</sup> − (Σd<sub>i</sub>)<sup>2</sup>/n]/(n − 1) = ${num(SD2)} &nbsp;&nbsp; V̂(μ̂<sub>yD</sub>) = ((N − n)/N)·S<sub>D</sub><sup>2</sup>/n = ${num(V)} &nbsp;&nbsp; B = ${num(B)}<br>Intervalo: ${S(`(${num(mu - B)} ; ${num(mu + B)})`)}`});
      if (d >= 1) ap.push({w: 1, t: `Estime con un intervalo de confianza las ventas totales de este año.`,
        s: `τ̂<sub>yD</sub> = N·μ̂<sub>yD</sub> = ${num(N * mu)} &nbsp;&nbsp; B = N·B<sub>μ</sub> = ${num(N * B)}<br>Intervalo: ${S(`(${num(N * (mu - B))} ; ${num(N * (mu + B))})`)}`});
      if (d === 2) {
        const B0 = red(B * (0.4 + 0.2 * R()), 2) || 0.1, D = B0 * B0 / 4, nn = N * SD2 / (N * D + SD2);
        ap.push({w: 1, t: `¿Cuántos puntos de venta habría que estudiar para estimar las ventas medias de este año con un error inferior a ${num(B0)} ${c.uy}?`,
          s: `D = B<sup>2</sup>/4 = ${num(D)} &nbsp;&nbsp; n = Nσ<sub>D</sub><sup>2</sup>/(ND + σ<sub>D</sub><sup>2</sup>) = ${num(nn)} → ${S(`n = ${techo(nn)}`)}`});
      }
    }
    return {tema: 3, intro, datos, ap};
  }

  // ---------- tema 4: muestreo sistemático ----------
  const CTX4 = [
    {txt: (N, k) => `Una cadena de librerías quiere estimar el importe medio de los tiques de compra emitidos durante la campaña de vuelta al cole. Se emitieron ${miles(String(N))} tiques y se toma una muestra sistemática de 1 en ${k}.`, v: "importe del tique (euros)", mu: [18, 45], cv: 0.5, q: "el importe medio de los tiques", tot: "el importe total facturado", u: "euros"},
    {txt: (N, k) => `Un servicio de atención al cliente recibió ${miles(String(N))} llamadas el mes pasado. Para estimar la duración media de las llamadas se toma una muestra sistemática de 1 en ${k} del registro de llamadas.`, v: "duración (minutos)", mu: [4, 12], cv: 0.45, q: "la duración media de las llamadas", tot: "el tiempo total dedicado a atender llamadas", u: "minutos"},
    {txt: (N, k) => `Un hotel quiere estimar la valoración media que le dieron sus ${miles(String(N))} huéspedes del último año en una plataforma de reservas (escala de 0 a 10). Se toma una muestra sistemática de 1 en ${k} del listado de reseñas.`, v: "valoración", mu: [6.5, 8.8], cv: 0.18, q: "la valoración media", tot: null, u: "puntos"},
  ];
  const CTX4P = [
    {txt: (N, k) => `La dirección de una cadena de supermercados, con ${miles(String(N))} tarjetas de cliente activas, quiere estimar cuántos clientes estarían interesados en un servicio de compra por suscripción. Se toma una muestra sistemática de 1 en ${k} de la base de datos de clientes (anotando 1 si el cliente está interesado y 0 en caso contrario).`, q: "el número total de clientes interesados"},
    {txt: (N, k) => `Una marca de ropa deportiva ha recibido ${miles(String(N))} pedidos online esta temporada y quiere estimar cuántos de ellos han sido devueltos. Se toma una muestra sistemática de 1 en ${k} de los pedidos (anotando 1 si el pedido fue devuelto).`, q: "el número total de pedidos devueltos"},
  ];
  function tema4(d) {
    const k = pick([5, 8, 10, 12, 15, 20, 25]), n = rr(d === 0 ? 40 : 60, 300, 5), N = n * k;
    const ap = [];
    if (R() < 0.5) {
      const c = pick(CTX4), ybar = c.mu[0] + R() * (c.mu[1] - c.mu[0]), Sd = ybar * c.cv * (0.7 + 0.6 * R());
      const sy = red(n * ybar, c.mu[1] < 10 ? 1 : 0), sy2 = red((n - 1) * Sd * Sd + sy * sy / n, 0);
      const S2 = (sy2 - sy * sy / n) / (n - 1), m = sy / n, V = S2 / n * (N - n) / N, B = 2 * Math.sqrt(V);
      const intro = `${c.txt(N, k)} Los resultados de la muestra (${c.v}) fueron:`;
      const datos = `<p class="tc3-centro">Σ y<sub>i</sub> = ${num(sy)} &nbsp;&nbsp;&nbsp; Σ y<sub>i</sub><sup>2</sup> = ${num(sy2)}</p>`;
      const usaTot = c.tot && R() < 0.5;
      const est = usaTot ? N * m : m, Be = usaTot ? N * B : B;
      ap.push({w: 1, t: `Estime ${usaTot ? c.tot : c.q} con un intervalo de confianza. ¿Cuál sería la previsión más optimista y la más pesimista?`,
        s: `n = N/k = ${N}/${k} = ${n} &nbsp;&nbsp; ȳ = ${num(sy)}/${n} = ${num(m)}<br>S<sup>2</sup> = [Σy<sub>i</sub><sup>2</sup> − (Σy<sub>i</sub>)<sup>2</sup>/n]/(n − 1) = ${num(S2)} &nbsp;&nbsp; V̂(ȳ) = (S<sup>2</sup>/n)(N − n)/N = ${num(V)}<br>${usaTot ? `τ̂ = N·ȳ = ${num(est)} &nbsp;&nbsp; B = N·2√V̂(ȳ) = ${num(Be)}` : `B = 2√V̂(ȳ) = ${num(Be)}`}<br>Intervalo (la más pesimista, la más optimista): ${S(`(${num(est - Be)} ; ${num(est + Be)})`)}`});
      const B0 = red(B * (0.55 + 0.25 * R()) * (usaTot ? N : 1), usaTot ? 0 : 2) || 0.01, D = usaTot ? B0 * B0 / (4 * N * N) : B0 * B0 / 4;
      const nn = N * S2 / ((N - 1) * D + S2), kk = Math.floor(N / techo(nn));
      ap.push({w: 1, t: `Si se quisiera estimar ${usaTot ? c.tot : c.q} con un error inferior a ${num(B0)} ${c.u}, ¿cómo debe tomarse la nueva muestra sistemática? (especifique los valores de n y k)`,
        s: `D = ${usaTot ? "B<sup>2</sup>/(4N<sup>2</sup>)" : "B<sup>2</sup>/4"} = ${num(D)} &nbsp;&nbsp; σ<sup>2</sup> ≈ S<sup>2</sup> = ${num(S2)}<br>n = Nσ<sup>2</sup>/[(N − 1)D + σ<sup>2</sup>] = ${num(nn)} → n = ${techo(nn)} &nbsp;&nbsp; k = N/n = ${num(N / techo(nn))} → ${S(`k = ${kk}`)} (se toma una unidad de cada ${kk})`});
      if (d === 2) ap.push({w: 0.5, t: `¿En qué tipo de poblaciones es el muestreo sistemático más preciso que el muestreo aleatorio simple? ¿Qué ocurre si la población es periódica?`,
        s: `En las poblaciones ordenadas (con tendencia según el orden del listado), el muestreo sistemático es más preciso porque reparte la muestra por toda la población. En las poblaciones aleatorias es equivalente al muestreo aleatorio simple. En las periódicas puede ser mucho menos preciso si k coincide con el periodo (o un múltiplo), porque todas las unidades muestreadas se parecen.`});
      return {tema: 4, intro, datos, ap};
    }
    const c = pick(CTX4P), p = rr(10, 60) / 100, a = Math.max(1, Math.round(n * p)), ph = a / n;
    const intro = `${c.txt(N, k)} Los resultados fueron:`;
    const datos = tabla(["Unidad muestreada", "Respuesta"], [[k - 3 > 0 ? k - 3 : 1, 1], [2 * k - 3 > 0 ? 2 * k - 3 : 2, 0], [3 * k - 3, 1], ["…", "…"], [N - 3, 0]]) + `<p class="tc3-centro">Σ y<sub>i</sub> = ${a}</p>`;
    const V = N * (N - n) * ph * (1 - ph) / (n - 1), B = 2 * Math.sqrt(V), tau = N * ph;
    ap.push({w: 1, t: `¿Cuál sería la previsión más optimista y la más pesimista en cuanto ${c.q.replace(/^el /, "al ")}?`,
      s: `n = N/k = ${N}/${k} = ${n} &nbsp;&nbsp; p̂ = ${a}/${n} = ${num(ph)} &nbsp;&nbsp; τ̂ = N·p̂ = ${num(tau)}<br>V̂(τ̂) = N(N − n)p̂q̂/(n − 1) = ${num(V)} &nbsp;&nbsp; B = 2√V̂(τ̂) = ${num(B)}<br>(τ̂ − B ; τ̂ + B) = ${S(`(${num(tau - B)} ; ${num(tau + B)})`)} = (la más pesimista, la más optimista)`});
    const B0 = red(B * (0.55 + 0.25 * R()), 0) || 1, D = B0 * B0 / (4 * N * N), nn = N * ph * (1 - ph) / ((N - 1) * D + ph * (1 - ph)), kk = Math.floor(N / techo(nn));
    ap.push({w: 1, t: `Si quisiéramos estimar ${c.q} con un error inferior a ${num(B0)}, ¿cómo debe tomarse la nueva muestra sistemática? (especifique los valores de n y k)`,
      s: `D = B<sup>2</sup>/(4N<sup>2</sup>) = ${num(D)}<br>n = Npq/[(N − 1)D + pq] = ${num(nn)} → n = ${techo(nn)} &nbsp;&nbsp; k = N/n = ${num(N / techo(nn))} → ${S(`k = ${kk}`)}`});
    if (d === 2) ap.push({w: 0.5, t: `Si la base de datos estuviera ordenada de forma que los clientes se alternan periódicamente según una característica relacionada con la respuesta, ¿qué riesgo tendría el muestreo sistemático?`,
      s: `Si la población es periódica y k coincide con el periodo (o un múltiplo), todas las unidades de la muestra tendrán un comportamiento parecido y la estimación puede estar muy sesgada; su precisión puede ser mucho peor que la del muestreo aleatorio simple. Conviene cambiar el arranque aleatorio varias veces o usar otro k.`});
    return {tema: 4, intro, datos, ap};
  }

  // ---------- tema 5: muestreo por conglomerados ----------
  const CTX5 = [
    {prop: true, txt: (N, n) => `Una marca de bebidas quiere estimar el porcentaje de clientes de bares que conocen su nueva bebida sin azúcar. Entre los ${N} bares de la ciudad selecciona al azar ${n} y, en cada uno, pregunta a todos los clientes presentes a una hora concreta.`, m: "clientes presentes", y: "clientes que conocen la bebida", ytot: "el número total de clientes que conocen la bebida", mm: [8, 40], p: [0.2, 0.6]},
    {prop: true, txt: (N, n) => `Una cadena de academias quiere estimar el porcentaje de estudiantes que la conocieron por publicidad en redes sociales. De sus ${N} grupos de clase selecciona al azar ${n} y pregunta a todos los estudiantes de cada grupo.`, m: "estudiantes del grupo", y: "estudiantes que la conocieron por redes sociales", ytot: "el número total de estudiantes que la conocieron por redes sociales", mm: [10, 30], p: [0.25, 0.65]},
    {prop: false, txt: (N, n) => `Una empresa de reparto quiere estimar el gasto medio por hogar en compras online en una ciudad dividida en ${N} manzanas. Selecciona al azar ${n} manzanas y anota el gasto mensual total en compras online de todos los hogares de cada manzana.`, m: "hogares de la manzana", y: "gasto total mensual (euros)", ytot: "el gasto mensual total en compras online de la ciudad", mm: [6, 24], mu: [60, 160], u: "euros por hogar"},
    {prop: false, txt: (N, n) => `Una cadena hotelera quiere estimar el gasto medio por cliente en el bar y la cafetería de sus hoteles. De los ${N} grupos turísticos alojados el último mes selecciona ${n} al azar y anota el gasto total de cada grupo.`, m: "personas del grupo", y: "gasto total del grupo (euros)", ytot: "el gasto total de todos los grupos", mm: [10, 45], mu: [20, 60], u: "euros por persona"},
  ];
  function tema5(d) {
    const c = pick(CTX5), N = rr(100, 900, 10), n = d === 2 ? ri(20, 30) : ri(5, 7);
    const m = Array.from({length: n}, () => ri(c.mm[0], c.mm[1]));
    const th = c.prop ? c.p[0] + R() * (c.p[1] - c.p[0]) : c.mu[0] + R() * (c.mu[1] - c.mu[0]);
    const y = m.map(v => c.prop ? Math.min(v, Math.max(0, Math.round(v * (th + (R() - 0.5) * 0.3)))) : Math.round(v * th * (0.7 + 0.6 * R())));
    const Sy = sum(y), Sm = sum(m), Sy2 = sum(y.map(v => v * v)), Sm2 = sum(m.map(v => v * v)), Sym = sum(y.map((v, i) => v * m[i]));
    const yb = Sy / Sm, mb = Sm / n, Sc2 = (Sy2 + yb * yb * Sm2 - 2 * yb * Sym) / (n - 1);
    const conoceM = d >= 1 && R() < 0.6, M = conoceM ? Math.round(N * mb * (0.9 + 0.2 * R())) : null, Mb = conoceM ? M / N : mb;
    const V = (1 / (Mb * Mb)) * (N - n) / N * Sc2 / n, B = 2 * Math.sqrt(V);
    const intro = c.txt(N, n) + (conoceM ? ` Se sabe que el número total de ${c.m.split(" ")[0]} es M = ${miles(String(M))}.` : "");
    const datos = n <= 8 ? tabla(["Conglomerado", `m<sub>i</sub> (${c.m})`, `y<sub>i</sub> (${c.y})`], m.map((v, i) => [i + 1, v, y[i]]))
      : `<p class="tc3-centro">n = ${n} &nbsp; Σ y<sub>i</sub> = ${num(Sy)} &nbsp; Σ m<sub>i</sub> = ${Sm} &nbsp; Σ y<sub>i</sub><sup>2</sup> = ${num(Sy2)} &nbsp; Σ m<sub>i</sub><sup>2</sup> = ${Sm2} &nbsp; Σ y<sub>i</sub>m<sub>i</sub> = ${num(Sym)}</p><p>(m<sub>i</sub> = ${c.m}; y<sub>i</sub> = ${c.y})</p>`;
    const sums = n <= 8 ? `Σy<sub>i</sub> = ${num(Sy)}; Σm<sub>i</sub> = ${Sm}; Σy<sub>i</sub><sup>2</sup> = ${num(Sy2)}; Σm<sub>i</sub><sup>2</sup> = ${Sm2}; Σy<sub>i</sub>m<sub>i</sub> = ${num(Sym)}<br>` : "";
    const ap = [];
    const qtxt = c.prop ? "el porcentaje de " + c.y.replace("clientes que ", "clientes que ").replace(/^(\w+)/, "$1") : "el gasto medio";
    ap.push({w: 1, t: c.prop ? `Estime el porcentaje de ${c.y.split(" que ")[0]} que ${c.y.split(" que ")[1]} y el límite para el error de estimación.` : `Estime el gasto medio (${c.u}) y el límite para el error de estimación.`,
      s: `${sums}${c.prop ? "p̂" : "ȳ"} = Σy<sub>i</sub>/Σm<sub>i</sub> = ${num(Sy)}/${Sm} = ${S(c.prop ? `${num(yb)} (${pct(yb)})` : num(yb))}<br>S<sub>c</sub><sup>2</sup> = [Σy<sub>i</sub><sup>2</sup> + ȳ<sup>2</sup>Σm<sub>i</sub><sup>2</sup> − 2ȳΣy<sub>i</sub>m<sub>i</sub>]/(n − 1) = ${num(Sc2)}<br>${conoceM ? `M̄ = M/N = ${num(Mb)}` : `M̄ ≈ m̄ = ${num(mb)}`} &nbsp;&nbsp; V̂ = (1/M̄<sup>2</sup>)·((N − n)/N)·S<sub>c</sub><sup>2</sup>/n = ${num(V)} &nbsp;&nbsp; B = 2√V̂ = ${S(c.prop ? `${num(B)} (${pct(B)})` : num(B))}`});
    if (d >= 1) {
      if (conoceM) ap.push({w: 1, t: `Estime con un intervalo de confianza ${c.ytot}.`,
        s: `τ̂ = M·${c.prop ? "p̂" : "ȳ"} = ${miles(String(M))}·${num(yb)} = ${num(M * yb)} &nbsp;&nbsp; B = M·B<sub>μ</sub> = ${num(M * B)}<br>Intervalo: ${S(`(${num(M * (yb - B))} ; ${num(M * (yb + B))})`)}`});
      else {
        const yt = Sy / n, St2 = (Sy2 - Sy * Sy / n) / (n - 1), Vt = N * (N - n) * St2 / n, Bt = 2 * Math.sqrt(Vt);
        ap.push({w: 1, t: `Sin conocer el número total de ${c.m.split(" ")[0]}, estime con un intervalo de confianza ${c.ytot}.`,
          s: `τ̂ = N·ȳ<sub>t</sub> con ȳ<sub>t</sub> = Σy<sub>i</sub>/n = ${num(yt)} → τ̂ = ${num(N * yt)}<br>S<sub>t</sub><sup>2</sup> = [Σy<sub>i</sub><sup>2</sup> − (Σy<sub>i</sub>)<sup>2</sup>/n]/(n − 1) = ${num(St2)} &nbsp;&nbsp; V̂(τ̂) = N(N − n)S<sub>t</sub><sup>2</sup>/n = ${num(Vt)} &nbsp;&nbsp; B = ${num(Bt)}<br>Intervalo: ${S(`(${num(N * yt - Bt)} ; ${num(N * yt + Bt)})`)}`});
      }
    }
    if (d !== 1 || R() < 0.5) {
      const B0 = c.prop ? red(B * (0.5 + 0.2 * R()), 3) || 0.005 : red(B * (0.5 + 0.2 * R()), 1) || 0.1, D = B0 * B0 * Mb * Mb / 4, nn = N * Sc2 / (N * D + Sc2);
      ap.push({w: 1, t: `Se quiere ampliar el estudio de forma que la estimación tenga un error inferior a ${c.prop ? pct(B0, 1) : num(B0) + " " + c.u}. ¿Cuántos conglomerados deberían observarse?`,
        s: `D = B<sup>2</sup>M̄<sup>2</sup>/4 = ${num(B0)}<sup>2</sup>·${num(Mb)}<sup>2</sup>/4 = ${num(D)}<br>n = Nσ<sub>c</sub><sup>2</sup>/(ND + σ<sub>c</sub><sup>2</sup>) = ${N}·${num(Sc2)}/(${N}·${num(D)} + ${num(Sc2)}) = ${num(nn)} → ${S(`n = ${techo(nn)}`)}`});
    }
    return {tema: 5, intro, datos, ap};
  }

  // ---------- tema 6: estimación del tamaño de la población ----------
  function tema6(d) {
    const ap = [];
    const modo = d === 0 ? "directo" : d === 1 ? pick(["directo", "inverso"]) : pick(["cuadros", "inverso", "directo"]);
    if (modo === "cuadros") {
      const ctx = pick([
        {txt: "Una marca de refrescos patrocina un festival de música al aire libre y quiere estimar el número de asistentes para valorar el impacto de su patrocinio", sitio: "el recinto", u: "personas"},
        {txt: "El organizador de una feria comercial quiere estimar el número de visitantes que había a mediodía para fijar el precio de los espacios publicitarios", sitio: "la zona de exposición", u: "visitantes"},
      ]);
      const A = rr(8000, 40000, 500), a = pick([10, 16, 20, 25]), n = ri(20, 40), mb = red(a * (0.6 + 2 * R()), 1);
      const lam = mb / a, Vl = mb / (a * a * n), Bl = 2 * Math.sqrt(Vl), M = lam * A, BM = A * Bl;
      const intro = `${ctx.txt}. ${ctx.sitio[0].toUpperCase() + ctx.sitio.slice(1)} tiene ${miles(String(A))} m². A partir de una foto aérea se seleccionan al azar ${n} cuadrículas de ${a} m² y se cuentan las ${ctx.u} de cada una; en promedio hay m̄ = ${num(mb)} ${ctx.u} por cuadrícula.`;
      ap.push({w: 1, t: `Estime la densidad de ${ctx.u} por metro cuadrado con un intervalo de confianza.`,
        s: `λ̂ = m̄/a = ${num(mb)}/${a} = ${num(lam)} &nbsp;&nbsp; V̂(λ̂) = m̄/(a<sup>2</sup>n) = ${num(Vl)} &nbsp;&nbsp; B = ${num(Bl)}<br>Intervalo: ${S(`(${num(lam - Bl)} ; ${num(lam + Bl)})`)} ${ctx.u}/m²`});
      ap.push({w: 1, t: `Estime con un intervalo de confianza el número total de ${ctx.u}.`,
        s: `M̂ = λ̂A = ${num(lam)}·${A} = ${num(M)} &nbsp;&nbsp; V̂(M̂) = A<sup>2</sup>V̂(λ̂) = ${num(A * A * Vl)} &nbsp;&nbsp; B = ${num(BM)}<br>Intervalo: ${S(`(${num(M - BM)} ; ${num(M + BM)})`)}`});
      const B0 = red(BM * (0.5 + 0.2 * R()), -1) || 10, D = B0 * B0 / (4 * A * A), nn = lam / (a * D);
      ap.push({w: 1, t: `¿Cuántas cuadrículas habría que contar para estimar el número total de ${ctx.u} con un error inferior a ${num(B0)}?`,
        s: `D = B<sup>2</sup>/(4A<sup>2</sup>) = ${num(D)} &nbsp;&nbsp; n = λ/(aD) = ${num(lam)}/(${a}·${num(D)}) = ${num(nn)} → ${S(`n = ${techo(nn)}`)}`});
      return {tema: 6, intro, datos: "", ap};
    }
    const ctx = pick([
      {pob: "clientes distintos que visitan un centro comercial durante un mes", marca: "un cupón numerado de regalo", mar: "con cupón", quien: "clientes"},
      {pob: "personas distintas que pasan por el stand de una marca en una feria de varios días", marca: "una pulsera promocional", mar: "con pulsera", quien: "visitantes"},
      {pob: "usuarios distintos de un carril bici en el que una marca quiere poner publicidad", marca: "una pegatina reflectante con el logotipo de la marca", mar: "con pegatina", quien: "ciclistas"},
    ]);
    const t = rr(100, 500, 10), Nreal = t * (4 + 10 * R()), n = rr(80, 400, 10), s = Math.max(5, Math.round(n * t / Nreal));
    const Nh = n * t / s;
    if (modo === "directo") {
      const V = t * t * n * (n - s) / s ** 3, B = 2 * Math.sqrt(V);
      const intro = `Para estimar el número de ${ctx.pob}, se entrega ${ctx.marca} a ${t} ${ctx.quien} elegidos al azar. Días después se selecciona una muestra de ${n} ${ctx.quien}, de los cuales ${s} iban ${ctx.mar}.`;
      ap.push({w: d === 0 ? 2 : 1, t: `Estime el número de ${ctx.quien} y el límite para el error de estimación${d >= 1 ? " (dé el intervalo de confianza)" : ""}.`,
        s: `Muestreo directo: N̂ = nt/s = ${n}·${t}/${s} = ${S(num(Nh))}<br>V̂(N̂) = t<sup>2</sup>n(n − s)/s<sup>3</sup> = ${num(V)} &nbsp;&nbsp; B = 2√V̂ = ${S(num(B))}${d >= 1 ? `<br>Intervalo: ${S(`(${num(Nh - B)} ; ${num(Nh + B)})`)}` : ""}`});
      if (d >= 1) ap.push({w: 1, t: `¿Es insesgado el estimador utilizado? Aproxime su sesgo usando la estimación anterior.`,
        s: `No es insesgado: E(N̂) = N + N(N − t)/(nt). Sustituyendo N por N̂: sesgo ≈ N̂(N̂ − t)/(nt) = ${S(num(Nh * (Nh - t) / (n * t)))}. Para evitar el sesgo puede usarse el muestreo inverso.`});
      return {tema: 6, intro, datos: "", ap};
    }
    const V = t * t * n * (n - s) / (s * s * (s + 1)), B = 2 * Math.sqrt(V);
    const intro = `Para estimar el número de ${ctx.pob}, se entrega ${ctx.marca} a ${t} ${ctx.quien} elegidos al azar. Después se van seleccionando ${ctx.quien} al azar hasta encontrar ${s} ${ctx.mar}, para lo que fue necesario observar a ${n} ${ctx.quien}.`;
    ap.push({w: 1, t: `¿Qué tipo de muestreo se ha utilizado? Estime el número de ${ctx.quien} con un intervalo de confianza.`,
      s: `Muestreo inverso (se fija el número de marcados s). N̂ = nt/s = ${n}·${t}/${s} = ${num(Nh)} (insesgado)<br>V̂(N̂) = t<sup>2</sup>n(n − s)/[s<sup>2</sup>(s + 1)] = ${num(V)} &nbsp;&nbsp; B = ${num(B)}<br>Intervalo: ${S(`(${num(Nh - B)} ; ${num(Nh + B)})`)}`});
    if (d === 2) {
      const Vd = t * t * n * (n - s) / s ** 3;
      ap.push({w: 1, t: `Si los mismos datos se hubieran obtenido con muestreo directo (fijando de antemano los ${n} ${ctx.quien}), ¿cuál sería el límite para el error de estimación? Compare ambos procedimientos.`,
        s: `V̂(N̂) = t<sup>2</sup>n(n − s)/s<sup>3</sup> = ${num(Vd)} → B = ${S(num(2 * Math.sqrt(Vd)))}. El estimador es el mismo, pero en el muestreo directo es sesgado y su varianza estimada es algo mayor; el muestreo inverso da un estimador insesgado.`});
    }
    return {tema: 6, intro, datos: "", ap};
  }

  // ---------- temas 8, 9 y 10: decisión ----------
  const CTXD = [
    {intro: "Una empresa de alimentación va a lanzar una nueva bebida y debe elegir la estrategia de comunicación. Los beneficios (en miles de euros) dependen de la acogida del producto en el mercado:",
     alt: ["Campaña en televisión", "Campaña con influencers", "Promoción en el punto de venta"], est: ["Acogida baja", "Acogida media", "Acogida alta"]},
    {intro: "Una cadena de moda debe decidir cómo ampliar su negocio el próximo año. Los beneficios (en miles de euros) dependen de cómo evolucione el consumo:",
     alt: ["Abrir nuevas tiendas físicas", "Potenciar la tienda online", "Mantener la estructura actual"], est: ["Consumo débil", "Consumo estable", "Consumo fuerte"]},
    {intro: "Una agencia de viajes debe decidir qué tipo de paquetes promocionar la próxima temporada. Los beneficios (en miles de euros) dependen de la demanda turística:",
     alt: ["Paquetes de lujo", "Paquetes familiares", "Escapadas low cost"], est: ["Demanda baja", "Demanda normal", "Demanda alta"]},
    {intro: "Una empresa de software debe decidir el precio de lanzamiento de una aplicación de suscripción. Los beneficios (en miles de euros) dependen de la respuesta de los clientes:",
     alt: ["Precio alto", "Precio medio", "Precio bajo con anuncios"], est: ["Respuesta débil", "Respuesta moderada", "Respuesta fuerte"]},
  ];
  const CTX_IND = {intro: "Una empresa de distribución planifica su estrategia comercial para el próximo año. Los beneficios (en miles de euros) de cada estrategia dependen de la situación económica del país:",
    alt: ["Campaña nacional en televisión", "Campaña digital segmentada", "Promociones en el punto de venta"], est: ["Crecimiento débil", "Crecimiento moderado", "Crecimiento fuerte"]};
  function matrizDecision(c, d) {
    const nA = c.alt.length, nE = c.est.length;
    for (let it = 0; it < 500; it++) {
      // alternativa arriesgada, intermedia y conservadora
      const base = [[-rr(40, 120, 5), rr(20, 90, 5), rr(150, 300, 5)], [rr(-30, 30, 5), rr(50, 110, 5), rr(110, 190, 5)], [rr(30, 80, 5), rr(50, 100, 5), rr(70, 120, 5)]];
      const v = shuffle(base).slice(0, nA).map(f => f.slice(0, nE));
      // ninguna alternativa dominada
      const domina = (a, b) => a.every((x, j) => x >= b[j]) && a.some((x, j) => x > b[j]);
      if (v.some((a, i) => v.some((b, k) => k !== i && domina(b, a)))) continue;
      return v;
    }
    return [[-60, 60, 200], [10, 80, 140], [50, 70, 90]];
  }
  const tablaDec = (c, v) => tabla(["", ...c.est], v.map((f, i) => [c.alt[i], ...f.map(x => num(x))]));
  const unico = (vals, mejorMax = true) => { const m = mejorMax ? Math.max(...vals) : Math.min(...vals); return vals.filter(x => Math.abs(x - m) < 1e-9).length === 1; };
  const elige = (vals, mejorMax = true) => { const m = mejorMax ? Math.max(...vals) : Math.min(...vals); return vals.findIndex(x => Math.abs(x - m) < 1e-9); };
  function priorsDe(ind, nE) {
    if (ind) return {p: ind.cuentas.map(x => x / sum(ind.cuentas)), cuentas: ind.cuentas, ind};
    const total = pick([20, 25, 30, 40]), c = []; let resto = total;
    for (let j = 0; j < nE - 1; j++) { const x = ri(2, Math.max(2, Math.round(resto * 0.6))); c.push(Math.min(x, resto - (nE - 1 - j) * 2)); resto -= c[j]; }
    c.push(resto); return {p: c.map(x => x / total), cuentas: c};
  }
  const textoPriors = (c, P) => P.ind
    ? `Según Eurostat (indicador «PIB: crecimiento interanual», disponible en CCEEscopio), en los ${sum(P.cuentas)} trimestres entre ${P.ind.desde} y ${P.ind.hasta} el PIB de España creció menos de un 1 % en ${P.cuentas[0]} trimestres (crecimiento débil), entre un 1 % y un 3 % en ${P.cuentas[1]} (crecimiento moderado) y más de un 3 % en ${P.cuentas[2]} (crecimiento fuerte). Utilice estas frecuencias como probabilidades de cada situación.`
    : `En los últimos ${sum(P.cuentas)} años se ha observado: ${c.est.map((e, j) => `${e.toLowerCase()}, ${P.cuentas[j]} años`).join("; ")}. Utilice estas frecuencias como probabilidades de cada estado.`;
  function tema8(d, ind) {
    const c = ind ? CTX_IND : pick(CTXD);
    let v, alfa;
    for (let it = 0; it < 200; it++) {
      v = matrizDecision(c, d); alfa = pick([0.3, 0.35, 0.4, 0.6, 0.65, 0.7]);
      const lap = v.map(f => sum(f) / f.length), wal = v.map(f => Math.min(...f)), hur = v.map(f => alfa * Math.max(...f) + (1 - alfa) * Math.min(...f));
      const L = v.map((f, i) => f.map((x, j) => Math.max(...v.map(g => g[j])) - x)), sav = L.map(f => Math.max(...f));
      if (unico(lap) && unico(wal) && unico(hur) && unico(sav, false) && new Set([elige(lap), elige(wal), elige(hur), elige(sav, false)]).size >= 2) break;
    }
    const lap = v.map(f => sum(f) / f.length), wal = v.map(f => Math.min(...f)), opt = v.map(f => Math.max(...f)), hur = v.map(f => alfa * Math.max(...f) + (1 - alfa) * Math.min(...f));
    const L = v.map((f, i) => f.map((x, j) => Math.max(...v.map(g => g[j])) - x)), sav = L.map(f => Math.max(...f));
    const crit = {
      laplace: {t: "Según el criterio de Laplace, ¿qué alternativa elegiría la empresa? ¿Qué beneficio medio espera obtener?",
        s: `${tabla(["", "Media de la fila"], c.alt.map((a, i) => [a, num(lap[i])]))}Se elige ${S(c.alt[elige(lap)])}, con un beneficio medio de ${num(Math.max(...lap))}.`},
      wald: {t: "Si la dirección de la empresa fuera pesimista (criterio de Wald), ¿qué alternativa elegiría y qué resultado obtendría como mínimo?",
        s: `${tabla(["", "Mínimo de la fila"], c.alt.map((a, i) => [a, num(wal[i])]))}Maximin: se elige ${S(c.alt[elige(wal)])}, que garantiza al menos ${num(Math.max(...wal))}.`},
      optimista: {t: "Si la empresa estuviera dirigida por una persona optimista, ¿qué alternativa elegiría y cuál sería el resultado que piensa obtener?",
        s: `${tabla(["", "Máximo de la fila"], c.alt.map((a, i) => [a, num(opt[i])]))}Maximax: se elige ${S(c.alt[elige(opt)])}, con ${num(Math.max(...opt))}.`},
      hurwicz: {t: `De acuerdo con el criterio de Hurwicz, con un índice de optimismo α = ${num(alfa)}, ¿qué alternativa elegiría la empresa? Dé el valor esperado ponderado para dicha alternativa.`,
        s: `H(a<sub>i</sub>) = α·máx + (1 − α)·mín:<br>${c.alt.map((a, i) => `${a}: ${num(alfa)}·${num(opt[i])} + ${num(1 - alfa)}·${num(wal[i])} = ${num(hur[i])}`).join("<br>")}<br>Se elige ${S(c.alt[elige(hur)])}, con ${num(Math.max(...hur))}.`},
      savage: {t: "Utilizando el criterio de Savage, indique cuál sería la mejor alternativa. ¿En qué pérdida de oportunidad se incurriría, como máximo, con esa elección?",
        s: `Tabla de pérdidas de oportunidad (máximo de cada columna menos cada valor):${tabla(["", ...c.est, "Máximo"], c.alt.map((a, i) => [a, ...L[i].map(x => num(x)), num(sav[i])]))}Minimax: se elige ${S(c.alt[elige(sav, false)])}, con una pérdida de oportunidad máxima de ${num(Math.min(...sav))}.`},
    };
    const lista = d === 0 ? shuffle(["laplace", "wald", "optimista"]).slice(0, 2) : d === 1 ? ["hurwicz", "savage", pick(["laplace", "wald"])] : ["wald", "hurwicz", "savage", "laplace"];
    return {tema: 8, intro: c.intro, datos: tablaDec(c, v), ap: lista.map(k => ({w: k === "hurwicz" || k === "savage" ? 1.5 : 1, ...crit[k]}))};
  }
  function analisisRiesgo(c, v, p) {
    const vme = v.map(f => sum(f.map((x, j) => x * p[j])));
    const mx = c.est.map((e, j) => Math.max(...v.map(f => f[j])));
    const vmeip = sum(mx.map((x, j) => x * p[j]));
    const L = v.map(f => f.map((x, j) => mx[j] - x)), poe = L.map(f => sum(f.map((x, j) => x * p[j])));
    return {vme, mx, vmeip, L, poe, a: elige(vme), vip: vmeip - Math.max(...vme)};
  }
  function tema9(d, ind) {
    const c = ind ? CTX_IND : pick(CTXD);
    const P = priorsDe(ind, c.est.length);
    let v, A;
    for (let it = 0; it < 200; it++) { v = matrizDecision(c, d); A = analisisRiesgo(c, v, P.p); if (unico(A.vme) && A.vip > 0.5) break; }
    const pr = P.p.map(x => num(x));
    const tabV = tabla(["P(e<sub>j</sub>)", ...pr, "VME(a<sub>i</sub>)"], c.alt.map((a, i) => [a, ...v[i].map(x => num(x)), num(A.vme[i])]));
    const ap = [];
    ap.push({w: 1, indicador: !!P.ind, t: "Teniendo en cuenta dicha información, ¿qué alternativa debería elegir la empresa según el criterio del valor monetario esperado y cuál sería el beneficio esperado?",
      s: `P(e<sub>j</sub>): ${c.est.map((e, j) => `${e} = ${P.cuentas[j]}/${sum(P.cuentas)} = ${pr[j]}`).join("; ")}${tabV}Se elige ${S(c.alt[A.a])}, con un beneficio esperado de ${S(num(Math.max(...A.vme)))}.`});
    if (d >= 1) ap.push({w: 1, t: "¿Cuál es el precio máximo que la empresa estaría dispuesta a pagar por conocer de antemano qué estado se va a producir?",
      s: `VMEIP = Σ P(e<sub>j</sub>)·máx<sub>i</sub> v<sub>ij</sub> = ${c.est.map((e, j) => `${pr[j]}·${num(A.mx[j])}`).join(" + ")} = ${num(A.vmeip)}<br>VIP = VMEIP − VME(óptimo) = ${num(A.vmeip)} − ${num(Math.max(...A.vme))} = ${S(num(A.vip))}`});
    if (d === 2) ap.push({w: 1, t: "Construya la tabla de pérdidas de oportunidad y elija la mejor alternativa según el criterio de la pérdida de oportunidad esperada. Compruebe que la pérdida de oportunidad esperada mínima coincide con el valor de la información perfecta.",
      s: `${tabla(["P(e<sub>j</sub>)", ...pr, "POE(a<sub>i</sub>)"], c.alt.map((a, i) => [a, ...A.L[i].map(x => num(x)), num(A.poe[i])]))}Se elige ${S(c.alt[elige(A.poe, false)])} (la misma que con el VME). POE mínima = ${num(Math.min(...A.poe))} = VIP.`});
    return {tema: 9, intro: `${c.intro}`, datos: tablaDec(c, v) + `<p>${textoPriors(c, P)}</p>`, ap};
  }
  function tema10(d, ind) {
    const c = ind ? CTX_IND : pick(CTXD);
    const P = priorsDe(ind, c.est.length), nE = c.est.length;
    const firma = pick(ind ? ["un servicio de estudios económicos", "una consultora de coyuntura"] : ["una empresa de investigación de mercados", "una consultora de marketing"]);
    // verosimilitudes P(c_k | e_j): la previsión acertada en la diagonal
    let lik;
    for (let it = 0; it < 100; it++) {
      lik = c.est.map((e, j) => { const ac = rr(55, 90, 5) / 100; const resto = Math.round((1 - ac) * 100); const otros = c.est.map((_, k) => k).filter(k => k !== j); const x = rr(0, resto, 5); const f = new Array(nE).fill(0); f[j] = ac; f[otros[0]] = x / 100; f[otros[1]] = (resto - x) / 100; return f.map(z => red(z, 2)); });
      if (lik.every(f => Math.abs(sum(f) - 1) < 1e-9)) break;
    }
    let v, A;
    for (let it = 0; it < 200; it++) { v = matrizDecision(c, d); A = analisisRiesgo(c, v, P.p); if (unico(A.vme) && A.vip > 0.5) break; }
    const pc = c.est.map((_, k) => sum(P.p.map((p, j) => p * lik[j][k])));
    const post = c.est.map((_, k) => P.p.map((p, j) => pc[k] > 0 ? p * lik[j][k] / pc[k] : 0));
    const k0 = pick(c.est.map((_, k) => k).filter(k => pc[k] > 0.05));
    const lab = (k) => `«${c.est[k].toLowerCase()}»`;
    const txtLik = c.est.map((e, j) => { const otros = c.est.map((_, k) => k).filter(k => k !== j && lik[j][k] > 0); return `Cuando se ha dado ${e.toLowerCase()}, la probabilidad de que el informe acierte es del ${num(100 * lik[j][j], 0)} %${otros.length ? `, ${otros.map(k => `la probabilidad de que prevea ${lab(k)} es del ${num(100 * lik[j][k], 0)} %`).join(" y ")}` : ""}.`; }).join(" ");
    const tablaBayes = (k) => tabla(["e<sub>j</sub>", "P(e<sub>j</sub>)", `P(c<sub>${k + 1}</sub>|e<sub>j</sub>)`, `P(c<sub>${k + 1}</sub>|e<sub>j</sub>)·P(e<sub>j</sub>)`, `P(e<sub>j</sub>|c<sub>${k + 1}</sub>)`],
      [...c.est.map((e, j) => [e, num(P.p[j]), num(lik[j][k]), num(P.p[j] * lik[j][k]), num(post[k][j])]), ["Sumas", "1", "", `P(c<sub>${k + 1}</sub>) = ${num(pc[k])}`, "1"]]);
    const vmePost = (k) => v.map(f => sum(f.map((x, j) => x * post[k][j])));
    const ap = [];
    ap.push({w: 1, t: `Obtenga la probabilidad de que el informe prevea ${lab(k0)} y las probabilidades a posteriori de cada estado en ese caso.`,
      s: `Informe c<sub>${k0 + 1}</sub> = ${lab(k0)}:${tablaBayes(k0)}P(c<sub>${k0 + 1}</sub>) = ${S(num(pc[k0]))}; a posteriori: ${c.est.map((e, j) => `P(${e.toLowerCase()}|c<sub>${k0 + 1}</sub>) = ${S(num(post[k0][j]))}`).join("; ")}`});
    if (d >= 1) {
      const vk = vmePost(k0);
      ap.push({w: 1, t: `Si el informe prevé ${lab(k0)}, ¿qué alternativa debería elegir la empresa y cuál sería su beneficio esperado?`,
        s: `${tabla(["P(e<sub>j</sub>|c)", ...post[k0].map(x => num(x)), "VME(a<sub>i</sub>)|c"], c.alt.map((a, i) => [a, ...v[i].map(x => num(x)), num(vk[i])]))}Se elige ${S(c.alt[elige(vk)])}, con un beneficio esperado de ${S(num(Math.max(...vk)))}.`});
    }
    if (d === 2) {
      const mejores = c.est.map((_, k) => Math.max(...vmePost(k)));
      const vmeii = sum(mejores.map((m, k) => m * pc[k])), vii = vmeii - Math.max(...A.vme);
      ap.push({w: 1.5, t: `¿Cuál es el precio máximo que podría pedir ${firma} a la empresa por su informe?`,
        s: `Sin informe (probabilidades a priori): VME = ${num(Math.max(...A.vme))} (${c.alt[A.a]}).<br>${c.est.map((e, k) => `Si el informe prevé ${lab(k)}: P(c<sub>${k + 1}</sub>) = ${num(pc[k])}, mejor VME a posteriori = ${num(mejores[k])} (${c.alt[elige(vmePost(k))]})`).join("<br>")}<br>VMEII = Σ P(c<sub>k</sub>)·VME*(c<sub>k</sub>) = ${num(vmeii)}<br>VII = VMEII − VME = ${num(vmeii)} − ${num(Math.max(...A.vme))} = ${S(num(vii))}`});
    }
    return {tema: 10, intro: `${c.intro}`, datos: tablaDec(c, v) + `<p>${textoPriors(c, P)}</p><p>La empresa puede encargar un informe a ${firma}, que prevé cuál será el estado. Se sabe que: ${txtLik}</p>`, ap};
  }

  const GEN = {1: tema1, 2: tema2, 3: tema3, 4: tema4, 5: tema5, 6: tema6, 8: tema8, 9: tema9, 10: tema10};
  const TITULOS = {1: "Muestreo aleatorio simple", 2: "Muestreo aleatorio estratificado", 3: "Muestreo con información auxiliar", 4: "Muestreo sistemático", 5: "Muestreo por conglomerados",
    6: "Estimación del tamaño de la población", 8: "Decisión en ambiente de incertidumbre", 9: "Decisión en ambiente de riesgo", 10: "Decisión bayesiana"};
  // Temas que pueden incluir datos de los indicadores de CCEEscopio
  const ACEPTA_IND = {1: "compras", 2: "poblacion", 9: "pib", 10: "pib"};

  // Reparte la puntuación entre los apartados (múltiplos de 0,25 si es posible) y la ajusta para que sume exactamente el total
  function repartir(preguntas, total) {
    const aps = preguntas.flatMap(q => q.ap);
    const W = sum(aps.map(a => a.w));
    const paso = total * 4 >= aps.length ? 0.25 : total * 10 >= aps.length ? 0.1 : total * 20 >= aps.length ? 0.05 : 0.01;
    const U = Math.round(total / paso);
    const exact = aps.map(a => Math.max(1, U * a.w / W));
    let u = exact.map(Math.floor);
    let resto = U - sum(u);
    const orden = exact.map((x, i) => [x - Math.floor(x), i]).sort((a, b) => b[0] - a[0]);
    for (let k = 0; resto > 0; k = (k + 1) % orden.length) { u[orden[k][1]]++; resto--; }
    while (resto < 0) { const i = u.indexOf(Math.max(...u)); u[i]--; resto++; }
    aps.forEach((a, i) => a.pts = red(u[i] * paso, 2));
  }

  // Elige los temas: un problema por tema; si hay más de una pregunta, una de decisión (temas 8, 9 o 10) y el resto de los temas 1-6
  function elegirTemas(nPreg, hayInd) {
    const muestreo = shuffle([1, 2, 3, 4, 5, 6]);
    let temas;
    if (nPreg <= 1) temas = [muestreo[0]];
    else temas = [...muestreo.slice(0, nPreg - 1), pick([8, 9, 10])];
    // al menos una pregunta con datos de los indicadores de la web
    if (hayInd && !temas.some(t => ACEPTA_IND[t])) {
      const dec = temas.findIndex(t => t >= 8);
      if (dec >= 0) temas[dec] = pick([9, 10]);
      else temas[0] = pick([1, 2]);
    }
    return temas.sort((a, b) => a - b);
  }

  function generarExamen(op, indicadores) {
    // op: {convocatoria, dificultad, nPreg, puntos, euf: {dificultad, puntos} | null, semilla}
    const semilla = op.semilla ?? Math.floor(Math.random() * 1e9);
    R = rngDe(semilla);
    const d = DIF[op.dificultad] ?? 1;
    const nPreg = Math.max(1, Math.min(7, op.nPreg));
    const disp = (t) => indicadores && indicadores[ACEPTA_IND[t]];
    const temas = elegirTemas(nPreg, !!indicadores && Object.values(indicadores).some(Boolean));
    // el indicador se usa en una sola pregunta (la de decisión si puede, si no la de muestreo)
    let temaInd = [...temas].reverse().find(t => disp(t));
    const preguntas = temas.map(t => GEN[t](d, t === temaInd ? disp(t) : null));
    repartir(preguntas, op.puntos);
    let euf = null;
    if (op.euf) {
      const usados = new Set(temas.map(t => t >= 8 ? "dec" : t));
      let libres = [1, 2, 3, 4, 5, 6].filter(t => !usados.has(t));
      if (!libres.length) libres = [8, 9, 10].filter(t => !temas.includes(t));
      const t = pick(libres);
      const de = DIF[op.euf.dificultad] ?? 1;
      euf = GEN[t](de, temaInd ? null : disp(t));
      repartir([euf], op.euf.puntos);
    }
    return {semilla, temas, preguntas, euf, titulos: TITULOS};
  }

  // ---------- presentación en HTML ----------
  const ptsTxt = (p) => `(${num(p).replace(/^1$/, "1")} punto${p === 1 ? "" : "s"})`;
  function htmlPregunta(q, i, conSol) {
    const etiqueta = typeof i === "number" ? `${i}.` : i;
    let h = "";
    if (q.ap.length === 1) {
      h += `<div class="tc3-preg"><p><b>${etiqueta}</b> <b>${ptsTxt(q.ap[0].pts)}</b> ${q.intro}</p>${q.datos}<p>${q.ap[0].t}</p>`;
    } else {
      h += `<div class="tc3-preg"><p><b>${etiqueta}</b> ${q.intro}</p>${q.datos}<ol type="a" class="tc3-ap">${q.ap.map(a => `<li><b>${ptsTxt(a.pts)}</b> ${a.t}</li>`).join("")}</ol>`;
    }
    if (conSol) h += `<div class="tc3-sol"><p><b>Solución ${etiqueta.replace(/\.$/, "")}</b> <span class="tc3-tema">(tema ${q.tema}: ${TITULOS[q.tema]})</span></p>${q.ap.map((a, k) => `<p>${q.ap.length > 1 ? `<b>${"abcdefgh"[k]})</b> ` : ""}${a.s}</p>`).join("")}</div>`;
    return h + "</div>";
  }
  function htmlExamen(ex, op, conSol) {
    const conv = {Ordinaria: "ORDINARIO", Extraordinaria: "EXTRAORDINARIO", Especial: "DE LA CONVOCATORIA ESPECIAL"}[op.convocatoria] ?? "";
    const f = op.fecha instanceof Date ? op.fecha : new Date(op.fecha);
    const fecha = `${f.getDate()}/${f.getMonth() + 1}/${f.getFullYear()}`;
    let h = `<div class="tc3-examen"><p class="tc3-titulo">EXAMEN FINAL ${conv} DE TÉCNICAS CUANTITATIVAS III. ${fecha}.${conSol ? " SOLUCIONES." : ""}</p>
      <p class="tc3-sub">Grado en Marketing e Investigación de Mercados · Facultad de Ciencias Económicas y Empresariales · Universidad de Granada</p>
      <table class="tc3-nombre"><tr><td style="width:58%">APELLIDOS, NOMBRE:</td><td style="width:24%">D.N.I.:</td><td>GRUPO:</td></tr></table>
      <p>Resuelva todos los ejercicios con un nivel de confianza del 95 %, z = 2.</p>
      <p class="tc3-meta">Duración: ${op.tiempo} minutos · Puntuación máxima: ${num(op.puntos)} puntos.${ex.euf ? ` El estudiantado de <b>Evaluación Única Final</b> debe responder además a la pregunta ${ex.preguntas.length + 1} (${num(op.euf.puntos)} puntos; ${op.euf.tiempo} minutos adicionales).` : ""}</p>`;
    h += ex.preguntas.map((q, i) => htmlPregunta(q, i + 1, conSol)).join("");
    if (ex.euf) h += `<div class="tc3-euf"><p class="tc3-titulo-euf">PREGUNTA ADICIONAL. SOLO EVALUACIÓN ÚNICA FINAL (${fecha}) · ${num(op.euf.puntos)} puntos · ${op.euf.tiempo} minutos</p>${htmlPregunta(ex.euf, `${ex.preguntas.length + 1}.`, conSol)}</div>`;
    h += `<p class="tc3-pie">Código del examen: ${ex.semilla}. Generado con CCEEscopio (FCCEE, Universidad de Granada).</p></div>`;
    return h;
  }
  return {generarExamen, htmlExamen, num, TITULOS};
}
if (typeof module !== "undefined") module.exports = crearMotorTC3;
