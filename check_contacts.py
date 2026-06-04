import json

with open(r'C:\Users\a1517\AppData\Roaming\weflow\cache\contacts.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f'Total contacts: {len(data)}')
for i, (k, v) in enumerate(list(data.items())[:10]):
    nickname = v.get('nickname', '')
    remark = v.get('remark', '')
    print(f'{i+1}. {k}: {nickname} / {remark}')
