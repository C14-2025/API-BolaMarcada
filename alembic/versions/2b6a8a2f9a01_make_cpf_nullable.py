"""make cpf nullable

Revision ID: 2b6a8a2f9a01
Revises: 8aa66d94db33
Create Date: 2025-11-11 00:00:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "2b6a8a2f9a01"
down_revision = "8aa66d94db33"
branch_labels = None
depends_on = None


def upgrade():
    # Torna a coluna cpf opcional (NULL permitido)
    op.alter_column("users", "cpf", nullable=True)


def downgrade():
    # Impede downgrade se houver linhas com cpf NULL
    conn = op.get_bind()
    nulls = conn.execute(sa.text("SELECT COUNT(*) FROM users WHERE cpf IS NULL")).scalar() or 0
    if nulls > 0:
        raise Exception(f"Cannot set users.cpf NOT NULL: {nulls} rows have NULL value.")
    op.alter_column("users", "cpf", nullable=False)
