"""migrations

Revision ID: bd8f552be0e8
Revises: 7c7a5ef1761e
Create Date: 2024-10-15 09:59:20.358309

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bd8f552be0e8'
down_revision: Union[str, None] = '7c7a5ef1761e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('counts_of_requests',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('model', sa.Enum('GPT_4O', 'GPT_4O_MINI', 'DALL_E_3', name='modelsenum'), nullable=True),
    sa.Column('count', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_counts_of_requests_user_id'), 'counts_of_requests', ['user_id'], unique=False)
    # ### end Alembic commands ###

def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_counts_of_requests_user_id'), table_name='counts_of_requests')
    op.drop_table('counts_of_requests')
    # ### end Alembic commands ###