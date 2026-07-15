"""Add project brain and workflow state

Revision ID: dc7ac55e10b8
Revises: da4c6fc78333
Create Date: 2026-07-10 19:36:48.952836

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'dc7ac55e10b8'
down_revision: Union[str, Sequence[str], None] = 'da4c6fc78333'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('projects', sa.Column('workflow_state', sa.String(), nullable=False, server_default='DISCOVERY'))
    op.add_column('projects', sa.Column('project_brain', sa.JSON(), nullable=True))
    op.add_column('projects', sa.Column('file_manifest', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('projects', 'file_manifest')
    op.drop_column('projects', 'project_brain')
    op.drop_column('projects', 'workflow_state')
