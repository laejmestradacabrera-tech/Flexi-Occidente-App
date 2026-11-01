"""Etapa 8: interfaz de solo lectura; contratos y reglas permanecen en sus módulos."""
from pathlib import Path
from datetime import date, timedelta
import json
import tempfile
from ingestion_recortes_etapa7 import ingerir
from adaptador_monitor_etapa7 import consultar
from etapa6_evidencia import evaluar_sin_escritura
from percepcion_checklist import percibir
from reglas_checklist import catalogo_reglas

RAIZ = Path(__file__).resolve().parent


def evaluar_recortes(documentos, raiz, tienda, visita):
    resultados = []
    esperado = (date.fromisoformat(visita) - timedelta(days=1)).isoformat()
    for documento in documentos:
        # Sólo archivos dentro del conjunto de evidencia; sin rutas externas.
        if any(Path(e['imagen']).is_absolute() or '..' in Path(e['imagen']).parts
               or (Path(raiz) / e['imagen']).resolve().parent != Path(raiz).resolve()
               for e in documento.get('imagenes', [])):
            raise ValueError('Ruta de imagen no admitida')
        r = ingerir(documento, raiz, tienda)
        for o in r['observaciones']:
            declarado = o.get('corte_declarado') or {}
            corte = o.get('corte') or declarado.get('fecha')
            o['compatibilidad_visita'] = ('CORTE_NO_ACREDITADO' if not corte else
                'DESACTUALIZADO' if corte < esperado else
                'CORTE_POSTERIOR_AL_REQUERIDO' if corte > esperado else
                'COINCIDE_FECHA_PENDIENTE_VALIDACION')
        resultados.append(dict(tipo=documento.get('tipo'), **r))
    return resultados


