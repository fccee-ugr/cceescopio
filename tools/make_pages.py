"""Genera las páginas de indicadores de CCEEscopio a partir de una única lista de definiciones.
Cada indicador se descarga en directo de la API de Eurostat. Para añadir uno nuevo, basta con
añadir un diccionario a la categoría correspondiente y volver a ejecutar: python3 tools/make_pages.py
"""
import json

def HICP(c):
    # Desde enero de 2026 Eurostat publica el IPCA con la clasificación ECOICOP ver. 2 (prc_hicp_minr).
    # Alternativas por si cambia el código del total y tabla anterior (prc_hicp_manr, hasta diciembre de 2025).
    alt = [] if c == "CP00" else [dict(code="prc_hicp_minr", query=f"&unit=RCH_A&coicop18={c}")]
    if c == "CP00": alt.append(dict(code="prc_hicp_minr", query="&unit=RCH_A&coicop18=CP00"))
    alt.append(dict(code="prc_hicp_manr", query=f"&coicop={c}"))
    return alt

import re, unicodedata
def slug(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:60]

def I(nombre, code, query, unidad, frecuencia, descripcion, **kw):
    d = dict(id=slug(nombre), nombre=nombre, code=code, query=query, unidad=unidad, frecuencia=frecuencia, descripcion=descripcion)
    d.update(kw)
    return d

