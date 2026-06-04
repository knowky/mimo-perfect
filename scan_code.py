from pathlib import Path
import re

base = Path(r'C:\Users\a1517\Desktop\wechat-decrypt-main')
files = [
    base / 'find_all_keys_windows.py',
    base / 'find_all_keys.py',
    base / 'key_scan_common.py',
    base / 'key_utils.py',
    base / 'decrypt_db.py',
]

keywords = [
    'SQLCipher', 'cipher', 'PRAGMA', 'pbkdf2', 'salt', 'aes', 'raw key', 'header', 'page_size', '400', 'mprotect', 'AES', 'key', 'hex', 'scan'
]

for path in files:
    if not path.exists():
        print(f'MISSING: {path}')
        continue
    text = path.read_text(encoding='utf-8', errors='ignore')
    print(f'\n=== {path.name} ({len(text.splitlines())} lines) ===')
    for kw in keywords:
        if kw.lower() in text.lower():
            print(f'contains: {kw}')
    # Show first 80 lines for quick inspection
    for i, line in enumerate(text.splitlines()[:80], 1):
        print(f'{i:03d}: {line}')
