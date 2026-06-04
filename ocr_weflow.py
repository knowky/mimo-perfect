import pyautogui
from pywinauto import Desktop
from rapidocr_onnxruntime import RapidOCR
import time

ocr = RapidOCR()

d = Desktop(backend='uia')
w = d.window(title='WeFlow')
w.set_focus()
time.sleep(1)

screenshot = pyautogui.screenshot()
screenshot.save(r'C:\Users\a1517\.openclaw\workspace\weflow_screen.png')

result, _ = ocr(r'C:\Users\a1517\.openclaw\workspace\weflow_screen.png')
if result:
    for line in result:
        print(line[1])
else:
    print('OCR returned no results')
