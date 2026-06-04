import pyautogui
import time
from pywinauto import Desktop

# Find and focus WeChat
d = Desktop(backend='uia')
wechat = None
for w in d.windows():
    try:
        if 'Qt5' in w.class_name():
            wechat = w
            break
    except:
        pass

if not wechat:
    print("WeChat not found")
    exit(1)

wechat.set_focus()
time.sleep(0.5)

rect = wechat.rectangle()
print(f"WeChat rect: {rect}")
print(f"Window size: {rect.width()}x{rect.height()}")

# Take screenshot of WeChat region
screenshot = pyautogui.screenshot(region=(rect.left, rect.top, rect.width(), rect.height()))
screenshot.save(r"C:\Users\a1517\.openclaw\workspace\wechat_chat.png")
print("Screenshot saved")

# Now scroll down and take multiple screenshots
chat_area_x = rect.left + rect.width() // 2
chat_area_y = rect.top + rect.height() // 2

# Click on chat area first
pyautogui.click(chat_area_x, chat_area_y)
time.sleep(0.3)

# Take screenshots while scrolling
screenshots = []
for i in range(8):
    screenshot = pyautogui.screenshot(region=(rect.left, rect.top, rect.width(), rect.height()))
    path = rf"C:\Users\a1517\.openclaw\workspace\wechat_scroll_{i}.png"
    screenshot.save(path)
    screenshots.append(path)
    print(f"Screenshot {i} saved")
    
    # Scroll down
    pyautogui.scroll(-5, x=chat_area_x, y=chat_area_y)
    time.sleep(0.5)

print(f"Total screenshots: {len(screenshots)}")
