import pandas as pd
import geopandas as gpd
import folium
import unicodedata
import json

def normalizar_nome(texto):
    if not isinstance(texto, str):
        return str(texto)
    nfkd = unicodedata.normalize('NFKD', texto)
    sem_acento = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return sem_acento.upper().strip()

# Carregar dados
print("Carregando GeoJSON...")
gdf = gpd.read_file('curitiba_bairros.geojson')
print(f"CRS original: {gdf.crs}")
gdf = gdf.to_crs(epsg=4326)
print(f"CRS convertido: {gdf.crs}")
gdf['chave_bairro'] = gdf['NOME'].apply(normalizar_nome)

print("\nCarregando CSV...")
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

stats['CATEGORIA'] = 'Sem Ocorrências'

high_score_mask = stats['SCORE'] > 0
df_high_score = stats[high_score_mask]

if not df_high_score.empty:
    stats.loc[high_score_mask, 'CATEGORIA'] = pd.qcut(
        df_high_score['SCORE'], 4, labels=CATEGORIAS_SEGURANCA, duplicates='drop'
    )

CORES_TODAS = CORES_SEGURANCA.copy()
CORES_TODAS['Sem Ocorrências'] = '#d3d3d3'

stats['COR'] = stats['CATEGORIA'].map(CORES_TODAS)

# Merge
print("\nFazendo merge...")
gdf_final = gdf.merge(stats[['chave_bairro', 'CATEGORIA', 'COR', 'SCORE']], on='chave_bairro', how='left')
gdf_final['COR'] = gdf_final['COR'].fillna('#d3d3d3')
gdf_final['CATEGORIA'] = gdf_final['CATEGORIA'].fillna('Sem Ocorrências')
gdf_final['SCORE'] = gdf_final['SCORE'].fillna(0)

print(f"\nTotal de bairros: {len(gdf_final)}")
print("\nExemplo de dados:")
print(gdf_final[['NOME', 'CATEGORIA', 'COR', 'SCORE']].head(10))

# Verificar geometria
print(f"\nTipo de geometria: {gdf_final.geometry.type.unique()}")
print(f"Bounds: {gdf_final.total_bounds}")

# Criar mapa centrado em Curitiba
centro = gdf_final.geometry.centroid.y.mean(), gdf_final.geometry.centroid.x.mean()
print(f"\nCentro calculado: {centro}")

mapa = folium.Map(location=[-25.4284, -49.2733], zoom_start=11, tiles="OpenStreetMap")

# Converter para GeoJSON
print("\nConvertendo para GeoJSON...")
geojson_str = gdf_final.to_json()
geojson_data = json.loads(geojson_str)

print(f"Tipo GeoJSON: {geojson_data['type']}")
print(f"Número de features: {len(geojson_data['features'])}")
print(f"Primeira feature props: {list(geojson_data['features'][0]['properties'].keys())}")

# Verificar uma feature
feat = geojson_data['features'][0]
print(f"\nPrimeira feature:")
print(f"  Nome: {feat['properties'].get('NOME')}")
print(f"  COR: {feat['properties'].get('COR')}")
print(f"  Geometry type: {feat['geometry']['type']}")

# Adicionar GeoJson
print("\nAdicionando ao mapa...")

def style_function(feature):
    cor = feature['properties'].get('COR', '#d3d3d3')
    return {
        'fillColor': cor,
        'color': '#000000',
        'weight': 2,
        'fillOpacity': 0.7
    }

folium.GeoJson(
    geojson_data,
    style_function=style_function,
    tooltip=folium.GeoJsonTooltip(
        fields=['NOME', 'CATEGORIA', 'SCORE'],
        aliases=['Bairro:', 'Classificação:', 'Score:']
    )
).add_to(mapa)

# Salvar
mapa.save('teste_mapa_v2.html')
print("\nMapa salvo em teste_mapa_v2.html")
print("Abra o arquivo no navegador para verificar!")
