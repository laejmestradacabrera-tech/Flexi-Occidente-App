# ============================================================
# 🧠 INTELIGENCIA COMERCIAL FLEXI
# ============================================================

import os
import re
import hashlib
import feedparser
import pandas as pd
import streamlit as st
from datetime import datetime


# ============================================================
# CONFIGURACIÓN
# ============================================================

ARCHIVO_INTELIGENCIA = "datos_inteligencia.csv"

META_CONVERSION = 10.9
META_TICKET = 1.29


# ============================================================
# FUENTES
# ============================================================

FUENTES = {

    "Mercado de Calzado": {
        "url": "https://wwd.com/footwear-news/feed/",
        "tipo": "Calzado"
    },

    "Retail": {
        "url": "https://www.retaildive.com/feeds/news/",
        "tipo": "Retail"
    },

    "Supply Chain": {
        "url": "https://www.supplychaindive.com/feeds/news/",
        "tipo": "Supply Chain"
    },

    "Economía México": {
        "url": "https://www.eleconomista.com.mx/rss/empresas/",
        "tipo": "Macroeconomía"
    },

    "INEGI": {
        "url": "https://www.inegi.org.mx/rss/noticias.xml",
        "tipo": "INEGI"
    }
}


# ============================================================
# PALABRAS CLAVE
# ============================================================

CLAVES_CALZADO = [
    "shoe", "shoes", "footwear", "calzado",
    "zapato", "zapatos", "sneaker", "sneakers",
    "boots", "botas", "zapatería",
    "leather", "piel", "suela"
]

CLAVES_RETAIL = [
    "retail", "store", "stores", "tienda",
    "tiendas", "sales", "ventas",
    "consumer", "consumidor",
    "shopping mall", "mall",
    "centro comercial", "plaza",
    "shopping center", "traffic",
    "foot traffic", "afluencia",
    "opening", "apertura",
    "closure", "cierre",
    "expansion", "expansión"
]

CLAVES_SUPPLY = [
    "supply chain", "logistics",
    "logística", "inventario",
    "inventory", "stock", "shortage",
    "quiebre", "warehouse",
    "almacén", "distribution",
    "distribución", "shipping",
    "freight", "transport"
]

CLAVES_MACRO = [
    "inflación", "inflation",
    "pib", "gdp",
    "consumidor", "consumer",
    "consumo", "consumption",
    "tasas", "interest",
    "interés", "economía",
    "economy", "empleo",
    "employment", "desempleo",
    "unemployment", "ventas",
    "sales", "comercio",
    "commerce", "precio",
    "prices", "poder adquisitivo",
    "banco de méxico", "banxico",
    "confianza del consumidor",
    "ingreso", "income"
]

CLAVES_MEXICO = [
    "méxico", "mexico", "mexican",
    "mexicana", "banxico",
    "banco de méxico", "inegi",
    "peso mexicano", "consumo interno"
]

CLAVES_COMPETENCIA = [
    "nike", "adidas", "puma",
    "skechers", "new balance",
    "hush puppies", "clarks",
    "aldo", "flexi"
]

PALABRAS_EXCLUIR = [
    "makeup", "beauty", "cosmetics",
    "maquillaje", "belleza",
    "grocery", "supermarket",
    "food", "comida", "ulta",
    "dollar general", "beverage",
    "skincare", "kroger",
    "farmacia", "cvs", "walgreens"
]


# ============================================================
# FUNCIONES
# ============================================================

