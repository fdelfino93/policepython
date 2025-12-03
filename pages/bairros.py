import streamlit as st

st.set_page_config(page_title="Região", layout="wide")

params = st.query_params
bairro = params.get("regiao")

if not bairro:
    st.error("Nenhuma região selecionada.")
    st.markdown("[Voltar ao mapa](../)")
    st.stop()

st.title(f"Bairro: {bairro}")
st.write(f"Informações sobre a região **{bairro}**.")

st.markdown("[Voltar ao mapa](../)")
