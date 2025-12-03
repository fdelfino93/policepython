import streamlit as st
import pandas as pd
import unicodedata
import geopandas as gpd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Consulta de Crimes por Bairro", layout="wide")

# =================================================
# FUNÇÕES DE LIMPEZA E CATEGORIZAÇÃO
# =================================================

CATEGORIAS_SEGURANCA = [
    'Alta segurança', 'Segurança moderada', 'Segurança baixa', 
    'Segurança muito baixa', 'Segurança crítica'
]
CORES_SEGURANCA = {
    'Seguro': '#2ecc71', 'Segurança moderada': '#f1c40f', 'Segurança baixa': '#e67e22', 
    'Segurança muito baixa': '#e74c3c', 'Segurança crítica': '#c0392b'
}
CORES_TODAS = CORES_SEGURANCA.copy()
CORES_TODAS['Sem Ocorrências'] = '#3186cc'
CORES_TODAS['Sem Classificação'] = '#808080'
CORES_TODAS['Análise Indisponível'] = '#808080'


def normalizar_nome(texto):
    if not isinstance(texto, str):
        return str(texto)
    nfkd = unicodedata.normalize('NFKD', texto)
    sem_acento = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return sem_acento.upper().strip()

# =================================================
# 1) CARREGAMENTO E PROCESSAMENTO DE DADOS (CACHE)
# =================================================
@st.cache_data
def carregar_e_processar_dados():
    
    gdf = None
    col_geo = None
    try:
        gdf = gpd.read_file("curitiba_bairros.geojson")
        gdf = gdf.to_crs(epsg=4326)
        possible_cols = ["NOME", "name", "BAIRRO", "bairro", "NOME_BAIRRO"]
        col_geo = next((c for c in possible_cols if c in gdf.columns), None)
        if not col_geo:
            raise ValueError("GeoJSON lacks a recognizable bairro column.")
        gdf['chave_bairro'] = gdf[col_geo].apply(normalizar_nome)
    except Exception as e:
        st.warning(f"Erro ao carregar GeoJSON para o mapa: O arquivo 'curitiba_bairros.geojson' não foi encontrado ou está inválido. {e}. O mapa não será exibido.")

    arquivos_csv = ["Dados_crimes.csv", "dados_crimes.csv", "Dados_crimes.csv.csv"]
    df = None
    
    for nome_arquivo in arquivos_csv:
        try:
            df = pd.read_csv(nome_arquivo, sep=";", encoding='latin1')
            st.success(f"Arquivo '{nome_arquivo}' carregado com sucesso!")
            break
        except FileNotFoundError:
            try:
                df = pd.read_csv(nome_arquivo, sep=";", encoding='utf-8')
                st.success(f"Arquivo '{nome_arquivo}' carregado com sucesso!")
                break
            except Exception:
                continue

    if df is None:
        st.error("ERRO: Nenhum arquivo de dados de crime foi encontrado.")
        return None, None, None, None, None
        
    df.columns = [c.upper().strip() for c in df.columns]
    col_csv_bairro = next((c for c in df.columns if 'BAIRRO' in c), None)
    col_csv_crime = next((c for c in df.columns if any(x in c for x in ['NATUREZA', 'CRIME', 'DELITO'])), None)

    if not col_csv_bairro or not col_csv_crime:
        st.error("ERRO: Colunas 'Bairro' ou 'Natureza' não encontradas no arquivo CSV.")
        return None, None, None, None, None
    
    if 'MUNICÍPIO' in df.columns:
        df_curitiba = df[df['MUNICÍPIO'].str.upper().str.strip() == 'CURITIBA'].copy()
    else:
        df_curitiba = df.copy() 

    df_curitiba['chave_bairro'] = df_curitiba[col_csv_bairro].apply(normalizar_nome)

    def definir_peso(crime):
        c = str(crime).upper()
        if any(x in c for x in ['HOMICIDIO', 'LATROCINIO', 'ESTUPRO', 'MORTE', 'CVLI']): return 10
        if any(x in c for x in ['ROUBO', 'ARMA', 'AGRESSAO']): return 5
        if any(x in c for x in ['FURTO', 'DANO', 'INVASAO', 'AMEACA']): return 2
        return 3 

    df_curitiba['PESO'] = df_curitiba[col_csv_crime].apply(definir_peso)
    stats = df_curitiba.groupby('chave_bairro')['PESO'].sum().reset_index()
    stats.columns = ['chave_bairro', 'SCORE']

    # Categorização de Segurança
    stats['CATEGORIA'] = 'Sem Classificação'
    stats.loc[stats['SCORE'] == 0, 'CATEGORIA'] = 'Sem Ocorrências'

    high_score_mask = stats['SCORE'] > 0
    df_high_score = stats[high_score_mask]

    if not df_high_score.empty:
        try:
            stats.loc[high_score_mask, 'CATEGORIA'] = pd.qcut(
                df_high_score['SCORE'], 5, labels=CATEGORIAS_SEGURANCA, duplicates='drop'
            )
        except Exception:
            stats.loc[high_score_mask, 'CATEGORIA'] = 'Análise Indisponível'
    
    stats['COR'] = stats['CATEGORIA'].map(CORES_TODAS)
    
    return gdf, col_geo, col_csv_bairro, df_curitiba, stats