def limpiar_texto(texto):

    if texto is None:
        return ""

    texto = re.sub(
        r"<[^>]+>",
        " ",
        str(texto)
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto.lower().strip()


def contiene(texto, lista):

    return any(
        palabra.lower() in texto
        for palabra in lista
    )


def generar_id(titulo, enlace):

    base = (
        str(titulo) +
        "|" +
        str(enlace)
    ).lower()

    return hashlib.md5(
        base.encode("utf-8")
    ).hexdigest()


def calcular_score(texto, tipo):

    score = 0

    if contiene(texto, CLAVES_CALZADO):
        score += 30

    if contiene(texto, CLAVES_RETAIL):
        score += 20

    if contiene(texto, CLAVES_SUPPLY):
        score += 10

    if contiene(texto, CLAVES_MEXICO):
        score += 20

    if contiene(texto, CLAVES_MACRO):
        score += 15

    if contiene(texto, CLAVES_COMPETENCIA):
        score += 20

    if tipo == "INEGI":
        score += 10

    if tipo == "Macroeconomía":
        score += 5

    if contiene(texto, PALABRAS_EXCLUIR):
        score -= 30

    return max(
        0,
        min(score, 100)
    )


def relevancia(score):

    if score >= 80:
        return "CRÍTICA"

    if score >= 60:
        return "ALTA"

    if score >= 40:
        return "MEDIA"

    return "BAJA"


def analizar_impacto(texto):

    resultados = []

    # --------------------------------------------
    # CONSUMO / INFLACIÓN
    # --------------------------------------------

    if contiene(
        texto,
        [
            "inflación",
            "inflation",
            "precio",
            "prices",
            "consumo",
            "consumption",
            "consumidor",
            "consumer"
        ]
    ):

        resultados.append({
            "impacto": "Presión sobre el comportamiento de compra",
            "kpi": "Ticket / Conversión",
            "nivel": "ALTO",
            "accion": (
                "Reforzar venta de segundo par, "
                "CREDICLUB y opciones de pago."
            )
        })

    # --------------------------------------------
    # EMPLEO
    # --------------------------------------------

    if contiene(
        texto,
        [
            "empleo",
            "employment",
            "desempleo",
            "unemployment",
            "ingreso",
            "income"
        ]
    ):

        resultados.append({
            "impacto": "Cambio en capacidad de compra",
            "kpi": "Conversión",
            "nivel": "MEDIO",
            "accion": (
                "Fortalecer argumento de valor, "
                "comodidad y alternativas de pago."
            )
        })

    # --------------------------------------------
    # CENTROS COMERCIALES
    # --------------------------------------------

    if contiene(
        texto,
        [
            "mall",
            "shopping mall",
            "centro comercial",
            "plaza",
            "traffic",
            "afluencia",
            "foot traffic"
        ]
    ):

        resultados.append({
            "impacto": "Posible cambio en afluencia",
            "kpi": "Conversión",
            "nivel": "ALTO",
            "accion": (
                "Asegurar abordaje efectivo y "
                "ejecución de Ruta del Cliente."
            )
        })

    # --------------------------------------------
    # INVENTARIO
    # --------------------------------------------

    if contiene(
        texto,
        [
            "supply chain",
            "inventario",
            "inventory",
            "stock",
            "shortage",
            "quiebre"
        ]
    ):

        resultados.append({
            "impacto": "Riesgo de disponibilidad de producto",
            "kpi": "Quiebres / Ticket",
            "nivel": "ALTO",
            "accion": (
                "Revisar inventario, tallas críticas "
                "y ejecutar nivelación."
            )
        })

    # --------------------------------------------
    # COMPETENCIA
    # --------------------------------------------

    if contiene(
        texto,
        CLAVES_COMPETENCIA
    ):

        resultados.append({
            "impacto": "Movimiento competitivo",
            "kpi": "Conversión / Ticket",
            "nivel": "MEDIO",
            "accion": (
                "Analizar precio, producto, propuesta "
                "de valor y experiencia de compra."
            )
        })

    # --------------------------------------------
    # DEFAULT
    # --------------------------------------------

    if not resultados:

        resultados.append({
            "impacto": "Información de contexto comercial",
            "kpi": "Estratégico",
            "nivel": "BAJO",
            "accion": (
                "Dar seguimiento y evaluar evolución."
            )
        })

    return resultados[0]


def obtener_fecha(entry):

    try:

        if (
            hasattr(entry, "published_parsed")
            and entry.published_parsed
        ):

            fecha = datetime(
                *entry.published_parsed[:6]
            )

            return fecha.strftime(
                "%Y-%m-%d"
            )

    except Exception:
        pass

    return datetime.now().strftime(
        "%Y-%m-%d"
    )


# ============================================================
# RECOLECTAR NOTICIAS
# ============================================================

def recolectar_noticias():

    datos = []

    for nombre, fuente in FUENTES.items():

        try:

            feed = feedparser.parse(
                fuente["url"],
                agent=(
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64)"
                )
            )

            contador = 0

            for entry in feed.entries:

                titulo = getattr(
                    entry,
                    "title",
                    "Sin título"
                )

                enlace = getattr(
                    entry,
                    "link",
                    ""
                )

                resumen = getattr(
                    entry,
                    "summary",
                    getattr(
                        entry,
                        "description",
                        ""
                    )
                )

                texto = limpiar_texto(
                    f"{titulo} {resumen}"
                )

                # Excluir basura
                if contiene(
                    texto,
                    PALABRAS_EXCLUIR
                ):
                    continue

                score = calcular_score(
                    texto,
                    fuente["tipo"]
                )

                # No aceptar información
                # demasiado irrelevante
                if score < 30:
                    continue

                impacto = analizar_impacto(
                    texto
                )

                datos.append({

                    "ID": generar_id(
                        titulo,
                        enlace
                    ),

                    "Categoría":
                        nombre,

                    "Tipo Fuente":
                        fuente["tipo"],

                    "Título":
                        titulo,

                    "Fecha":
                        obtener_fecha(entry),

                    "Relevancia":
                        relevancia(score),

                    "Score":
                        score,

                    "Impacto Flexi":
                        impacto["impacto"],

                    "KPI Afectado":
                        impacto["kpi"],

                    "Nivel Impacto":
                        impacto["nivel"],

                    "Acción Sugerida":
                        impacto["accion"],

                    "Enlace":
                        enlace,

                    "Última Actualización":
                        datetime.now().strftime(
                            "%Y-%m-%d %H:%M"
                        )
                })

                contador += 1

                if contador >= 6:
                    break

        except Exception as e:

            print(
                f"Error en {nombre}: {e}"
            )

    if not datos:

        return pd.DataFrame()

    df_nuevo = pd.DataFrame(
        datos
    )

    # --------------------------------------------
    # ELIMINAR DUPLICADOS
    # --------------------------------------------

    df_nuevo = (
        df_nuevo
        .drop_duplicates(
            subset=["ID"]
        )
    )

    # --------------------------------------------
    # ORDENAR
    # --------------------------------------------

    df_nuevo = (
        df_nuevo
        .sort_values(
            by="Score",
            ascending=False
        )
    )

    # --------------------------------------------
    # GUARDAR
    # --------------------------------------------

    df_nuevo.to_csv(
        ARCHIVO_INTELIGENCIA,
        index=False,
        encoding="utf-8-sig"
    )

    return df_nuevo


