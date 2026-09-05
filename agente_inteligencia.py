# ============================================================
# 🧠 INTELIGENCIA COMERCIAL
# ============================================================

import streamlit as st
import pandas as pd
from datetime import datetime
import html


# ============================================================
# CONFIGURACIÓN
# ============================================================

ARCHIVO_INTELIGENCIA = "datos_inteligencia.csv"

META_CONVERSION = 10.9
META_TICKET = 1.29


# ============================================================
# CARGA DE INFORMACIÓN
# ============================================================

@st.cache_data(ttl=900)
def cargar_inteligencia():

    try:

        df = pd.read_csv(
            ARCHIVO_INTELIGENCIA,
            encoding="utf-8-sig"
        )

        if df.empty:
            return pd.DataFrame()

        # Convertir score a número
        if "Score" in df.columns:
            df["Score"] = pd.to_numeric(
                df["Score"],
                errors="coerce"
            ).fillna(0)

        # Convertir fecha
        if "Fecha" in df.columns:
            df["Fecha_dt"] = pd.to_datetime(
                df["Fecha"],
                errors="coerce"
            )

        return df

    except FileNotFoundError:

        return pd.DataFrame()

    except Exception as e:

        st.error(
            f"Error cargando inteligencia comercial: {e}"
        )

        return pd.DataFrame()


df_intel = cargar_inteligencia()


# ============================================================
# ENCABEZADO
# ============================================================

