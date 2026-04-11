import urllib.request
import json

def fetch(url: str):
    with urllib.request.urlopen(url) as resp:
        body = resp.read().decode("utf-8")
        return resp.status, body

def test_health_endpoint():
    status, body = fetch("http://127.0.0.1:8000/health")
    assert status == 200
    assert "ok" in body

def test_ui_reachable():
    status, body = fetch("http://127.0.0.1:5173")
    assert status == 200
    assert "Nexus" in body or "Command Center" in body
