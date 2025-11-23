"""add_address_field_to_users

Revision ID: 5975dae29910
Revises: 6d5f5d60dac2
Create Date: 2025-11-23 17:43:55.089246

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5975dae29910"
down_revision: Union[str, Sequence[str], None] = "6d5f5d60dac2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("users", sa.Column("address", sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "address")
