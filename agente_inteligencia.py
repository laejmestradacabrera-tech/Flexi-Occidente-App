# ============================================================
# 🧠 INTELIGENCIA COMERCIAL FLEXI
# VERSIÓN SEGURA - NO ALTERA ARCHIVOS NI OTRAS PESTAÑAS
# ============================================================

import os
import re
import hashlib
from datetime import datetime

import pandas as pd
import streamlit as st
import requests
import feedparser


# ============================================================
# CONFIGURACIÓN
# ============================================================

ARCHIVO_INTELIGENCIA = "datos_inteligencia.csv"

META_CONVERSION = 10.9
META_TICKET = 1.29

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/126.0 Safari/537.36"
)


# ============================================================
# FUENTES DE INTELIGENCIA
# ============================================================

FUENTES_INTELIGENCIA = {

    "Mercado de Calzado": {
        "url": "https://wwd.com/footwear-news/feed/",
        "tipo": "Calzado",
        "max": 8
    },

    "Retail Dive": {
        "url": "https://www.retaildive.com/feeds/news/",
        "tipo": "Retail",
        "max": 8
    },

    "Supply Chain Dive": {
        "url": "https://www.supplychaindive.com/feeds/news/",
        "tipo": "Supply Chain",
        "max": 8
    },

    "El Economista": {
        "url": "https://www.eleconomista.com.mx/rss/empresas/",
        "tipo": "Macroeconomía",
        "max": 8
    },

    "INEGI": {
        "url": "https://www.inegi.org.mx/rss/noticias.xml",
        "tipo": "INEGI",
        "max": 8
    }
}


# ============================================================
# PALABRAS CLAVE
# ============================================================

CLAVES_CALZADO = [
    "shoe",
    "shoes",
    "footwear",
    "calzado",
    "zapato",
    "zapatos",
    "sneaker",
    "sneakers",
    "boots",
    "botas",
    "zapatería",
    "zapateria",
    "leather",
    "piel",
    "suela"
]


CLAVES_RETAIL = [
    "retail",
    "store",
    "stores",
    "tienda",
    "tiendas",
    "sales",
    "ventas",
    "consumer",
    "consumidor",
    "shopping mall",
    "mall",
    "shopping center",
    "centro comercial",
    "plaza",
    "traffic",
    "foot traffic",
    "afluencia",
    "opening",
    "apertura",
    "closure",
    "cierre",
    "expansion",
    "expansión"
]


CLAVES_SUPPLY = [
    "supply chain",
    "logistics",
    "logística",
    "inventario",
    "inventory",
    "stock",
    "shortage",
    "quiebre",
    "quiebres",
    "warehouse",
    "almacén",
    "distribution",
    "distribución",
    "shipping",
    "freight",
    "transport",
    "transporte"
]


CLAVES_MACRO = [
    "inflación",
    "inflation",
    "pib",
    "gdp",
    "consumidor",
    "consumer",
    "consumo",
    "consumption",
    "tasas",
    "interest",
    "interés",
    "economía",
    "economy",
    "empleo",
    "employment",
    "desempleo",
    "unemployment",
    "ventas",
    "sales",
    "comercio",
    "commerce",
    "precio",
    "prices",
    "poder adquisitivo",
    "banco de méxico",
    "banxico",
    "confianza del consumidor",
    "ingreso",
    "income",
    "salario",
    "salarios"
]


CLAVES_MEXICO = [
    "méxico",
    "mexico",
    "mexican",
    "mexicana",
    "mexicanos",
    "banxico",
    "banco de méxico",
    "inegi",
    "peso mexicano",
    "consumo interno"
]


CLAVES_COMPETENCIA = [
    "nike",
    "adidas",
    "puma",
    "skechers",
    "new balance",
    "clarks",
    "aldo",
    "flexi"
]


PALABRAS_EXCLUIR = [
    "makeup",
    "beauty",
    "cosmetics",
    "maquillaje",
    "belleza",
    "grocery",
    "supermarket",
    "food",
    "comida",
    "ulta",
    "dollar general",
    "beverage",
    "skincare",
    "kroger",
    "farmacia",
    "cvs",
    "walgreens"
]


