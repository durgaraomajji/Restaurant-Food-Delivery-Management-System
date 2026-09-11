"""Initial database schema.

The application can auto-create the schema for a zero-config SQLite demo. Alembic remains
available for controlled environments: this revision creates the same SQLAlchemy metadata
against the configured database connection.
"""
from alembic import op
from app.models.models import Base
revision='0001_initial'
down_revision=None
branch_labels=None
depends_on=None

def upgrade(): Base.metadata.create_all(bind=op.get_bind())
def downgrade(): Base.metadata.drop_all(bind=op.get_bind())
