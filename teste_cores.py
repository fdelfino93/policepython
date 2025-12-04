import pandas as pd
import geopandas as gpd
import folium
import unicodedata

def normalizar_nome(texto):
    if not isinstance(texto, str):
        return str(texto)
    nfkd = unicodedata.normalize('NFKD', texto)
    sem_acento = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return sem_acento.upper().strip()

# Carregar dados
gdf = gpd.read_file('curitiba_bairros.geojson')
gdf = gdf.to_crs(epsg=4326)
gdf['chave_bairro'] = gdf['NOME'].apply(normalizar_nome)

df = pd.read_csv('Dados_crimes.csv', sep=';', encoding='utf-8-sig')
df['chave_bairro'] = df['Bairro'].apply(normalizar_nome)

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

# Categorização
CATEGORIAS_SEGURANCA = ['Alta segurança', 'Segurança moderada', 'Segurança baixa', 'Segurança crítica']
CORES_SEGURANCA = {
    'Alta segurança': '#2ecc71',
    'Segurança moderada': '#f1c40f',
    'Segurança baixa': '#e67e22',
    'Segurança crítica': '#e74c3c'
}

stats['CATEGORIA'] = 'Sem Classificação'
stats.loc[stats['SCORE'] == 0, 'CATEGORIA'] = 'Sem Ocorrências'

high_score_mask = stats['SCORE'] > 0
df_high_score = stats[high_score_mask]

if not df_high_score.empty:
    stats.loc[high_score_mask, 'CATEGORIA'] = pd.qcut(
        df_high_score['SCORE'], 4, labels=CATEGORIAS_SEGURANCA, duplicates='drop'
    )

CORES_TODAS = CORES_SEGURANCA.copy()
CORES_TODAS['Sem Ocorrências'] = '#3186cc'
CORES_TODAS['Sem Classificação'] = '#d3d3d3'

stats['COR'] = stats['CATEGORIA'].map(CORES_TODAS)

# Merge
gdf_final = gdf.merge(stats[['chave_bairro', 'CATEGORIA', 'COR', 'SCORE']], on='chave_bairro', how='left')
gdf_final['COR'] = gdf_final['COR'].fillna('#d3d3d3')
gdf_final['CATEGORIA'] = gdf_final['CATEGORIA'].fillna('Sem Ocorrências')
gdf_final['SCORE'] = gdf_final['SCORE'].fillna(0)

print("Bairros com cores:")
print(gdf_final[['NOME', 'CATEGORIA', 'COR', 'SCORE']].head(20))
print(f"\nTotal de bairros: {len(gdf_final)}")
print(f"Distribuição de categorias:")
print(gdf_final['CATEGORIA'].value_counts())

# Criar mapa simples
mapa = folium.Map(location=[-25.4284, -49.2733], zoom_start=11)

# Converter para GeoJSON e adicionar
geojson_data = gdf_final.__geo_interface__

folium.GeoJson(
    geojson_data,
    style_function=lambda feature: {
        'fillColor': feature['properties']['COR'],
        'color': 'black',
        'weight': 2,
        'fillOpacity': 0.7
    },
    tooltip=folium.GeoJsonTooltip(
        fields=['NOME', 'CATEGORIA', 'SCORE'],
        aliases=['Bairro:', 'Classificação:', 'Score:']
    )
).add_to(mapa)

mapa.save('teste_mapa.html')
print("\nMapa salvo em teste_mapa.html")
