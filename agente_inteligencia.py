# ============================================================
# 🧠 PESTAÑA: INTELIGENCIA COMERCIAL
# ============================================================

import os
import html
import textwrap
import pandas as pd
import streamlit as st


# ============================================================
# CONFIGURACIÓN
# ============================================================

ARCHIVO_INTELIGENCIA = "datos_inteligencia.csv"

META_CONVERSION = 10.9
META_TICKET = 1.29


# ============================================================
# CARGAR DATOS
# ============================================================

@st.cache_data(ttl=900)
def cargar_datos_inteligencia():

    if not os.path.exists(ARCHIVO_INTELIGENCIA):
        return pd.DataFrame()

    try:

        df = pd.read_csv(
            ARCHIVO_INTELIGENCIA,
            encoding="utf-8-sig"
        )

        if df.empty:
            return df

        # Asegurar columnas aunque el archivo
        # provenga de una versión anterior
        columnas = {
            "ID": "",
            "Categoría": "Sin categoría",
            "Tipo Fuente": "",
            "Título": "Sin título",
            "Título Original": "",
            "Fecha": "",
            "Relevancia": "MEDIA",
            "Score": 0,
            "Impacto Flexi": "Información de contexto",
            "KPI Afectado": "Estratégico",
            "Nivel Impacto": "BAJO",
            "Acción Sugerida": "Dar seguimiento.",
            "Enlace": "",
            "Última Actualización": ""
        }

        for columna, valor in columnas.items():

            if columna not in df.columns:
                df[columna] = valor

        # Score numérico
        df["Score"] = pd.to_numeric(
            df["Score"],
            errors="coerce"
        ).fillna(0)

        # Texto limpio
        columnas_texto = [
            "Categoría",
            "Título",
            "Relevancia",
            "Impacto Flexi",
            "KPI Afectado",
            "Nivel Impacto",
            "Acción Sugerida",
            "Enlace",
            "Fecha",
            "Última Actualización"
        ]

        for columna in columnas_texto:

            df[columna] = (
                df[columna]
                .fillna("")
                .astype(str)
            )

        # Fecha para ordenar
        df["_Fecha"] = pd.to_datetime(
            df["Fecha"],
            errors="coerce"
        )

        # Ordenar por score
        df = df.sort_values(
            by=["Score", "_Fecha"],
            ascending=[False, False]
        )

        return df

    except Exception as e:

        st.error(
            f"Error al leer {ARCHIVO_INTELIGENCIA}: {e}"
        )

        return pd.DataFrame()


# ============================================================
# ESTILOS
# ============================================================

st.markdown(
    textwrap.dedent(
        """
        <style>

        .intel-header {
            background: linear-gradient(
                135deg,
                #E30613,
                #B0000B
            );
            color: white;
            padding: 24px 28px;
            border-radius: 14px;
            margin-bottom: 20px;
        }

        .intel-title {
            font-size: 30px;
            font-weight: 800;
            letter-spacing: -0.5px;
        }

        .intel-subtitle {
            font-size: 15px;
            margin-top: 6px;
            opacity: 0.92;
        }

        .news-card {
            border: 1px solid #E2E2E2;
            border-radius: 12px;
            padding: 18px;
            margin-bottom: 12px;
            background: white;
        }

        .news-title {
            font-size: 18px;
            font-weight: 750;
            line-height: 1.3;
            margin-bottom: 8px;
        }

        .news-meta {
            font-size: 12px;
            color: #666666;
        }

        .impact-box {
            background: #F7F7F7;
            border-radius: 8px;
            padding: 12px;
            margin-top: 12px;
        }

        .action-box {
            background: #FFF7F7;
            border-left: 4px solid #E30613;
            border-radius: 6px;
            padding: 12px;
            margin-top: 10px;
        }

        .section-title {
            font-size: 23px;
            font-weight: 800;
            margin-top: 10px;
            margin-bottom: 12px;
        }

        </style>
        """
    ),
    unsafe_allow_html=True
)


# ============================================================
# CARGAR
# ============================================================

df = cargar_datos_inteligencia()


# ============================================================
# ENCABEZADO
# ============================================================

st.markdown(
    textwrap.dedent(
        """
        <div class="intel-header">

            <div class="intel-title">
                🧠 INTELIGENCIA COMERCIAL
            </div>

            <div class="intel-subtitle">
                Señales externas que pueden impactar el desempeño
                comercial de Flexi y las decisiones de Zona Occidente.
            </div>

        </div>
        """
    ),
    unsafe_allow_html=True
)


# ============================================================
# SI NO EXISTE INFORMACIÓN
# ============================================================

if df.empty:

    st.warning(
        "No hay información disponible en datos_inteligencia.csv."
    )

    st.info(
        "Ejecuta primero el proceso de recolección de noticias "
        "para generar la información."
    )

    st.stop()


# ============================================================
# ACTUALIZACIÓN
# ============================================================

col_actualizacion, col_refrescar = st.columns(
    [5, 1]
)

