import pyautogui
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.webdriver.common.action_chains import ActionChains

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

# Abrir o Google
driver.get("https://www.google.com")
time.sleep(1)

imagem = r"C:\Harve-Aula4-IMG\IMG.png"

posicao = pyautogui.locateCenterOnScreen(imagem, confidence=0.8)
pyautogui.click(posicao)
time.sleep(3)

elemento = driver.find_element(By.XPATH, '//*[@id="APjFqb"]')
elemento.send_keys('Notebook Dell')
time.sleep(2)
elemento.submit()
time.sleep(2)

imagem_2 = r'C:\Harve-Aula4-IMG\Modelo.png'

posicao = pyautogui.locateCenterOnScreen(imagem_2, confidence=0.8)
pyautogui.click(posicao)
time.sleep(3)

imagem_3 = r'C:\Harve-Aula4-IMG\item.png'

posicao = pyautogui.locateCenterOnScreen(imagem_3, confidence=0.8)
pyautogui.click(posicao)
time.sleep(5)
