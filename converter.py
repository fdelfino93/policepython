import geopandas as gpd
import pyogrio
from shapely.geometry import shape

# Caminho para o .shp
caminho = r"D:\vitor\Estudo\PythonHarve\DIVISA_DE_BAIRROS\DIVISA_DE_BAIRROS.shp"

# 1. Ler os dados usando pyogrio
df = pyogrio.read_dataframe(caminho)

# 2. Converter para GeoDataFrame do GeoPandas
gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")

# 3. Exportar para GeoJSON
gdf.to_file("curitiba_bairros.geojson", driver="GeoJSON")

print("GeoJSON criado com sucesso usando pyogrio!")
