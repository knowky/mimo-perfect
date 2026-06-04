import json

with open(r'C:\Users\a1517\AppData\Roaming\weflow\WeFlow-config.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

token = data.get('httpApiToken', '')
print(f'httpApiToken: [{token}]')
print(f'httpApiEnabled: {data.get("httpApiEnabled")}')
print(f'httpApiPort: {data.get("httpApiPort")}')
print(f'httpApiHost: {data.get("httpApiHost")}')
