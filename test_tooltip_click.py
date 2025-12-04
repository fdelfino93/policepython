"""Testar tooltip com homicídios e clique no bairro"""
import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    print("Acessando aplicação Streamlit...")
    page.goto("http://localhost:8501")
    time.sleep(6)  # Aguardar carregamento completo

    print("Tirando screenshot inicial...")
    page.screenshot(path="test_click_1_inicial.png")

    # Encontrar o iframe do mapa e clicar em um bairro
    print("Procurando iframe do mapa...")
    iframes = page.query_selector_all("iframe")
    print(f"Encontrados {len(iframes)} iframes")

    if iframes:
        # Pegar bounding box do iframe
        bbox = iframes[0].bounding_box()
        if bbox:
            # Clicar no centro do mapa
            click_x = bbox['x'] + bbox['width'] / 2
            click_y = bbox['y'] + bbox['height'] / 2
            print(f"Clicando em ({click_x}, {click_y})...")

            page.mouse.click(click_x, click_y)
            time.sleep(4)
            page.screenshot(path="test_click_2_apos_clique.png")

            # Verificar se navegou para detalhes do bairro
            page.screenshot(path="test_click_3_final.png")
            print("Screenshots salvos!")

    time.sleep(2)
    browser.close()
    print("\nTeste concluído!")
