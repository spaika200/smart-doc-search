import urllib.request
import json
req = urllib.request.Request(
    'http://localhost:8000/ask/', 
    data=json.dumps({"query": "tere", "chat_id": 1, "history": [], "tone": "Tavaline"}).encode('utf-8'),
    headers={'Content-Type': 'application/json'},
    method='POST'
)
try:
    print(urllib.request.urlopen(req).read().decode('utf-8'))
except Exception as e:
    print(e.read().decode('utf-8'))
