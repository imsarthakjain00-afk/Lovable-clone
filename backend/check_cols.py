from src.utils.db import engine
from sqlalchemy import inspect

insp = inspect(engine)
cols = [c['name'] for c in insp.get_columns('projects')]
print('Columns:', cols)
print('deployed_url present:', 'deployed_url' in cols)