CATS = {
"precios": dict(
  titulo="Precios e inflación",
  subtitulo="Inflación general y por componentes, y precios de la vivienda",
  intro="La inflación mide el ritmo al que suben los precios y es una variable central para la política monetaria del Banco Central Europeo, la negociación salarial y la evaluación del poder adquisitivo de los hogares. Se utiliza el **Índice de Precios de Consumo Armonizado (IPCA)**, comparable entre países de la UE; en España, el INE publica además el IPC nacional.",
  docencia=["Macroeconomía y política monetaria: relación entre inflación y tipos de interés (véase la rentabilidad del bono en *Sector público y mercados*).", "Economía española: episodio inflacionista de 2021-2023 y papel de la energía y los alimentos.", "Métodos Cuantitativos: números índice, tasas de variación interanual y efecto escalón."],
  ind=[
    I("IPCA: inflación general (tasa anual)", "prc_hicp_minr", "&unit=RCH_A&coicop18=TOTAL", "%", "Mensual", "Tasa de variación anual del Índice de Precios de Consumo Armonizado (todos los bienes y servicios).", cero=True, desde=2005, alt=HICP("CP00")),
    I("IPCA: alimentos y bebidas no alcohólicas (tasa anual)", "prc_hicp_minr", "&unit=RCH_A&coicop18=CP01", "%", "Mensual", "Tasa de variación anual de los precios de los alimentos y bebidas no alcohólicas.", cero=True, desde=2005, alt=HICP("CP01")),
    I("IPCA: energía (tasa anual)", "prc_hicp_minr", "&unit=RCH_A&coicop18=NRG", "%", "Mensual", "Tasa de variación anual de los precios de la energía (electricidad, gas, combustibles).", cero=True, desde=2005, alt=HICP("NRG")),
    I("IPCA: servicios (tasa anual)", "prc_hicp_minr", "&unit=RCH_A&coicop18=SERV", "%", "Mensual", "Tasa de variación anual de los precios de los servicios.", cero=True, desde=2005, alt=HICP("SERV")),
    I("Precio de la vivienda (tasa anual)", "prc_hpi_q", "&purchase=TOTAL&unit=RCH_A", "%", "Trimestral", "Tasa de variación anual del índice de precios de la vivienda (nueva y de segunda mano).", cero=True, desde=2008),
    I("IPCA: inflación subyacente (sin energía ni alimentos)", "prc_hicp_minr", "&unit=RCH_A&coicop18=TOT_X_NRG_FOOD", "%", "Mensual", "Tasa de variación anual del IPCA excluidos la energía y los alimentos: aproxima la tendencia de fondo de los precios.", cero=True, desde=2005, alt=HICP("TOT_X_NRG_FOOD")),
    I("Precios industriales (tasa anual)", "sts_inppd_m", "&nace_r2=B-E36&s_adj=NSA&unit=PCH_SM", "%", "Mensual", "Variación anual de los precios de producción industrial en el mercado interior (anticipa la inflación de consumo).", cero=True, desde=2005),
    I("Nivel de precios comparado (UE-27 = 100)", "prc_ppp_ind", "&na_item=PLI_EU27_2020&ppp_cat=GDP", "Índice (UE-27 = 100)", "Anual", "Nivel general de precios de cada país respecto a la media de la UE, a partir de las paridades de poder de compra.", desde=2000),
  ]),
"empleo": dict(
  titulo="Mercado laboral",
  subtitulo="Paro, empleo y diferencias por edad y sexo",
  intro="El mercado laboral es uno de los ámbitos en los que la economía española presenta mayores diferencias con Europa, especialmente en el **paro juvenil**. Los datos proceden de la Encuesta de Población Activa armonizada (Eurostat), comparable entre países.",
  docencia=["Economía del trabajo: brechas por sexo y edad en el desempleo.", "Econometría: series temporales desestacionalizadas y relación con el ciclo económico (ley de Okun, junto con el PIB de *Actividad económica*).", "TFG/TFM: análisis del paro juvenil en España frente a la UE."],
  ind=[
    I("Tasa de paro", "une_rt_m", "&s_adj=SA&age=TOTAL&sex=T&unit=PC_ACT", "% de la población activa", "Mensual", "Porcentaje de personas desempleadas sobre la población activa (15-74 años), desestacionalizado.", desde=2005),
    I("Tasa de paro juvenil (menores de 25 años)", "une_rt_m", "&s_adj=SA&age=Y_LT25&sex=T&unit=PC_ACT", "% de la población activa", "Mensual", "Paro de las personas menores de 25 años, desestacionalizado.", desde=2005),
    I("Tasa de paro de las mujeres", "une_rt_m", "&s_adj=SA&age=TOTAL&sex=F&unit=PC_ACT", "% de la población activa", "Mensual", "Tasa de paro femenina, desestacionalizada.", desde=2005),
    I("Tasa de empleo (20-64 años)", "lfsi_emp_a", "&indic_em=EMP_LFS&sex=T&age=Y20-64&unit=PC_POP", "% de la población", "Anual", "Porcentaje de personas ocupadas de 20 a 64 años; el objetivo de la UE para 2030 es el 78 %.", desde=2005),
    I("Tasa de paro por regiones", "lfst_r_lfu3rt", "&sex=T&age=Y15-74&unit=PC", "% de la población activa", "Anual", "Tasa de paro de las comunidades autónomas (NUTS 2).", regional=True, desde=2005),
    I("Paro de larga duración", "une_ltu_a", "&sex=T&age=Y15-74&indic_em=LTU&unit=PC_ACT", "% de la población activa", "Anual", "Personas que llevan 12 meses o más buscando empleo, en porcentaje de la población activa.", desde=2005),
    I("Jóvenes que ni estudian ni trabajan (15-29 años)", "sdg_08_20", "&sex=T&age=Y15-29&unit=PC", "% de la población de 15-29 años", "Anual", "Jóvenes que no tienen empleo ni siguen ningún tipo de educación o formación (indicador NEET).", desde=2005),
    I("Coste laboral por hora", "lc_lci_lev", "&nace_r2=B-S_X_O&lcstruct=D1_D4_MD5&unit=EUR", "€ por hora", "Anual", "Coste laboral medio por hora trabajada (salarios y cotizaciones sociales) en la industria, la construcción y los servicios.", desde=2008),
    I("Salario mínimo mensual", "earn_mw_cur", "&currency=EUR", "€ al mes", "Semestral", "Salario mínimo legal mensual bruto en los países que lo tienen establecido.", desde=2005),
    I("Brecha salarial de género", "sdg_05_20", "&unit=PC", "% del salario medio de los hombres", "Anual", "Diferencia entre la ganancia media por hora de hombres y mujeres, en porcentaje de la de los hombres.", desde=2007),
    I("Tasa de empleo por regiones (20-64 años)", "lfst_r_lfe2emprt", "&sex=T&age=Y20-64&unit=PC", "% de la población", "Anual", "Tasa de empleo de las comunidades autónomas.", regional=True, desde=2005),
  ]),
"actividad": dict(
  titulo="Actividad económica y coyuntura",
  subtitulo="Crecimiento del PIB, producción industrial, comercio y clima económico",
  intro="Estos indicadores permiten seguir el **ciclo económico**: el crecimiento del PIB resume la actividad, mientras que la producción industrial, las ventas del comercio minorista y el indicador de sentimiento económico se publican antes y anticipan su evolución.",
  docencia=["Macroeconomía: fases del ciclo y comparación de la recuperación tras la crisis de 2008 y la COVID-19.", "Economía aplicada: convergencia del PIB per cápita de las regiones españolas con la UE.", "Coyuntura: indicadores adelantados frente a indicadores de actividad."],
  ind=[
    I("PIB: crecimiento interanual (trimestral)", "namq_10_gdp", "&unit=CLV_PCH_SM&na_item=B1GQ&s_adj=SCA", "% de variación interanual", "Trimestral", "Tasa de variación del PIB en volumen respecto al mismo trimestre del año anterior.", cero=True, desde=2005),
    I("PIB per cápita en paridad de poder de compra", "nama_10r_2gdp", "&unit=PPS_EU27_2020_HAB", "PPC por habitante", "Anual", "PIB por habitante en paridad de poder de compra; permite comparar el nivel de vida entre regiones y países.", regional=True, desde=2005),
    I("Índice de producción industrial", "sts_inpr_m", "&nace_r2=B-D&s_adj=SCA&unit=I21", "Índice (2021 = 100)", "Mensual", "Volumen de producción de la industria (extractiva, manufacturera y energía), corregido de estacionalidad y calendario.", desde=2008),
    I("Índice de comercio minorista", "sts_trtu_m", "&nace_r2=G47&s_adj=SCA&unit=I21", "Índice (2021 = 100)", "Mensual", "Volumen de ventas del comercio minorista, corregido de estacionalidad y calendario.", desde=2008),
    I("Indicador de sentimiento económico", "ei_bssi_m_r2", "&indic=BS-ESI-I&s_adj=SA", "Índice (media a largo plazo = 100)", "Mensual", "Indicador compuesto de confianza de industria, servicios, consumidores, construcción y comercio (Comisión Europea).", desde=2008),
    I("Consumo de los hogares: crecimiento interanual", "namq_10_gdp", "&unit=CLV_PCH_SM&na_item=P31_S14_S15&s_adj=SCA", "% de variación interanual", "Trimestral", "Gasto en consumo final de los hogares y las ISFLSH, en volumen.", cero=True, desde=2005),
    I("Inversión (formación bruta de capital fijo): crecimiento interanual", "namq_10_gdp", "&unit=CLV_PCH_SM&na_item=P51G&s_adj=SCA", "% de variación interanual", "Trimestral", "Inversión en bienes de equipo, construcción y activos intangibles, en volumen.", cero=True, desde=2005),
    I("Producción en la construcción", "sts_copr_m", "&nace_r2=F&s_adj=SCA&unit=I21", "Índice (2021 = 100)", "Mensual", "Volumen de producción del sector de la construcción, corregido de estacionalidad y calendario.", desde=2008),
    I("Productividad del trabajo por hora: variación anual", "nama_10_lp_ulc", "&na_item=RLPR_HW&unit=PCH_PRE", "% de variación anual", "Anual", "Crecimiento del PIB real por hora trabajada.", cero=True, desde=2000),
    I("Costes laborales unitarios nominales: variación anual", "nama_10_lp_ulc", "&na_item=NULC_PER&unit=PCH_PRE", "% de variación anual", "Anual", "Coste laboral por unidad producida; indicador de competitividad-precio.", cero=True, desde=2000),
    I("Confianza del consumidor", "ei_bsco_m", "&indic=BS-CSMCI&s_adj=SA", "Saldo de respuestas (%)", "Mensual", "Indicador de confianza de los consumidores de la Comisión Europea (expectativas sobre su situación financiera, la economía y las compras importantes).", cero=True, desde=2008),
  ]),
"empresa": dict(
  titulo="Empresa, innovación y digitalización",
  subtitulo="I+D, inteligencia artificial, comercio electrónico y confianza empresarial",
  intro="La **transformación digital** y la innovación son determinantes de la productividad y la competitividad de las empresas. Esta sección reúne indicadores de inversión en I+D, adopción de la inteligencia artificial y comercio electrónico, junto con la confianza de la industria.",
  docencia=["Dirección y organización de empresas: adopción de la IA según el tamaño de la empresa y el país.", "Economía de la innovación: esfuerzo en I+D de las regiones españolas.", "Marketing: evolución del comercio electrónico entre los consumidores."],
  ind=[
    I("Gasto en I+D (% del PIB)", "rd_e_gerdtot", "&sectperf=TOTAL&unit=PC_GDP", "% del PIB", "Anual", "Gasto interno total en investigación y desarrollo; el objetivo europeo es el 3 % del PIB.", desde=2005),
    I("Gasto en I+D por regiones (% del PIB)", "rd_e_gerdreg", "&sectperf=TOTAL&unit=PC_GDP", "% del PIB", "Anual", "Gasto interno en I+D de las comunidades autónomas.", regional=True, desde=2005),
    I("Empresas que usan inteligencia artificial", "isoc_eb_ai", "&indic_is=E_AI_TANY&size_emp=GE10&unit=PC_ENT", "% de empresas", "Anual", "Porcentaje de empresas de 10 o más personas empleadas que usan al menos una tecnología de inteligencia artificial.", desde=2021),
    I("Personas que compran por internet", "isoc_ec_ibuy", "&indic_is=I_BUY3&ind_type=IND_TOTAL&unit=PC_IND", "% de personas", "Anual", "Porcentaje de personas de 16 a 74 años que han comprado bienes o servicios por internet en los últimos 12 meses.", desde=2008),
    I("Confianza de la industria", "ei_bsin_m_r2", "&indic=BS-ICI-BAL&s_adj=SA", "Saldo de respuestas (%)", "Mensual", "Indicador de confianza industrial: diferencia entre respuestas positivas y negativas sobre pedidos, existencias y producción esperada.", cero=True, desde=2008),
    I("Declaraciones de quiebra de empresas (índice)", "sts_rb_q", "&indic_bt=BKRT&nace_r2=B-S_X_O_S94&s_adj=SCA&unit=I21", "Índice (2021 = 100)", "Trimestral", "Evolución del número de empresas declaradas en quiebra o concurso.", desde=2015),
    I("Registros de nuevas empresas (índice)", "sts_rb_q", "&indic_bt=REG&nace_r2=B-S_X_O_S94&s_adj=SCA&unit=I21", "Índice (2021 = 100)", "Trimestral", "Evolución del número de empresas de nueva creación inscritas en los registros.", desde=2015),
    I("Confianza en los servicios", "ei_bsse_m_r2", "&indic=BS-SCI-BAL&s_adj=SA", "Saldo de respuestas (%)", "Mensual", "Indicador de confianza de las empresas de servicios (Comisión Europea).", cero=True, desde=2008),
    I("Confianza del comercio minorista", "ei_bsrt_m_r2", "&indic=BS-RCI-BAL&s_adj=SA", "Saldo de respuestas (%)", "Mensual", "Indicador de confianza del comercio minorista (Comisión Europea).", cero=True, desde=2008),
    I("Confianza de la construcción", "ei_bsbu_m_r2", "&indic=BS-CCI-BAL&s_adj=SA", "Saldo de respuestas (%)", "Mensual", "Indicador de confianza de las empresas de construcción (Comisión Europea).", cero=True, desde=2008),
    I("Hogares con acceso a internet", "isoc_ci_in_h", "&unit=PC_HH&hhtyp=TOTAL&indic_is=H_IACC", "% de hogares", "Anual", "Porcentaje de hogares con acceso a internet en casa.", desde=2008),
  ]),
"turismo": dict(
  titulo="Turismo",
  subtitulo="Viajeros y pernoctaciones en alojamientos turísticos",
  intro="El turismo es uno de los sectores clave de la economía española y andaluza. Se muestran las **pernoctaciones** (noches que pasan los viajeros en un alojamiento) y las **llegadas de viajeros** a hoteles, para residentes y no residentes, con detalle regional.",
  docencia=["Economía del turismo: estacionalidad de la demanda hotelera y efecto de la COVID-19.", "Métodos Cuantitativos: descomposición de series en tendencia y estacionalidad.", "TFG/TFM: peso del turismo internacional en Andalucía frente a otras comunidades."],
  ind=[
    I("Pernoctaciones en hoteles", "tour_occ_nim", "&c_resid=TOTAL&unit=NR&nace_r2=I551", "Número de pernoctaciones", "Mensual", "Noches pasadas por residentes y no residentes en hoteles y alojamientos similares.", desde=2008),
    I("Pernoctaciones de no residentes en hoteles", "tour_occ_nim", "&c_resid=FOR&unit=NR&nace_r2=I551", "Número de pernoctaciones", "Mensual", "Noches pasadas por viajeros residentes en el extranjero.", desde=2008),
    I("Llegadas de viajeros a hoteles", "tour_occ_arm", "&c_resid=TOTAL&unit=NR&nace_r2=I551", "Número de viajeros", "Mensual", "Viajeros que se alojan en hoteles y alojamientos similares.", desde=2008),
    I("Pernoctaciones por regiones", "tour_occ_nin2", "&c_resid=TOTAL&unit=NR&nace_r2=I551-I553", "Número de pernoctaciones", "Anual", "Pernoctaciones en hoteles, alojamientos de corta estancia y campings de las comunidades autónomas.", regional=True, desde=2008),
    I("Pernoctaciones de residentes en hoteles", "tour_occ_nim", "&c_resid=NAT&unit=NR&nace_r2=I551", "Número de pernoctaciones", "Mensual", "Noches pasadas en hoteles por viajeros residentes en el propio país (turismo interno).", desde=2008),
    I("Pernoctaciones en apartamentos y alojamientos de corta estancia", "tour_occ_nim", "&c_resid=TOTAL&unit=NR&nace_r2=I552", "Número de pernoctaciones", "Mensual", "Noches pasadas en apartamentos turísticos, casas rurales y otros alojamientos de corta estancia.", desde=2008),
    I("Tasa de ocupación de las plazas hoteleras", "tour_occ_mnor", "&accomunit=BEDPL&nace_r2=I551", "% de plazas ocupadas", "Mensual", "Porcentaje de plazas en hoteles ocupadas en el mes.", desde=2010),
  ]),
"publico": dict(
  titulo="Sector público y mercados financieros",
  subtitulo="Deuda y déficit públicos, tipos de interés y tipo de cambio",
  intro="Las cuentas públicas y las condiciones de financiación condicionan la política económica. Se incluyen la **deuda y el déficit públicos** (criterios de Maastricht), la **rentabilidad del bono a 10 años** y el **tipo de cambio del euro**.",
  docencia=["Hacienda pública: reglas fiscales europeas (60 % de deuda y 3 % de déficit).", "Economía financiera: prima de riesgo como diferencia entre la rentabilidad del bono español y el alemán.", "Economía internacional: evolución del euro frente al dólar."],
  ind=[
    I("Deuda pública (% del PIB)", "gov_10dd_edpt1", "&unit=PC_GDP&sector=S13&na_item=GD", "% del PIB", "Anual", "Deuda bruta consolidada de las administraciones públicas (criterio de Maastricht).", desde=2000),
    I("Déficit (−) o superávit (+) público (% del PIB)", "gov_10dd_edpt1", "&unit=PC_GDP&sector=S13&na_item=B9", "% del PIB", "Anual", "Capacidad o necesidad de financiación de las administraciones públicas.", cero=True, desde=2000),
    I("Rentabilidad del bono a 10 años", "irt_lt_mcby_m", "&int_rt=MCBY", "%", "Mensual", "Rendimiento de la deuda pública a largo plazo (criterio de convergencia de Maastricht).", desde=2000),
    I("Tipo de cambio euro / dólar", "ert_bil_eur_m", "&currency=USD&statinfo=AVG", "Dólares por euro", "Mensual", "Media mensual del tipo de cambio de referencia del euro frente al dólar estadounidense.", sinGeo=True, serie="Euro / dólar", desde=2000),
    I("Ingresos fiscales (% del PIB)", "gov_10a_taxag", "&unit=PC_GDP&sector=S13_S212&na_item=D2_D5_D91_D61_M_D995", "% del PIB", "Anual", "Impuestos y cotizaciones sociales recaudados por las administraciones públicas y las instituciones de la UE (presión fiscal).", desde=2000),
    I("Gasto público total (% del PIB)", "gov_10a_exp", "&unit=PC_GDP&sector=S13&na_item=TE&cofog99=TOTAL", "% del PIB", "Anual", "Gasto total de las administraciones públicas.", desde=2000),
    I("Gasto público en sanidad (% del PIB)", "gov_10a_exp", "&unit=PC_GDP&sector=S13&na_item=TE&cofog99=GF07", "% del PIB", "Anual", "Gasto de las administraciones públicas en sanidad (clasificación COFOG).", desde=2000),
    I("Gasto público en educación (% del PIB)", "gov_10a_exp", "&unit=PC_GDP&sector=S13&na_item=TE&cofog99=GF09", "% del PIB", "Anual", "Gasto de las administraciones públicas en educación (clasificación COFOG).", desde=2000),
    I("Gasto público en protección social (% del PIB)", "gov_10a_exp", "&unit=PC_GDP&sector=S13&na_item=TE&cofog99=GF10", "% del PIB", "Anual", "Gasto en pensiones, desempleo, familia, vivienda y exclusión social (clasificación COFOG).", desde=2000),
    I("Euríbor a 3 meses", "irt_st_m", "&int_rt=IRT_M3&geo=EA", "%", "Mensual", "Tipo de interés del mercado interbancario de la zona euro a tres meses, referencia de muchos préstamos.", sinGeo=True, serie="Euríbor a 3 meses", cero=True, desde=2000),
  ]),
"desigualdad": dict(
  titulo="Desigualdad, pobreza y condiciones de vida",
  subtitulo="Desigualdad de la renta, pobreza, privación material y vivienda",
  intro="La desigualdad y la pobreza son retos estratégicos de la Agenda 2030 (ODS 10 y ODS 1). Los indicadores proceden de la Encuesta de Condiciones de Vida armonizada (EU-SILC).",
  docencia=["Economía aplicada: medición de la desigualdad (Gini, S80/S20, índices de Theil) y su descomposición.", "Métodos Cuantitativos: estimación a partir de encuestas y margen de error de los indicadores.", "TFG/TFM: pobreza y exclusión en las comunidades autónomas."],
  ind=[
    I("Índice de Gini", "ilc_di12", "", "Coeficiente (0-100)", "Anual", "Coeficiente de Gini de la renta disponible equivalente (0 = igualdad perfecta; 100 = máxima desigualdad).", desde=2005),
    I("Ratio S80/S20", "ilc_di11", "", "Ratio", "Anual", "Renta del 20 % más rico dividida entre la del 20 % más pobre.", desde=2005),
    I("Riesgo de pobreza o exclusión social (AROPE)", "ilc_peps01n", "&unit=PC&age=TOTAL&sex=T", "% de la población", "Anual", "Personas en riesgo de pobreza, con carencia material y social severa o en hogares con baja intensidad de empleo.", desde=2015),
    I("Riesgo de pobreza o exclusión social por regiones", "ilc_peps11n", "&unit=PC", "% de la población", "Anual", "Tasa AROPE de las comunidades autónomas.", regional=True, desde=2015),
    I("Tasa de riesgo de pobreza (60 % de la mediana)", "ilc_li02", "&indic_il=LI_R_MD60&age=TOTAL&sex=T&unit=PC", "% de la población", "Anual", "Personas con una renta disponible equivalente inferior al 60 % de la mediana nacional.", desde=2005),
    I("Umbral de pobreza (hogar de una persona)", "ilc_li01", "&hhtyp=A1&indic_il=LI_C_MD60&currency=EUR", "€ al año", "Anual", "Renta anual por debajo de la cual una persona que vive sola se considera en riesgo de pobreza.", desde=2005),
    I("Riesgo de pobreza o exclusión social: menores de 18 años", "ilc_peps01n", "&unit=PC&age=Y_LT18&sex=T", "% de la población menor de 18 años", "Anual", "Tasa AROPE infantil.", desde=2015),
    I("Carencia material y social severa", "ilc_mdsd11", "&unit=PC&age=TOTAL&sex=T", "% de la población", "Anual", "Personas que no pueden permitirse al menos 7 de 13 elementos básicos (pagar facturas, calefacción, imprevistos, etc.).", desde=2015),
    I("Pobreza de las personas que trabajan", "ilc_iw01", "&wstatus=EMP&sex=T&age=Y18-64&unit=PC", "% de las personas ocupadas", "Anual", "Personas ocupadas de 18 a 64 años en riesgo de pobreza (pobreza laboral).", desde=2005),
    I("Sobrecarga del coste de la vivienda", "ilc_lvho07a", "&age=TOTAL&sex=T&incgrp=TOTAL&unit=PC", "% de la población", "Anual", "Personas que destinan más del 40 % de su renta disponible a la vivienda.", desde=2005),
    I("Renta mediana equivalente", "ilc_di03", "&age=TOTAL&sex=T&indic_il=MED_E&unit=EUR", "€ al año", "Anual", "Renta disponible equivalente mediana por persona.", desde=2005),
    I("Tasa de riesgo de pobreza por regiones", "ilc_li41", "&unit=PC", "% de la población", "Anual", "Tasa de riesgo de pobreza de las comunidades autónomas.", regional=True, desde=2008),
  ]),
"sostenibilidad": dict(
  titulo="Energía y sostenibilidad",
  subtitulo="Energías renovables, precios de la electricidad y emisiones",
  intro="La transición energética afecta a los costes de las empresas y de los hogares. Se muestran la **cuota de energías renovables**, el **precio de la electricidad** para los hogares y la evolución de las **emisiones de gases de efecto invernadero**.",
  docencia=["Economía de la energía y del medio ambiente: objetivos europeos de renovables y emisiones.", "Dirección de operaciones: impacto del precio de la energía en los costes empresariales.", "Economía española: ventaja de España en energía solar y eólica."],
  ind=[
    I("Cuota de energías renovables", "nrg_ind_ren", "&nrg_bal=REN&unit=PC", "% del consumo final bruto de energía", "Anual", "Porcentaje de energía procedente de fuentes renovables; el objetivo europeo para 2030 es el 42,5 %.", desde=2005),
    I("Precio de la electricidad para hogares", "nrg_pc_204", "&product=6000&nrg_cons=KWH2500-4999&unit=KWH&tax=I_TAX&currency=EUR", "€ por kWh (con impuestos)", "Semestral", "Precio medio de la electricidad para consumidores domésticos con un consumo anual de 2.500-5.000 kWh.", desde=2008),
    I("Emisiones netas de gases de efecto invernadero", "sdg_13_10", "&unit=I90", "Índice (1990 = 100)", "Anual", "Emisiones netas de gases de efecto invernadero, incluido el uso del suelo, respecto a 1990.", desde=2000),
    I("Emisiones de gases de efecto invernadero por habitante", "sdg_13_10", "&unit=T_HAB", "Toneladas de CO₂ equivalente por habitante", "Anual", "Emisiones netas de gases de efecto invernadero por habitante.", desde=2000),
    I("Dependencia energética", "nrg_ind_id", "&siec=TOTAL&unit=PC", "% de las necesidades energéticas", "Anual", "Parte de la energía que un país necesita y que tiene que importar.", desde=2000),
    I("Precio del gas natural para hogares", "nrg_pc_202", "&product=4100&nrg_cons=GJ20-199&unit=KWH&tax=I_TAX&currency=EUR", "€ por kWh (con impuestos)", "Semestral", "Precio medio del gas natural para consumidores domésticos con consumo medio.", desde=2008),
    I("Residuos municipales por habitante", "env_wasmun", "&wst_oper=GEN&unit=KG_HAB", "kg por habitante", "Anual", "Residuos urbanos generados por habitante.", desde=2000),
    I("Tasa de reciclaje de residuos municipales", "sdg_11_60", "&unit=PC", "% de los residuos municipales", "Anual", "Porcentaje de los residuos municipales que se recicla o composta.", desde=2000),
  ]),
"poblacion": dict(
  titulo="Población, educación y salud",
  subtitulo="Demografía, envejecimiento, capital humano y esperanza de vida",
  intro="La población y el **capital humano** son la base del crecimiento económico, del mercado de trabajo y de la sostenibilidad del sistema de pensiones. Se reúnen indicadores de demografía, educación y salud comparables entre países y regiones.",
  docencia=["Macroeconomía y crecimiento: capital humano y envejecimiento como determinantes del crecimiento a largo plazo.", "Economía del sector público: sostenibilidad de las pensiones y tasa de dependencia.", "Marketing: tamaño y estructura de los mercados por países y regiones."],
  ind=[
    I("Población", "demo_pjan", "&sex=T&age=TOTAL", "Personas", "Anual", "Población residente a 1 de enero.", desde=2000),
    I("Población por regiones", "demo_r_d2jan", "&sex=T&age=TOTAL", "Personas", "Anual", "Población residente a 1 de enero en las comunidades autónomas.", regional=True, desde=2000),
    I("Tasa de fecundidad", "demo_find", "&indic_de=TOTFERRT", "Hijos por mujer", "Anual", "Número medio de hijos por mujer (indicador coyuntural de fecundidad).", desde=2000),
    I("Tasa de dependencia de las personas mayores", "demo_pjanind", "&indic_de=OLDDEP1", "% de la población de 15-64 años", "Anual", "Población de 65 años o más en relación con la población en edad de trabajar.", desde=2000),
    I("Esperanza de vida al nacer", "demo_mlexpec", "&sex=T&age=Y_LT1&unit=YR", "Años", "Anual", "Número medio de años que se espera que viva una persona recién nacida.", desde=2000),
    I("Población de 25-34 años con estudios superiores", "sdg_04_20", "&sex=T&unit=PC", "% de la población de 25-34 años", "Anual", "Personas jóvenes con educación terciaria; el objetivo europeo para 2030 es el 45 %.", desde=2005),
    I("Abandono temprano de la educación y la formación", "sdg_04_10", "&sex=T&unit=PC", "% de la población de 18-24 años", "Anual", "Jóvenes que solo tienen la educación secundaria obligatoria y no siguen estudiando; el objetivo europeo para 2030 es menos del 9 %.", desde=2005),
  ]),
"internacional": dict(
  titulo="Economía internacional y sector exterior",
  subtitulo="Comercio exterior, balanza de pagos y convergencia internacional",
  intro="La apertura al exterior y la posición frente al resto del mundo condicionan el crecimiento y la estabilidad de una economía. Se incluyen el **comercio exterior**, la **balanza por cuenta corriente**, la **posición de inversión internacional** y la **convergencia** del nivel de vida con la UE.",
  docencia=["Economía mundial e internacional: grado de apertura y desequilibrios exteriores en la UE.", "Comercio exterior y marketing internacional: dinamismo exportador de España frente a sus socios.", "Integración económica: convergencia del PIB per cápita y de los precios en la UE."],
  ind=[
    I("Exportaciones de bienes y servicios (% del PIB)", "nama_10_gdp", "&unit=PC_GDP&na_item=P6", "% del PIB", "Anual", "Peso de las exportaciones en el PIB: indicador del grado de apertura.", desde=2000),
    I("Importaciones de bienes y servicios (% del PIB)", "nama_10_gdp", "&unit=PC_GDP&na_item=P7", "% del PIB", "Anual", "Peso de las importaciones en el PIB.", desde=2000),
    I("Exportaciones: crecimiento interanual (trimestral)", "namq_10_gdp", "&unit=CLV_PCH_SM&na_item=P6&s_adj=SCA", "% de variación interanual", "Trimestral", "Exportaciones de bienes y servicios en volumen.", cero=True, desde=2005),
    I("Saldo por cuenta corriente (% del PIB)", "bop_gdp6_q", "&bop_item=CA&stk_flow=BAL&partner=WRL_REST&unit=PC_GDP&s_adj=NSA", "% del PIB", "Trimestral", "Diferencia entre ingresos y pagos por bienes, servicios y rentas con el resto del mundo.", cero=True, desde=2008),
    I("Posición de inversión internacional neta (% del PIB)", "tipsii10", "", "% del PIB", "Anual", "Activos financieros frente al exterior menos pasivos; los valores negativos indican endeudamiento exterior neto.", cero=True, desde=2008),
    I("PIB per cápita en PPC (UE-27 = 100)", "tec00114", "", "Índice (UE-27 = 100)", "Anual", "Volumen del PIB por habitante en paridad de poder de compra respecto a la media de la UE.", desde=2005),
  ]),
"andalucia": dict(
  titulo="Andalucía y las regiones españolas",
  subtitulo="Indicadores regionales para comparar Andalucía con el resto de comunidades autónomas y la UE",
  intro="Esta página reúne los indicadores con **detalle regional (NUTS 2)**. Por defecto se muestran Andalucía, España, Madrid, Cataluña y la Comunidad Valenciana; puedes añadir cualquier otra comunidad autónoma.",
  docencia=["Economía regional: convergencia de Andalucía con España y la UE.", "Econometría espacial: diferencias territoriales en paro, renta e I+D.", "TFG/TFM: diagnóstico socioeconómico de Andalucía."],
  ind=[
    I("PIB per cápita en paridad de poder de compra", "nama_10r_2gdp", "&unit=PPS_EU27_2020_HAB", "PPC por habitante", "Anual", "PIB por habitante en paridad de poder de compra.", regional=True, desde=2005),
    I("Tasa de paro", "lfst_r_lfu3rt", "&sex=T&age=Y15-74&unit=PC", "% de la población activa", "Anual", "Tasa de paro de las comunidades autónomas.", regional=True, desde=2005),
    I("Gasto en I+D (% del PIB)", "rd_e_gerdreg", "&sectperf=TOTAL&unit=PC_GDP", "% del PIB", "Anual", "Gasto interno en I+D de las comunidades autónomas.", regional=True, desde=2005),
    I("Pernoctaciones turísticas", "tour_occ_nin2", "&c_resid=TOTAL&unit=NR&nace_r2=I551-I553", "Número de pernoctaciones", "Anual", "Pernoctaciones en alojamientos turísticos.", regional=True, desde=2008),
    I("Riesgo de pobreza o exclusión social (AROPE)", "ilc_peps11n", "&unit=PC", "% de la población", "Anual", "Tasa AROPE de las comunidades autónomas.", regional=True, desde=2015),
    I("Tasa de empleo (20-64 años)", "lfst_r_lfe2emprt", "&sex=T&age=Y20-64&unit=PC", "% de la población", "Anual", "Tasa de empleo de las comunidades autónomas.", regional=True, desde=2005),
    I("Tasa de riesgo de pobreza", "ilc_li41", "&unit=PC", "% de la población", "Anual", "Tasa de riesgo de pobreza de las comunidades autónomas.", regional=True, desde=2008),
    I("Población", "demo_r_d2jan", "&sex=T&age=TOTAL", "Personas", "Anual", "Población residente a 1 de enero.", regional=True, desde=2000),
  ]),
}