def mostrar_panel():
    import streamlit as st
    from cobertura_occidente import tiendas
    st.subheader('Agente Check List')
    st.caption('Zona Occidente · Preparación de visita y revisión de pendientes')
    st.warning('BORRADOR INCOMPLETO')
    a, b = st.columns(2)
    opciones = {f"{t['Tienda']} · {t['Plaza']}": str(t['Tienda']) for t in tiendas()}
    seleccion = a.selectbox('Tienda', ['Seleccionar'] + list(opciones), key='e8_tienda')
    tienda_raw = opciones.get(seleccion, '')
    import re
    numero = re.search(r'\d+', tienda_raw)
    tienda = 'T-' + numero.group() if numero else ''
    visita = b.date_input('Visita', key='e8_visita')
    st.caption(f'Información requerida al día anterior: {(visita - timedelta(days=1)).isoformat()} · Visita pendiente de confirmar con el Plan de Trabajo.')
    archivo = st.file_uploader('Check List original · XLSX / XLSM', type=['xlsx', 'xlsm'], key='e8_libro')
    lectura = st.container()
    st.markdown('#### Cuota y Comparativo')
    imagenes = st.file_uploader('Recortes Cuota y Comparativo', type=['png','jpg','jpeg'], accept_multiple_files=True, key='e8_imagenes')
    evidencia = st.container()
    evidencia.info('Cuota / Comparativo: carga los recortes. La lectura automática está pendiente; los importes requieren revisión.')
    ticket = st.container()
    st.markdown('#### Inventario y otras evidencias')
    st.caption('Se incorporarán cuando correspondan a la visita. Revisión pendiente.')
    st.markdown('#### Pendientes')
    st.write('• Confirmar la visita con el Plan de Trabajo.\n• Revisar asistencia y horarios.\n• Completar información y observaciones pendientes del Check List.\n• Revisar Cuota y Comparativo con información del día anterior a la visita.\n• Actualizar Ticket y Conversión.')
    if archivo is None:
        st.info('Falta cargar el Check List original.')
    if not tienda:
        st.info('Falta seleccionar la tienda.')
    st.markdown('#### Propuestas · siguiente fase')
    st.caption('Pendientes para la siguiente fase.')
    st.button('Generar Check List', disabled=True, key='e8_generar')
    with st.expander('Auditoría del Agente', expanded=False):
        st.caption('Etapa 8 · Inspección técnica de evidencia, fuentes y protecciones.')
        st.info('Dato disponible ≠ dato validado. Certificar una celda tampoco valida su contenido.')
        matriz = None
        if archivo is not None:
            try:
                with tempfile.TemporaryDirectory(prefix='checklist_e8_') as tmp:
                    p = Path(tmp) / ('checklist' + Path(archivo.name).suffix.lower())
                    p.write_bytes(archivo.getvalue())
                    percepcion = percibir(p)
                    if tienda:
                        matriz = evaluar_sin_escritura(p, tienda, visita.isoformat())
                    lectura.success('Check List original leído. Archivo conservado sin cambios.')
                    st.caption('SHA-256: ' + percepcion['sha256_antes'])
                    with st.container():
                        st.markdown('#### Identificación y percepción de plantilla')
                        st.write('Tienda/fecha: contexto manual pendiente de confirmar contra el documento y Plan.')
                        st.json({'hojas': [h['nombre'] for h in percepcion['inventario']['hojas']],
                                 'original_intacto': percepcion['original_intacto']})
            except Exception:
                lectura.error('No se pudo leer el Check List. Revisa el formato del archivo.')
        st.markdown('#### Fuentes y evidencia')
        st.caption('Estados: VALIDADO · REQUIERE VALIDACIÓN · FALTANTE · AMBIGUO · DESACTUALIZADO. La evidencia nueva no se promueve al manifiesto aprobado.')
        contrato = st.file_uploader('Tablas de visión · contrato JSON de Etapa 7', type=['json'], key='e8_contrato')
        st.caption('Las imágenes solas quedan pendientes: Etapa 7 exige tablas de visión, encabezados, localizadores y SHA-256. No hay OCR automático.')
        resultados = []
        if tienda:
            try:
                if contrato:
                    docs = json.loads(contrato.getvalue().decode('utf-8-sig'))
                    if not isinstance(docs, list):
                        docs = [docs]
                    with tempfile.TemporaryDirectory(prefix='recortes_e8_') as tmp:
                        nombres = set()
                        for img in imagenes:
                            nombre = Path(img.name).name
                            if nombre in nombres:
                                raise ValueError('Imagen duplicada')
                            nombres.add(nombre)
                            (Path(tmp) / nombre).write_bytes(img.getvalue())
                        resultados = evaluar_recortes(docs, tmp, tienda, visita.isoformat())
            except Exception:
                st.error('Contrato o evidencia no admisible. Verifica estructura, nombres de imágenes y hashes.')
                evidencia.warning('Cuota / Comparativo: la evidencia requiere revisión.')
            for r in resultados:
                st.write(f"{r['tipo']} · {r['estado']}")
                if r['observaciones']:
                    st.dataframe([{k: o.get(k) for k in ('tienda','encabezado','valor_observado','destino_propuesto','estado_corte','corte','corte_declarado','compatibilidad_visita','estado','dato_validado')} for o in r['observaciones']], hide_index=True)
            try:
                monitor = consultar(RAIZ, tienda)
                st.write('Ticket / Conversión · ' + monitor['conexion'])
                ticket.info('Ticket / Conversión · Pendiente de actualización y validación de la fuente vigente.')
                st.caption('Lectura local histórica/no acreditada: no demuestra conexión operativa ni corte vigente.')
                st.write(monitor['estado'])
                if monitor['observaciones']:
                    st.dataframe(monitor['observaciones'], hide_index=True)
            except Exception:
                st.warning('Ticket / Conversión · NO CONECTADO · No se pudo leer la fuente local.')
                ticket.warning('Ticket / Conversión · Fuente pendiente de conexión.')
        else:
            st.write('Ticket / Conversión · NO CONECTADO')
            ticket.info('Ticket / Conversión · Selecciona una tienda para revisar su disponibilidad.')
            st.info('Selecciona una tienda para consultar recortes y adaptador Monitor.')
        st.markdown('#### Cobertura de las 21 reglas')
        reglas = catalogo_reglas()
        certificadas = matriz['certificacion']['reglas_certificadas'] if matriz else 0
        st.progress(certificadas / len(reglas), text=f'{certificadas}/{len(reglas)} reglas con identidad certificada')
        st.caption(f"Datos validados: {matriz['datos_validados'] if matriz else 0} · Los recortes y KPI observados se muestran por separado y no completan reglas automáticamente.")
        if matriz:
            st.dataframe([{'regla': f['regla'], 'identidad_certificada': f['certificada'], 'fuente': f['fuente_requerida'], 'estado': f['estado_fuente'], 'bloqueos': '; '.join(f['bloqueo'])} for f in matriz['cobertura']], hide_index=True)
            with st.container():
                st.markdown('#### Detalle de campos y certificación')
                st.json(matriz)
        else:
            st.dataframe([{'regla': r['id'], 'fuente': r['fuente'], 'estado': 'FALTANTE: cargar Check List y seleccionar tienda'} for r in reglas], hide_index=True)
        with st.container():
            st.markdown('#### Pendientes y bloqueos técnicos')
            st.write('• Plan de Trabajo: visita sin acreditar.\n• Asistencia: horario y registros pendientes.\n• E22/M5: preservar ambigüedad y autoría.\n• Cuota/Comparativo: validar procedencia, asociación y corte D-1.\n• Ticket/Conversión: fuente operativa vigente no acreditada.')
