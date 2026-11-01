"""Etapa 7 aditiva: observaciones de visión; nunca escribe ni certifica Excel."""
from pathlib import Path
import hashlib,json,re
from decimal import Decimal
MAPEOS={
 'Cuota':{'CALZADO META':'B10','VENTA CALZADO':'C10','ACC META':'E10','VENTA ACC':'F10'},
 'Comparativo de Total de pares':{'PESOS 2025':'B26','PESOS 2026':'C26'},
 'Comparativo de Accesorios':{'PESOS 2025':'E26','PESOS 2026':'F26'}}
def huella(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def normalizar(s): return ' '.join(str(s).upper().split())
def ingerir(documento, raiz, tienda):
    """Consume tabla estructurada por visión con texto literal y localizadores.
    Rechaza duplicados, sustituciones y valores ambiguos. Sin OCR ni coordenadas.
    La revisión de visión no equivale a revisión humana ni a validación de corte.
    """
    def rechazo(m): return {'estado':m,'observaciones':[], 'escritura_habilitada':False}
    if documento.get('tipo') not in MAPEOS: return rechazo('ENCABEZADO_INCORRECTO')
    evidencias=[]
    for e in documento.get('imagenes',[]):
        p=Path(raiz)/e['imagen']
        if not p.is_file() or huella(p)!=e['sha256']: return rechazo('HASH_INVALIDO')
        evidencias.append(dict(e,archivo=str(p.resolve())))
    if not evidencias: return rechazo('SIN_EVIDENCIA')
    filas=[r for r in documento.get('filas',[]) if str(r.get('tienda'))==tienda]
    if len(filas)!=1: return rechazo('TIENDA_AUSENTE' if not filas else 'FILA_AMBIGUA')
    fila=filas[0]; mapa=MAPEOS[documento['tipo']]
    columnas=[normalizar(c) for c in documento.get('encabezados',[])]
    if any(columnas.count(c)!=1 for c in mapa): return rechazo('ENCABEZADO_INCORRECTO')
    obs=[]
    for encabezado,destino in mapa.items():
        celdas=[c for c in fila.get('celdas',[]) if normalizar(c.get('encabezado'))==encabezado]
        if len(celdas)!=1: return rechazo('VALOR_AMBIGUO')
        c=celdas[0]; raw=c.get('observado','')
        if not isinstance(raw,str) or not re.fullmatch(r'\$?(?:\d{1,3}(?:,\d{3})+|\d+)\.\d{2}',raw): return rechazo('VALOR_AMBIGUO')
        if not c.get('localizador') or not fila.get('nombre'): return rechazo('SIN_LOCALIZADOR')
        corte=documento.get('corte')
        if corte and (not documento.get('localizador_corte') or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',corte)): return rechazo('CORTE_AMBIGUO')
        obs.append(dict(tienda=tienda,nombre=fila['nombre'],tabla=documento['tipo'],encabezado=encabezado,
          valor_observado=raw,valor_decimal=str(Decimal(raw.replace('$','').replace(',',''))),destino_propuesto=destino,
          localizador=c['localizador'],imagenes=evidencias,revision=documento.get('revision'),
          corte=corte,corte_declarado=documento.get('corte_declarado'),estado_corte='CORTE_VISIBLE_PENDIENTE_VALIDACION' if corte else 'CORTE_NO_VISIBLE',
          estado='REQUIERE_VALIDACION_HUMANA',dato_validado=None,aceptada_etapa5=False))
    return {'estado':'REQUIERE_VALIDACION_HUMANA','observaciones':obs,'escritura_habilitada':False}
def cargar_evidencia():
    raiz=Path(__file__).with_name('evidencia_etapa7')
    return raiz,json.loads((raiz/'tablas_vision.json').read_text(encoding='utf-8'))
