import geopandas as gpd

# Carregar o GeoJSON
gdf = gpd.read_file('curitiba_bairros.geojson')

print("CRS original (errado):", gdf.crs)
print("Bounds originais:", gdf.total_bounds)

# Forcar o CRS correto - as coordenadas sao UTM zona 22S (SIRGAS 2000)
gdf = gdf.set_crs(epsg=31982, allow_override=True)
print("\nCRS forcado:", gdf.crs)

# Agora converter para WGS84 (lat/long)
gdf = gdf.to_crs(epsg=4326)
print("CRS convertido:", gdf.crs)
print("Novos bounds:", gdf.total_bounds)

# Verificar primeiro ponto
print("\nPrimeiro ponto convertido:", list(gdf.geometry.iloc[0].exterior.coords)[0])

# Salvar arquivo corrigido
gdf.to_file('curitiba_bairros_corrigido.geojson', driver='GeoJSON')
print("\nArquivo corrigido salvo como 'curitiba_bairros_corrigido.geojson'")
