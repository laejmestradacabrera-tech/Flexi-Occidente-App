"""Etapa 5. Contratos de evidencia solo lectura; no importa ni modifica el Monitor.

Los adaptadores reciben exportaciones verificables, nunca credenciales. Un fixture
puede probar el contrato pero nunca produce DISPONIBLE_VALIDADO.
"""
from dataclasses import dataclass, asdict
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path
from certificacion_semantica_checklist import certificar_archivo
from reglas_checklist import catalogo_reglas, MAPEO_CUOTA, evaluar_asistencia

ESTADOS = ('DISPONIBLE_VALIDADO', 'FALTANTE', 'AMBIGUO', 'DESACTUALIZADO',
           'ERROR', 'REQUIERE_VALIDACION_HUMANA')
FUENTES = {
    'H1_FECHA': 'PLAN', 'H3_PREVIA': 'PLAN', 'H3_DIAS': 'PLAN',
    'H1_FOLIO': 'DIVEC', 'H2_CUOTA': 'DIVEC_CUOTA',
    'H2_COMPARATIVO': 'COMPARATIVO', 'H2_EXISTENCIA': 'MONITOR_PREPARACION',
    'H4_CATALOGO': 'MONITOR_CATALOGO', 'H3_TICKET': 'MONITOR_GERENCIAL',
    'H3_CONVERSION': 'MONITOR_GERENCIAL', 'H4_CALIFICACION': 'CALIFICACION',
    'H5_ENCARGADA': 'ENCARGADA', 'H5_CLIENTE': 'CLIENTE', 'ASISTENCIA': 'ASISTENCIA'}
MAPEOS = {
    'H1_FOLIO': {'B18': 'folio_B18', 'B19': 'folio_B19'},
    'H1_FECHA': {'G8': 'fecha_visita'}, 'H3_PREVIA': {'I4': 'visita_previa'},
    'H2_CUOTA': MAPEO_CUOTA, 'H2_EXISTENCIA': {'G73': 'existencia_1_3_pares'},
    'H4_CATALOGO': {'F5': 'catalogo_activo_pies_exhibidos'},
    'H3_TICKET': {'G12': 'ticket_previo', 'E13': 'ticket_actual'},
    'H3_CONVERSION': {'F19': 'conversion_previa', 'E20': 'conversion_actual'},
    'H5_ENCARGADA': {'B50': 'lectura_mercado'},
    'H5_CLIENTE': {'B53': 'expectativa_producto'},
    'H4_CALIFICACION': {'M5': 'E22'}, 'ASISTENCIA': {'': 'asistencia'}}
D1 = {'H2_CUOTA', 'H2_COMPARATIVO', 'H2_EXISTENCIA', 'H4_CATALOGO',
      'H3_TICKET', 'H3_CONVERSION', 'ASISTENCIA'}


@dataclass(frozen=True)
class Evidencia:
    fuente: str
    tienda: str
    visita: str
    corte: str
    campo: str
    valor: object
    procedencia: str
    sha256: str
    localizador: str
    validacion: str
    real: bool = False
    oficial: bool = False
    humano: str = ''
    metodo: str = 'DIRECTO'
    periodo: str = 'vigente'
    cuota_vigente: object = None
    unidad: str = ''
    destino_validado: str = ''


class AdaptadorFuente:
    """Una instancia por fuente; sin conexión implícita por existir un archivo.

    procedencia+sha256+localizador deben identificar el artefacto original.
    La validación humana del origen es explícita y no se aprende de la plantilla.
    """
    def __init__(self, fuente, registros=(), error=None):
        self.fuente, self.registros, self.error = fuente, tuple(registros), error

    def consultar(self, tienda, campo):
        if self.error:
            raise RuntimeError(self.error)
        return [e for e in self.registros if e.fuente == self.fuente and e.campo == campo]


