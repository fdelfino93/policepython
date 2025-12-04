"""Testar se o mapa HTML gerado tem cores"""
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    # Abrir o arquivo HTML de teste
    page.goto("file:///c:/Users/Fernando/Documents/PY/PolicePython/policepython/teste_mapa.html")

    time.sleep(3)

    # Tirar screenshot
    page.screenshot(path="teste_mapa_screenshot.png")
    print("Screenshot do mapa HTML salvo!")

    time.sleep(2)
    browser.close()
