// Cálculo del tamaño muestral para CCEEscopio (tamano-muestral.qmd).
// Usa las distribuciones de tools/estadistica.js (EST). Lo incrusta tools/make_muestra.py; también se puede probar con Node:
//   node tools/muestra.js
function crearMuestra(EST) {
  const z = (p) => EST.normInv(p);
  const zAlfa = (alfa, colas) => z(1 - alfa / colas);
  const sube = (x) => Math.ceil(x - 1e-9);
  // Corrección por población finita (Cochran, 1977): n = n0 / (1 + (n0 - 1) / N)
  const finita = (n0, N) => (N && N > 0) ? n0 / (1 + (n0 - 1) / N) : n0;

  // ---------- distribuciones no centrales ----------
  const pois = (j, m) => Math.exp(-m + j * Math.log(m) - EST.lgamma(j + 1));
  const sumaPois = (m, f) => { // suma de Poisson(m) · f(j) alrededor de la moda
    if (m < 1e-12) return f(0);
    const j0 = Math.floor(m); let s = 0;
    for (let j = j0; j < j0 + 5000; j++) { const w = pois(j, m), t = w * f(j); s += t; if (w < 1e-14 && j > m + 10) break; }
    for (let j = j0 - 1; j >= 0; j--) { const w = pois(j, m); s += w * f(j); if (w < 1e-14) break; }
    return s;
  };
  const cdfF = (x, d1, d2) => x <= 0 ? 0 : 1 - EST.pF(x, d1, d2);
  const cdfFnc = (x, d1, d2, lam) => x <= 0 ? 0 : sumaPois(lam / 2, j => EST.ibeta(d1 * x / (d1 * x + d2), d1 / 2 + j, d2 / 2));
  const cdfChi = (x, k) => x <= 0 ? 0 : EST.gammainc(k / 2, x / 2);
  const cdfChinc = (x, k, lam) => x <= 0 ? 0 : sumaPois(lam / 2, j => EST.gammainc(k / 2 + j, x / 2));
  const cuantil = (cdf, p) => { let lo = 0, hi = 1; while (cdf(hi) < p && hi < 1e7) hi *= 2; for (let i = 0; i < 200; i++) { const m = (lo + hi) / 2; if (cdf(m) < p) lo = m; else hi = m; } return (lo + hi) / 2; };
  // Menor n entero (≥ nMin) con potencia(n) ≥ objetivo
  const menorN = (pot, objetivo, nMin) => {
    let lo = nMin, hi = nMin; while (pot(hi) < objetivo) { lo = hi; hi = hi * 2; if (hi > 1e7) return NaN; }
    while (hi - lo > 1) { const m = Math.floor((lo + hi) / 2); if (pot(m) >= objetivo) hi = m; else lo = m; }
    return pot(lo) >= objetivo ? lo : hi;
  };

  // ---------- escenarios ----------
  // Cada función devuelve {n0 (sin redondear), n (por grupo si procede), grupos, pasos: [[etiqueta, valor]], potencia?}
  const E = {};
  // 1. Proporción con error de muestreo absoluto (Cochran, 1977)
  E.propAbs = ({conf, p, e, N}) => { const za = zAlfa(1 - conf, 2), n0 = za * za * p * (1 - p) / (e * e), n1 = finita(n0, N);
    return {n0, nf: n1, n: sube(n1), grupos: 1, pasos: [["z", za], ["n₀ = z²·p·(1 − p) / e²", n0], ...(N ? [["n = n₀ / (1 + (n₀ − 1)/N)", n1]] : [])]}; };
  // 2. Proporción con error relativo: e = er · p
  E.propRel = ({conf, p, er, N}) => { const r = E.propAbs({conf, p, e: er * p, N}); r.pasos.unshift(["Error absoluto e = er · p", er * p]); return r; };
  // 3. Media con error absoluto, desviación típica σ
  E.mediaAbs = ({conf, sigma, e, N}) => { const za = zAlfa(1 - conf, 2), n0 = za * za * sigma * sigma / (e * e), n1 = finita(n0, N);
    return {n0, nf: n1, n: sube(n1), grupos: 1, pasos: [["z", za], ["n₀ = z²·σ² / e²", n0], ...(N ? [["n = n₀ / (1 + (n₀ − 1)/N)", n1]] : [])]}; };
  // 4. Media con error relativo: coeficiente de variación CV y error relativo er
  E.mediaRel = ({conf, cv, er, N}) => { const za = zAlfa(1 - conf, 2), n0 = za * za * cv * cv / (er * er), n1 = finita(n0, N);
    return {n0, nf: n1, n: sube(n1), grupos: 1, pasos: [["z", za], ["n₀ = z²·CV² / er²", n0], ...(N ? [["n = n₀ / (1 + (n₀ − 1)/N)", n1]] : [])]}; };
  // 5. Contraste sobre una proporción (aproximación normal)
  E.test1p = ({alfa, colas, pot, p0, p1}) => { const za = zAlfa(alfa, colas), zb = z(pot), num = za * Math.sqrt(p0 * (1 - p0)) + zb * Math.sqrt(p1 * (1 - p1)), n0 = num * num / ((p1 - p0) ** 2);
    return {n0, nf: n0, n: sube(n0), grupos: 1, pasos: [["z₁₋α" + (colas === 2 ? "/2" : ""), za], ["z₁₋β", zb], ["n = [z₁₋α·√(p₀q₀) + z₁₋β·√(p₁q₁)]² / (p₁ − p₀)²", n0]]}; };
  // 6. Contraste sobre una media: tamaño del efecto d = (μ₁ − μ₀)/σ, con corrección iterativa por la t de Student
  E.test1m = ({alfa, colas, pot, d}) => { const za = zAlfa(alfa, colas), zb = z(pot), nz = ((za + zb) / d) ** 2;
    const potT = (n) => { const gl = n - 1, tc = EST.tInv(alfa * (2 / colas), gl), del = d * Math.sqrt(n); return 1 - cdfT(tc, gl, del) + (colas === 2 ? cdfT(-tc, gl, del) : 0); };
    const n = menorN(potT, pot, 2);
    return {n0: nz, nf: n, n, grupos: 1, potencia: potT(n), pasos: [["z₁₋α" + (colas === 2 ? "/2" : ""), za], ["z₁₋β", zb], ["Aproximación normal: n = (z₁₋α + z₁₋β)² / d²", nz], ["Con la t de Student (t no central)", n]]}; };
  // 7. Comparación de dos proporciones (Fleiss, Levin y Paik, 2003), con corrección de continuidad opcional
  E.test2p = ({alfa, colas, pot, p1, p2, cc, k = 1}) => { const za = zAlfa(alfa, colas), zb = z(pot), pm = (p1 + k * p2) / (1 + k), d = Math.abs(p1 - p2);
    const num = za * Math.sqrt((1 + 1 / k) * pm * (1 - pm)) + zb * Math.sqrt(p1 * (1 - p1) + p2 * (1 - p2) / k), n0 = num * num / (d * d);
    const ncc = cc ? n0 / 4 * (1 + Math.sqrt(1 + 2 * (1 + 1 / k) / (n0 * d))) ** 2 : n0;
    return {n0, nf: ncc, n: sube(ncc), n2: sube(k * ncc), grupos: 2, pasos: [["z₁₋α" + (colas === 2 ? "/2" : ""), za], ["z₁₋β", zb], ["p̄ (proporción media)", pm], ["n₁ sin corrección", n0], ...(cc ? [["n₁ con corrección de continuidad", ncc]] : [])]}; };
  // 8. Comparación de dos medias (grupos independientes), d de Cohen, con la t de Student
  E.test2m = ({alfa, colas, pot, d, k = 1}) => { const za = zAlfa(alfa, colas), zb = z(pot), nz = (1 + 1 / k) * ((za + zb) / d) ** 2;
    const potT = (n) => { const n2 = Math.ceil(k * n), gl = n + n2 - 2, tc = EST.tInv(alfa * (2 / colas), gl), del = d / Math.sqrt(1 / n + 1 / n2); return 1 - cdfT(tc, gl, del) + (colas === 2 ? cdfT(-tc, gl, del) : 0); };
    const n = menorN(potT, pot, 2);
    return {n0: nz, nf: n, n, n2: Math.ceil(k * n), grupos: 2, potencia: potT(n), pasos: [["z₁₋α" + (colas === 2 ? "/2" : ""), za], ["z₁₋β", zb], ["Aproximación normal: n₁ = (1 + 1/k)(z₁₋α + z₁₋β)² / d²", nz], ["Con la t de Student (t no central)", n]]}; };
  // 9. Coeficiente de correlación de Pearson (transformación z de Fisher)
  E.correl = ({alfa, colas, pot, r}) => { const za = zAlfa(alfa, colas), zb = z(pot), C = 0.5 * Math.log((1 + r) / (1 - r)), n0 = ((za + zb) / C) ** 2 + 3;
    return {n0, nf: n0, n: sube(n0), grupos: 1, pasos: [["z₁₋α" + (colas === 2 ? "/2" : ""), za], ["z₁₋β", zb], ["C = ½·ln[(1 + r)/(1 − r)]", C], ["n = [(z₁₋α + z₁₋β)/C]² + 3", n0]]}; };
  // 10. Regresión lineal múltiple: contraste F de significación conjunta, f² de Cohen (λ = f²·n)
  E.regresion = ({alfa, pot, f2, k}) => { const potF = (n) => { const d2 = n - k - 1; if (d2 < 1) return 0; const fc = cuantil(x => cdfF(x, k, d2), 1 - alfa); return 1 - cdfFnc(fc, k, d2, f2 * n); };
    const n = menorN(potF, pot, k + 2);
    return {n0: n, nf: n, n, grupos: 1, potencia: potF(n), pasos: [["λ = f²·n (parámetro de no centralidad)", f2 * n], ["Grados de libertad", `${k} y ${n - k - 1}`], ["Regla de Green (1991), contraste global: 50 + 8k", 50 + 8 * k], ["Regla de Green (1991), coeficientes individuales: 104 + k", 104 + k]]}; };
  // 11. Contraste chi-cuadrado (bondad del ajuste o independencia), w de Cohen (λ = w²·n)
  E.chi = ({alfa, pot, w, gl}) => { const cc = cuantil(x => cdfChi(x, gl), 1 - alfa), potC = (n) => 1 - cdfChinc(cc, gl, w * w * n);
    const n = menorN(potC, pot, 2);
    return {n0: n, nf: n, n, grupos: 1, potencia: potC(n), pasos: [["Valor crítico χ²", cc], ["λ = w²·n (parámetro de no centralidad)", w * w * n]]}; };

  // t no central: P(T ≤ x) con gl grados de libertad y no centralidad del (integración numérica sobre la chi)
  function cdfT(x, gl, del) {
    // T = (Z + del) / sqrt(V/gl): P(T ≤ x) = E_V[Φ(x·sqrt(V/gl) − del)]; se integra en V con Simpson en la escala de sqrt(V)
    const a = 0, b = Math.sqrt(gl) + 12, m = 400, h = (b - a) / m; let s = 0;
    const dens = (u) => { if (u <= 0) return 0; const v = u * u; return 2 * u * Math.exp((gl / 2 - 1) * Math.log(v) - v / 2 - (gl / 2) * Math.log(2) - EST.lgamma(gl / 2)); };
    for (let i = 0; i <= m; i++) { const u = a + i * h, w = i === 0 || i === m ? 1 : i % 2 ? 4 : 2; s += w * dens(u) * EST.normCdf(x * u / Math.sqrt(gl) - del); }
    return s * h / 3;
  }

  // Ajustes finales: efecto de diseño (Kish, 1965) y tasa de respuesta esperada
  const ajustar = (n, deff = 1, resp = 1) => { const nd = n * deff, nr = nd / resp; return {nd, nr, n: sube(nr)}; };
  // Afijación proporcional por estratos: n_h = n · N_h / N (redondeo por el método del mayor resto)
  const afijacion = (n, estratos) => { const N = estratos.reduce((a, e) => a + e.N, 0); const q = estratos.map(e => n * e.N / N); const b = q.map(Math.floor);
    let resto = n - b.reduce((a, x) => a + x, 0); q.map((x, i) => [x - b[i], i]).sort((u, v) => v[0] - u[0]).forEach(([, i]) => { if (resto > 0) { b[i]++; resto--; } });
    return estratos.map((e, i) => ({...e, n: b[i], peso: e.N / N})); };
  return {E, finita, ajustar, afijacion, cdfT, cdfFnc, cdfChinc, zAlfa};
}
if (typeof module !== "undefined") {
  const EST = new Function(require("fs").readFileSync(__dirname + "/estadistica.js", "utf8").replace(/if \(typeof module[\s\S]*$/, "") + "; return crearEstadistica();")();
  const M = crearMuestra(EST);
  console.log("Proporción, p = 0,5, e = 0,05, 95 %:", M.E.propAbs({conf: .95, p: .5, e: .05}).n, "(esperado 385)");
  console.log("  … con N = 1.000:", M.E.propAbs({conf: .95, p: .5, e: .05, N: 1000}).n, "(esperado 278)");
  console.log("Media, σ = 10, e = 2, 95 %:", M.E.mediaAbs({conf: .95, sigma: 10, e: 2}).n, "(esperado 97)");
  console.log("Una media, d = 0,5, bilateral, 80 %:", M.E.test1m({alfa: .05, colas: 2, pot: .8, d: .5}).n, "(G*Power: 34)");
  console.log("Dos medias, d = 0,5, bilateral, 80 %:", M.E.test2m({alfa: .05, colas: 2, pot: .8, d: .5}).n, "por grupo (G*Power: 64)");
  console.log("Dos proporciones 0,5 frente a 0,4, bilateral, 80 %:", M.E.test2p({alfa: .05, colas: 2, pot: .8, p1: .5, p2: .4}).n, "(Fleiss sin corrección: 388)");
  console.log("  … con corrección de continuidad:", M.E.test2p({alfa: .05, colas: 2, pot: .8, p1: .5, p2: .4, cc: true}).n, "(Fleiss: 408)");
  console.log("Correlación r = 0,3, bilateral, 80 %:", M.E.correl({alfa: .05, colas: 2, pot: .8, r: .3}).n, "(85)");
  console.log("Regresión f² = 0,15, k = 5, 80 %:", M.E.regresion({alfa: .05, pot: .8, f2: .15, k: 5}).n, "(G*Power: 92)");
  console.log("Chi-cuadrado w = 0,3, gl = 1, 80 %:", M.E.chi({alfa: .05, pot: .8, w: .3, gl: 1}).n, "(G*Power: 88)");
  console.log("Una proporción 0,5 frente a 0,6, bilateral, 80 %:", M.E.test1p({alfa: .05, colas: 2, pot: .8, p0: .5, p1: .6}).n, "(≈ 194)");
}