# ============================================================
# CARGAR CSV
# ============================================================

@st.cache_data(ttl=900)
def cargar_noticias():

    if not os.path.exists(
        ARCHIVO_INTELIGENCIA
    ):
        return pd.DataFrame()

    try:

        df = pd.read_csv(
            ARCHIVO_INTELIGENCIA,
            encoding="utf-8-sig"
        )

        if df.empty:
            return df

        df["Score"] = pd.to_numeric(
            df["Score"],
            errors="coerce"
        ).fillna(0)

        df["_Fecha"] = pd.to_datetime(
            df["Fecha"],
            errors="coerce"
        )

        return (
            df
            .sort_values(
                ["Score", "_Fecha"],
                ascending=[False, False]
            )
        )

    except Exception:

        return pd.DataFrame()


# ============================================================
# ENCABEZADO
# ============================================================

st.title(
    "🧠 Inteligencia Comercial"
)

st.caption(
    "Señales externas para anticipar riesgos, "
    "oportunidades y decisiones comerciales de Flexi."
)


# ============================================================
# BOTÓN ACTUALIZAR
# ============================================================

col1, col2 = st.columns(
    [4, 1]
)

with col1:

    st.info(
        "La inteligencia comercial analiza calzado, "
        "retail, centros comerciales, supply chain, "
        "macroeconomía e indicadores de México."
    )

with col2:

    actualizar = st.button(
        "🔄 Actualizar noticias",
        use_container_width=True
    )


if actualizar:

    with st.spinner(
        "Analizando fuentes de inteligencia..."
    ):

        resultado = recolectar_noticias()

    if resultado.empty:

        st.error(
            "No se encontraron noticias relevantes."
        )

    else:

        st.success(
            f"Se analizaron "
            f"{len(resultado)} noticias relevantes."
        )

        st.cache_data.clear()

        st.rerun()


# ============================================================
# CARGAR INFORMACIÓN
# ============================================================

df = cargar_noticias()


# ============================================================
# SI TODAVÍA NO HAY DATOS
# ============================================================

if df.empty:

    st.warning(
        "Todavía no existen datos de inteligencia."
    )

    st.markdown(
        """
        ### Para comenzar

        Presiona **🔄 Actualizar noticias**.

        El Monitor consultará automáticamente las fuentes
        configuradas y construirá el análisis comercial.
        """
    )

    st.stop()


