import sys
import os

# Try to use Windows OCR API
try:
    from winsdk.windows.media.ocr import OcrEngine
    from winsdk.windows.graphics.imaging import BitmapDecoder, SoftwareBitmap
    from winsdk.windows.storage import StorageFile, FileAccessMode
    import asyncio
    
    async def ocr_image(image_path):
        # Load the image
        file = await StorageFile.get_file_from_path_async(image_path)
        stream = await file.open_async(FileAccessMode.READ)
        
        # Decode the bitmap
        decoder = await BitmapDecoder.create_async(stream)
        bitmap = await decoder.get_software_bitmap_async()
        
        # Create OCR engine
        engine = OcrEngine.try_create_from_user_profile_languages()
        if engine is None:
            print("OCR engine not available")
            return None
        
        # Recognize text
        result = await engine.recognize_async(bitmap)
        return result.text
    
    # OCR all screenshots
    for i in range(8):
        path = rf"C:\Users\a1517\.openclaw\workspace\wechat_scroll_{i}.png"
        if os.path.exists(path):
            text = asyncio.run(ocr_image(path))
            print(f"\n=== Screenshot {i} ===")
            print(text)
    
except ImportError as e:
    print(f"winsdk not available: {e}")
    print("Trying alternative...")
    
    # Alternative: use tesseract if available
    try:
        import pytesseract
        from PIL import Image
        
        for i in range(8):
            path = rf"C:\Users\a1517\.openclaw\workspace\wechat_scroll_{i}.png"
            if os.path.exists(path):
                img = Image.open(path)
                text = pytesseract.image_to_string(img, lang='chi_sim+eng')
                print(f"\n=== Screenshot {i} ===")
                print(text)
    except Exception as e2:
        print(f"Alternative failed: {e2}")
        print("Please install tesseract or winsdk")