# ============================================================
# FUNCIONES DE TEXTO
# ============================================================

def limpiar_texto(texto):

    if texto is None:
        return ""

    texto = str(texto)

    texto = re.sub(
        r"<[^>]*>",
        " ",
        texto
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto.lower().strip()


def contiene(texto, palabras):

    texto = limpiar_texto(texto)

    return any(
        palabra.lower() in texto
        for palabra in palabras
    )


def generar_id(titulo, enlace):

    contenido = (
        str(titulo).strip().lower()
        + "|"
        + str(enlace).strip().lower()
    )

    return hashlib.md5(
        contenido.encode("utf-8")
    ).hexdigest()


# ============================================================
# SCORE DE INTELIGENCIA
# ============================================================

def calcular_score(texto, tipo):

    score = 0

    if contiene(texto, CLAVES_CALZADO):
        score += 30

    if contiene(texto, CLAVES_RETAIL):
        score += 20

    if contiene(texto, CLAVES_SUPPLY):
        score += 15

    if contiene(texto, CLAVES_MACRO):
        score += 15

    if contiene(texto, CLAVES_MEXICO):
        score += 20

    if contiene(texto, CLAVES_COMPETENCIA):
        score += 15

    if tipo == "INEGI":
        score += 10

    if tipo == "Macroeconomía":
        score += 5

    if contiene(texto, PALABRAS_EXCLUIR):
        score -= 40

    return max(
        0,
        min(score, 100)
    )


def determinar_relevancia(score):

    if score >= 80:
        return "CRÍTICA"

    if score >= 60:
        return "ALTA"

    if score >= 40:
        return "MEDIA"

    return "BAJA"


# ============================================================
# ANÁLISIS COMERCIAL
# ============================================================

def analizar_impacto(texto):

    texto = limpiar_texto(texto)

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
            "consumer",
            "poder adquisitivo"
        ]
    ):

        return {
            "impacto": (
                "Puede modificar la disposición de compra "
                "y la sensibilidad al precio."
            ),
            "kpi": "Ticket / Conversión",
            "nivel": "ALTO",
            "accion": (
                "Reforzar la venta de segundo par, "
                "CREDICLUB y las diferentes opciones de pago."
            )
        }

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
            "income",
            "salario",
            "salarios"
        ]
    ):

        return {
            "impacto": (
                "Puede modificar la capacidad de compra "
                "del consumidor."
            ),
            "kpi": "Conversión",
            "nivel": "MEDIO",
            "accion": (
                "Fortalecer el argumento de valor, "
                "calidad, comodidad y alternativas de pago."
            )
        }

    # --------------------------------------------
    # CENTROS COMERCIALES / AFLUENCIA
    # --------------------------------------------

    if contiene(
        texto,
        [
            "mall",
            "shopping mall",
            "shopping center",
            "centro comercial",
            "plaza",
            "traffic",
            "foot traffic",
            "afluencia"
        ]
    ):

        return {
            "impacto": (
                "Puede afectar la afluencia y el número "
                "de oportunidades de venta."
            ),
            "kpi": "Conversión",
            "nivel": "ALTO",
            "accion": (
                "Maximizar cada oportunidad mediante "
                "abordaje inmediato y ejecución de "
                "Ruta del Cliente."
            )
        }

    # --------------------------------------------
    # INVENTARIO / SUPPLY CHAIN
    # --------------------------------------------

    if contiene(
        texto,
        [
            "supply chain",
            "inventario",
            "inventory",
            "stock",
            "shortage",
            "quiebre",
            "warehouse",
            "distribution"
        ]
    ):

        return {
            "impacto": (
                "Puede incrementar el riesgo de faltantes "
                "o retrasos de producto."
            ),
            "kpi": "Quiebres / Ticket",
            "nivel": "ALTO",
            "accion": (
                "Revisar existencia, tallas críticas "
                "y ejecutar nivelación de inventario."
            )
        }

    # --------------------------------------------
    # COMPETENCIA
    # --------------------------------------------

    if contiene(
        texto,
        CLAVES_COMPETENCIA
    ):

        return {
            "impacto": (
                "Movimiento competitivo que puede modificar "
                "la decisión del consumidor."
            ),
            "kpi": "Conversión / Ticket",
            "nivel": "MEDIO",
            "accion": (
                "Reforzar propuesta de valor, producto, "
                "servicio y cierre de venta."
            )
        }

    # --------------------------------------------
    # DEFAULT
    # --------------------------------------------

    return {
        "impacto": (
            "Señal de contexto que debe mantenerse "
            "bajo seguimiento."
        ),
        "kpi": "Estratégico",
        "nivel": "BAJO",
        "accion": (
            "Dar seguimiento y validar si la tendencia "
            "se refleja en los indicadores comerciales."
        )
    }


