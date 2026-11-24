"""
pipeline_limpieza.py
Pipeline reproducible que integra TomTom Traffic Index y OECD City Economy.
Reproduce el dataset final del notebook notebooks/01_analisis_movilidad_latam.ipynb.

Uso:
    python src/pipeline_limpieza.py datasets/tomtom_traffic.csv datasets/oecd_city_economy.csv data/ladb_mobility_economy_2024_clean.csv
"""
import sys
import pandas as pd

COLUMNAS_TRAFICO = ['city', 'country', 'year', 'jamsdelay', 'trafficindexlive', 'jamslengthinkms',
                    'jamscount', 'minsdelay', 'traveltimeliveper10kmsmins', 'traveltimehistoricper10kmsmins']
COLUMNAS_ECONOMIA = ['city', 'city_gdp/capita', 'unemployment_%', 'pm2.5_(μg/m³)', 'population']


def _estandarizar_columnas(df):
    df.columns = df.columns.str.lower().str.replace(' ', '_')
    return df


def limpiar_trafico(ruta, anio=2024):
    """Carga TomTom, convierte fechas, filtra el año y promedia por ciudad."""
    df = _estandarizar_columnas(pd.read_csv(ruta))
    for col in ('updatetimeutc', 'updatetimeutcweekago'):
        df[col] = pd.to_datetime(df[col], errors='coerce')
    df['year'] = df['updatetimeutc'].dt.year
    df = df[df['year'] == anio]
    metricas = ['jamsdelay', 'trafficindexlive', 'jamslengthinkms', 'jamscount',
                'minsdelay', 'traveltimeliveper10kmsmins', 'traveltimehistoricper10kmsmins']
    agregado = df.groupby(['city', 'country', 'year'])[metricas].mean().reset_index()
    return agregado[COLUMNAS_TRAFICO]


def limpiar_economia(ruta, anio=2024):
    """Carga OECD, convierte textos con separadores a números y filtra el año."""
    df = _estandarizar_columnas(pd.read_csv(ruta))
    df['city_gdp/capita'] = (df['city_gdp/capita'].astype(str)
                             .str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float))
    df['unemployment_%'] = (df['unemployment_%'].astype(str)
                            .str.replace('%', '', regex=False).str.replace(',', '.', regex=False).astype(float))
    df['pm2.5_(μg/m³)'] = df['pm2.5_(μg/m³)'].astype(str).str.replace(',', '.', regex=False).astype(float)
    df['population'] = df['population_(m)'].astype(str).str.replace(',', '.', regex=False).astype(float) * 1_000_000
    return df[df['year'] == anio][COLUMNAS_ECONOMIA].copy()


def construir_dataset(ruta_trafico, ruta_economia, anio=2024):
    """Une tráfico y economía (inner join por ciudad) para un único año."""
    return limpiar_trafico(ruta_trafico, anio).merge(limpiar_economia(ruta_economia, anio), on='city', how='inner')


if __name__ == '__main__':
    trafico, economia, salida = sys.argv[1:4]
    dataset = construir_dataset(trafico, economia)
    dataset.to_csv(salida, index=False)
    print(f'Dataset exportado: {salida} ({dataset.shape[0]} ciudades x {dataset.shape[1]} columnas)')
