"""Testar tooltip com homicídios"""
import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    print("Acessando aplicação Streamlit...")
    page.goto("http://localhost:8501")
    time.sleep(6)

    # Limpar seleção atual se houver
    limpar_btn = page.query_selector("text=Limpar Seleção")
    if limpar_btn:
        limpar_btn.click()
        time.sleep(3)

    print("Tirando screenshot do mapa...")
    page.screenshot(path="test_final_1_mapa.png")

    # Mover mouse sobre o mapa para ver tooltip
    iframes = page.query_selector_all("iframe")
    if iframes:
        bbox = iframes[0].bounding_box()
        if bbox:
            # Mover para diferentes posições
            for i, (dx, dy) in enumerate([(0.3, 0.5), (0.5, 0.4), (0.6, 0.6)]):
                x = bbox['x'] + bbox['width'] * dx
                y = bbox['y'] + bbox['height'] * dy
                page.mouse.move(x, y)
                time.sleep(1.5)
                page.screenshot(path=f"test_final_2_hover_{i+1}.png")
                print(f"Screenshot {i+1} salvo!")

    time.sleep(2)
    browser.close()
    print("Teste concluído!")
