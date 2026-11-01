"""Regla Maestra Flexi, etapa 2: especificación auditable, sin E/S de Excel.

Procedencia: solicitud explícita de Etapa 2 y conversación
6ab030b6-8ca0-83e8-aa95-b1c4b0601273. No conecta fuentes ni autoriza escritura.
Los destinos son referencias lógicas; requieren validar plantilla y autorización.
"""
from datetime import date, datetime, timedelta
from copy import deepcopy
import re

CONVERSION_META = 10.9
TICKET_META = 1.29
CORREOS_META = 15
CORTE = "D-1"
FUENTES = (
    "Hoja 1", "Hoja 2", "Hoja 3", "Hoja 4", "Hoja 5",
    "Cuota", "Comparativo", "Ticket", "Conversión", "Correos",
    "Asistencia", "Inventario", "Aparadores", "Encargada", "Cliente",
)
REGLA_MAESTRA = (
    "Lo nuevo se agrega; lo que ya funciona no se modifica. "
    "No inventar datos ni declarar completo con información o validación faltante. "
    "Encargada interpreta mercado; Cliente expresa expectativa concreta de producto."
)
VERSION_REGLAS = "2.0"
CONSERVACION = (
    "Trabajar sobre copia; nunca alterar el original.",
    "Escritura deshabilitada en Etapa 2; futura escritura solo tras aprobación humana.",
    "Preservar fórmulas, formatos, merges, impresión y estructura.",
    "No alterar celdas protegidas ni fuera de autorización validada.",
    "Limpiar contenido sin escribir cero; no borrar fórmulas dentro de rangos.",
)
RAZONAMIENTO = (
    "dato", "desviación", "cruce", "evidencia", "causa validada/probable",
    "variable controlable", "acción", "compromiso medible",
)
ENFOQUES = {
    "Cuota": "Producto/surtido cuando corresponda.",
    "Comparativo": "Ejecución comercial.",
    "Ticket": "Segundo par y disponibilidad.",
    "Conversión": "Ruta del Cliente y cierre.",
}
REGLAS_REDACCION = (
    "Dato + contexto + interpretación + acción; breve y ajustada al espacio.",
    "Evitar respuestas genéricas, repetitivas y causas sin evidencia.",
    "Compromisos separados para Cuota, Comparativo, Ticket y Conversión, correlacionados con resultados.",
    "Si el resultado es positivo, reconocer fortaleza y buscar crecimiento adicional.",
)


def _regla(id, hoja, destinos, accion, fuente, criterio):
    return dict(id=id, hoja=hoja, destinos=tuple(destinos.split()), accion=accion,
                fuente=fuente, criterio=criterio, requiere_validacion_humana=True)


