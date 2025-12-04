"""Script para debugar st_folium"""
import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import json

st.set_page_config(page_title="Debug st_folium", layout="wide")

# Carregar dados
gdf = gpd.read_file("curitiba_bairros_corrigido.geojson")
gdf = gdf.to_crs(epsg=4326)

# Criar mapa
mapa = folium.Map(location=[-25.4284, -49.2733], zoom_start=12)

# Adicionar GeoJSON
geojson_data = json.loads(gdf.to_json())
folium.GeoJson(
    geojson_data,
    style_function=lambda f: {'fillColor': '#3186cc', 'color': '#333', 'weight': 1, 'fillOpacity': 0.5},
    tooltip=folium.GeoJsonTooltip(fields=['NOME'], aliases=['Bairro:'])
).add_to(mapa)

# Exibir mapa
st.write("Clique em um bairro e veja os dados retornados:")
map_data = st_folium(mapa, width=800, height=500)

# Mostrar dados retornados
st.write("### Dados retornados pelo st_folium:")
st.json(map_data)
