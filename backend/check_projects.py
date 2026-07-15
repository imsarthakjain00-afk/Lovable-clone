from dotenv import load_dotenv
load_dotenv()
from src.utils.db import LocalSession
from src.Projects.models import ProjectModel

db = LocalSession()
projects = db.query(ProjectModel).all()
for p in projects:
    html_len = len(p.generated_html) if p.generated_html else 0
    print(f"ID={p.id} title={p.title!r} workflow_state={p.workflow_state} generated_html={html_len} chars")
db.close()