_REGLAS = (
    _regla("H1_FECHA", "Hoja 1", "G8", "DATO_DIRECTO", "Plan mensual", "Fecha desde Plan mensual."),
    _regla("H1_FOLIO", "Hoja 1", "B18 B19", "LIMPIAR_FOLIO", "DIVEC", "Quitar solo folio DIVEC; conservar concepto. Identificar folio por evidencia, sin patrón supuesto."),
    _regla("H1_RESET", "Hoja 1", "C14 C15 C16 C18 C19 C20 C21 G27 H28 I27 I28 C31 D31 E31", "LIMPIAR_CAPTURA", "Check List", "Borrar contenido sin cero y preservar fórmulas/formatos."),
    _regla("H1_CAJA", "Hoja 1", "H31 I31 J31", "LIMPIAR_CAPTURA", "Caja", "Borrar contenido sin escribir cero."),
    _regla("H2_ANALISIS", "Hoja 2", "B5 B6 B7 B20 B21 C35 C37", "ANALIZAR/PROPONER", "Evidencia validada", "Aplicar cadena de razonamiento y revisión humana."),
    _regla("H2_CUOTA", "Hoja 2", "B10 C10 E10 F10", "DATO_DIRECTO", "DIVEC Avance de cuotas", "Corte D-1. B10 CALZADO META; C10 VENTA/CALZADO; E10 ACC META; F10 VENTA/ACC. Sin cuota vigente: sin proyección, usar último mes cerrado."),
    _regla("H2_COMPARATIVO", "Hoja 2", "B26 C26 E26 F26", "DATO_DIRECTO", "Comparativo", "Importes en pesos; no sustituir por porcentajes ni inventar submapeos."),
    _regla("H2_EXISTENCIA", "Hoja 2", "G73", "DATO_DIRECTO", "Monitor Preparación de Visita", "Existencia de 1–3 pares."),
    _regla("H3_PREVIA", "Hoja 3", "I4", "DATO_DIRECTO", "Check List o Inventario", "Visita previa válida, anterior a visita actual y con evidencia."),
    _regla("H3_DIAS", "Hoja 3", "I5", "DIAS_CALENDARIO", "I4 y visita actual", "Diferencia en días calendario, no días hábiles."),
    _regla("H3_TICKET", "Hoja 3", "G12 E13", "DATO_DIRECTO", "Monitor Módulo Gerencial", "G12 previo; E13 actual. No recalcular."),
    _regla("H3_CONVERSION", "Hoja 3", "F19 E20", "DATO_DIRECTO", "Monitor Módulo Gerencial", "F19 previo; E20 actual. No recalcular."),
    _regla("H3_ANALISIS", "Hoja 3", "B17", "ANALIZAR/PROPONER", "Evidencia validada", "Aplicar cadena de razonamiento."),
    _regla("H3_RESET", "Hoja 3", "I7 L7", "LIMPIAR_CAPTURA", "Check List", "Borrar contenido respetando merges; resolver ancla antes de proponer."),
    _regla("H4_CATALOGO", "Hoja 4", "F5", "DATO_DIRECTO", "Monitor", "Catálogo Activo/pies exhibidos."),
    _regla("H4_CALIFICACION", "Hoja 4", "M5", "DATO_DIRECTO", "Calificación E22", "Dato directo de E22."),
    _regla("H4_RESET", "Hoja 4", "B10:F15 B19:F23", "LIMPIAR_CAPTURA", "Check List", "Solo capturas; preservar fórmulas y formatos."),
    _regla("H5_CONTENIDO", "Hoja 5", "", "RESOLVER_POR_CONTENIDO", "Plantilla validada", "Nunca coordenada ciega; no sobrescribir preguntas; ambigüedad queda pendiente."),
    _regla("H5_ENCARGADA", "Hoja 5", "", "ANALIZAR/PROPONER", "Encargada", "Evidencia de encargada tiene prioridad: lectura competitiva/mercado y contexto real de tienda."),
    _regla("H5_CLIENTE", "Hoja 5", "", "ANALIZAR/PROPONER", "Cliente", "Expectativa concreta de producto; no inventar voz del cliente. Modelos Flexi solo con evidencia/disponibilidad validada."),
    _regla("ASISTENCIA", "Asistencia", "", "VALIDAR", "Horario teórico y registros", "Primera entrada: tolerancia exacta 5:00. Continuo 2 registros; partido 4. No evaluar comida/salida final. Descanso, Vacaciones y Cambio de Tienda Temporal no son incumplimiento automático."),
)
MAPEO_CUOTA = {"B10": "CALZADO META", "C10": "VENTA/CALZADO", "E10": "ACC META", "F10": "VENTA/ACC"}


def catalogo_reglas():
    """Copia independiente para inspección/exportación sin mutar catálogo base."""
    return deepcopy(_REGLAS)


def _celdas(destino):
    def partes(c):
        m = re.fullmatch(r"([A-Z]+)([1-9][0-9]*)", c)
        if not m:
            raise ValueError("Destino inválido: " + c)
        col = 0
        for letra in m[1]:
            col = col * 26 + ord(letra) - 64
        return col, int(m[2])
    extremos = destino.split(":")
    a = partes(extremos[0]); b = partes(extremos[-1])
    if len(extremos) > 2 or a[0] > b[0] or a[1] > b[1]:
        raise ValueError("Rango inválido: " + destino)
    return {(c, f) for c in range(a[0], b[0]+1) for f in range(a[1], b[1]+1)}


def validar_catalogo(reglas=None):
    errores, ids, ocupadas = [], set(), {}
    for r in catalogo_reglas() if reglas is None else reglas:
        if r['id'] in ids:
            errores.append("ID duplicado: " + r['id'])
        ids.add(r['id'])
        for d in r['destinos']:
            for celda in _celdas(d):
                clave = (r['hoja'], celda)
                if clave in ocupadas:
                    errores.append("Conflicto/duplicado: " + r['id'] + " / " + ocupadas[clave])
                ocupadas[clave] = r['id']
    return errores


