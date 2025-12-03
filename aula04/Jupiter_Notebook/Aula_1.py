from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys  # ← IMPORTANTE!
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
import time

# Configurar o WebDriver automaticamente
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

# Abrir o formulário
driver.get("https://form.respondi.app/WlvJ2EEh")
time.sleep(2)

# Preencher nome
elemento = driver.find_element(By.XPATH, '//*[@id="988d86bfb8b0-input"]')
elemento.send_keys("Vitor Menegusso")
elemento.send_keys(Keys.ENTER)
time.sleep(2)

# Preencher telefone
elemento = driver.find_element(By.XPATH, '//*[@id="xi29fyr0s5y-input"]')
elemento.send_keys("41998260414")
elemento.send_keys(Keys.ENTER)
time.sleep(2)

# Preencher e-mail
elemento = driver.find_element(By.XPATH, '//*[@id="xe6erhg1bvw-input"]')
elemento.send_keys("vitormene14@hotmail.com")
elemento.send_keys(Keys.ENTER)
time.sleep(5)

driver.quit()