def verificar_artefacto(e):
    p = Path(e.procedencia)
    return (p.is_file() and len(e.sha256) == 64 and
            hashlib.sha256(p.read_bytes()).hexdigest() == e.sha256)


def cargar_adaptadores(manifiesto):
    """JSON local revisado: {fuentes: {ID: {registros: [...], error: null}}}.

    Cada registro conserva los campos de Evidencia. Las rutas son absolutas.
    Se suministra evidencia revisada; esta función no autentica servidores.
    """
    contenido = json.loads(Path(manifiesto).read_text(encoding='utf-8-sig'))
    adaptadores = {}
    for fuente, contrato in contenido['fuentes'].items():
        if fuente not in set(FUENTES.values()):
            raise ValueError('Fuente desconocida: ' + fuente)
        registros = [Evidencia(**e) for e in contrato.get('registros', [])]
        if any(e.fuente != fuente for e in registros):
            raise ValueError('Registro de otra fuente')
        adaptadores[fuente] = AdaptadorFuente(fuente, registros, contrato.get('error'))
    return adaptadores


def validar(adaptador, regla, campo, destino, certificado, tienda, visita):
    r = dict(regla_destino=regla, destino=destino, campo_fuente=campo,
             fuente=adaptador.fuente, tienda=tienda, visita=visita,
             corte_requerido=str(date.fromisoformat(visita)-timedelta(days=1)) if regla in D1 else visita,
             estado='FALTANTE', valor_observado=None, dato_validado=None,
             evidencia=[], bloqueo='', campo_certificado=certificado)
    def fin(estado, motivo):
        r.update(estado=estado, bloqueo=motivo)
        return r
    try:
        if FUENTES.get(regla) != adaptador.fuente:
            return fin('ERROR', 'FUENTE_INCORRECTA')
        esperado_campo = MAPEOS.get(regla, {}).get(destino)
        if esperado_campo and campo != esperado_campo:
            return fin('ERROR', 'CAMPO_FUENTE_INCORRECTO')
        encontrados = adaptador.consultar(tienda, campo)
        r['evidencia'] = [asdict(e) for e in encontrados]
        if not encontrados:
            return fin('FALTANTE', 'NO CONECTADA o campo ausente')
        propios = [e for e in encontrados if e.tienda == tienda]
        if not propios:
            return fin('ERROR', 'TIENDA_INCORRECTA')
        if len(propios) != 1:
            return fin('AMBIGUO', 'Más de una evidencia; resolver corte/versiones explícitamente')
        e = propios[0]; r['valor_observado'] = e.valor
        if not e.real or not e.oficial:
            return fin('REQUIERE_VALIDACION_HUMANA', 'Fixture o procedencia no oficial')
        if not e.localizador or not e.validacion or not e.humano or not verificar_artefacto(e):
            return fin('REQUIERE_VALIDACION_HUMANA', 'Origen/hash/localizador/revisor sin acreditar')
        if e.visita != visita:
            return fin('ERROR', 'FECHA_VISITA_INCORRECTA')
        corte = date.fromisoformat(e.corte)
        esperado = date.fromisoformat(r['corte_requerido'])
        if regla == 'H2_CUOTA' and e.periodo == 'ultimo_mes_cerrado':
            ultimo = date.fromisoformat(visita).replace(day=1)-timedelta(days=1)
            if e.cuota_vigente is not False or corte != ultimo:
                return fin('DESACTUALIZADO', 'Último mes cerrado o ausencia de cuota vigente no acreditados')
        elif corte != esperado:
            return fin('DESACTUALIZADO' if corte < esperado else 'ERROR', 'CORTE_INCORRECTO')
        if e.valor is None or e.valor == '':
            return fin('FALTANTE', 'Valor ausente')
        if regla in ('H3_TICKET', 'H3_CONVERSION', 'H2_CUOTA') and e.metodo != 'DIRECTO':
            return fin('ERROR', 'RECALCULO_O_PROYECCION_PROHIBIDOS')
        if regla == 'H2_COMPARATIVO' and (e.unidad != 'MXN' or e.destino_validado != destino):
            return fin('AMBIGUO', 'Falta mapeo oficial por destino e importes MXN')
        if regla == 'H1_FECHA' and e.valor != visita:
            return fin('ERROR', 'Fecha del Plan distinta de visita')
        if regla == 'H3_PREVIA' and date.fromisoformat(e.valor) >= date.fromisoformat(visita):
            return fin('ERROR', 'Visita previa no anterior')
        if regla == 'ASISTENCIA':
            a = e.valor
            evaluacion = evaluar_asistencia(a.get('entrada_teorica'), a.get('registros'), a.get('horario'), a.get('situacion'))
            r['evaluacion_asistencia'] = evaluacion
            if evaluacion['estado'] != 'EVALUADA' or not evaluacion['numero_registros_valido']:
                return fin('REQUIERE_VALIDACION_HUMANA', 'Horario y registros reales suficientes 2/4 requeridos')
            if date.fromisoformat(a['entrada_teorica'][:10]) != corte:
                return fin('ERROR', 'Fecha de registros distinta del corte')
        if regla == 'H4_CALIFICACION' or not certificado:
            return fin('REQUIERE_VALIDACION_HUMANA', 'PRESERVAR: identidad/contradicción semántica sin resolver')
        r['dato_validado'] = e.valor
        return fin('DISPONIBLE_VALIDADO', '')
    except Exception as exc:
        return fin('ERROR', type(exc).__name__ + ': ' + str(exc))


