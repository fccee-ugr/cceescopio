/* CCEEscopio · Simulador «Gestiona tu destino turístico»
   Modelo anual simplificado de un destino urbano ficticio de tamaño medio (inspirado en ciudades como Granada), con fines docentes. */
(function (raiz) {
  "use strict";
  const BASE = {residentes: 230000, viajeros: 2.0e6, estancia: 2.0, precioRef: 95, plazasHotel: 10000, plazasVut: 7000, gastoDiario: 78, empleoPorMillon: 18};
  const POLITICAS = {
    libre: {n: "Libre: sin límites a las viviendas turísticas", crec: 0.10, alivio: 0},
    licencias: {n: "Licencias limitadas por barrios", crec: 0.03, alivio: 0.005},
    moratoria: {n: "Moratoria y reconversión en alquiler residencial", crec: -0.08, alivio: 0.015},
  };
  const EVENTOS = [
    {t: "✈️ Una aerolínea abre nuevas rutas internacionales", dem: 0.10, x: "Llegan más turistas extranjeros."},
    {t: "🎤 La ciudad acoge un gran congreso internacional", dem: 0.05, x: "Más turismo de negocios, que gasta más."},
    {t: "🥵 Un verano de calor extremo", dem: -0.06, x: "Muchos turistas aplazan o cambian de destino."},
    {t: "📉 Crisis económica en los principales mercados emisores", dem: -0.12, x: "Los turistas viajan menos y gastan menos."},
    {t: "🎬 La ciudad aparece en una serie de televisión de éxito", dem: 0.15, x: "Efecto llamada: más visitantes… y más presión sobre el centro."},
    {t: "🚆 Huelga en el transporte y retrasos en el aeropuerto", dem: -0.05, x: "Algunas reservas se cancelan."},
    {t: "🌿 Un premio europeo de turismo sostenible", dem: 0.04, rep: 0.04, x: "Mejora la imagen del destino (más si eres sostenible)."},
    {t: "🌤️ Un año sin sobresaltos", dem: 0, x: "La demanda depende solo de tus decisiones."},
  ];

  function inicial() {
    return {ano: 0, plazasHotel: BASE.plazasHotel, plazasVut: BASE.plazasVut, rep: 1, satisf: 62, sost: 50, alquiler: 100, nuevas: 0,
      noches: BASE.viajeros * BASE.estancia, empleo: null, empleoRef: null, ingresosAloj: null};
  }

  // Un año del destino: e = estado, d = decisiones, ev = evento
  function ano(e, d, ev) {
    const pol = POLITICAS[d.politica];
    const plazasHotel = e.plazasHotel + e.nuevas;                       // las plazas autorizadas el año anterior ya están abiertas
    const plazasVut = Math.max(0, e.plazasVut * (1 + pol.crec));
    const precioPlaza = d.precio / 2;                                     // precio de la habitación doble → por persona
    const demanda = BASE.viajeros * Math.pow(d.precio / BASE.precioRef, -1.1) * (1 + 0.07 * Math.log(1 + 2 * d.promo)) * e.rep *
                    (1 + (ev.dem || 0)) * (1 - 0.025 * d.tasa);
    const nochesDem = demanda * BASE.estancia;
    const cuotaHotel = Math.max(0.4, Math.min(0.85, 0.62 * Math.pow(BASE.precioRef / d.precio, 0.5)));
    const capHotel = plazasHotel * 365 * 0.92, capVut = plazasVut * 365 * 0.75;
    const nHotel = Math.min(nochesDem * cuotaHotel, capHotel);
    const nVut = Math.min(nochesDem - nHotel, capVut);
    const noches = nHotel + nVut, perdidas = Math.max(0, nochesDem - noches);
    const ocupacion = nHotel / (plazasHotel * 365);
    const ingresosAloj = nHotel * precioPlaza + nVut * precioPlaza * 0.8;
    const gasto = ingresosAloj + noches * BASE.gastoDiario;
    const empleo = gasto / 1e6 * BASE.empleoPorMillon;
    const recaudacion = d.tasa * noches;
    const fondoVivienda = recaudacion * d.vivienda / 100, fondoServicios = recaudacion - fondoVivienda;
    const presion = noches / 365 / BASE.residentes * 100;                   // turistas por cada 100 residentes, de media diaria
    const presionRef = BASE.viajeros * BASE.estancia / 365 / BASE.residentes * 100;
    // alquiler: inflación general + viviendas turísticas + presión turística − vivienda asequible
    const varAlq = 0.025 + 0.35 * (plazasVut / e.plazasVut - 1) + 0.04 * (presion / presionRef - 1) - pol.alivio - fondoVivienda / 1e6 * 0.002;
    const alquiler = e.alquiler * (1 + varAlq);
    const empRef = e.empleoRef ?? empleo;
    const satisf = Math.max(0, Math.min(100, e.satisf + 0.5 - 14 * Math.max(0, presion / presionRef - 1.05) - 60 * Math.max(0, varAlq - 0.03)
      + 0.35 * fondoServicios / 1e6 + 0.5 * fondoVivienda / 1e6 + (e.empleo ? 25 * (empleo / e.empleo - 1) : 0)
      - 18 * Math.max(0, 1 - empleo / empRef) - (ocupacion > 0.88 ? 3 : 0)));
    const ratio = noches / (BASE.viajeros * BASE.estancia);
    const sost = Math.max(0, Math.min(100, e.sost - 1.5 - (ratio > 1 ? 15 * (ratio - 1) : -5 * (1 - ratio)) + 0.5 * fondoServicios / 1e6 + (d.politica === "libre" ? -2 : 1)));
    const rep = Math.max(0.75, Math.min(1.25, e.rep + 0.04 * (sost - 50) / 50 + 0.03 * (satisf - 50) / 50 - (ocupacion > 0.9 ? 0.03 : 0) + (ev.rep || 0) * (sost >= 55 ? 1 : 0.3)));
    return {ano: e.ano + 1, empleoRef: empRef, plazasHotel, plazasVut, nuevas: d.nuevas, rep, satisf, sost, alquiler, varAlq,
      viajeros: noches / BASE.estancia, noches, perdidas, ocupacion, ingresosAloj, gasto, empleo, recaudacion, presion, precio: d.precio};
  }

  // Puntuación final (0-100): empleo e ingresos frente al punto de partida, residentes, sostenibilidad y vivienda
  const DEF = {precio: 95, promo: 1, tasa: 0, politica: "libre", nuevas: 0, vivienda: 0};
  let _eb = null;
  const empleoBase = () => _eb ?? (_eb = ano(inicial(), DEF, {dem: 0}).empleo);
  function puntuar(h) {
    const u = h.at(-1);
    const pEmpleo = Math.max(0, Math.min(25, 12.5 + 60 * (u.empleo / empleoBase() - 1)));
    const pResid = Math.max(0, Math.min(25, u.satisf / 4));
    const pSost = Math.max(0, Math.min(25, u.sost / 4));
    const pViv = Math.max(0, Math.min(25, 25 - 1.2 * Math.max(0, (u.alquiler - 100) - 5 * 2.5)));
    // media geométrica: descuidar por completo un objetivo hunde la nota
    const total = Math.round(4 * Math.pow([pEmpleo, pResid, pSost, pViv].map(v => Math.max(1, v)).reduce((a, b) => a * b, 1), 1 / 4));
    return {total, pEmpleo, pResid, pSost, pViv};
  }

  const T = {BASE, POLITICAS, EVENTOS, DEF, inicial, ano, puntuar, empleoBase};
  if (typeof module !== "undefined") module.exports = T; else raiz.SimTurismo = T;
})(typeof window !== "undefined" ? window : globalThis);
