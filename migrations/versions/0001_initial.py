"""Initial schema: all tables.

Revision ID: 0001
Revises:
Create Date: 2026-04-25
"""

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "episodes",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column("company_name", sa.String(500), nullable=False),
        sa.Column("company_domain", sa.String(255), nullable=True),
        sa.Column("company_linkedin_url", sa.String(500), nullable=True),
        sa.Column("contact_name", sa.String(255), nullable=True),
        sa.Column("contact_linkedin_url", sa.String(500), nullable=True),
        sa.Column("contact_role", sa.String(255), nullable=True),
        sa.Column("draft_email", sa.Text(), nullable=True),
        sa.Column("final_email", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="drafted"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("eval_scores", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_episodes_user_id", "episodes", ["user_id"])
    op.create_index("ix_episodes_user_domain", "episodes", ["user_id", "company_domain"])

    op.create_table(
        "procedural_memory",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column("current_doc", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_procedural_user"),
    )

    op.create_table(
        "procedural_memory_history",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column("doc", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("change_reason", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_proc_history_user_id", "procedural_memory_history", ["user_id"])

    op.create_table(
        "semantic_profile",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column("profile_doc", sa.Text(), nullable=False, server_default=""),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_semantic_user"),
    )

    op.create_table(
        "proxycurl_cache",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column("response_json", sa.JSON(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url", name="uq_proxycurl_url"),
    )
    op.create_index("ix_proxycurl_url", "proxycurl_cache", ["url"])

    op.create_table(
        "firecrawl_cache",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column("response_markdown", sa.Text(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url", name="uq_firecrawl_url"),
    )
    op.create_index("ix_firecrawl_url", "firecrawl_cache", ["url"])


def downgrade() -> None:
    op.drop_table("firecrawl_cache")
    op.drop_table("proxycurl_cache")
    op.drop_table("semantic_profile")
    op.drop_table("procedural_memory_history")
    op.drop_table("procedural_memory")
    op.drop_table("episodes")