EXTRA = {
"desigualdad": """
::: {.callout-tip appearance="simple"}
**Más datos de desigualdad.** El Banco Mundial publica el índice de Gini y la desviación logarítmica media (índice de Theil T₀) de más de 170 países en su [Poverty and Inequality Platform](https://pip.worldbank.org/), y el INE publica la Encuesta de Condiciones de Vida con detalle por comunidades autónomas ([INEbase](https://www.ine.es/dyngs/INEbase/es/operacion.htm?c=Estadistica_C&cid=1254736176807&menu=ultiDatos&idp=1254735976608)).
:::
""",
"turismo": """
::: {.callout-tip appearance="simple"}
**Más datos de turismo.** El INE publica la *Coyuntura Turística Hotelera* con detalle provincial (incluida Granada), y Frontur y Egatur sobre la llegada y el gasto de los turistas internacionales: [ine.es](https://www.ine.es/dyngs/INEbase/es/categoria.htm?c=Estadistica_P&cid=1254735576863). La Junta de Andalucía ofrece estadísticas de turismo andaluz en el [IECA](https://www.juntadeandalucia.es/institutodeestadisticaycartografia).
:::
""",
"precios": """
::: {.callout-tip appearance="simple"}
**Precios de productos concretos.** La gasolina, el gasóleo, la luz, el gas y los productos de la cesta de la compra, comparados con el IPC, en [Precios de productos](precios-productos.qmd).
:::

::: {.callout-tip appearance="simple"}
**IPC nacional y por comunidades autónomas.** El INE publica el IPC general y por grupos, con detalle por comunidades autónomas y provincias: [IPC en INEbase](https://www.ine.es/dyngs/INEbase/es/operacion.htm?c=Estadistica_C&cid=1254736176802&menu=ultiDatos&idp=1254735976607).
:::
""",
}

