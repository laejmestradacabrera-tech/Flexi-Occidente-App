"""Lectura de la misma fuente local del Monitor, sin importar su app Streamlit."""
from pathlib import Path
import re
from ingestion_recortes_etapa7 import huella
CABECERAS=('Ticket prom. Actual','Ticket prom. Anterior','Conv. Año Actual','Conv. Año Anterior')
def consultar(raiz_monitor,tienda):
    import pandas as pd
    # Misma selección de app_occidente.buscar_archivo('Conversion'), en raíz explícita.
    candidatos=sorted(p for p in Path(raiz_monitor).iterdir() if p.is_file() and 'conversion' in p.name.lower() and p.suffix in ('.xlsx','.csv'))
    base={'conexion':'NO CONECTADO','escritura_habilitada':False,'dato_validado':None}
    if not candidatos: return dict(base,estado='FUENTE_AUSENTE',observaciones=[])
    p=candidatos[-1]; sha=huella(p)
    df=pd.read_excel(p) if p.suffix=='.xlsx' else pd.read_csv(p)
    if any(list(df.columns).count(c)!=1 for c in ('Tienda',)+CABECERAS): return dict(base,estado='ENCABEZADO_INCORRECTO',observaciones=[])
    filas=df[df['Tienda'].astype(str).str.extract(r'^\s*(\d+)\b',expand=False)==tienda.removeprefix('T-')]
    if len(filas)!=1: return dict(base,estado='TIENDA_AUSENTE_O_AMBIGUA',observaciones=[])
    fila=filas.iloc[0]
    if any(pd.isna(fila[c]) for c in CABECERAS): return dict(base,estado='VALOR_AMBIGUO',observaciones=[])
    return dict(base,estado='REQUIERE_VALIDACION_HUMANA',lectura_local='REAL',archivo=str(p.resolve()),sha256=sha,corte=None,
      estado_corte='CORTE_NO_VISIBLE',anios='NO_ACREDITADOS',observaciones=[{'tienda':tienda,'encabezado':c,'valor_observado':float(fila[c]),'localizador':f'primera hoja; fila {int(filas.index[0])+2}; columna {c}','unidad':'fracción o porcentaje pendiente de acreditar' if c.startswith('Conv') else 'unidades por ticket'} for c in CABECERAS])
