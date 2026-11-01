"""Etapa 6 aditiva: observación de artefactos reales, nunca autorización de escritura.

No autentica sistemas ni acredita por sí sola oficialidad. Las observaciones
no son Evidencia aprobada; la validación y certificación siguen en Etapas 4–5.
"""
from pathlib import Path
import hashlib
import re
from datetime import date
from openpyxl import load_workbook
from fuentes_checklist import matriz, cargar_adaptadores, MAPEO_CUOTA


def huella(archivo):
    h = hashlib.sha256()
    with Path(archivo).open('rb') as f:
        for bloque in iter(lambda: f.read(1024 * 1024), b''):
            h.update(bloque)
    return h.hexdigest()


def observacion(archivo, tienda, campo, valor, localizador, corte=None, estado='ambiguo', revision=''):
    return dict(artefacto=Path(archivo).name, procedencia=str(Path(archivo).resolve()),
                sha256=huella(archivo), tienda=tienda, visita='2026-10-29', corte=corte,
                campo_fuente=campo, valor_observado=valor, dato_validado=None,
                localizador=localizador, revision=revision, estado=estado,
                real=True, oficialidad_acreditada=False, aceptada_etapa5=False)


def inspeccionar_plan(archivo):
    """Lee exclusivamente calendario A1:H15; no copia notas privadas del libro."""
    antes = huella(archivo)
    w = load_workbook(archivo, read_only=True, data_only=True)
    encontrados = []
    try:
        for nombre in ('Octubre', 'Septiembre ', 'Agosto', 'Julio'):
            if nombre not in w.sheetnames:
                continue
            s = w[nombre]
            titulo = str(s['A1'].value)
            mes = {'Octubre': 10, 'Septiembre ': 9, 'Agosto': 8, 'Julio': 7}[nombre]
            coherente = nombre.strip().upper() in titulo.upper() and '2026' in titulo
            for fila in (5, 7, 9, 11, 13, 15):
                for col in range(1, 8):
                    texto = str(s.cell(fila, col).value or '')
                    dia = s.cell(fila - 1, col).value
                    if not isinstance(dia, int) or not 1 <= dia <= 31:
                        continue
                    for tienda in ('T-157', 'T-59'):
                        patron = re.escape(tienda) + r'(?!\d)(.*?)(?=●|$)'
                        for m in re.finditer(patron, texto):
                            evento = m.group(0).strip()
                            tipo = 'Check List' if 'check list' in evento.lower() else 'Inventario' if 'inventario' in evento.lower() else None
                            if not tipo:
                                continue
                            fecha = str(date(2026, mes, dia))
                            o = observacion(archivo, tienda, 'evento_plan',
                                {'fecha_candidata': fecha, 'tipo': tipo, 'texto': evento, 'encabezado': titulo},
                                f"'{nombre}'!{s.cell(fila,col).coordinate}; día {s.cell(fila-1,col).coordinate}; A1",
                                fecha if coherente else None, 'pendiente' if coherente else 'ambiguo',
                                'Lectura directa. Requiere acreditación de origen/revisión humana.' if coherente else
                                'Conflicto entre nombre de pestaña/calendario y encabezado. No resolver automáticamente.')
                            encontrados.append(o)
    finally:
        w.close()
    assert huella(archivo) == antes, 'El Plan cambió durante la lectura'
    return encontrados


def inspeccionar_kpi(archivo):
    antes = huella(archivo)
    w = load_workbook(archivo, read_only=True, data_only=True)
    resultado = []
    try:
        s = w['Conv. y Tick']
        esperados = ['Tienda', 'Ticket prom. Actual', 'Ticket prom. Anterior', 'Conv. Año Actual', 'Conv. Año Anterior']
        if [s.cell(1,c).value for c in range(1,6)] != esperados:
            raise ValueError('Cabeceras KPI distintas: revisión requerida')
        campos = {2:'ticket_actual',3:'ticket_previo',4:'conversion_actual',5:'conversion_previa'}
        for row in s.iter_rows(min_row=2,max_col=5):
            for numero in (157,59):
                if not re.match(r'^' + str(numero) + r'\s', str(row[0].value)):
                    continue
                for col,campo in campos.items():
                    c = row[col-1]
                    resultado.append(observacion(archivo,f'T-{numero}',campo,c.value,
                        f"'{s.title}'!{c.coordinate}; identidad {row[0].coordinate}; cabecera {c.column_letter}1",
                        revision='Valor directo sin recálculo. Sin fecha/corte ni años explícitos en la tabla; el nombre del archivo no acredita periodo ni oficialidad.'))
    finally:
        w.close()
    assert huella(archivo) == antes
    return resultado


