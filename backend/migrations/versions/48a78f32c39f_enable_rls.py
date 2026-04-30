"""enable rls

Revision ID: 48a78f32c39f
Revises: ff14c3b9b1d4
Create Date: 2026-04-29 22:09:32.120688

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '48a78f32c39f'
down_revision: Union[str, None] = 'ff14c3b9b1d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable RLS on all user-facing tables
    op.execute("ALTER TABLE books ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE book_subjects ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE reading_progress ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE bookmarks ENABLE ROW LEVEL SECURITY")

    # books — public read, no direct writes (backend owns all writes)
    op.execute("""
        CREATE POLICY books_public_read ON books
        FOR SELECT USING (true)
    """)

    # book_subjects — public read
    op.execute("""
        CREATE POLICY book_subjects_public_read ON book_subjects
        FOR SELECT USING (true)
    """)

    # reading_progress — users can only see and modify their own rows
    op.execute("""
        CREATE POLICY progress_owner ON reading_progress
        FOR ALL USING (user_id = auth.uid())
    """)

    # bookmarks — users can only see and modify their own rows
    op.execute("""
        CREATE POLICY bookmarks_owner ON bookmarks
        FOR ALL USING (user_id = auth.uid())
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS bookmarks_owner ON bookmarks")
    op.execute("DROP POLICY IF EXISTS progress_owner ON reading_progress")
    op.execute("DROP POLICY IF EXISTS book_subjects_public_read ON book_subjects")
    op.execute("DROP POLICY IF EXISTS books_public_read ON books")

    op.execute("ALTER TABLE bookmarks DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE reading_progress DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE book_subjects DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE books DISABLE ROW LEVEL SECURITY")
