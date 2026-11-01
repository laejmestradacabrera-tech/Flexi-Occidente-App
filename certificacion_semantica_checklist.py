"""Etapa 4 aditiva: certificación estructural conservadora, sin E/S de escritura Excel.

El perfil revisado es una allowlist de evidencia, no se aprende del libro candidato.
Se reutilizan el lector Etapa 3 y las 21 reglas Etapa 2 sin modificarlos.
"""
import hashlib
import json
from pathlib import Path
from percepcion_checklist import inventariar, normalizar
from reglas_checklist import catalogo_reglas, _celdas, CONSERVACION

PERFIL = Path(__file__).with_name('perfil_semantico_checklist.json')

def cargar_perfil():
    return json.loads(PERFIL.read_text(encoding='utf-8'))

def _coincide(hoja, ancla):
    encontrados = [a for a,c in hoja['celdas'].items()
        if isinstance(c['valor'], str) and ' '.join(c['valor'].casefold().split()) == ' '.join(ancla['texto'].casefold().split())]
    return sorted(encontrados) == sorted(ancla.get('ocurrencias', [ancla['celda']])) and hoja['celdas'][ancla['celda']]['formula'] == ancla['formula']

def certificar(inventario, perfil=None):
    perfil = cargar_perfil() if perfil is None else perfil
    catalogo = {r['id']:r for r in catalogo_reglas()}
    resultados=[]
    etiquetas = {a['texto'] for s in perfil['reglas'] for a in s['anclas']}
    for s in perfil['reglas']:
        regla=catalogo[s['regla']]
        candidatos=[h for h in inventario['hojas'] if s['marcador'] and _coincide(h,s['marcador'])]
        hoja=candidatos[0] if len(candidatos)==1 else None
        problemas=[]
        if hoja is None: problemas.append('HOJA_AUSENTE_O_AMBIGUA')
        elif not all(_coincide(hoja,a) for a in s['anclas']): problemas.append('ETIQUETA_POSICION_FORMULA_O_UNICIDAD_CAMBIADA')
        if hoja and not all(hoja['celdas'].get(a['celda'],{}).get('formula') == a['formula'] for a in s.get('formulas_contexto',[])): problemas.append('FORMULA_DE_CONTEXTO_CAMBIADA')
        if hoja and hoja['estructura']['sheetProtection']: problemas.append('PROTECCION_PRESERVAR')
        campos=[]
        for f in s['campos']:
            incidencias=list(problemas)
            d=f['destino']; c=hoja['celdas'].get(d) if hoja else None
            if f['pendiente']: incidencias.append(f['pendiente'])
            if c is None: incidencias.append('DESTINO_AUSENTE')
            else:
                if c['formula'] is not None: incidencias.append('FORMULA_PRESERVAR')
                if c['pregunta'] or c['valor'] in etiquetas: incidencias.append('PREGUNTA_O_ETIQUETA_PRESERVAR')
            xy=next(iter(_celdas(d))); ax=next(iter(_celdas(s['anclas'][0]['celda'])))
            if [xy[0]-ax[0],xy[1]-ax[1]] != f['offset']: incidencias.append('POSICION_RELATIVA_INCOMPATIBLE')
            merges=[m for m in hoja['merges'] if xy in _celdas(m)] if hoja else []
            if merges!=f['merges'] or any(m not in f['merges_admitidos'] or m.split(':')[0]!=d for m in merges):
                incidencias.append('MERGE_INCOMPATIBLE')
            if any(d==a['celda'] for a in s['anclas']): incidencias.append('DESTINO_ES_ETIQUETA')
            campos.append(dict(destino=d,identidad_semantica=f['identidad'],certificado=not incidencias,
                accion_autorizada='PRESERVAR' if incidencias else 'CERTIFICAR_IDENTIDAD_SOLO_LECTURA',
                accion_prevista=regla['accion'],incidencias=incidencias,
                evidencia=dict(anclas=s['anclas'],marcador=s['marcador'],offset=f['offset'],merges_observados=merges,
                    formulas_contexto=s.get('formulas_contexto',[]),formula_observada=c['formula'] if c else None),fuente_oficial_prevista=regla['fuente'],
                restricciones=list(CONSERVACION)+perfil['restricciones']))
        if not campos: problemas.append('SIN_DESTINO_CERTIFICABLE; SOLO_SECCION_PUNTUALIDAD' if s['regla']=='ASISTENCIA' else 'SIN_DESTINO')
        resultados.append(dict(regla=s['regla'],hoja_logica=regla['hoja'],hoja_real=hoja['nombre'] if hoja else None,
            identidad=s['identidad'],evidencia_seccion=s['anclas'],campos=campos,incidencias=problemas,
            certificada=bool(campos) and all(c['certificado'] for c in campos) and not problemas))
    certificados=[(r['hoja_real'],c['destino']) for r in resultados for c in r['campos'] if c['certificado']]
    # E22 se inspecciona en cada candidato, no se hereda un dictamen por hash.
    mapeo=[]
    for seccion in perfil['hojas']:
        candidatas=[h for h in inventario['hojas'] if all(_coincide(h,a) for a in seccion['anclas'])]
        mapeo.append(dict(hoja_logica=seccion['logica'],hoja_real=candidatas[0]['nombre'] if len(candidatas)==1 else None,certificada=len(candidatas)==1,evidencia=seccion['anclas']))
    cal=perfil['calificacion']; calmap=mapeo[-1]; hojas=[h for h in inventario['hojas'] if calmap['certificada'] and h['nombre']==calmap['hoja_real']]
    observado={a:hojas[0]['celdas'].get(a) for a in cal['evidencia']} if len(hojas)==1 else {}
    return dict(estado='BORRADOR INCOMPLETO',completo=False,escritura_habilitada=False,fuentes_conectadas=False,
        hojas=mapeo,reglas=resultados,reglas_certificadas=sum(r['certificada'] for r in resultados),
        reglas_con_algun_destino_certificado=sum(any(c['certificado'] for c in r['campos']) for r in resultados),
        destinos_certificados=len(certificados),destinos_unicos_certificados=len(set(certificados)),
        calificacion=dict(certificada_para_H4=False,observado=observado,conclusion=cal['conclusion']),
        pendientes=['Fuentes oficiales no conectadas; sin respuestas comerciales ni escritura.',
        'Asistencia: sección de puntualidad localizada; no hay horario teórico ni registros 2/4 ni destino inequívoco.',
        'La identidad de los bloques de Hoja 5 no prueba quién emitió los comentarios existentes.'])

def certificar_archivo(archivo, perfil=None):
    path=Path(archivo); datos=path.read_bytes(); antes=hashlib.sha256(datos).hexdigest()
    try:
        resultado=certificar(inventariar(datos),perfil)
    finally:
        despues=hashlib.sha256(path.read_bytes()).hexdigest()
        if antes!=despues: raise RuntimeError('Original cambió durante lectura')
    resultado.update(archivo=str(path.resolve()),sha256_antes=antes,sha256_despues=despues,original_intacto=True)
    return resultado

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('archivo'); args=parser.parse_args()
    print(json.dumps(certificar_archivo(args.archivo),ensure_ascii=False,indent=2))