# ============================================================
# FECHA
# ============================================================

def obtener_fecha(entry):

    try:

        fecha = getattr(
            entry,
            "published_parsed",
            None
        )

        if fecha:

            fecha_obj = datetime(
                *fecha[:6]
            )

            return fecha_obj.strftime(
                "%Y-%m-%d"
            )

    except Exception:
        pass

    try:

        fecha = getattr(
            entry,
            "updated_parsed",
            None
        )

        if fecha:

            fecha_obj = datetime(
                *fecha[:6]
            )

            return fecha_obj.strftime(
                "%Y-%m-%d"
            )

    except Exception:
        pass

    return datetime.now().strftime(
        "%Y-%m-%d"
    )


# ============================================================
# LEER RSS DE FORMA SEGURA
# ============================================================

def leer_fuente(url):

    try:

        respuesta = requests.get(
            url,
            headers={
                "User-Agent": USER_AGENT
            },
            timeout=15
        )

        if respuesta.status_code != 200:

            return None

        return feedparser.parse(
            respuesta.content
        )

    except Exception:

        return None


# ============================================================
# RECOLECTOR
# ============================================================

def recolectar_noticias():

    datos = []

    errores = []

    for nombre, fuente in FUENTES_INTELIGENCIA.items():

        feed = leer_fuente(
            fuente["url"]
        )

        if feed is None:

            errores.append(
                nombre
            )

            continue

        contador = 0

        for entry in feed.entries:

            titulo = getattr(
                entry,
                "title",
                ""
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

            # ------------------------------------
            # EXCLUSIÓN
            # ------------------------------------

            if contiene(
                texto,
                PALABRAS_EXCLUIR
            ):

                continue

            # ------------------------------------
            # SCORE
            # ------------------------------------

            score = calcular_score(
                texto,
                fuente["tipo"]
            )

            if score < 30:

                continue

            # ------------------------------------
            # IMPACTO
            # ------------------------------------

            impacto = analizar_impacto(
                texto
            )

            # ------------------------------------
            # REGISTRO
            # ------------------------------------

            datos.append({

                "ID":
                    generar_id(
                        titulo,
                        enlace
                    ),

                "Categoría":
                    nombre,

                "Tipo Fuente":
                    fuente["tipo"],

                "Título":
                    str(titulo).strip(),

                "Resumen":
                    limpiar_texto(
                        resumen
                    ),

                "Fecha":
                    obtener_fecha(
                        entry
                    ),

                "Relevancia":
                    determinar_relevancia(
                        score
                    ),

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

            if contador >= fuente["max"]:

                break

    # ========================================================
    # DATAFRAME
    # ========================================================

    if not datos:

        return pd.DataFrame(), errores

    df_nuevo = pd.DataFrame(
        datos
    )

    # Eliminar duplicados
    df_nuevo = (
        df_nuevo
        .drop_duplicates(
            subset=["ID"]
        )
    )

    # Ordenar
    df_nuevo = (
        df_nuevo
        .sort_values(
            by=["Score", "Fecha"],
            ascending=[False, False]
        )
        .reset_index(
            drop=True
        )
    )

    return df_nuevo, errores


# ============================================================
# CARGAR DATOS EXISTENTES
# ============================================================

def cargar_archivo_inteligencia():

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

        if "Score" in df.columns:

            df["Score"] = pd.to_numeric(
                df["Score"],
                errors="coerce"
            ).fillna(0)

        return df

    except Exception:

        return pd.DataFrame()


# ============================================================
# INICIALIZAR SESSION STATE
#
# IMPORTANTE:
# SOLO usamos una variable exclusiva de esta pestaña.
# No limpiamos ni modificamos ninguna otra.
# ============================================================

if "inteligencia_comercial_df" not in st.session_state:

    st.session_state[
        "inteligencia_comercial_df"
    ] = cargar_archivo_inteligencia()


# ============================================================
# TÍTULO
# ============================================================

st.title(
    "🧠 Inteligencia Comercial"
)

st.caption(
    "Señales externas para anticipar riesgos, "
    "oportunidades y decisiones comerciales de Flexi."
)


# ============================================================
# PANEL SUPERIOR
# ============================================================

col_info, col_boton = st.columns(
    [4, 1]
)


with col_info:

    st.info(
        "Analiza calzado, retail, centros comerciales, "
        "supply chain, macroeconomía e indicadores oficiales "
        "de México."
    )


with col_boton:

    actualizar = st.button(
        "🔄 Actualizar noticias",
        use_container_width=True,
        key="btn_actualizar_inteligencia"
    )


# ============================================================
# ACTUALIZAR
#
# NO HAY:
# st.rerun()
# st.cache_data.clear()
# limpieza de session_state
# eliminación de archivos
#
# SOLO actualiza inteligencia_comercial_df
# ============================================================

if actualizar:

    with st.spinner(
        "Consultando fuentes de inteligencia..."
    ):

        df_nuevo, errores = (
            recolectar_noticias()
        )

    if df_nuevo.empty:

        st.error(
            "No fue posible obtener noticias relevantes "
            "en este momento."
        )

        if errores:

            st.caption(
                "Fuentes sin respuesta: "
                + ", ".join(errores)
            )

    else:

        # Guardamos SOLO esta información
        st.session_state[
            "inteligencia_comercial_df"
        ] = df_nuevo.copy()

        # Guardamos SOLO el archivo de inteligencia
        try:

            df_nuevo.to_csv(
                ARCHIVO_INTELIGENCIA,
                index=False,
                encoding="utf-8-sig"
            )

        except Exception as e:

            st.warning(
                "Las noticias se cargaron correctamente, "
                "pero no fue posible guardar el archivo local: "
                f"{e}"
            )

        st.success(
            f"✅ Inteligencia actualizada: "
            f"{len(df_nuevo)} noticias relevantes."
        )

        if errores:

            st.caption(
                "Algunas fuentes no respondieron: "
                + ", ".join(errores)
            )


# ============================================================
# RECUPERAR DATOS
# ============================================================

df = st.session_state[
    "inteligencia_comercial_df"
].copy()


# ============================================================
# SIN INFORMACIÓN
# ============================================================

if df.empty:

    st.warning(
        "Todavía no existen datos de inteligencia."
    )

    st.markdown(
        """
        ### Para comenzar

        Presiona **🔄 Actualizar noticias**.

        La pestaña consultará las fuentes configuradas,
        filtrará la información relevante y construirá
        el análisis comercial.

        **Esta acción no modifica tus archivos adjuntos
        ni las demás pestañas del Monitor.**
        """
    )

    st.stop()


# ============================================================
# NORMALIZAR COLUMNAS
# ============================================================

columnas_esperadas = [
    "Categoría",
    "Título",
    "Fecha",
    "Relevancia",
    "Score",
    "Impacto Flexi",
    "KPI Afectado",
    "Nivel Impacto",
    "Acción Sugerida",
    "Enlace"
]


for columna in columnas_esperadas:

    if columna not in df.columns:

        df[columna] = ""


# ============================================================
# PANORAMA
# ============================================================

st.divider()

st.subheader(
    "📊 Panorama de hoy"
)


criticas = len(
    df[
        df["Relevancia"]
        .astype(str)
        .str.upper()
        == "CRÍTICA"
    ]
)


altas = len(
    df[
        df["Relevancia"]
        .astype(str)
        .str.upper()
        == "ALTA"
    ]
)


impactos_altos = len(
    df[
        df["Nivel Impacto"]
        .astype(str)
        .str.upper()
        == "ALTO"
    ]
)


total_noticias = len(df)


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
        total_noticias
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
    ]

    categorias += sorted(
        [
            str(x)
            for x in
            df["Categoría"]
            .dropna()
            .unique()
            if str(x).strip()
        ]
    )

    filtro_categoria = st.selectbox(
        "Categoría",
        categorias,
        key="intel_filtro_categoria"
    )


with f2:

    filtro_relevancia = st.selectbox(
        "Relevancia",
        [
            "Todas",
            "CRÍTICA",
            "ALTA",
            "MEDIA",
            "BAJA"
        ],
        key="intel_filtro_relevancia"
    )


with f3:

    filtro_impacto = st.selectbox(
        "Impacto",
        [
            "Todos",
            "ALTO",
            "MEDIO",
            "BAJO"
        ],
        key="intel_filtro_impacto"
    )


df_vista = df.copy()


if filtro_categoria != "Todas":

    df_vista = df_vista[
        df_vista["Categoría"]
        == filtro_categoria
    ]


if filtro_relevancia != "Todas":

    df_vista = df_vista[
        df_vista["Relevancia"]
        .astype(str)
        .str.upper()
        == filtro_relevancia
    ]


if filtro_impacto != "Todos":

    df_vista = df_vista[
        df_vista["Nivel Impacto"]
        .astype(str)
        .str.upper()
        == filtro_impacto
    ]


# ============================================================
# 🎯 QUÉ DEBO SABER HOY
# ============================================================

st.divider()

st.subheader(
    "🎯 ¿Qué debo saber hoy?"
)


top3 = (
    df_vista
    .sort_values(
        by="Score",
        ascending=False
    )
    .head(3)
)


if top3.empty:

    st.info(
        "No existen señales para los filtros seleccionados."
    )

else:

    for _, row in top3.iterrows():

        relevancia = (
            str(row["Relevancia"])
            .upper()
        )

        if relevancia == "CRÍTICA":

            icono = "🔴"

        elif relevancia == "ALTA":

            icono = "🟠"

        elif relevancia == "MEDIA":

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
                    f"**Impacto para Flexi**\n\n"
                    f"{row['Impacto Flexi']}"
                )

            with b:

                st.markdown(
                    f"**KPI relacionado**\n\n"
                    f"🎯 {row['KPI Afectado']}"
                )

            st.info(
                f"🎯 **Acción recomendada:** "
                f"{row['Acción Sugerida']}"
            )

            if str(row["Enlace"]).strip():

                st.link_button(
                    "📰 Leer noticia",
                    str(row["Enlace"])
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
        .astype(str)
        .str.upper()
        == "ALTO"
    ]
    .sort_values(
        by="Score",
        ascending=False
    )
    .head(5)
)