# =================================================
# EXECUÇÃO DO CÓDIGO PRINCIPAL
# =================================================

gdf_map, col_name_geo, col_name_csv, df_crimes_raw, df_stats = carregar_e_processar_dados()

if df_stats is None:
    st.stop()
    
stats_bairros = df_stats.set_index('chave_bairro').to_dict('index')
lista_bairros = sorted(df_crimes_raw[col_name_csv].unique()) 


# =================================================
# 2) SIDEBAR E SELEÇÃO
# =================================================
with st.sidebar:
    st.header("Consulta de Dados")
    
    bairro_atual = st.query_params.get("regiao", "Selecione...")
    
    try:
        default_index = lista_bairros.index(bairro_atual) + 1 
    except ValueError:
        default_index = 0

    bairro_selecionado = st.selectbox(
        "Escolha um bairro:",
        options=["Selecione..."] + lista_bairros,
        index=default_index
    )
    
    if bairro_selecionado != bairro_atual and bairro_selecionado != "Selecione...":
        st.query_params["regiao"] = bairro_selecionado
        st.rerun()

    if st.button("Limpar Seleção"):
        if "regiao" in st.query_params:
            st.query_params.clear()
            st.rerun()
        
    st.markdown("### Classificação de Risco")
    st.markdown("🟢 **Alta segurança**")
    st.markdown("🟡 **Segurança moderada**")
    st.markdown("🟠 **Segurança baixa**")
    st.markdown("🔴 **Segurança muito baixa**")
    st.markdown("⚫ **Segurança crítica**")


# =================================================
# 3) EXIBIÇÃO DE DETALHES OU MAPA HOME
# =================================================
bairro_foco = st.query_params.get("regiao")

if bairro_foco and bairro_foco != "Selecione...":
    
    st.title(f"Dados Detalhados: {bairro_foco}")
    
    bairro_key = normalizar_nome(bairro_foco)
    
    dados_stats = stats_bairros.get(bairro_key, {})
    val_score = dados_stats.get('SCORE', 0)
    val_cat = dados_stats.get('CATEGORIA', 'Sem dados')
    cor = dados_stats.get('COR', '#3186cc')

    c1, c2 = st.columns(2)
    c1.markdown(f"**Nível de Segurança (Calculado):** <span style='color:{cor}'>**{val_cat}**</span>", unsafe_allow_html=True)
    c2.metric("Score de Risco (Acumulado)", f"{val_score:.0f}")
    
    st.markdown("---")
    
    df_bairro = df_crimes_raw[df_crimes_raw['chave_bairro'] == bairro_key].drop(columns=['chave_bairro', 'PESO'], errors='ignore')
    
    if not df_bairro.empty:
        st.subheader(f"Lista de Ocorrências ({len(df_bairro)} registros)")
        
        cols_to_show = [
            'NATUREZA', 'MUNICÍPIO', col_name_csv, 'ANO', 'MÊS', 'DIA', 
            'DIA DA SEMANA', 'HORA', 'IDADE', 'SEXO', 'RAÇA/COR'
        ]
        df_display = df_bairro[[c for c in cols_to_show if c in df_bairro.columns]]

        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("Nenhuma ocorrência detalhada de crime encontrada neste bairro.")

    st.stop()

else:
    
    st.title("Mapa Curitiba")
    st.markdown("---")
    
    if gdf_map is not None:
        st.subheader("Clique em um bairro para ver os detalhes:")
        
        gdf_map_final = gdf_map.merge(df_stats[['chave_bairro', 'CATEGORIA', 'COR']], 
                                      on='chave_bairro', how='left')
        
        gdf_map_final['COR'] = gdf_map_final['COR'].fillna('#808080')
        
        centro = [-25.4284, -49.2733]
        zoom = 11

        mapa = folium.Map(location=centro, zoom_start=zoom, tiles="CartoDB positron")

        folium.GeoJson(
            gdf_map_final,
            name="Segurança",
            style_function=lambda x: {
                'fillColor': x['properties'].get('COR', '#808080'), 
                'color': 'black',
                'weight': 1,
                'fillOpacity': 0.7
            },
            tooltip=folium.GeoJsonTooltip(
                fields=[col_name_geo, 'CATEGORIA'], 
                aliases=['Bairro:', 'Nível:'],
            )
        ).add_to(mapa)

        result = st_folium(mapa, width=1200, height=600)
        
        if result and "last_object_clicked" in result:
            item = result["last_object_clicked"]
            
            if item and "properties" in item:
                if col_name_geo in item["properties"]:
                    bairro_clicado = item["properties"][col_name_geo]
                    st.query_params["regiao"] = bairro_clicado
                    st.rerun()
        
    else:
        st.error("ERRO: O mapa não pode ser exibido. O arquivo 'curitiba_bairros.geojson' não foi encontrado na mesma pasta do script.")
        st.info("⬅️ **Selecione um bairro na barra lateral (Sidebar) para visualizar a lista completa de ocorrências.**")