HELPERS = open("_helpers.qmd").read().strip()
PANEL = open("_panel.qmd").read().strip()

def page(key, c):
    js = json.dumps(c["ind"], ensure_ascii=False, indent=2)
    doc = "\n".join(f"- {x}" for x in c["docencia"])
    return f"""---
title: "{c['titulo']}"
subtitle: "{c['subtitulo']}"
---

{c['intro']}

Elige un indicador y los territorios que quieras comparar. Pasa el ratón sobre las líneas para ver los valores y descarga los datos en CSV para usarlos en clase o en tu investigación.

```{{ojs}}
//| echo: false
indicadores = {js}
```

{HELPERS}

{PANEL}
{EXTRA.get(key, "")}
## Ideas para la docencia y la investigación

{doc}

<p class="source">¿Echas en falta algún indicador? Escríbenos a [investiga_ccee@ugr.es](mailto:investiga_ccee@ugr.es).</p>
"""

for k, c in CATS.items():
    open(f"{k}.qmd", "w").write(page(k, c))
n = sum(len(c["ind"]) for c in CATS.values())
print(f"{len(CATS)} páginas, {n} indicadores")
catalogo = [dict(id=i["id"], nombre=i["nombre"], pagina=k, categoria=c["titulo"], code=i["code"], unidad=i["unidad"],
                 frecuencia=i["frecuencia"], descripcion=i["descripcion"], regional=bool(i.get("regional")))
            for k, c in CATS.items() for i in c["ind"]]
open("data/indicadores.json", "w").write(json.dumps(catalogo, ensure_ascii=False, indent=1))
open("data/indicadores_specs.json", "w").write(json.dumps({k: c["ind"] for k, c in CATS.items()}, ensure_ascii=False))
print(f"Catálogo: {len(catalogo)} indicadores en data/indicadores.json")