st.markdown(
    """
    <div style="
        background: linear-gradient(
            90deg,
            #E30613 0%,
            #B0000B 100%
        );
        padding: 22px 28px;
        border-radius: 12px;
        margin-bottom: 20px;
        color: white;
    ">

        <div style="
            font-size: 30px;
            font-weight: 800;
        ">
            🧠 INTELIGENCIA COMERCIAL
        </div>

        <div style="
            font-size: 15px;
            margin-top: 6px;
            opacity: 0.95;
        ">
            Señales externas que pueden impactar el desempeño
            comercial de Flexi.
        </div>

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SIN INFORMACIÓN
# ============================================================

if df_intel.empty:

    st.warning(
        "No existen noticias disponibles. "
        "Ejecuta primero el agente de recolección."
    )

    st.stop()


# ============================================================
# FECHA DE ACTUALIZACIÓN
# ============================================================

ultima_actualizacion = "Sin información"

if "Última Actualización" in df_intel.columns:

    valores_fecha = (
        df_intel["Última Actualización"]
        .dropna()
        .astype(str)
    )

    if len(valores_fecha) > 0:
        ultima_actualizacion = valores_fecha.iloc[-1]


st.caption(
    f"Última actualización: {ultima_actualizacion}"
)


# ============================================================
# KPIs EJECUTIVOS
# ============================================================

criticas = len(
    df_intel[
        df_intel["Relevancia"] == "CRÍTICA"
    ]
)

altas = len(
    df_intel[
        df_intel["Relevancia"] == "ALTA"
    ]
)

senales = len(df_intel)

impacto_alto = len(
    df_intel[
        df_intel["Nivel Impacto"] == "ALTO"
    ]
)


c1, c2, c3, c4 = st.columns(4)


with c1:

    st.metric(
        "🔴 Riesgos críticos",
        criticas
    )


with c2:

    st.metric(
        "🟠 Señales de alta relevancia",
        altas
    )


with c3:

    st.metric(
        "📰 Noticias analizadas",
        senales
    )


with c4:

    st.metric(
        "⚠️ Impactos altos",
        impacto_alto
    )


st.markdown("---")


# ============================================================
# FILTROS
# ============================================================

st.markdown(
    "### 🔎 Explorar inteligencia"
)


f1, f2, f3 = st.columns(3)


with f1:

    categorias = [
        "Todas"
    ] + sorted(
        df_intel["Categoría"]
        .dropna()
        .unique()
        .tolist()
    )

    filtro_categoria = st.selectbox(
        "Categoría",
        categorias
    )


with f2:

    relevancias = [
        "Todas",
        "CRÍTICA",
        "ALTA",
        "MEDIA",
        "BAJA"
    ]

    filtro_relevancia = st.selectbox(
        "Relevancia",
        relevancias
    )


with f3:

    impactos = [
        "Todos",
        "ALTO",
        "MEDIO",
        "BAJO"
    ]

    filtro_impacto = st.selectbox(
        "Nivel de impacto",
        impactos
    )


df_filtrado = df_intel.copy()


if filtro_categoria != "Todas":

    df_filtrado = df_filtrado[
        df_filtrado["Categoría"]
        == filtro_categoria
    ]


if filtro_relevancia != "Todas":

    df_filtrado = df_filtrado[
        df_filtrado["Relevancia"]
        == filtro_relevancia
    ]


if filtro_impacto != "Todos":

    df_filtrado = df_filtrado[
        df_filtrado["Nivel Impacto"]
        == filtro_impacto
    ]


# ============================================================
# 🎯 ¿QUÉ DEBO SABER HOY?
# ============================================================

st.markdown("---")

st.markdown(
    """
    <div style="
        font-size: 24px;
        font-weight: 800;
        margin-bottom: 12px;
    ">
        🎯 ¿QUÉ DEBO SABER HOY?
    </div>
    """,
    unsafe_allow_html=True
)


top_hoy = (
    df_filtrado
    .sort_values(
        "Score",
        ascending=False
    )
    .head(3)
)


if top_hoy.empty:

    st.info(
        "No hay señales que coincidan con los filtros seleccionados."
    )

else:

    for _, row in top_hoy.iterrows():

        relevancia = row.get(
            "Relevancia",
            "MEDIA"
        )

        if relevancia == "CRÍTICA":
            color = "#E30613"
            icono = "🔴"

        elif relevancia == "ALTA":
            color = "#F28C28"
            icono = "🟠"

        elif relevancia == "MEDIA":
            color = "#D6A700"
            icono = "🟡"

        else:
            color = "#4A9B68"
            icono = "🟢"


        st.markdown(
            f"""
            <div style="
                border-left: 6px solid {color};
                padding: 15px 18px;
                margin-bottom: 12px;
                background: #F8F8F8;
                border-radius: 8px;
            ">

                <div style="
                    font-size: 12px;
                    color: {color};
                    font-weight: 800;
                ">
                    {icono} {relevancia}
                    &nbsp; | &nbsp;
                    SCORE {int(row["Score"])}
                </div>

                <div style="
                    font-size: 18px;
                    font-weight: 800;
                    margin-top: 5px;
                ">
                    {html.escape(str(row["Título"]))}
                </div>

                <div style="
                    margin-top: 8px;
                    font-size: 14px;
                ">
                    <b>Impacto Flexi:</b>
                    {html.escape(str(row["Impacto Flexi"]))}
                    <br>

                    <b>KPI afectado:</b>
                    {html.escape(str(row["KPI Afectado"]))}
                    <br>

                    <b>Nivel:</b>
                    {html.escape(str(row["Nivel Impacto"]))}
                </div>

                <div style="
                    margin-top: 10px;
                    padding: 10px;
                    background: white;
                    border-radius: 6px;
                ">
                    <b>🎯 Acción recomendada:</b><br>
                    {html.escape(str(row["Acción Sugerida"]))}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# 🔴 RIESGOS
# ============================================================

st.markdown("---")

st.markdown(
    "### 🔴 Riesgos para la operación"
)


riesgos = (
    df_filtrado[
        df_filtrado["Nivel Impacto"] == "ALTO"
    ]
    .sort_values(
        "Score",
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
                f"**{row['Título']}**"
            )

            st.caption(
                f"{row['Categoría']} · "
                f"{row['Fecha']}"
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                st.markdown(
                    f"**Impacto**  \n"
                    f"🔴 {row['Impacto Flexi']}"
                )

            with col2:

                st.markdown(
                    f"**KPI**  \n"
                    f"🎯 {row['KPI Afectado']}"
                )

            with col3:

                st.markdown(
                    f"**Relevancia**  \n"
                    f"{row['Relevancia']} ({int(row['Score'])})"
                )

            st.markdown(
                f"**Acción:** {row['Acción Sugerida']}"
            )


# ============================================================
# 🟢 OPORTUNIDADES
# ============================================================

st.markdown("---")

st.markdown(
    "### 🟢 Oportunidades"
)


oportunidades = df_filtrado[
    (
        df_filtrado["Relevancia"]
        .isin(["CRÍTICA", "ALTA"])
    )
]


oportunidades = (
    oportunidades
    .sort_values(
        "Score",
        ascending=False
    )
    .head(5)
)


if oportunidades.empty:

    st.info(
        "No se identificaron oportunidades relevantes "
        "con los filtros actuales."
    )

else:

    for _, row in oportunidades.iterrows():

        with st.container(
            border=True
        ):

            st.markdown(
                f"**{row['Título']}**"
            )

            st.markdown(
                f"""
                🟢 **Oportunidad:** {row['Impacto Flexi']}
                
                **KPI:** {row['KPI Afectado']}
                
                **Acción recomendada:** {row['Acción Sugerida']}
                """
            )


# ============================================================
# 📰 TODAS LAS NOTICIAS
# ============================================================

st.markdown("---")

st.markdown(
    "### 📰 Noticias relevantes"
)


if df_filtrado.empty:

    st.info(
        "No hay noticias para los filtros seleccionados."
    )

else:

    for indice, row in df_filtrado.iterrows():

        titulo = str(
            row.get(
                "Título",
                "Sin título"
            )
        )

        relevancia = str(
            row.get(
                "Relevancia",
                "MEDIA"
            )
        )

        score = int(
            row.get(
                "Score",
                0
            )
        )

        categoria = str(
            row.get(
                "Categoría",
                ""
            )
        )

        fecha = str(
            row.get(
                "Fecha",
                ""
            )
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
            f"{icono} {titulo}"
        ):

            col1, col2, col3 = st.columns(3)


            with col1:

                st.markdown(
                    f"**Relevancia**  \n"
                    f"{relevancia}"
                )


            with col2:

                st.markdown(
                    f"**Score**  \n"
                    f"{score}/100"
                )


            with col3:

                st.markdown(
                    f"**Fecha**  \n"
                    f"{fecha}"
                )


            st.markdown("---")


            st.markdown(
                f"""
                **Categoría:** {categoria}

                **Impacto Flexi:**  
                {row.get("Impacto Flexi", "Sin análisis")}

                **KPI afectado:**  
                🎯 {row.get("KPI Afectado", "No identificado")}

                **Nivel de impacto:**  
                {row.get("Nivel Impacto", "No identificado")}

                **🎯 Acción recomendada:**  
                {row.get("Acción Sugerida", "Sin recomendación")}
                """
            )


            enlace = row.get(
                "Enlace",
                ""
            )


            if pd.notna(enlace) and enlace:

                st.link_button(
                    "📰 Leer noticia original",
                    enlace
                )


# ============================================================
# 📊 RELACIÓN CON KPIs FLEXI
# ============================================================

st.markdown("---")

st.markdown(
    "### 📊 Señales externas y KPIs Flexi"
)


kpis = {}


for kpi in [
    "Conversión",
    "Ticket",
    "Conversión / Ticket",
    "Quiebres / Ticket",
    "Estratégico"
]:

    kpis[kpi] = len(
        df_filtrado[
            df_filtrado["KPI Afectado"]
            .astype(str)
            .str.contains(
                kpi,
                case=False,
                na=False
            )
        ]
    )


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "🎯 Conversión",
        kpis.get(
            "Conversión",
            0
        )
    )


with col2:

    st.metric(
        "👟 Ticket",
        kpis.get(
            "Ticket",
            0
        )
    )


with col3:

    st.metric(
        "📦 Quiebres",
        kpis.get(
            "Quiebres / Ticket",
            0
        )
    )


with col4:

    st.metric(
        "⚡ Estratégico",
        kpis.get(
            "Estratégico",
            0
        )
    )


# ============================================================
# 🎯 REFERENCIA DE METAS
# ============================================================

st.markdown("---")

st.markdown(
    "### 🎯 Metas comerciales de referencia"
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
    "Las señales externas representan contexto comercial. "
    "No sustituyen el análisis de resultados internos de las tiendas."
)
