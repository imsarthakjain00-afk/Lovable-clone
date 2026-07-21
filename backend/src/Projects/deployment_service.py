import asyncio
import httpx
import re
import logging
from fastapi import HTTPException, status
from src.utils.settings import settings

logger = logging.getLogger(__name__)

VERCEL_API = "https://api.vercel.com"
DEPLOY_TIMEOUT = 120
POLL_INTERVAL = 3


async def _disable_deployment_protection(client: httpx.AsyncClient, project_id: str, headers: dict, team_id: str = None):
    """Disable SSO/password protection on the Vercel project so URLs are publicly accessible."""
    try:
        url = f"{VERCEL_API}/v9/projects/{project_id}"
        if team_id:
            url += f"?teamId={team_id}"
        resp = await client.patch(
            url,
            json={"ssoProtection": None, "passwordProtection": None},
            headers=headers,
        )
        logger.info(f"[DEPLOY] Protection disabled for project {project_id}: {resp.status_code}")
    except Exception as e:
        logger.warning(f"[DEPLOY] Could not disable protection: {e}")


async def _poll_until_ready(client: httpx.AsyncClient, deployment_id: str, headers: dict, team_id: str = None) -> dict:
    """Poll until readyState is READY or ERROR/CANCELED. Returns final deployment data."""
    elapsed = 0
    while elapsed < DEPLOY_TIMEOUT:
        await asyncio.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL

        url = f"{VERCEL_API}/v13/deployments/{deployment_id}"
        if team_id:
            url += f"?teamId={team_id}"

        resp = await client.get(
            url,
            headers=headers,
        )
        if resp.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Vercel status check failed: {resp.text}",
            )

        data = resp.json()
        ready_state = data.get("readyState") or data.get("status", "")
        logger.info(f"[DEPLOY] {deployment_id} → {ready_state} ({elapsed}s)")

        if ready_state in ("READY", "ready"):
            return data
        if ready_state in ("ERROR", "CANCELED", "error", "canceled"):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Vercel deployment failed with state: {ready_state}",
            )

    raise HTTPException(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        detail=f"Vercel deployment timed out after {DEPLOY_TIMEOUT}s.",
    )


async def deploy_to_vercel(html_content: str, project_title: str) -> str:
    if not settings.VERCEL_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Vercel deployment is not configured (missing VERCEL_TOKEN).",
        )

    safe_name = re.sub(r"[^a-z0-9-]", "-", project_title.lower())
    safe_name = re.sub(r"-+", "-", safe_name).strip("-") or "lovable-project"
    safe_name = safe_name[:100]

    payload = {
        "name": safe_name,
        "files": [
            {
                "file": "index.html",
                "data": html_content,
                "encoding": "utf-8",
            }
        ],
        "target": "production",
        "projectSettings": {
            "framework": None,
            "buildCommand": None,
            "outputDirectory": None,
            "installCommand": None,
            "devCommand": None,
        },
    }

    if settings.VERCEL_PROJECT_ID:
        payload["project"] = settings.VERCEL_PROJECT_ID

    auth_headers = {
        "Authorization": f"Bearer {settings.VERCEL_TOKEN}",
        "Content-Type": "application/json",
    }
    poll_headers = {"Authorization": f"Bearer {settings.VERCEL_TOKEN}"}

    async with httpx.AsyncClient(timeout=120.0) as client:
        # Step 1: Create the deployment
        logger.info(f"[DEPLOY] Creating Vercel deployment for '{safe_name}'")
        deploy_url = f"{VERCEL_API}/v13/deployments?skipAutoDetectionConfirmation=1"
        if settings.VERCEL_TEAM_ID:
            deploy_url += f"&teamId={settings.VERCEL_TEAM_ID}"

        response = await client.post(
            deploy_url,
            json=payload,
            headers=auth_headers,
        )

        if response.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Vercel deployment creation failed: {response.text}",
            )

        data = response.json()
        deployment_id = data.get("id")
        project_id = data.get("projectId")
        initial_state = data.get("readyState") or data.get("status", "")
        url = data.get("url", "")

        logger.info(f"[DEPLOY] Created id={deployment_id} projectId={project_id} state={initial_state} url={url}")

        if not deployment_id:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Vercel returned no deployment ID.",
            )

        # Step 2: Disable deployment protection so URL is public (no "You need access")
        if project_id:
            await _disable_deployment_protection(client, project_id, auth_headers, team_id=settings.VERCEL_TEAM_ID)

        # Step 3: If already READY return immediately
        if initial_state in ("READY", "ready"):
            logger.info(f"[DEPLOY] Already READY: https://{url}")
            return f"https://{url}"

        # Step 4: Poll until READY
        logger.info(f"[DEPLOY] Polling {deployment_id}...")
        final_data = await _poll_until_ready(client, deployment_id, poll_headers, team_id=settings.VERCEL_TEAM_ID)

        final_url = final_data.get("url") or url
        if not final_url:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Vercel deployment completed but returned no URL.",
            )

        logger.info(f"[DEPLOY] READY: https://{final_url}")
        return f"https://{final_url}"
