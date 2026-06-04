import os
from rapidocr_onnxruntime import RapidOCR

ocr = RapidOCR()

all_text = []
seen = set()

for i in range(15):
    path = rf"C:\Users\a1517\.openclaw\workspace\wechat_chat_{i}.png"
    if os.path.exists(path):
        result, _ = ocr(path)
        if result:
            new_lines = []
            for line in result:
                text = line[1].strip()
                confidence = line[2]
                if confidence > 0.5 and text and text not in seen:
                    # Filter out UI elements
                    if not any(skip in text for skip in ['按住Ctrl', '发送', '语音输入', 'Y', '口', 'U', '截图', '表情', '文件', '红包', '转账']):
                        new_lines.append(text)
                        seen.add(text)
            
            if new_lines:
                print(f"\n=== Screenshot {i} ===")
                for line in new_lines:
                    print(line)
                    all_text.append(line)

print(f"\n\n{'='*60}")
print(f"=== COMPLETE CHAT HISTORY ({len(all_text)} unique lines) ===")
print(f"{'='*60}\n")
for line in all_text:
    print(line)