if riesgos.empty:

    st.success(
        "No se detectaron riesgos de impacto alto "
        "con los filtros actuales."
    )

else:

    for _, row in riesgos.iterrows():

        with st.container(
            border=True
        ):

            st.markdown(
                f"### 🔴 {row['Título']}"
            )

            st.caption(
                f"{row['Categoría']} · "
                f"{row['Fecha']} · "
                f"Relevancia: {row['Relevancia']}"
            )

            c1, c2, c3 = st.columns(3)

            with c1:

                st.markdown(
                    f"**Impacto**\n\n"
                    f"{row['Impacto Flexi']}"
                )

            with c2:

                st.markdown(
                    f"**KPI**\n\n"
                    f"🎯 {row['KPI Afectado']}"
                )

            with c3:

                st.markdown(
                    f"**Nivel**\n\n"
                    f"🔴 {row['Nivel Impacto']}"
                )

            st.warning(
                f"🎯 **Acción:** "
                f"{row['Acción Sugerida']}"
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
        .astype(str)
        .str.upper()
        .isin(
            [
                "CRÍTICA",
                "ALTA"
            ]
        )
    ]
    .sort_values(
        by="Score",
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
                f"### 🟢 {row['Título']}"
            )

            st.caption(
                f"{row['Categoría']} · "
                f"{row['Fecha']}"
            )

            st.markdown(
                f"""
                **Señal:**  
                {row['Impacto Flexi']}

                **KPI relacionado:**  
                🎯 {row['KPI Afectado']}

                **Acción recomendada:**  
                {row['Acción Sugerida']}
                """
            )


