import json

with open(r'C:\Users\a1517\AppData\Roaming\weflow\cache\contacts.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f'Total contacts: {len(data)}')
print()
for i, item in enumerate(list(data.items())[:10]):
    k = item[0]
    v = item[1]
    keys = list(v.keys()) if isinstance(v, dict) else ['not dict']
    print(f'{i+1}. key={k}, type={type(v).__name__}')
    if isinstance(v, dict):
        for sk in list(v.keys())[:5]:
            val = str(v[sk])[:50]
            print(f'   {sk}: {val}')
