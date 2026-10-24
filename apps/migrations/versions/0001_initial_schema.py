"""Create normalized Cronos persistence tables."""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("datasets", sa.Column("id", sa.String(64), primary_key=True), sa.Column("payload", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("optimization_runs", sa.Column("id", sa.String(64), primary_key=True), sa.Column("dataset_id", sa.String(64), nullable=False), sa.Column("status", sa.String(32), nullable=False), sa.Column("payload", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("scheduled_sessions", sa.Column("id", sa.String(128), primary_key=True), sa.Column("run_id", sa.String(64), sa.ForeignKey("optimization_runs.id", ondelete="CASCADE"), nullable=False), sa.Column("payload", sa.JSON(), nullable=False))


def downgrade() -> None:
    op.drop_table("scheduled_sessions")
    op.drop_table("optimization_runs")
    op.drop_table("datasets")