with col_actualizacion:

    ultima_actualizacion = (
        df["Última Actualización"]
        .replace("", pd.NA)
        .dropna()
    )

    if not ultima_actualizacion.empty:

        st.caption(
            f"🕐 Última actualización: "
            f"{ultima_actualizacion.iloc[0]}"
        )

    else:

        st.caption(
            "🕐 Fecha de actualización no disponible"
        )


with col_refrescar:

    if st.button(
        "🔄 Actualizar",
        use_container_width=True
    ):

        st.cache_data.clear()
        st.rerun()


# ============================================================
# INDICADORES EJECUTIVOS
# ============================================================

total_noticias = len(df)

criticas = len(
    df[
        df["Relevancia"].str.upper()
        == "CRÍTICA"
    ]
)

altas = len(
    df[
        df["Relevancia"].str.upper()
        == "ALTA"
    ]
)

impactos_altos = len(
    df[
        df["Nivel Impacto"].str.upper()
        == "ALTO"
    ]
)


st.markdown(
    '<div class="section-title">📊 Panorama de hoy</div>',
    unsafe_allow_html=True
)


c1, c2, c3, c4 = st.columns(4)


with c1:

    st.metric(
        "🔴 Riesgos críticos",
        criticas
    )


with c2:

    st.metric(
        "🟠 Alta relevancia",
        altas
    )


with c3:

    st.metric(
        "📰 Noticias relevantes",
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

with st.expander(
    "🔎 Filtros de inteligencia",
    expanded=False
):

    f1, f2, f3 = st.columns(3)

    with f1:

        categorias = [
            "Todas"
        ] + sorted(
            [
                x for x in
                df["Categoría"].unique()
                if x
            ]
        )

        filtro_categoria = st.selectbox(
            "Categoría",
            categorias
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
            ]
        )

    with f3:

        filtro_impacto = st.selectbox(
            "Impacto",
            [
                "Todos",
                "ALTO",
                "MEDIO",
                "BAJO"
            ]
        )


df_filtrado = df.copy()


if filtro_categoria != "Todas":

    df_filtrado = df_filtrado[
        df_filtrado["Categoría"]
        == filtro_categoria
    ]


if filtro_relevancia != "Todas":

    df_filtrado = df_filtrado[
        df_filtrado["Relevancia"].str.upper()
        == filtro_relevancia
    ]


if filtro_impacto != "Todos":

    df_filtrado = df_filtrado[
        df_filtrado["Nivel Impacto"].str.upper()
        == filtro_impacto
    ]


# ============================================================
# 🎯 ¿QUÉ DEBO SABER HOY?
# ============================================================

st.markdown("---")

st.markdown(
    '<div class="section-title">🎯 ¿QUÉ DEBO SABER HOY?</div>',
    unsafe_allow_html=True
)


top_hoy = (
    df_filtrado
    .sort_values(
        by="Score",
        ascending=False
    )
    .head(3)
)


if top_hoy.empty:

    st.info(
        "No existen señales para los filtros seleccionados."
    )

