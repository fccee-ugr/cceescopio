// Funciones estadísticas de CCEEscopio: distribuciones, regresión MCO y contrastes de supuestos.
// Lo incrusta tools/make_apps4.py en las páginas de calculadoras; también se puede probar con Node.
function crearEstadistica() {
  // ---------- distribuciones ----------
  const lgamma = (x) => {
    const c = [76.18009172947146, -86.50532032941677, 24.01409824083091, -1.231739572450155, 0.1208650973866179e-2, -0.5395239384953e-5];
    let y = x, tmp = x + 5.5; tmp -= (x + 0.5) * Math.log(tmp);
    let ser = 1.000000000190015; for (const ci of c) ser += ci / ++y;
    return -tmp + Math.log(2.5066282746310005 * ser / x);
  };
  const betacf = (a, b, x) => {
    const MAXIT = 300, EPS = 3e-16, FPMIN = 1e-300;
    let qab = a + b, qap = a + 1, qam = a - 1, c = 1, d = 1 - qab * x / qap;
    if (Math.abs(d) < FPMIN) d = FPMIN; d = 1 / d; let h = d;
    for (let m = 1; m <= MAXIT; m++) {
      const m2 = 2 * m;
      let aa = m * (b - m) * x / ((qam + m2) * (a + m2));
      d = 1 + aa * d; if (Math.abs(d) < FPMIN) d = FPMIN; c = 1 + aa / c; if (Math.abs(c) < FPMIN) c = FPMIN; d = 1 / d; h *= d * c;
      aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2));
      d = 1 + aa * d; if (Math.abs(d) < FPMIN) d = FPMIN; c = 1 + aa / c; if (Math.abs(c) < FPMIN) c = FPMIN; d = 1 / d;
      const del = d * c; h *= del; if (Math.abs(del - 1) < EPS) break;
    }
    return h;
  };
  // Beta incompleta regularizada I_x(a, b)
  const ibeta = (x, a, b) => {
    if (x <= 0) return 0; if (x >= 1) return 1;
    const bt = Math.exp(lgamma(a + b) - lgamma(a) - lgamma(b) + a * Math.log(x) + b * Math.log(1 - x));
    return x < (a + 1) / (a + b + 2) ? bt * betacf(a, b, x) / a : 1 - bt * betacf(b, a, 1 - x) / b;
  };
  // Gamma incompleta regularizada inferior P(a, x)
  const gammainc = (a, x) => {
    if (x <= 0) return 0;
    if (x < a + 1) { let ap = a, sum = 1 / a, del = sum; for (let n = 0; n < 500; n++) { ap++; del *= x / ap; sum += del; if (Math.abs(del) < Math.abs(sum) * 1e-15) break; } return sum * Math.exp(-x + a * Math.log(x) - lgamma(a)); }
    let b = x + 1 - a, c = 1e300, d = 1 / b, h = d;
    for (let i = 1; i < 500; i++) { const an = -i * (i - a); b += 2; d = an * d + b; if (Math.abs(d) < 1e-300) d = 1e-300; c = b + an / c; if (Math.abs(c) < 1e-300) c = 1e-300; d = 1 / d; const del = d * c; h *= del; if (Math.abs(del - 1) < 1e-15) break; }
    return 1 - Math.exp(-x + a * Math.log(x) - lgamma(a)) * h;
  };
  const pT = (t, df) => ibeta(df / (df + t * t), df / 2, 0.5);           // p-valor bilateral de la t de Student
  const pF = (f, d1, d2) => f <= 0 ? 1 : ibeta(d2 / (d2 + d1 * f), d2 / 2, d1 / 2); // p-valor de la F de Snedecor
  const pChi = (x, k) => x <= 0 ? 1 : 1 - gammainc(k / 2, x / 2);       // p-valor de la chi-cuadrado
  const normCdf = (z) => { const t = 1 / (1 + 0.2316419 * Math.abs(z)), d = 0.3989422804014327 * Math.exp(-z * z / 2);
    const p = d * t * (0.319381530 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429)))); return z > 0 ? 1 - p : p; };
  const normInv = (p) => { // Acklam
    const a = [-39.69683028665376, 220.9460984245205, -275.9285104469687, 138.3577518672690, -30.66479806614716, 2.506628277459239];
    const b = [-54.47609879822406, 161.5858368580409, -155.6989798598866, 66.80131188771972, -13.28068155288572];
    const c = [-7.784894002430293e-3, -0.3223964580411365, -2.400758277161838, -2.549732539343734, 4.374664141464968, 2.938163982698783];
    const d = [7.784695709041462e-3, 0.3224671290700398, 2.445134137142996, 3.754408661907416];
    const q = Math.min(p, 1 - p);
    let x;
    if (q < 0.02425) { const r = Math.sqrt(-2 * Math.log(q)); x = (((((c[0] * r + c[1]) * r + c[2]) * r + c[3]) * r + c[4]) * r + c[5]) / ((((d[0] * r + d[1]) * r + d[2]) * r + d[3]) * r + 1); x = p < 0.5 ? x : -x; }
    else { const r = (p - 0.5), s = r * r; x = (((((a[0] * s + a[1]) * s + a[2]) * s + a[3]) * s + a[4]) * s + a[5]) * r / (((((b[0] * s + b[1]) * s + b[2]) * s + b[3]) * s + b[4]) * s + 1); }
    return x;
  };
  const tInv = (p, df) => { // cuantil bilateral: t tal que P(|T| > t) = p
    let lo = 0, hi = 1000; for (let i = 0; i < 200; i++) { const m = (lo + hi) / 2; if (pT(m, df) > p) lo = m; else hi = m; } return (lo + hi) / 2;
  };

  // ---------- álgebra ----------
  const invertir = (A) => {
    const n = A.length, M = A.map((r, i) => [...r, ...Array.from({length: n}, (_, j) => +(i === j))]);
    for (let c = 0; c < n; c++) {
      let p = c; for (let r = c + 1; r < n; r++) if (Math.abs(M[r][c]) > Math.abs(M[p][c])) p = r;
      if (Math.abs(M[p][c]) < 1e-12) return null;
      [M[c], M[p]] = [M[p], M[c]];
      const piv = M[c][c]; for (let j = 0; j < 2 * n; j++) M[c][j] /= piv;
      for (let r = 0; r < n; r++) if (r !== c) { const f = M[r][c]; if (f) for (let j = 0; j < 2 * n; j++) M[r][j] -= f * M[c][j]; }
    }
    return M.map(r => r.slice(n));
  };
  const media = (a) => a.reduce((s, x) => s + x, 0) / a.length;

  // ---------- regresión MCO ----------
  // y: vector; X: matriz n×k SIN columna de unos (se añade la constante)
  function mco(y, X, conConstante = true) {
    const n = y.length, Z = X.map(r => conConstante ? [1, ...r] : r.slice()), k = Z[0].length;
    const ZtZ = Array.from({length: k}, (_, i) => Array.from({length: k}, (_, j) => Z.reduce((s, r) => s + r[i] * r[j], 0)));
    const inv = invertir(ZtZ); if (!inv) return null;
    const Zty = Array.from({length: k}, (_, i) => Z.reduce((s, r, t) => s + r[i] * y[t], 0));
    const b = inv.map(r => r.reduce((s, v, j) => s + v * Zty[j], 0));
    const ajuste = Z.map(r => r.reduce((s, v, j) => s + v * b[j], 0)), e = y.map((v, t) => v - ajuste[t]);
    const scr = e.reduce((s, v) => s + v * v, 0), ym = media(y), sct = y.reduce((s, v) => s + (v - ym) ** 2, 0);
    const gl = n - k, s2 = scr / gl, se = inv.map((r, i) => Math.sqrt(s2 * r[i]));
    const r2 = conConstante ? 1 - scr / sct : 1 - scr / y.reduce((s, v) => s + v * v, 0);
    const r2a = 1 - (1 - r2) * (n - 1) / gl, q = k - (conConstante ? 1 : 0);
    const F = q > 0 ? (r2 / q) / ((1 - r2) / gl) : NaN;
    const ll = -n / 2 * (Math.log(2 * Math.PI) + Math.log(scr / n) + 1);
    return {n, k, b, se, t: b.map((v, i) => v / se[i]), p: b.map((v, i) => pT(v / se[i], gl)), ajuste, e, scr, sct, s2, gl, r2, r2a, F, pFv: q > 0 ? pF(F, q, gl) : NaN,
      aic: -2 * ll + 2 * k, bic: -2 * ll + k * Math.log(n), inv, Z};
  }

  // ---------- contrastes de supuestos ----------
  function supuestos(y, X, m) {
    const n = m.n, e = m.e, out = {};
    // Normalidad: Jarque-Bera
    const em = media(e), m2 = media(e.map(v => (v - em) ** 2)), m3 = media(e.map(v => (v - em) ** 3)), m4 = media(e.map(v => (v - em) ** 4));
    const S = m3 / m2 ** 1.5, K = m4 / m2 ** 2, JB = n / 6 * (S * S + (K - 3) ** 2 / 4);
    out.normalidad = {nombre: "Normalidad de los residuos (Jarque-Bera)", est: JB, p: pChi(JB, 2), asimetria: S, curtosis: K};
    // Homocedasticidad: Breusch-Pagan (versión de Koenker, n·R²)
    const e2 = e.map(v => v * v), bp = mco(e2, X);
    if (bp) { const LM = n * bp.r2; out.homocedasticidad = {nombre: "Homocedasticidad (Breusch-Pagan)", est: LM, p: pChi(LM, X[0].length)}; }
    // Autocorrelación: Durbin-Watson y Breusch-Godfrey de orden 1
    let num = 0; for (let t = 1; t < n; t++) num += (e[t] - e[t - 1]) ** 2;
    const DW = num / m.scr;
    const Xbg = X.map((r, t) => [...r, t ? e[t - 1] : 0]), bg = mco(e, Xbg);
    out.autocorrelacion = {nombre: "Ausencia de autocorrelación (Breusch-Godfrey, orden 1)", est: bg ? n * bg.r2 : NaN, p: bg ? pChi(n * bg.r2, 1) : NaN, dw: DW};
    // Forma funcional: RESET de Ramsey (ŷ² y ŷ³)
    const yh = m.ajuste, sd = Math.sqrt(media(yh.map(v => (v - media(yh)) ** 2))) || 1, c = media(yh);
    const Xr = X.map((r, t) => [...r, ((yh[t] - c) / sd) ** 2, ((yh[t] - c) / sd) ** 3]), rr = mco(y, Xr);
    if (rr && rr.gl > 0) { const Fr = ((m.scr - rr.scr) / 2) / (rr.scr / rr.gl); out.linealidad = {nombre: "Forma funcional lineal (RESET de Ramsey)", est: Fr, p: pF(Fr, 2, rr.gl)}; }
    // Multicolinealidad: factores de inflación de la varianza
    if (X[0].length >= 2) out.vif = X[0].map((_, j) => { const xj = X.map(r => r[j]), otras = X.map(r => r.filter((_, i) => i !== j)), a = mco(xj, otras); return a ? 1 / (1 - a.r2) : NaN; });
    return out;
  }

  // ---------- estadística descriptiva ----------
  function cuantil(ordenados, q) { const h = (ordenados.length - 1) * q, l = Math.floor(h); return ordenados[l] + (h - l) * ((ordenados[l + 1] ?? ordenados[l]) - ordenados[l]); }
  function describir(v) {
    const a = v.filter(Number.isFinite), n = a.length; if (!n) return null;
    const o = a.slice().sort((x, y) => x - y), m = media(a);
    const s2 = n > 1 ? a.reduce((s, x) => s + (x - m) ** 2, 0) / (n - 1) : NaN, s = Math.sqrt(s2);
    const m2 = a.reduce((s, x) => s + (x - m) ** 2, 0) / n, m3 = a.reduce((s, x) => s + (x - m) ** 3, 0) / n, m4 = a.reduce((s, x) => s + (x - m) ** 4, 0) / n;
    return {n, media: m, mediana: cuantil(o, 0.5), sd: s, var: s2, cv: m !== 0 ? 100 * s / Math.abs(m) : NaN, min: o[0], max: o[n - 1], q1: cuantil(o, 0.25), q3: cuantil(o, 0.75),
      iqr: cuantil(o, 0.75) - cuantil(o, 0.25), asimetria: m3 / m2 ** 1.5, curtosis: m4 / m2 ** 2 - 3, suma: a.reduce((s, x) => s + x, 0)};
  }
  function correlacion(a, b) { const p = a.map((x, i) => [x, b[i]]).filter(([x, y]) => Number.isFinite(x) && Number.isFinite(y)); if (p.length < 3) return {r: NaN, n: p.length, p: NaN};
    const mx = media(p.map(q => q[0])), my = media(p.map(q => q[1]));
    const r = p.reduce((s, [x, y]) => s + (x - mx) * (y - my), 0) / Math.sqrt(p.reduce((s, [x]) => s + (x - mx) ** 2, 0) * p.reduce((s, [, y]) => s + (y - my) ** 2, 0));
    const t = r * Math.sqrt((p.length - 2) / (1 - r * r)); return {r, n: p.length, p: pT(t, p.length - 2)}; }

  return {lgamma, ibeta, gammainc, pT, pF, pChi, normCdf, normInv, tInv, invertir, mco, supuestos, describir, cuantil, correlacion, media};
}
if (typeof module !== "undefined") module.exports = crearEstadistica;