# ============================================================
# PANORAMA EJECUTIVO
# ============================================================

st.divider()

st.subheader(
    "📊 Panorama de hoy"
)


criticas = len(
    df[
        df["Relevancia"] == "CRÍTICA"
    ]
)

altas = len(
    df[
        df["Relevancia"] == "ALTA"
    ]
)

impactos_altos = len(
    df[
        df["Nivel Impacto"] == "ALTO"
    ]
)

total = len(df)


c1, c2, c3, c4 = st.columns(4)


with c1:

    st.metric(
        "🔴 Riesgos críticos",
        criticas
    )


with c2:

    st.metric(
        "🟠 Señales relevantes",
        altas
    )


with c3:

    st.metric(
        "📰 Noticias",
        total
    )


with c4:

    st.metric(
        "⚠️ Impactos altos",
        impactos_altos
    )


# ============================================================
# FILTROS
# ============================================================

st.divider()

st.subheader(
    "🔎 Explorar inteligencia"
)


f1, f2, f3 = st.columns(3)


with f1:

    categorias = [
        "Todas"
    ] + sorted(
        df["Categoría"]
        .dropna()
        .unique()
        .tolist()
    )

    categoria = st.selectbox(
        "Categoría",
        categorias
    )


with f2:

    filtro_rel = st.selectbox(
        "Relevancia",
        [
            "Todas",
            "CRÍTICA",
            "ALTA",
            "MEDIA",
            "BAJA"
        ]
    )


with f3:

    filtro_imp = st.selectbox(
        "Impacto",
        [
            "Todos",
            "ALTO",
            "MEDIO",
            "BAJO"
        ]
    )


df_vista = df.copy()


if categoria != "Todas":

    df_vista = df_vista[
        df_vista["Categoría"]
        == categoria
    ]


if filtro_rel != "Todas":

    df_vista = df_vista[
        df_vista["Relevancia"]
        == filtro_rel
    ]


if filtro_imp != "Todos":

    df_vista = df_vista[
        df_vista["Nivel Impacto"]
        == filtro_imp
    ]


# ============================================================
# 🎯 ¿QUÉ DEBO SABER HOY?
# ============================================================

st.divider()

st.subheader(
    "🎯 ¿Qué debo saber hoy?"
)


top3 = (
    df_vista
    .sort_values(
        "Score",
        ascending=False
    )
    .head(3)
)


if top3.empty:

    st.info(
        "No hay señales con los filtros seleccionados."
    )

else:

    for _, row in top3.iterrows():

        relevancia_actual = row[
            "Relevancia"
        ]

        if relevancia_actual == "CRÍTICA":
            icono = "🔴"

        elif relevancia_actual == "ALTA":
            icono = "🟠"

        elif relevancia_actual == "MEDIA":
            icono = "🟡"

        else:
            icono = "🟢"

        with st.container(
            border=True
        ):

            st.markdown(
                f"### {icono} {row['Título']}"
            )

            st.caption(
                f"{row['Categoría']} · "
                f"{row['Fecha']} · "
                f"Score {int(row['Score'])}/100"
            )

            a, b = st.columns(2)

            with a:

                st.markdown(
                    f"**Impacto Flexi**  \n"
                    f"{row['Impacto Flexi']}"
                )

            with b:

                st.markdown(
                    f"**KPI afectado**  \n"
                    f"🎯 {row['KPI Afectado']}"
                )

            st.info(
                f"🎯 **Acción recomendada:** "
                f"{row['Acción Sugerida']}"
            )


# ============================================================
# 🔴 RIESGOS
# ============================================================

st.divider()

st.subheader(
    "🔴 Riesgos prioritarios"
)


riesgos = (
    df_vista[
        df_vista["Nivel Impacto"]
        == "ALTO"
    ]
    .sort_values(
        "Score",
        ascending=False
    )
    .head(5)
)


if riesgos.empty:

    st.success(
        "No se detectaron riesgos de impacto alto."
    )

else:

    for _, row in riesgos.iterrows():

        with st.container(
            border=True
        ):

            st.markdown(
                f"**🔴 {row['Título']}**"
            )

            st.caption(
                f"{row['Categoría']} · "
                f"{row['Fecha']} · "
                f"Relevancia: {row['Relevancia']}"
            )

            st.markdown(
                f"""
                **Impacto:** {row['Impacto Flexi']}

                **KPI:** 🎯 {row['KPI Afectado']}

                **Acción:** {row['Acción Sugerida']}
                """
            )

            if row["Enlace"]:

                st.link_button(
                    "📰 Leer noticia original",
                    row["Enlace"]
                )


