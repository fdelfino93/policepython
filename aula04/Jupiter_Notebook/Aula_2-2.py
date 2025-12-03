import pyautogui
import time

time.sleep(1)
pyautogui.click(x=1775, y=15)
time.sleep(1)
# pyautogui.click(x=50, y=589, button='right', clicks = 1) - Para clicar com o botão direito do mouse
pyautogui.click(x=50, y=589, clicks = 2)
time.sleep(1)
# pyautogui.click(x=150, y=1008) - Para ver propriedades
pyautogui.write("PSN Trophies", interval = 0.25)
pyautogui.press("enter")
time.sleep(1)
pyautogui.click(x=1241, y=58)
time.sleep(1)
# pyautogui.press("down") or pyautogui.scroll(-500) - Para dar scroll na tela
for _ in range(10):
    pyautogui.press("down")
    time.sleep(0.2)
time.sleep(1)
pyautogui.click(x=331, y=606)
time.sleep(3)
pyautogui.click(x=765, y=130)
time.sleep(3)
pyautogui.click(x=1442, y=817)
time.sleep(3)
pyautogui.moveTo(x=386, y=647) # Usar o moveTo como a posição inicial
# Pressionar o mouse
pyautogui.mouseDown()
# Arrastar até outro ponto para copiar
pyautogui.dragTo(x=181, y=650, duration=0.5) # Usar o dragTo como posição final
# Soltar o mouse
pyautogui.mouseUp()
time.sleep(1)
pyautogui.hotkey("ctrl", "c")
time.sleep(1)
pyautogui.click(x=728, y=21)
time.sleep(1)
pyautogui.hotkey("ctrl", "v")
pyautogui.press("enter")
time.sleep(1)