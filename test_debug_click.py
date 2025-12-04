"""Testar debug do clique"""
import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.set_viewport_size({"width": 1400, "height": 1200})

    print("Acessando aplicação de debug...")
    page.goto("http://localhost:8502")
    time.sleep(6)

    # Clicar no mapa
    iframes = page.query_selector_all("iframe")
    if iframes:
        bbox = iframes[0].bounding_box()
        if bbox:
            click_x = bbox['x'] + bbox['width'] / 2
            click_y = bbox['y'] + bbox['height'] / 2
            print(f"Clicando em ({click_x}, {click_y})...")
            page.mouse.click(click_x, click_y)
            time.sleep(3)

            # Scroll para ver os dados retornados
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            page.screenshot(path="debug_3_dados.png", full_page=True)
            print("Screenshot salvo!")

    time.sleep(2)
    browser.close()
    print("Teste concluído!")