# ============================================================
# 🟢 OPORTUNIDADES
# ============================================================

st.divider()

st.subheader(
    "🟢 Oportunidades"
)


oportunidades = (
    df_vista[
        df_vista["Relevancia"]
        .isin(
            ["CRÍTICA", "ALTA"]
        )
    ]
    .sort_values(
        "Score",
        ascending=False
    )
    .head(5)
)


if oportunidades.empty:

    st.info(
        "No se identificaron oportunidades "
        "relevantes en este corte."
    )

else:

    for _, row in oportunidades.iterrows():

        with st.container(
            border=True
        ):

            st.markdown(
                f"**🟢 {row['Título']}**"
            )

            st.caption(
                f"{row['Categoría']} · "
                f"{row['Fecha']}"
            )

            st.markdown(
                f"""
                **Señal:** {row['Impacto Flexi']}

                **KPI:** 🎯 {row['KPI Afectado']}

                **Qué hacer:** {row['Acción Sugerida']}
                """
            )

            if row["Enlace"]:

                st.link_button(
                    "📰 Leer noticia",
                    row["Enlace"]
                )


# ============================================================
# 📰 MONITOR DE NOTICIAS
# ============================================================

st.divider()

st.subheader(
    "📰 Monitor de noticias"
)


st.caption(
    f"{len(df_vista)} noticias encontradas."
)


for _, row in df_vista.iterrows():

    if row["Relevancia"] == "CRÍTICA":
        icono = "🔴"

    elif row["Relevancia"] == "ALTA":
        icono = "🟠"

    elif row["Relevancia"] == "MEDIA":
        icono = "🟡"

    else:
        icono = "🟢"

    with st.expander(
        f"{icono} {row['Título']}"
    ):

        a, b, c, d = st.columns(4)

        with a:

            st.metric(
                "Relevancia",
                row["Relevancia"]
            )

        with b:

            st.metric(
                "Score",
                f"{int(row['Score'])}/100"
            )

        with c:

            st.metric(
                "Impacto",
                row["Nivel Impacto"]
            )

        with d:

            st.metric(
                "KPI",
                row["KPI Afectado"]
            )

        st.divider()

        st.markdown(
            f"**Categoría:** {row['Categoría']}"
        )

        st.markdown(
            f"**Fecha:** {row['Fecha']}"
        )

        st.markdown(
            f"**Impacto para Flexi:** "
            f"{row['Impacto Flexi']}"
        )

        st.info(
            f"🎯 **Acción recomendada:** "
            f"{row['Acción Sugerida']}"
        )

        if row["Enlace"]:

            st.link_button(
                "📰 Leer noticia original",
                row["Enlace"]
            )


# ============================================================
# 📊 EXPOSICIÓN DE KPIs
# ============================================================

st.divider()

st.subheader(
    "📊 ¿Qué KPI está más expuesto?"
)


def contar_kpi(texto):

    return int(
        df_vista["KPI Afectado"]
        .astype(str)
        .str.contains(
            texto,
            case=False,
            na=False
        )
        .sum()
    )


kpi_conversion = contar_kpi(
    "Conversión"
)

kpi_ticket = contar_kpi(
    "Ticket"
)

kpi_quiebres = contar_kpi(
    "Quiebres"
)

kpi_estrategico = contar_kpi(
    "Estratégico"
)


a, b, c, d = st.columns(4)


with a:

    st.metric(
        "🎯 Conversión",
        kpi_conversion
    )


with b:

    st.metric(
        "👟 Ticket",
        kpi_ticket
    )


with c:

    st.metric(
        "📦 Quiebres",
        kpi_quiebres
    )


with d:

    st.metric(
        "♟ Estratégico",
        kpi_estrategico
    )


# ============================================================
# 🎯 METAS FLEXI
# ============================================================

st.divider()

st.subheader(
    "🎯 Metas comerciales de referencia"
)


a, b = st.columns(2)


with a:

    st.metric(
        "Conversión objetivo",
        f"{META_CONVERSION:.1f}%"
    )


with b:

    st.metric(
        "Ticket objetivo",
        f"{META_TICKET:.2f}"
    )


st.caption(
    "Las señales externas son un insumo de inteligencia. "
    "Su impacto debe contrastarse con los resultados reales "
    "de Zona Occidente."
)
