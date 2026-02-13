"""ensure index on (user_id, login_time desc)"""

from alembic import op

# Revisions
revision = "0003_sync_login_history_index"
down_revision = "0002_partition_login_history"

def upgrade():
    # Safe: if the index already exists, this is a no-op
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE c.relname = 'ix_login_history_user_id_time'
                  AND n.nspname = 'public'
            ) THEN
                CREATE INDEX ix_login_history_user_id_time
                    ON login_history (user_id, login_time DESC);
            END IF;
        END$$;
    """)

def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_login_history_user_id_time;")
