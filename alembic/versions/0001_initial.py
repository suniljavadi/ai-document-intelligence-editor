"""Initial document intelligence schema."""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("documents", sa.Column("id", sa.Integer, primary_key=True), sa.Column("title", sa.String(255), nullable=False), sa.Column("file_type", sa.String(20), nullable=False), sa.Column("created_at", sa.DateTime), sa.Column("updated_at", sa.DateTime))
    op.create_table("document_versions", sa.Column("id", sa.Integer, primary_key=True), sa.Column("document_id", sa.Integer, sa.ForeignKey("documents.id")), sa.Column("version_number", sa.Integer), sa.Column("content", sa.Text), sa.Column("change_summary", sa.String(500)), sa.Column("created_at", sa.DateTime))
    op.create_table("document_chunks", sa.Column("id", sa.Integer, primary_key=True), sa.Column("document_id", sa.Integer, sa.ForeignKey("documents.id")), sa.Column("chunk_index", sa.Integer), sa.Column("text", sa.Text), sa.Column("section", sa.String(255)), sa.Column("page_number", sa.Integer))
    op.create_table("document_analysis", sa.Column("id", sa.Integer, primary_key=True), sa.Column("document_id", sa.Integer, sa.ForeignKey("documents.id"), unique=True), sa.Column("payload", sa.Text), sa.Column("created_at", sa.DateTime))


def downgrade():
    op.drop_table("document_analysis")
    op.drop_table("document_chunks")
    op.drop_table("document_versions")
    op.drop_table("documents")