def matriz(archivo, tienda, visita, adaptadores=None):
    adaptadores = adaptadores or {}
    cert = certificar_archivo(archivo)
    filas = []
    for regla, sem in zip(catalogo_reglas(), cert['reglas']):
        id = regla['id']; fuente = FUENTES.get(id)
        datos = []
        mapa = MAPEOS.get(id, {})
        if id == 'H2_COMPARATIVO':
            mapa = {d: 'comparativo_' + d for d in regla['destinos']}
        for destino, campo in mapa.items():
            c = next((c for c in sem['campos'] if c['destino'] == destino), {})
            datos.append(validar(adaptadores.get(fuente, AdaptadorFuente(fuente)), id,
                                 campo, destino, c.get('certificado', False), tienda, visita))
        filas.append(dict(regla=id, fuente_requerida=fuente or regla['fuente'],
            campos=sem['campos'], certificada=sem['certificada'], datos=datos,
            estado_fuente=('DISPONIBLE_VALIDADO' if datos and all(d['estado']=='DISPONIBLE_VALIDADO' for d in datos)
                           else next((d['estado'] for d in datos if d['estado']!='DISPONIBLE_VALIDADO'), 'REQUIERE_VALIDACION_HUMANA')),
            conexion='EVIDENCIA_SUMINISTRADA' if fuente in adaptadores and adaptadores[fuente].registros else 'NO CONECTADA',
            bloqueo=([d['bloqueo'] for d in datos if d['bloqueo']] or
                     ([] if datos else ['Fuera de alcance: limpieza, derivación o generación comercial; PRESERVAR'])),
            incidencias_semanticas=sem['incidencias']))
    return dict(estado='BORRADOR INCOMPLETO', completo=False, escritura_habilitada=False,
                generacion_comercial=False, tienda=tienda, visita=visita, certificacion=cert,
                cobertura=filas, datos_validados=sum(d['estado']=='DISPONIBLE_VALIDADO' for f in filas for d in f['datos']))


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('archivo'); p.add_argument('--tienda', required=True); p.add_argument('--visita', required=True)
    p.add_argument('--evidencias', help='Manifiesto local de evidencias revisadas; sin credenciales')
    a = p.parse_args()
    print(json.dumps(matriz(a.archivo, a.tienda, a.visita,
                           cargar_adaptadores(a.evidencias) if a.evidencias else None), ensure_ascii=False, indent=2))
