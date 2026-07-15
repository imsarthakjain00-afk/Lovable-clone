"""
End-to-end deploy test using the actual project 12 HTML from the database.
"""
from dotenv import load_dotenv
load_dotenv()
import asyncio
from src.utils.db import LocalSession
from src.Projects.models import ProjectModel
from src.Projects.deployment_service import deploy_to_vercel

async def test():
    db = LocalSession()
    project = db.query(ProjectModel).filter(ProjectModel.id == 12).first()
    db.close()
    
    if not project or not project.generated_html:
        print("ERROR: project 12 has no generated_html")
        return
    
    print(f"Project: {project.title!r}")
    print(f"HTML size: {len(project.generated_html)} chars")
    print("Deploying to Vercel...")
    
    url = await deploy_to_vercel(project.generated_html, project.title)
    print(f"Deployed! URL: {url}")

asyncio.run(test())