def corte_d1(visita):
    return date.fromisoformat(str(visita)) - timedelta(days=1)


def dias_calendario(previa, actual, fuente, validada):
    if fuente not in ("Check List", "Inventario") or validada is not True:
        raise ValueError("Visita previa sin fuente válida o validación.")
    diferencia = (date.fromisoformat(str(actual)) - date.fromisoformat(str(previa))).days
    if diferencia <= 0:
        raise ValueError("La visita previa debe ser anterior.")
    return diferencia


def seleccionar_cuota(vigente, ultimo_mes_cerrado):
    """Selecciona datos suministrados; no consulta DIVEC ni calcula proyecciones."""
    return {"datos": deepcopy(vigente if vigente is not None else ultimo_mes_cerrado),
            "periodo": "vigente" if vigente is not None else "último mes cerrado",
            "proyeccion_permitida": vigente is not None,
            "pendiente": vigente is None and ultimo_mes_cerrado is None}


def evaluar_asistencia(entrada_teorica, registros, horario, situacion=None):
    """ISO datetimes con fecha; no evalúa comidas ni salida final."""
    if situacion in ("Descanso", "Vacaciones", "Cambio de Tienda Temporal"):
        return {"estado": "REQUIERE VALIDACIÓN", "incumplimiento_automatico": False}
    esperados = {"continuo": 2, "partido": 4}.get(horario)
    if esperados is None or not entrada_teorica or not registros:
        return {"estado": "INCOMPLETA", "pendiente": "Horario/primera entrada/registros"}
    teorica = datetime.fromisoformat(entrada_teorica)
    marcas = sorted(datetime.fromisoformat(r) for r in registros)
    if any(r.date() != teorica.date() for r in marcas):
        return {"estado": "INCOMPLETA", "pendiente": "Validar fecha de registros"}
    return {"estado": "EVALUADA", "primera_entrada": marcas[0].isoformat(),
            "incidencia_entrada": marcas[0] > teorica + timedelta(minutes=5),
            "registros_esperados": esperados, "registros_observados": len(marcas),
            "numero_registros_valido": len(marcas) == esperados}


def resolver_campo_hoja5(contenido, campos):
    """Campos identificados por lectura de plantilla; jamás infiere coordenadas.

    Cada candidato declara contenido, destino, es_pregunta y validado.
    Solo coincidencia de contenido única y validada permite una propuesta.
    """
    normalizar = lambda s: " ".join(s.casefold().split())
    candidatos = [c for c in campos if normalizar(c.get('contenido', '')) == normalizar(contenido)]
    if not contenido.strip() or len(candidatos) != 1:
        return None
    c = candidatos[0]
    if c.get('es_pregunta') is not False or c.get('validado') is not True:
        return None
    return c.get('destino') or None


def especificacion():
    return dict(version=VERSION_REGLAS, reglas=catalogo_reglas(), conservacion=CONSERVACION,
                metas={"Conversión": CONVERSION_META, "Ticket": TICKET_META, "Correos": CORREOS_META},
                corte=CORTE, razonamiento=RAZONAMIENTO, enfoques=deepcopy(ENFOQUES),
                redaccion=REGLAS_REDACCION, escritura_habilitada=False)


def auditar(contexto, archivo, propuestas, aceptado):
    # Mantiene la firma pública y el bloqueo conservador del orquestador de Etapa 1.
    pendientes = [
        "Fuentes reales, datos obligatorios y corte D-1 pendientes de validación.",
        "Respuestas y campos autorizados pendientes de revisión humana especialista.",
        "Conservación de fórmulas, formatos, merges e impresión pendiente de auditoría del libro.",
        "Etapa 2: especificación integrada; escritura Excel deshabilitada.",
    ]
    if not contexto.get("tienda") or not contexto.get("visita"):
        pendientes.append("Seleccionar tienda y visita.")
    if not archivo:
        pendientes.append("Cargar Check List.")
    if not propuestas.strip() or aceptado is not True:
        pendientes.append("Aceptar o editar propuestas.")
    pendientes.extend(validar_catalogo())
    return {"estado": "BORRADOR INCOMPLETO", "completo": False, "pendientes": pendientes,
            "version_reglas": VERSION_REGLAS}
