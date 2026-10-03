"""Permit explicit PASS audit cases in the existing review workflow."""
from alembic import op
revision='0008_intelligence_audit'
down_revision='0007_intelligence'
branch_labels=None
depends_on=None

def upgrade():
    op.execute("DO $$ DECLARE n text; BEGIN SELECT conname INTO n FROM pg_constraint WHERE conrelid='review_cases'::regclass AND contype='c' AND pg_get_constraintdef(oid) LIKE '%decision%'; IF n IS NOT NULL THEN EXECUTE format('ALTER TABLE review_cases DROP CONSTRAINT %I',n); END IF; END $$")
    op.execute("ALTER TABLE review_cases ADD CONSTRAINT ck_review_decision CHECK (decision IN ('PASS','REVIEW','HOLD'))")

def downgrade():
    op.execute('ALTER TABLE review_cases DROP CONSTRAINT ck_review_decision')
    op.execute("ALTER TABLE review_cases ADD CONSTRAINT ck_review_decision CHECK (decision IN ('REVIEW','HOLD'))")
