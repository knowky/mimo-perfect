import pyautogui
import time
import os
from pywinauto import Desktop
from rapidocr_onnxruntime import RapidOCR

ocr = RapidOCR()

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
time.sleep(1)

rect = wechat.rectangle()
chat_x = rect.left + rect.width() // 2
chat_y = rect.top + rect.height() // 2

# Click chat area
pyautogui.click(chat_x, chat_y)
time.sleep(0.5)

# Scroll to TOP first
for i in range(30):
    pyautogui.scroll(10, x=chat_x, y=chat_y)
    time.sleep(0.05)
time.sleep(1)

# Now scroll down and OCR each screenshot
all_messages = []
seen = set()
prev_text = ""

for i in range(25):
    # Take screenshot
    screenshot = pyautogui.screenshot(region=(rect.left, rect.top, rect.width(), rect.height()))
    path = rf"C:\Users\a1517\.openclaw\workspace\ws_{i}.png"
    screenshot.save(path)
    
    # OCR
    result, _ = ocr(path)
    if result:
        current_text = ""
        for line in result:
            text = line[1].strip()
            confidence = line[2]
            if confidence > 0.4 and text:
                current_text += text + " "
                # Filter UI elements and deduplicate
                if (confidence > 0.5 and 
                    text not in seen and 
                    len(text) > 1 and
                    not any(skip in text for skip in [
                        '按住', '发送', '语音', '截图', '表情', '文件', 
                        '红包', '转账', '消息', '置顶', '备注', '标签',
                        '添加', '删除', '举报', '投诉', '搜索', '更多',
                        'Y', '口', 'U', '群公告', '群成员', '聊天信息'
                    ])):
                    seen.add(text)
                    all_messages.append(text)
        
        # Check if content changed
        if current_text != prev_text:
            print(f"\n--- Page {i} ---")
            for line in result:
                text = line[1].strip()
                conf = line[2]
                if conf > 0.4 and text and len(text) > 1:
                    print(f"  {text}")
            prev_text = current_text
    
    # Scroll down
    pyautogui.scroll(-6, x=chat_x, y=chat_y)
    time.sleep(0.6)

# Print final clean chat
print(f"\n\n{'='*70}")
print(f"CLEAN CHAT HISTORY ({len(all_messages)} messages)")
print(f"{'='*70}\n")
for msg in all_messages:
    print(msg)
