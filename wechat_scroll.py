import pyautogui
import time
from pywinauto import Desktop

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
time.sleep(1)

rect = wechat.rectangle()
print(f"WeChat rect: {rect}")

# Click on chat area (center of window)
chat_x = rect.left + rect.width() // 2
chat_y = rect.top + rect.height() // 2
pyautogui.click(chat_x, chat_y)
time.sleep(0.5)

# First scroll to TOP to see oldest messages
for i in range(20):
    pyautogui.scroll(10, x=chat_x, y=chat_y)
    time.sleep(0.1)

time.sleep(1)

# Now scroll down slowly and take screenshots
for i in range(15):
    path = rf"C:\Users\a1517\.openclaw\workspace\wechat_chat_{i}.png"
    screenshot = pyautogui.screenshot(region=(rect.left, rect.top, rect.width(), rect.height()))
    screenshot.save(path)
    print(f"Screenshot {i} saved")
    
    # Scroll down slowly
    pyautogui.scroll(-8, x=chat_x, y=chat_y)
    time.sleep(0.8)

print("Done!")
