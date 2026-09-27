from pathlib import Path
import app

p = Path('static/uploads/verify.png')
p.parent.mkdir(parents=True, exist_ok=True)
p.write_bytes(b'PNG')

client = app.app.test_client()
print('uploads-status', client.get('/uploads/verify.png').status_code)
print('index-status', client.get('/').status_code)
print('draw-status', client.get('/draw').status_code)