else:

    for numero, (_, row) in enumerate(
        top_hoy.iterrows(),
        start=1
    ):

        relevancia = row["Relevancia"].upper()

        if relevancia == "CRÍTICA":

            icono = "🔴"

        elif relevancia == "ALTA":

            icono = "🟠"

        elif relevancia == "MEDIA":

            icono = "🟡"

        else:

            icono = "🟢"


        st.markdown(
            f"""
            <div class="news-card">

                <div class="news-meta">
                    {icono} {relevancia}
                    &nbsp; | &nbsp;
                    SCORE {int(row["Score"])}/100
                </div>

                <div class="news-title">
                    {html.escape(row["Título"])}
                </div>

                <div class="news-meta">
                    {html.escape(row["Categoría"])}
                    &nbsp; · &nbsp;
                    {html.escape(row["Fecha"])}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


        col_a, col_b = st.columns(2)

        with col_a:

            st.markdown(
                f"""
                **Impacto Flexi**

                {row["Impacto Flexi"]}
                """
            )

        with col_b:

            st.markdown(
                f"""
                **KPI relacionado**

                🎯 {row["KPI Afectado"]}
                """
            )

        st.markdown(
            f"""
            <div class="action-box">

            <b>🎯 Acción recomendada</b><br>

            {html.escape(row["Acción Sugerida"])}

            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# 🔴 RIESGOS
# ============================================================

st.markdown("---")

st.markdown(
    '<div class="section-title">🔴 RIESGOS PRIORITARIOS</div>',
    unsafe_allow_html=True
)


riesgos = (
    df_filtrado[
        df_filtrado["Nivel Impacto"].str.upper()
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

            if row["Relevancia"].upper() == "CRÍTICA":

                icono = "🔴"

            elif row["Relevancia"].upper() == "ALTA":

                icono = "🟠"

            else:

                icono = "🟡"


            st.markdown(
                f"### {icono} {row['Título']}"
            )

            st.caption(
                f"{row['Categoría']} · "
                f"{row['Fecha']} · "
                f"Score {int(row['Score'])}/100"
            )


            a, b, c = st.columns(3)


            with a:

                st.markdown(
                    f"""
                    **Impacto**

                    🔴 {row["Impacto Flexi"]}
                    """
                )


            with b:

                st.markdown(
                    f"""
                    **KPI**

                    🎯 {row["KPI Afectado"]}
                    """
                )


            with c:

                st.markdown(
                    f"""
                    **Nivel**

                    🔴 {row["Nivel Impacto"]}
                    """
                )


            st.info(
                f"🎯 **Acción recomendada:** "
                f"{row['Acción Sugerida']}"
            )


# ============================================================
# 🟢 OPORTUNIDADES
# ============================================================

st.markdown("---")

st.markdown(
    '<div class="section-title">🟢 OPORTUNIDADES</div>',
    unsafe_allow_html=True
)


# Las noticias de alta relevancia pueden representar
# oportunidades o señales estratégicas.
oportunidades = (
    df_filtrado[
        df_filtrado["Relevancia"].str.upper()
        .isin(["CRÍTICA", "ALTA"])
    ]
    .sort_values(
        by="Score",
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
                f"### 🟢 {row['Título']}"
            )

            st.caption(
                f"{row['Categoría']} · "
                f"{row['Fecha']}"
            )

            st.markdown(
                f"""
                **Señal detectada:**  
                {row["Impacto Flexi"]}

                **KPI relacionado:**  
                🎯 {row["KPI Afectado"]}

                **Acción recomendada:**  
                {row["Acción Sugerida"]}
                """
            )


# ============================================================
# 📰 TODAS LAS NOTICIAS
# ============================================================

st.markdown("---")

st.markdown(
    '<div class="section-title">📰 MONITOR DE NOTICIAS</div>',
    unsafe_allow_html=True
)


st.caption(
    f"Mostrando {len(df_filtrado)} noticias."
)


if df_filtrado.empty:

    st.info(
        "No existen noticias para los filtros seleccionados."
    )

else:

    for _, row in df_filtrado.iterrows():

        relevancia = row["Relevancia"].upper()

        if relevancia == "CRÍTICA":

            icono = "🔴"

        elif relevancia == "ALTA":

            icono = "🟠"

        elif relevancia == "MEDIA":

            icono = "🟡"

        else:

            icono = "🟢"


        titulo_corto = row["Título"]

        # Cada noticia queda compacta y desplegable
        with st.expander(
            f"{icono} {titulo_corto}"
        ):

            a, b, c, d = st.columns(4)


            with a:

                st.markdown(
                    f"**Relevancia**  \n"
                    f"{relevancia}"
                )


            with b:

                st.markdown(
                    f"**Score**  \n"
                    f"{int(row['Score'])}/100"
                )


            with c:

                st.markdown(
                    f"**Impacto**  \n"
                    f"{row['Nivel Impacto']}"
                )


            with d:

                st.markdown(
                    f"**KPI**  \n"
                    f"{row['KPI Afectado']}"
                )


            st.markdown("---")


            st.markdown(
                f"""
                **Categoría:**  
                {row["Categoría"]}

                **Fecha:**  
                {row["Fecha"]}

                **Impacto para Flexi:**  
                {row["Impacto Flexi"]}
                """
            )


            # Si en una futura versión el CSV contiene
            # una columna Resumen, la mostramos.
            if "Resumen" in row.index:

                resumen = str(
                    row["Resumen"]
                ).strip()

                if resumen:

                    st.markdown(
                        f"""
                        **¿Qué dice la noticia?**

                        {resumen}
                        """
                    )


            st.markdown(
                f"""
                <div class="action-box">

                <b>🎯 ¿Qué deberíamos hacer?</b><br>

                {html.escape(row["Acción Sugerida"])}

                </div>
                """,
                unsafe_allow_html=True
            )


            enlace = str(
                row["Enlace"]
            ).strip()


            if enlace and enlace != "nan":

                st.link_button(
                    "📰 Leer noticia original",
                    enlace
                )


# ============================================================
# 📊 MAPA DE KPIs
# ============================================================

st.markdown("---")

st.markdown(
    '<div class="section-title">📊 ¿Qué KPI está más expuesto?</div>',
    unsafe_allow_html=True
)


def contar_kpi(df_data, texto):

    return int(
        df_data["KPI Afectado"]
        .astype(str)
        .str.contains(
            texto,
            case=False,
            na=False
        )
        .sum()
    )


kpi_conversion = contar_kpi(
    df_filtrado,
    "Conversión"
)

kpi_ticket = contar_kpi(
    df_filtrado,
    "Ticket"
)

kpi_quiebres = contar_kpi(
    df_filtrado,
    "Quiebres"
)

kpi_estrategico = contar_kpi(
    df_filtrado,
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

st.markdown("---")

st.markdown(
    '<div class="section-title">🎯 Referencia comercial Flexi</div>',
    unsafe_allow_html=True
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
    "Las noticias representan señales externas y contexto "
    "comercial. El impacto debe contrastarse con los resultados "
    "reales de las tiendas."
)


# ============================================================
# FIN
# ============================================================