def inspeccionar_cuota(archivo):
    # xlrd es sólo lector BIFF. Nunca convierte ni guarda libros.
    import xlrd
    antes = huella(archivo)
    w = xlrd.open_workbook(str(archivo), on_demand=True)
    resultado = []
    try:
        s = w.sheet_by_name('AVANCE')
        if '30 de septiembre de 2026' not in str(s.cell_value(2,0)):
            raise ValueError('Corte interno distinto: no usar el nombre de archivo')
        if 'Distribuidores y Vendedores' not in str(s.cell_value(0,0)):
            raise ValueError('Emisor interno ausente')
        headers = [str(v).strip() for v in s.row_values(4)]
        for fila in range(5,s.nrows):
            numero = s.cell_value(fila,1)
            if numero not in (157,59):
                continue
            for destino,campo in MAPEO_CUOTA.items():
                col = headers.index(campo)
                o = observacion(archivo,f'T-{int(numero)}',campo,s.cell_value(fila,col),
                    f"AVANCE!{xlrd.formula.colname(col)}{fila+1}; tienda B{fila+1}; cabecera {xlrd.formula.colname(col)}5; emisor A1; corte A3",
                    '2026-09-30','desactualizado',
                    'Exportación con emisor y corte internos. No es D-1. Falta ausencia explícita de cuota vigente y revisión de procedencia; no habilitar sustitución.')
                o['destino_propuesto']=destino
                resultado.append(o)
    finally:
        w.release_resources()
    assert huella(archivo) == antes
    return resultado


def evaluar_sin_escritura(checklist, tienda, visita, manifiesto=None):
    """Reutiliza íntegramente Etapa 5. No promueve observaciones a evidencia."""
    antes = huella(checklist)
    r = matriz(checklist,tienda,visita,cargar_adaptadores(manifiesto) if manifiesto else None)
    assert huella(checklist) == antes
    assert r['estado']=='BORRADOR INCOMPLETO' and not r['escritura_habilitada'] and not r['generacion_comercial']
    return r


def inspeccionar_comparativo(archivo):
    """Registra sólo importes MXN con cabeceras; nunca asigna B26/C26/E26/F26."""
    import xlrd
    antes = huella(archivo)
    w = xlrd.open_workbook(str(archivo), on_demand=True)
    resultado = []
    try:
        for s in w.sheets():
            if s.nrows < 6 or s.ncols < 7:
                continue
            periodo = str(s.cell_value(1,0)).strip()
            if '31 AGOSTO 2026' not in periodo:
                raise ValueError('Periodo interno inesperado; revisión requerida')
            if str(s.cell_value(4,4)).strip() != 'Pesos' or str(s.cell_value(4,6)).strip() != 'Pesos':
                continue
            for fila in range(5,s.nrows):
                numero = s.cell_value(fila,1)
                if numero not in (157,59):
                    continue
                for col,anio in ((4,2025),(6,2026)):
                    o = observacion(archivo,f'T-{int(numero)}',f'{s.name}_pesos_{anio}',s.cell_value(fila,col),
                        f"'{s.name}'!{xlrd.formula.colname(col)}{fila+1}; identidad B{fila+1}; periodo A2; años D4/F4; unidad E5/G5",
                        '2026-08-31','desactualizado',
                        'Importe observado en columna Pesos; falta corte 28/10 y correspondencia oficial de los cuatro destinos. No sumar ni sustituir porcentajes/pares.')
                    o.update(unidad='MXN',periodo_observado=periodo,destino_validado=None)
                    resultado.append(o)
    finally:
        w.release_resources()
    assert huella(archivo)==antes
    return resultado
