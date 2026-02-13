"""partition login_history by month (range on login_time)

Revision ID: 0002_partition_login_history
Revises: 0001_init_with_social
Create Date: 2025-09-29
"""
from alembic import op
import sqlalchemy as sa


# identifiers
revision = "0002_partition_login_history"
down_revision = "0001_init_with_social"
branch_labels = None
depends_on = None


def upgrade():
    # 1) Create the parent table (PK must include the partition key!)
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS login_history_new (
            id UUID NOT NULL,
            user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            user_agent VARCHAR(255),
            ip_address VARCHAR(50),
            login_time TIMESTAMP NOT NULL,
            PRIMARY KEY (id, login_time)
        ) PARTITION BY RANGE (login_time);
        """
    )

    # 2) Indexes (created as partitioned indexes)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_login_history_user_id_time
            ON login_history_new (user_id, login_time DESC);
        """
    )

    # 3) Default partition (safety net)
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS login_history_default
        PARTITION OF login_history_new DEFAULT;
        """
    )

    # 4) Monthly partitions (12 months back and 12 months ahead)
    op.execute(
        """
        DO $$
        DECLARE
            start_ts TIMESTAMP := date_trunc('month', now()) - INTERVAL '12 months';
            end_ts   TIMESTAMP := date_trunc('month', now()) + INTERVAL '12 months';
            p_ts     TIMESTAMP;
            partname TEXT;
        BEGIN
            p_ts := start_ts;
            WHILE p_ts < end_ts LOOP
                partname := 'login_history_' || to_char(p_ts, 'YYYY_MM');
                EXECUTE format(
                    'CREATE TABLE IF NOT EXISTS %I PARTITION OF login_history_new
                       FOR VALUES FROM (%L) TO (%L);',
                    partname, p_ts, p_ts + INTERVAL '1 month'
                );
                p_ts := p_ts + INTERVAL '1 month';
            END LOOP;
        END $$;
        """
    )

    # 5) Backfill existing data (if any source table exists).
    #    If migration 0001 created login_history, copy from it.
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'login_history'
            ) THEN
                EXECUTE '
                    INSERT INTO login_history_new (id, user_id, user_agent, ip_address, login_time)
                    SELECT id, user_id, user_agent, ip_address, login_time
                    FROM login_history
                ';
            END IF;
        END $$;
        """
    )

    # 6) Rename tables
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'login_history'
            ) THEN
                EXECUTE 'ALTER TABLE login_history RENAME TO login_history_old';
            END IF;
        END $$;
        """
    )
    op.execute("ALTER TABLE login_history_new RENAME TO login_history;")

    # 7) Cleanup old objects
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'login_history_old'
            ) THEN
                EXECUTE 'DROP TABLE login_history_old';
            END IF;
        END $$;
        """
    )


def downgrade():
    # Reverse migration back to a non-partitioned ("flat") table
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS login_history_flat (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            user_agent VARCHAR(255),
            ip_address VARCHAR(50),
            login_time TIMESTAMP NOT NULL
        );
        """
    )
    op.execute(
        """
        INSERT INTO login_history_flat (id, user_id, user_agent, ip_address, login_time)
        SELECT id, user_id, user_agent, ip_address, login_time
        FROM login_history;
        """
    )
    op.execute("DROP TABLE IF EXISTS login_history CASCADE;")
    op.execute("ALTER TABLE login_history_flat RENAME TO login_history;")