# ============================================================
# 📰 MONITOR COMPLETO DE NOTICIAS
# ============================================================

st.divider()

st.subheader(
    "📰 Monitor de noticias"
)


st.caption(
    f"Mostrando {len(df_vista)} noticias."
)


for _, row in df_vista.iterrows():

    relevancia = (
        str(row["Relevancia"])
        .upper()
    )

    if relevancia == "CRÍTICA":

        icono = "🔴"

    elif relevancia == "ALTA":

        icono = "🟠"

    elif relevancia == "MEDIA":

        icono = "🟡"

    else:

        icono = "🟢"


    with st.expander(
        f"{icono} {row['Título']}"
    ):

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            st.metric(
                "Relevancia",
                relevancia
            )

        with c2:

            st.metric(
                "Score",
                int(row["Score"])
            )

        with c3:

            st.metric(
                "Impacto",
                row["Nivel Impacto"]
            )

        with c4:

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

        # Mostrar resumen si existe
        resumen = str(
            row.get(
                "Resumen",
                ""
            )
        ).strip()

        if resumen:

            st.markdown(
                f"**Resumen:**  \n{resumen}"
            )

        st.info(
            f"🎯 **Acción recomendada:** "
            f"{row['Acción Sugerida']}"
        )

        enlace = str(
            row["Enlace"]
        ).strip()

        if enlace:

            st.link_button(
                "📰 Leer noticia original",
                enlace
            )


