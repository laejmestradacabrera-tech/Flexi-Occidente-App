"""Etapa 3: percepción OOXML en memoria. Sin escritura ni conexiones.

No evalúa fórmulas, macros ni enlaces. La identidad semántica de plantilla
requiere un perfil revisado, ligado al hash del libro; nombres solos no bastan.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import posixpath
import re
import unicodedata
from zipfile import ZipFile
from xml.etree import ElementTree as ET

from reglas_checklist import catalogo_reglas, _celdas, resolver_campo_hoja5

NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
RID = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'


def normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFKD', texto.casefold())
                   if not unicodedata.combining(c) and c.isalnum())


def coordenada(col, fila):
    letras = ''
    while col:
        col, resto = divmod(col-1, 26)
        letras = chr(65+resto) + letras
    return letras + str(fila)


def pregunta(valor):
    return isinstance(valor, str) and ('?' in valor or '¿' in valor)


def inventariar(datos):
    """Lee una representación inmutable; conserva XML de formatos y protección."""
    with ZipFile(io.BytesIO(datos)) as z:
        if sum(i.file_size for i in z.infolist()) > 100_000_000:
            raise ValueError('Libro demasiado grande para percepción segura (100 MB).')
        def xml(nombre):
            contenido = z.read(nombre)
            if b'<!DOCTYPE' in contenido.upper() or b'<!ENTITY' in contenido.upper():
                raise ValueError('XML con declaraciones no admitidas.')
            return ET.fromstring(contenido)
        def cadena(e):
            return ''.join(t.text or '' for t in e.findall('.//s:t', NS))
        strings = [cadena(e) for e in xml('xl/sharedStrings.xml')] if 'xl/sharedStrings.xml' in z.namelist() else []
        relaciones = {e.attrib['Id']: e.attrib for e in xml('xl/_rels/workbook.xml.rels')}
        wb = xml('xl/workbook.xml')
        hojas = []
        for sheet in wb.findall('s:sheets/s:sheet', NS):
            rel = relaciones[sheet.attrib[RID]]
            if rel.get('TargetMode') == 'External':
                raise ValueError('Hoja externa no admitida.')
            destino = rel['Target']
            destino = destino.lstrip('/') if destino.startswith('/') else posixpath.normpath('xl/' + destino)
            tree = xml(destino)
            celdas = {}
            for c in tree.findall('s:sheetData/s:row/s:c', NS):
                v = c.find('s:v', NS)
                valor = v.text if v is not None else None
                if c.get('t') == 's' and valor is not None:
                    valor = strings[int(valor)]
                elif c.get('t') == 'inlineStr':
                    valor = cadena(c)
                f = c.find('s:f', NS)
                celdas[c.attrib['r']] = dict(valor=valor, tipo=c.get('t'), estilo=c.get('s', '0'),
                    formula=None if f is None else dict(texto=f.text, atributos=f.attrib),
                    pregunta= pregunta(valor))
            estructura = {}
            for tag in ('dimension', 'sheetProtection', 'protectedRanges', 'printOptions',
                        'pageMargins', 'pageSetup', 'headerFooter', 'rowBreaks', 'colBreaks',
                        'cols', 'dataValidations', 'conditionalFormatting', 'sheetViews'):
                estructura[tag] = [ET.tostring(e, encoding='unicode') for e in tree.findall('s:'+tag, NS)]
            hojas.append(dict(nombre=sheet.get('name'), identidad=sheet.get('sheetId'),
                parte=destino, estado=sheet.get('state', 'visible'), celdas=celdas,
                merges=[e.attrib['ref'] for e in tree.findall('s:mergeCells/s:mergeCell', NS)],
                filas=[e.attrib for e in tree.findall('s:sheetData/s:row', NS)], estructura=estructura))
        return dict(hojas=hojas, nombres_definidos=[dict(e.attrib, contenido=e.text) for e in wb.findall('s:definedNames/s:definedName', NS)],
                    estilos_xml=z.read('xl/styles.xml').decode('utf-8') if 'xl/styles.xml' in z.namelist() else None,
                    partes_no_ejecutadas=[n for n in z.namelist() if 'externalLink' in n or 'vbaProject' in n])


def mapear(inventario, sha256, perfil=None):
    """Perfil opcional: sha256, validado, hojas, campos y hoja5.

    campos: {ID: {A1: {contenido: valor exacto, validado: true}}}.
    hoja5: {ID: [{contenido, etiqueta, destino, es_pregunta, validado}]}.
    etiqueta identifica texto único observado; destino debe existir y ser distinto.
    El perfil es evidencia humana, no una fuente oficial ni permiso de escritura.
    """
    perfil = perfil or {}
    valido = perfil.get('validado') is True and perfil.get('sha256') == sha256
    resultados = []
    for regla in catalogo_reglas():
        candidatos = [h for h in inventario['hojas'] if normalizar(h['nombre']) == normalizar(regla['hoja'])]
        # Identidad declarada dentro del libro; nunca posición de pestaña.
        numero = re.fullmatch(r'Hoja ([1-5])', regla['hoja'])
        if not candidatos and numero:
            patron = re.compile(r'^\s*hoja\s*' + numero[1] + r'\s*/\s*\d+\s*$', re.I)
            candidatos = [h for h in inventario['hojas'] if any(
                isinstance(c['valor'], str) and patron.fullmatch(c['valor'])
                for c in h['celdas'].values())]
        nombre_validado = perfil.get('hojas', {}).get(regla['hoja']) if valido else None
        if nombre_validado:
            candidatos = [h for h in inventario['hojas'] if h['nombre'] == nombre_validado]
        hoja = candidatos[0] if len(candidatos) == 1 else None
        incidencias, campos = [], []
        if hoja is None:
            incidencias.append('HOJA_NO_ENCONTRADA' if not candidatos else 'HOJA_AMBIGUA')
        accion = {'DATO_DIRECTO':'ACTUALIZAR', 'DIAS_CALENDARIO':'ACTUALIZAR',
                  'LIMPIAR_FOLIO':'LIMPIAR', 'LIMPIAR_CAPTURA':'LIMPIAR',
                  'ANALIZAR/PROPONER':'ANALIZAR_PROPONER'}.get(regla['accion'], 'VALIDACION_HUMANA')
        if hoja:
            destinos = [coordenada(c,f) for d in regla['destinos'] for c,f in sorted(_celdas(d))]
            if regla['hoja'] == 'Hoja 5':
                for candidato in perfil.get('hoja5', {}).get(regla['id'], []) if valido else []:
                    texto = candidato.get('contenido', '')
                    coincidencias = [a for a,c in hoja['celdas'].items() if c['valor'] == texto]
                    destino = resolver_campo_hoja5(texto, perfil['hoja5'][regla['id']])
                    if len(coincidencias) == 1 and coincidencias[0] == candidato.get('etiqueta') and destino != coincidencias[0] and destino in hoja['celdas']:
                        destinos.append(destino)
                    else:
                        incidencias.append('CONTENIDO_AMBIGUO_O_NO_VALIDADO')
            if not destinos:
                incidencias.append('DESTINO_PENDIENTE_POR_CONTENIDO')
            for destino in destinos:
                celda = hoja['celdas'].get(destino)
                problemas = []
                if celda is None:
                    problemas.append('CELDA_NO_ENCONTRADA')
                if celda and celda['formula'] is not None:
                    problemas.append('FORMULA_PRESERVAR')
                if celda and celda['pregunta']:
                    problemas.append('PREGUNTA_PRESERVAR')
                for merge in hoja['merges']:
                    if next(iter(_celdas(destino))) in _celdas(merge):
                        if destino != merge.split(':')[0] or not _celdas(merge).issubset(set().union(*(_celdas(d) for d in regla['destinos'])) if regla['destinos'] else _celdas(destino)):
                            problemas.append('MERGE_REQUIERE_VALIDACION')
                evidencia = perfil.get('campos', {}).get(regla['id'], {}).get(destino, {}) if valido else {}
                semantica = valido and (regla['hoja'] == 'Hoja 5' or
                    (evidencia.get('validado') is True and celda is not None and 'contenido' in evidencia and evidencia['contenido'] == celda['valor']))
                if not semantica:
                    problemas.append('IDENTIDAD_CAMPO_NO_VALIDADA')
                if hoja['estructura']['sheetProtection']:
                    problemas.append('PROTECCION_REQUIERE_VALIDACION')
                campos.append(dict(destino=destino, observado=celda, clasificacion='PRESERVAR' if problemas else accion,
                                   incidencias=problemas, validado=not problemas))
        mapeada = bool(campos) and all(c['validado'] for c in campos) and not incidencias
        resultados.append(dict(regla=regla, hoja_real=hoja['nombre'] if hoja else None,
            accion_prevista=accion, clasificaciones=list(dict.fromkeys([accion, 'VALIDACION_HUMANA'] +
                ([] if regla['fuente'] == 'Check List' else ['FUENTE_EXTERNA']))),
            campos=campos, incidencias=incidencias, mapeada=mapeada,
            puede_preparar_localmente=mapeada and accion == 'LIMPIAR' and regla['accion'] != 'LIMPIAR_FOLIO',
            requiere=regla['fuente']))
    return resultados


def percibir(archivo=None, perfil=None):
    reporte = dict(estado='BORRADOR INCOMPLETO', completo=False, escritura_habilitada=False,
        pendientes=['Fuentes y datos obligatorios sin conectar.', 'Validación humana pendiente.'],
        limitaciones=['Sin evaluación de fórmulas, macros ni enlaces.',
                      'Solo OOXML xlsx/xlsm; xls/PDF requieren un lector específico.',
                      'Nombre y coordenada no certifican identidad semántica de plantilla.'])
    if archivo is None:
        reporte.update(muestra_real_disponible=False, inventario=None,
            reglas=mapear({'hojas':[]}, '', perfil))
        reporte['pendientes'].append('Falta muestra real de Check List.')
        return reporte
    path = Path(archivo)
    antes = hashlib.sha256(path.read_bytes()).hexdigest()
    try:
        if path.suffix.lower() not in ('.xlsx', '.xlsm'):
            raise ValueError('Formato no admitido: se requiere xlsx/xlsm.')
        datos = path.read_bytes()
        if hashlib.sha256(datos).hexdigest() != antes:
            raise RuntimeError('El archivo cambió antes de leerlo.')
        inventario = inventariar(datos)
        reporte.update(archivo=str(path.resolve()), inventario=inventario,
                       reglas=mapear(inventario, antes, perfil))
    finally:
        despues = hashlib.sha256(path.read_bytes()).hexdigest()
        if antes != despues:
            raise RuntimeError('El original cambió durante la percepción.')
    reporte.update(sha256_antes=antes, sha256_despues=despues, original_intacto=True,
        plantilla_validada=bool(perfil and perfil.get('validado') is True and perfil.get('sha256') == antes
                                and all(r['mapeada'] for r in reporte['reglas'])))
    reporte['pendientes'].extend(r['regla']['id'] for r in reporte['reglas'] if not r['mapeada'])
    return reporte


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archivo', nargs='?')
    parser.add_argument('--perfil', help='JSON de validación humana vinculado al SHA-256')
    args = parser.parse_args()
    perfil = json.loads(Path(args.perfil).read_text(encoding='utf-8-sig')) if args.perfil else None
    print(json.dumps(percibir(args.archivo, perfil), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
