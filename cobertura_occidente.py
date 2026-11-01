"""Cobertura de la vista previa. Lectura del catálogo, sin datos de contacto."""
from pathlib import Path
import openpyxl

CATALOGO = Path(__file__).with_name('CORREO DE TIENDAS.xlsx')
ZONAS = ('Jalisco', 'Aguascalientes', 'Manzanillo', 'Tepic')
TERMINOS_LOCALES = ['comercio', 'comercios', 'comercial', 'tiendas', 'plaza', 'plazas',
    'lluvia', 'lluvias', 'inundacion', 'inundaciones', 'bloqueo', 'bloqueos',
    'cierre', 'cierres', 'vialidad', 'vialidades', 'movilidad', 'seguridad', 'turismo',
    'turistas', 'huracan', 'tormenta', 'obras', 'obra', 'desvio', 'desvios',
    'pavimentacion', 'rehabilitacion', 'accesos', 'acceso', 'transporte', 'apagones']
LOCALIDADES = ['jalisco', 'guadalajara', 'zapopan', 'tlaquepaque', 'tlajomulco',
              'puerto vallarta', 'aguascalientes', 'manzanillo', 'tepic']


def tiendas():
    wb = openpyxl.load_workbook(CATALOGO, read_only=True, data_only=True)
    try:
        rows = []
        for row in wb.active.iter_rows(min_row=2, values_only=True):
            if not row[0] or not row[1]:
                continue
            nombre = str(row[1]).strip()
            n = nombre.upper()
            # El usuario confirmó estas cuatro zonas y la integridad del catálogo.
            # Jalisco es asignación regional por exclusión, no geocodificación municipal.
            zona = next((z for z in ZONAS[1:] if z.upper() in n), 'Jalisco')
            rows.append({'Tienda': str(row[0]), 'Plaza': nombre, 'Zona': zona})
        return rows
    finally:
        wb.close()


def consultas_locales():
    tema = '(comercio OR tiendas OR "centro comercial" OR lluvias OR inundaciones OR bloqueos OR cierres OR movilidad OR obras OR desvíos OR pavimentación OR seguridad OR turismo)'
    ubicaciones = {'Jalisco': '(Jalisco OR Guadalajara OR Zapopan OR Tlaquepaque OR Tlajomulco OR "Puerto Vallarta")',
                   'Aguascalientes': 'Aguascalientes México', 'Manzanillo': 'Manzanillo Colima México',
                   'Tepic': 'Tepic Nayarit México'}
    consultas = {f'Entorno local · {zona}': f'{lugar} {tema}' for zona,lugar in ubicaciones.items()}
    for zona, lugar in ubicaciones.items():
        consultas[f'Entorno local · Obras y accesos · {zona}'] = f'{lugar} ("cierre vial" OR "cierres viales" OR obras OR desvíos OR pavimentación OR "restricción de acceso")'
    # Nombres públicos de plazas solamente. No se transmite encargado ni correo.
    for zona in ZONAS:
        nombres = [r['Plaza'] for r in tiendas() if r['Zona'] == zona]
        for start in range(0, len(nombres), 5):
            group = nombres[start:start+5]
            consultas[f'Plazas · {zona} · {start//5+1}'] = '(' + ' OR '.join('"'+n.replace('"','')+'"' for n in group) + f') {ubicaciones[zona]}'
    return consultas
