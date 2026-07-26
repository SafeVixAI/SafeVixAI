"""create update_management tables (UpdateRelease, UpdateInstallation, UpdateSetting)

Revision ID: 10017_update_management
Revises: bdf0a2be195c
Create Date: 2026-07-26 12:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "10017_update_management"
down_revision = "bdf0a2be195c"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "update_releases",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("uuid", sa.Uuid(), nullable=False),
        sa.Column("version", sa.String(32), nullable=False),
        sa.Column("previous_version", sa.String(32), nullable=True),
        sa.Column(
            "channel",
            sa.Enum("stable", "beta", "nightly", "pre-release", name="release_channel"),
            nullable=False,
            server_default="stable",
        ),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("is_mandatory", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_security", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("download_url", sa.String(1024), nullable=True),
        sa.Column("checksum_sha256", sa.String(64), nullable=True),
        sa.Column("signature_gpg", sa.Text(), nullable=True),
        sa.Column("asset_size_bytes", sa.Integer(), nullable=True),
        sa.Column("release_notes_url", sa.String(1024), nullable=True),
        sa.Column("github_release_id", sa.Integer(), nullable=True, unique=True),
        sa.Column("github_tag_name", sa.String(64), nullable=True),
        sa.Column("is_draft", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_prerelease", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("extra_data", sa.JSONB(), nullable=True, server_default=sa.text("'{}'::jsonb")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("channel", "version", name="uq_channel_version"),
    )
    op.create_index("ix_update_releases_version", "update_releases", ["version"])
    op.create_index("ix_update_releases_uuid", "update_releases", ["uuid"], unique=True)
    op.create_index(
        "ix_update_releases_github_release_id", "update_releases", ["github_release_id"],
        unique=True, postgresql_where=sa.text("github_release_id IS NOT NULL"),
    )

    op.create_table(
        "update_installations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("uuid", sa.Uuid(), nullable=False),
        sa.Column("release_id", sa.Integer(), nullable=False),
        sa.Column("release_version", sa.String(32), nullable=False),
        sa.Column("previous_version", sa.String(32), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending", "downloading", "downloaded", "verifying", "verified",
                "installing", "installed", "failed", "rolled_back", "skipped",
                name="update_status",
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "channel",
            sa.Enum("stable", "beta", "nightly", "pre-release", name="install_channel"),
            nullable=False,
            server_default="stable",
        ),
        sa.Column("is_offline", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("downloaded_bytes", sa.Integer(), nullable=True, server_default=sa.text("0")),
        sa.Column("total_bytes", sa.Integer(), nullable=True, server_default=sa.text("0")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("extra_data", sa.JSONB(), nullable=True, server_default=sa.text("'{}'::jsonb")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_update_installations_uuid", "update_installations", ["uuid"], unique=True)
    op.create_index("ix_update_installations_release_id", "update_installations", ["release_id"])
    op.create_index(
        "ix_update_installations_status_created",
        "update_installations", ["status", "created_at"],
    )

    op.create_table(
        "update_settings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("uuid", sa.Uuid(), nullable=False),
        sa.Column("auto_update_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "channel",
            sa.Enum("stable", "beta", "nightly", "pre-release", name="setting_channel"),
            nullable=False,
            server_default="stable",
        ),
        sa.Column("schedule", sa.String(32), nullable=False, server_default="daily"),
        sa.Column("background_download", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("auto_restart", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("notify_on_update", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_check_result", sa.String(32), nullable=True),
        sa.Column("last_update_version", sa.String(32), nullable=True),
        sa.Column("extra_data", sa.JSONB(), nullable=True, server_default=sa.text("'{}'::jsonb")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_update_settings_uuid", "update_settings", ["uuid"], unique=True)


def downgrade():
    op.drop_table("update_settings")
    op.drop_table("update_installations")
    op.drop_table("update_releases")
    op.execute("DROP TYPE IF EXISTS setting_channel")
    op.execute("DROP TYPE IF EXISTS install_channel")
    op.execute("DROP TYPE IF EXISTS update_status")
    op.execute("DROP TYPE IF EXISTS release_channel")
