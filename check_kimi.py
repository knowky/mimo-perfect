import pyautogui
import time
from pywinauto import Desktop

# Find Kimi browser window
d = Desktop(backend='uia')
kimi = None
for w in d.windows():
    try:
        title = w.window_text()
        if 'Kimi' in title and '星愿' in title:
            kimi = w
            break
    except:
        pass

if not kimi:
    print("Kimi window not found")
    exit(1)

kimi.set_focus()
time.sleep(1)

rect = kimi.rectangle()
print(f"Kimi rect: {rect}")

# Screenshot
screenshot = pyautogui.screenshot(region=(rect.left, rect.top, rect.width(), rect.height()))
screenshot.save(r"C:\Users\a1517\.openclaw\workspace\kimi_now.png")
print("Screenshot saved")

# Try to find the chat input area and type
# First click somewhere in the middle of the page
center_x = rect.left + rect.width() // 2
center_y = rect.top + rect.height() // 2

# Scroll down to see content
pyautogui.click(center_x, center_y)
time.sleep(0.5)

# Take another screenshot after scrolling
for i in range(5):
    pyautogui.scroll(-5, x=center_x, y=center_y)
    time.sleep(0.5)

screenshot2 = pyautogui.screenshot(region=(rect.left, rect.top, rect.width(), rect.height()))
screenshot2.save(r"C:\Users\a1517\.openclaw\workspace\kimi_scrolled.png")
print("Scrolled screenshot saved")
