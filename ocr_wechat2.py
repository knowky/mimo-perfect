import os
from rapidocr_onnxruntime import RapidOCR

ocr = RapidOCR()

results = []
for i in range(8):
    path = rf"C:\Users\a1517\.openclaw\workspace\wechat_scroll_{i}.png"
    if os.path.exists(path):
        result, _ = ocr(path)
        print(f"\n=== Screenshot {i} ===")
        if result:
            for line in result:
                text = line[1]
                confidence = line[2]
                if confidence > 0.5:
                    print(text)
                    results.append(text)
        else:
            print("(no text detected)")

print(f"\n\n=== ALL TEXT ({len(results)} lines) ===")
for line in results:
    print(line)
