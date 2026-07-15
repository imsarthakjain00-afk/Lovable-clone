from dotenv import load_dotenv
load_dotenv()
import asyncio, httpx
from src.utils.settings import settings

async def test():
    print(f"VERCEL_TOKEN present: {bool(settings.VERCEL_TOKEN)}")
    print(f"Token starts with: {settings.VERCEL_TOKEN[:10]}...")
    
    # Test the token by listing deployments
    headers = {"Authorization": f"Bearer {settings.VERCEL_TOKEN}"}
    async with httpx.AsyncClient() as client:
        r = await client.get("https://api.vercel.com/v6/deployments?limit=1", headers=headers)
    print(f"Vercel API status: {r.status_code}")
    if r.status_code == 200:
        print("✅ Token is valid!")
    else:
        print(f"❌ Error: {r.text[:300]}")

asyncio.run(test())
