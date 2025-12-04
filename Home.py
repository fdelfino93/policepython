import streamlit as st
import pandas as pd
import unicodedata
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import json

st.set_page_config(page_title="Consulta de Crimes por Bairro", layout="wide")

# Esconder navegação lateral (links Home/bairros)
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# =================================================
# FUNÇÕES DE LIMPEZA E CATEGORIZAÇÃO
# =================================================

CATEGORIAS_SEGURANCA = [
    'Alta segurança', 'Segurança moderada', 'Segurança baixa', 'Segurança crítica'
]
CORES_SEGURANCA = {
    'Alta segurança': '#2ecc71',        # Verde (🟢)
    'Segurança moderada': '#f1c40f',    # Amarelo (🟡)
    'Segurança baixa': '#e67e22',       # Laranja (🟠)
    'Segurança crítica': '#e74c3c'      # Vermelho (🔴)
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
        # Tentar carregar arquivo corrigido primeiro, senao o original
        try:
            gdf = gpd.read_file("curitiba_bairros_corrigido.geojson")
        except:
            gdf = gpd.read_file("curitiba_bairros.geojson")
            # Corrigir CRS se necessario (arquivo original tem CRS errado)
            if gdf.total_bounds[0] > 1000:  # Coordenadas em metros, nao graus
                gdf = gdf.set_crs(epsg=31982, allow_override=True)
                gdf = gdf.to_crs(epsg=4326)
            else:
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
            df = pd.read_csv(nome_arquivo, sep=";", encoding='utf-8-sig')
            break
        except (FileNotFoundError, UnicodeDecodeError):
            try:
                df = pd.read_csv(nome_arquivo, sep=";", encoding='latin1')
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

    # Calcular contagem de homicídios/mortes por bairro
    def is_homicidio(crime):
        c = str(crime).upper()
        return any(x in c for x in ['HOMICIDIO', 'HOMICÍDIO', 'LATROCINIO', 'LATROCÍNIO', 'MORTE', 'CVLI'])

    df_curitiba['IS_HOMICIDIO'] = df_curitiba[col_csv_crime].apply(is_homicidio)
    homicidios = df_curitiba[df_curitiba['IS_HOMICIDIO']].groupby('chave_bairro').size().reset_index()
    homicidios.columns = ['chave_bairro', 'HOMICIDIOS']
    stats = stats.merge(homicidios, on='chave_bairro', how='left')
    stats['HOMICIDIOS'] = stats['HOMICIDIOS'].fillna(0).astype(int)

    # Categorização de Segurança
    stats['CATEGORIA'] = 'Sem Classificação'
    stats.loc[stats['SCORE'] == 0, 'CATEGORIA'] = 'Sem Ocorrências'

    high_score_mask = stats['SCORE'] > 0
    df_high_score = stats[high_score_mask]

    if not df_high_score.empty:
        try:
            stats.loc[high_score_mask, 'CATEGORIA'] = pd.qcut(
                df_high_score['SCORE'], 4, labels=CATEGORIAS_SEGURANCA, duplicates='drop'
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
    st.markdown("🔴 **Segurança crítica**")


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
        # RESUMO DE CRIMES POR CATEGORIA
        st.subheader("Resumo de Ocorrências")

        # Categorizar crimes
        def categorizar_crime(crime):
            c = str(crime).upper()
            if any(x in c for x in ['HOMICIDIO', 'HOMICÍDIO', 'MORTE', 'CVLI', 'LATROCINIO', 'LATROCÍNIO']):
                return 'Homicídios e Mortes'
            if any(x in c for x in ['ROUBO']):
                return 'Roubos'
            if any(x in c for x in ['FURTO']):
                return 'Furtos'
            if any(x in c for x in ['ESTUPRO', 'FEMINICIDIO', 'FEMINICÍDIO']):
                return 'Crimes Sexuais e Feminicídio'
            if any(x in c for x in ['AGRESSAO', 'AGRESSÃO', 'LESAO', 'LESÃO']):
                return 'Agressões'
            if any(x in c for x in ['AMEACA', 'AMEAÇA']):
                return 'Ameaças'
            return 'Outros'

        col_crime = next((c for c in df_bairro.columns if any(x in c.upper() for x in ['NATUREZA', 'CRIME', 'DELITO'])), None)

        if col_crime:
            df_bairro['CATEGORIA_CRIME'] = df_bairro[col_crime].apply(categorizar_crime)
            resumo = df_bairro['CATEGORIA_CRIME'].value_counts().sort_values(ascending=False)

            # Exibir resumo em colunas
            cols = st.columns(3)
            for idx, (categoria, quantidade) in enumerate(resumo.items()):
                with cols[idx % 3]:
                    st.metric(label=categoria, value=int(quantidade))

        st.markdown("---")

        # LISTA DETALHADA DE OCORRÊNCIAS
        st.subheader(f"Lista Detalhada de Ocorrências ({len(df_bairro)} registros)")

        cols_to_show = [
            'NATUREZA', 'MUNICÍPIO', col_name_csv, 'ANO', 'MÊS', 'DIA',
            'DIA DA SEMANA', 'HORA', 'IDADE', 'SEXO', 'RAÇA/COR'
        ]
        df_display = df_bairro[[c for c in cols_to_show if c in df_bairro.columns]]

        st.dataframe(df_display, width='stretch')
    else:
        st.info("Nenhuma ocorrência detalhada de crime encontrada neste bairro.")

    st.stop()

else:
    
    st.title("Mapa Curitiba")
    st.markdown("---")
    
    if gdf_map is not None:
        st.subheader("Selecione um bairro na barra lateral ou passe o mouse no mapa:")

        # Fazer merge dos dados
        gdf_map_final = gdf_map.merge(df_stats[['chave_bairro', 'CATEGORIA', 'COR', 'SCORE', 'HOMICIDIOS']],
                                      on='chave_bairro', how='left')

        # Preencher valores NaN
        gdf_map_final['COR'] = gdf_map_final['COR'].fillna('#d3d3d3')
        gdf_map_final['CATEGORIA'] = gdf_map_final['CATEGORIA'].fillna('Sem Ocorrências')
        gdf_map_final['SCORE'] = gdf_map_final['SCORE'].fillna(0)
        gdf_map_final['HOMICIDIOS'] = gdf_map_final['HOMICIDIOS'].fillna(0).astype(int)

        # Criar mapa
        centro = [-25.4284, -49.2733]
        mapa = folium.Map(location=centro, zoom_start=12, tiles="cartodbpositron")

        # Converter GeoDataFrame para GeoJSON com as propriedades corretas
        geojson_str = gdf_map_final.to_json()
        geojson_data = json.loads(geojson_str)

        # Adicionar camada GeoJSON com estilo baseado na propriedade COR
        geojson_layer = folium.GeoJson(
            geojson_data,
            name="Bairros",
            style_function=lambda feature: {
                'fillColor': feature['properties']['COR'],
                'color': '#333333',
                'weight': 1.5,
                'fillOpacity': 0.7
            },
            highlight_function=lambda feature: {
                'fillColor': feature['properties']['COR'],
                'color': '#000000',
                'weight': 3,
                'fillOpacity': 0.9
            },
            tooltip=folium.GeoJsonTooltip(
                fields=[col_name_geo, 'CATEGORIA', 'SCORE', 'HOMICIDIOS'],
                aliases=['Bairro:', 'Classificação:', 'Score:', 'Homicídios/Mortes:'],
                style="font-size: 14px;"
            )
        )
        geojson_layer.add_to(mapa)

        # Exibir mapa usando st_folium com suporte a clique
        map_data = st_folium(mapa, width=1100, height=600)

        # Verificar se o usuário clicou em um bairro
        if map_data and map_data.get("last_clicked"):
            clicked = map_data["last_clicked"]
            lat = clicked.get("lat")
            lng = clicked.get("lng")
            if lat and lng:
                from shapely.geometry import Point
                ponto = Point(lng, lat)
                # Encontrar bairro pelo ponto clicado
                for idx, row in gdf_map_final.iterrows():
                    if row.geometry.contains(ponto):
                        bairro_clicado = row[col_name_geo]
                        if bairro_clicado and bairro_clicado in lista_bairros:
                            st.query_params["regiao"] = bairro_clicado
                            st.rerun()
                        break
        
    else:
        st.error("ERRO: O mapa não pode ser exibido. O arquivo 'curitiba_bairros.geojson' não foi encontrado na mesma pasta do script.")
        st.info("⬅️ **Selecione um bairro na barra lateral para visualizar a lista completa de ocorrências.**")