"""Script de teste para a aplicação Streamlit usando Playwright"""
from playwright.sync_api import sync_playwright
import time

def test_streamlit_app():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print("Acessando aplicação Streamlit...")
        page.goto("http://localhost:8501")

        # Aguardar carregamento
        time.sleep(3)

        print("Testando visualização inicial do mapa...")
        # Verificar se o título está presente
        if page.locator("text=Mapa Curitiba").is_visible():
            print("[OK] Titulo 'Mapa Curitiba' encontrado")
        else:
            print("[ERRO] Titulo 'Mapa Curitiba' nao encontrado")

        # Verificar se existe o sidebar
        print("\nTestando sidebar...")
        if page.locator("text=Consulta de Dados").is_visible():
            print("[OK] Sidebar 'Consulta de Dados' encontrada")
        else:
            print("[ERRO] Sidebar 'Consulta de Dados' nao encontrada")

        # Verificar classificação de risco
        print("\nVerificando classificacao de risco...")
        if page.locator("text=Classificação de Risco").is_visible():
            print("[OK] Classificacao de Risco encontrada")
        else:
            print("[ERRO] Classificacao de Risco nao encontrada")

        # Testar seleção de bairro
        print("\nTestando seleção de bairro...")
        time.sleep(2)

        try:
            # Clicar no selectbox
            selectbox = page.locator("div[data-testid='stSelectbox']").first
            if selectbox.is_visible():
                selectbox.click()
                time.sleep(1)

                # Selecionar um bairro (exemplo: CENTRO)
                option = page.locator("text=CENTRO").first
                if option.is_visible():
                    option.click()
                    print("[OK] Bairro 'CENTRO' selecionado")
                    time.sleep(3)

                    # Verificar se os dados detalhados aparecem
                    if page.locator("text=Dados Detalhados").is_visible():
                        print("[OK] Dados detalhados do bairro exibidos")
                    else:
                        print("[ERRO] Dados detalhados do bairro nao encontrados")
                else:
                    print("[ERRO] Opcao 'CENTRO' nao encontrada")
            else:
                print("[ERRO] Selectbox nao encontrado")
        except Exception as e:
            print(f"Erro ao testar selecao de bairro: {e}")

        # Tirar screenshot
        print("\nTirando screenshot da aplicacao...")
        page.screenshot(path="streamlit_test_screenshot.png")
        print("[OK] Screenshot salvo como 'streamlit_test_screenshot.png'")

        # Verificar dados do CSV
        print("\nVerificando informações do CSV...")
        time.sleep(2)

        print("\n" + "="*50)
        print("Teste concluído!")
        print("="*50)

        # Manter navegador aberto por alguns segundos
        time.sleep(5)

        browser.close()

if __name__ == "__main__":
    test_streamlit_app()
