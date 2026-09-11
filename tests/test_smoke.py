from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)
def test_root():
 r=client.get('/'); assert r.status_code==200; assert r.json()['version']=='1.0.0'
def test_docs(): assert client.get('/docs').status_code==200
