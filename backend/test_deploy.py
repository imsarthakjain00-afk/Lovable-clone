from dotenv import load_dotenv
load_dotenv()
import asyncio, httpx
from src.utils.settings import settings

async def test_deploy():
    html = """<!DOCTYPE html>
<html><head><title>Test Deploy</title></head>
<body style="font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;background:#0f0f0f;color:white;">
<h1>Lovable Clone - Deployment Test OK</h1>
</body></html>"""
    
    payload = {
        "name": "lovable-deploy-test",
        "files": [{"file": "index.html", "data": html, "encoding": "utf-8"}],
        "target": "production",
        "projectSettings": {
            "framework": None,
            "buildCommand": None,
            "outputDirectory": None,
            "installCommand": None,
            "devCommand": None
        }
    }
    headers = {
        "Authorization": f"Bearer {settings.VERCEL_TOKEN}",
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post("https://api.vercel.com/v13/deployments?skipAutoDetectionConfirmation=1", json=payload, headers=headers)
    
    print(f"Status: {r.status_code}")
    data = r.json()
    if r.status_code < 400:
        url = data.get("url", "")
        print(f"SUCCESS - URL: https://{url}")
    else:
        print(f"FAILED: {r.text[:500]}")

asyncio.run(test_deploy())