# ============================================================
# 📊 EXPOSICIÓN POR KPI
# ============================================================

st.divider()

st.subheader(
    "📊 ¿Qué KPI está más expuesto?"
)


def contar_kpi(texto):

    return int(
        df_vista[
            "KPI Afectado"
        ]
        .astype(str)
        .str.contains(
            texto,
            case=False,
            na=False
        )
        .sum()
    )


conversion = contar_kpi(
    "Conversión"
)

ticket = contar_kpi(
    "Ticket"
)

quiebres = contar_kpi(
    "Quiebres"
)

estrategico = contar_kpi(
    "Estratégico"
)


c1, c2, c3, c4 = st.columns(4)


with c1:

    st.metric(
        "🎯 Conversión",
        conversion
    )


with c2:

    st.metric(
        "👟 Ticket",
        ticket
    )


with c3:

    st.metric(
        "📦 Quiebres",
        quiebres
    )


with c4:

    st.metric(
        "♟ Estratégico",
        estrategico
    )


# ============================================================
# 🎯 REFERENCIA COMERCIAL
# ============================================================

st.divider()

st.subheader(
    "🎯 Referencia comercial"
)


c1, c2 = st.columns(2)


with c1:

    st.metric(
        "Conversión objetivo",
        f"{META_CONVERSION:.1f}%"
    )


with c2:

    st.metric(
        "Ticket objetivo",
        f"{META_TICKET:.2f}"
    )


st.caption(
    "La inteligencia comercial funciona como sistema "
    "de alerta temprana. Las señales externas deben "
    "contrastarse con los resultados reales de las tiendas."
)
