/* CCEEscopio · Simulador «Gobernador del Banco Central»
   Modelo neokeynesiano simplificado de la zona euro (trimestral), con fines docentes. */
(function (raiz) {
  "use strict";
  const P = {obj: 2, rEstrella: 0.5, gPot: 1.2, persist: 0.72, sensTipo: 0.3, persInf: 0.55, kappa: 0.3, okun: 0.45, retardo: 0.5};

  // Expectativas de inflación: ancladas al 2 % según la credibilidad del banco central
  const expectativas = (pi, cred) => P.obj + (1 - cred) * (pi - P.obj);

  // Un trimestre: estado (inflación, brecha de producción, paro, tipo anterior...) + decisión de tipos + perturbaciones
  function paso(e, tipo, sh, ruido = [0, 0]) {
    const pie = expectativas(e.pi, e.cred);
    const rAhora = tipo - pie, rAntes = e.rReal ?? rAhora;
    const rEf = (1 - P.retardo) * rAhora + P.retardo * rAntes;            // la política monetaria actúa con retraso
    // las perturbaciones de oferta (energía) suben los precios y además restan actividad (estanflación)
    const gap = P.persist * e.gap - P.sensTipo * (rEf - P.rEstrella) + (sh.d || 0) - 0.25 * (sh.s || 0) + 0.15 * ruido[0];
    const pi = P.persInf * e.pi + (1 - P.persInf) * pie + P.kappa * gap + (sh.s || 0) + 0.12 * ruido[1];
    const u = e.uEst - P.okun * gap;
    const crecT = P.gPot / 4 + (gap - e.gap);                                // crecimiento trimestral aproximado (%)
    let cred = e.cred;
    const desv = Math.abs(pi - P.obj);
    if (desv < 0.75) cred += 0.05; else if (desv > 2 && tipo - e.pi < -2) cred -= 0.07; else if (desv > 1.5) cred -= 0.03;
    cred = Math.max(0.4, Math.min(1, cred));
    return {pi, gap, u, tipo, rReal: rAhora, cred, crecT, uEst: e.uEst, crecHist: [...(e.crecHist || []), crecT].slice(-4)};
  }
  // Crecimiento interanual aproximado: suma de los cuatro últimos trimestres
  const interanual = (e) => (e.crecHist || []).length ? e.crecHist.reduce((a, b) => a + b, 0) * 4 / e.crecHist.length : P.gPot;

  // Regla de Taylor (con suelo en −0,5 % y cambios de como mucho 0,75 puntos por trimestre)
  function taylor(e, anterior) {
    const t = P.rEstrella + e.pi + 0.5 * (e.pi - P.obj) + 0.5 * e.gap;
    const lim = Math.max(anterior - 0.75, Math.min(anterior + 0.75, t));
    return Math.max(-0.5, Math.round(lim * 4) / 4);
  }

  // Pérdida del trimestre: desviación de la inflación, brecha de producción, recesión y cambios bruscos de tipos
  function perdida(e, recesion, salto) {
    return (e.pi - P.obj) ** 2 + 0.6 * e.gap ** 2 + (recesion ? 6 : 0) + 0.4 * Math.max(0, Math.abs(salto) - 0.75) ** 2;
  }
  // Puntuación relativa: seguir la regla de Taylor con las mismas perturbaciones da 80 puntos; hacerlo mejor, más
  const puntuacion = (perdidaTotal, perdidaRef) => Math.max(0, Math.min(100, Math.round(80 * Math.exp(-1.2 * (perdidaTotal / Math.max(perdidaRef, 0.5) - 1)))));

  function jugar(inicial, decisiones, shocks, ruidos) {
    let e = inicial, ant = inicial.tipo, tray = [], total = 0, crecAnt = null;
    decisiones.forEach((tipo, k) => {
      const n = paso(e, tipo, shocks[k] || {}, ruidos ? ruidos[k] : [0, 0]);
      const recesion = n.crecT < 0 && crecAnt != null && crecAnt < 0;
      total += perdida(n, recesion, tipo - ant);
      tray.push({...n, recesion, interanual: interanual(n)});
      crecAnt = n.crecT; ant = tipo; e = n;
    });
    return {tray, total};
  }
  function jugarTaylor(inicial, shocks, ruidos) {
    let e = inicial, ant = inicial.tipo; const dec = [];
    for (let k = 0; k < shocks.length; k++) {
      const t = taylor(e, ant); dec.push(t);
      e = paso(e, t, shocks[k] || {}, ruidos ? ruidos[k] : [0, 0]); ant = t;
    }
    return {...jugar(inicial, dec, shocks, ruidos), decisiones: dec};
  }

  // Partida completa: trayectoria del jugador, de la regla de Taylor y puntuación
  function evaluar(inicial, decisiones, shocks, ruidos) {
    const tu = jugar(inicial, decisiones, shocks, ruidos), ref = jugarTaylor(inicial, shocks, ruidos);
    return {tu, taylor: ref, puntos: puntuacion(tu.total, ref.total)};
  }

  const BC = {evaluar, P, paso, taylor, perdida, puntuacion, jugar, jugarTaylor, interanual, expectativas};
  if (typeof module !== "undefined") module.exports = BC; else raiz.SimBC = BC;
})(typeof window !== "undefined" ? window : globalThis);
