import pyautogui
from pywinauto import Desktop
import time

d = Desktop(backend='uia')
w = d.window(title='WeFlow')
w.set_focus()
time.sleep(1)

rect = w.rectangle()

# 找"批量导出"按钮位置 - 根据OCR结果，它在左侧面板
# 先截图确认位置
screenshot = pyautogui.screenshot()
screenshot.save(r'C:\Users\a1517\.openclaw\workspace\weflow_before_click.png')

# 点击左侧"批量导出"按钮（聊天文本区域的批量导出）
# 从OCR结果看，"批量导出"出现在左侧菜单
# 大约在 x=250, y=430 附近
pyautogui.click(250, 430)
time.sleep(1)

screenshot2 = pyautogui.screenshot()
screenshot2.save(r'C:\Users\a1517\.openclaw\workspace\weflow_after_click.png')
print('Clicked batch export')
