import pandas as pd
import geopandas as gpd
import unicodedata

def normalizar_nome(texto):
    if not isinstance(texto, str):
        return str(texto)
    nfkd = unicodedata.normalize('NFKD', texto)
    sem_acento = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return sem_acento.upper().strip()

# Carregar GeoJSON
gdf = gpd.read_file('curitiba_bairros.geojson')
print('Colunas do GeoJSON:', gdf.columns.tolist())
print('\nTotal de bairros no GeoJSON:', len(gdf))
print('\nPrimeiros 5 bairros do GeoJSON:')
print(gdf['NOME'].head().tolist())

# Carregar CSV
df = pd.read_csv('Dados_crimes.csv', sep=';', encoding='utf-8-sig')
print('\n\nTotal de registros no CSV:', len(df))
print('Bairros únicos no CSV:', df['Bairro'].nunique())
print('\nPrimeiros 5 bairros do CSV:')
print(df['Bairro'].unique()[:5])

# Normalizar e comparar
gdf['chave_bairro'] = gdf['NOME'].apply(normalizar_nome)
df['chave_bairro'] = df['Bairro'].apply(normalizar_nome)

print('\n\nBairros normalizados do GeoJSON (5 primeiros):')
print(gdf['chave_bairro'].head().tolist())

print('\nBairros normalizados do CSV (5 primeiros):')
print(df['chave_bairro'].unique()[:5])

# Calcular scores
def definir_peso(crime):
    c = str(crime).upper()
    if any(x in c for x in ['HOMICIDIO', 'LATROCINIO', 'ESTUPRO', 'MORTE', 'CVLI']): return 10
    if any(x in c for x in ['ROUBO', 'ARMA', 'AGRESSAO']): return 5
    if any(x in c for x in ['FURTO', 'DANO', 'INVASAO', 'AMEACA']): return 2
    return 3

df['PESO'] = df['Natureza'].apply(definir_peso)
stats = df.groupby('chave_bairro')['PESO'].sum().reset_index()
stats.columns = ['chave_bairro', 'SCORE']

print('\n\nStatísticas de crimes por bairro (10 primeiros):')
print(stats.sort_values('SCORE', ascending=False).head(10))

# Merge
merged = gdf.merge(stats, on='chave_bairro', how='left')
print('\n\nTotal de bairros após merge:', len(merged))
print('Bairros com dados de crime:', merged['SCORE'].notna().sum())
print('Bairros sem dados de crime:', merged['SCORE'].isna().sum())

print('\n\nBairros do GeoJSON que não têm correspondência no CSV:')
sem_match = gdf[~gdf['chave_bairro'].isin(df['chave_bairro'])]
print(sem_match[['NOME', 'chave_bairro']].head(10))
