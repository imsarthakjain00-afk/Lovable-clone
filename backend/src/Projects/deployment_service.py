import httpx
import re
from fastapi import HTTPException, status
from src.utils.settings import settings


async def deploy_to_vercel(html_content: str, project_title: str) -> str:
    if not settings.VERCEL_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Vercel deployment is not configured (missing VERCEL_TOKEN).",
        )

    safe_name = re.sub(r'[^a-z0-9-]', '-', project_title.lower())
    safe_name = re.sub(r'-+', '-', safe_name).strip('-')
    if not safe_name:
        safe_name = "lovable-project"

    payload = {
        "name": safe_name,
        "files": [
            {
                "file": "index.html",
                "data": html_content
            }
        ],
        "target": "production"
    }

    if settings.VERCEL_PROJECT_ID:
        payload["project"] = settings.VERCEL_PROJECT_ID

    headers = {
        "Authorization": f"Bearer {settings.VERCEL_TOKEN}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.vercel.com/v13/deployments",
            json=payload,
            headers=headers,
        )

    if response.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Vercel deployment failed: {response.text}",
        )

    data = response.json()
    url = data.get("url")
    if not url:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Vercel deployment succeeded but returned no URL.",
        )

    return f"https://{url}"
