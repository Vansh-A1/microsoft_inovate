"""Add versioned review and operational reliability facts; preserve prior migrations."""
from alembic import op
revision="0006_workflow"
down_revision="0005_finance"
branch_labels=None
depends_on=None

def upgrade():
    op.execute('ALTER TABLE review_cases ADD COLUMN owner_id UUID')
    op.execute('ALTER TABLE review_cases ADD COLUMN row_version INTEGER NOT NULL DEFAULT 1')
    op.execute('ALTER TABLE review_cases ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT now()')
    op.execute('ALTER TABLE review_cases ADD CHECK (row_version>0)')
    op.execute('CREATE INDEX ix_review_owner ON review_cases (tenant_id,legal_entity_id,owner_id,state,created_at,id)')
    op.execute('ALTER TABLE jobs ADD COLUMN failure_retryable BOOLEAN NOT NULL DEFAULT false')
    op.execute('ALTER TABLE jobs ADD COLUMN first_failure_at TIMESTAMPTZ')
    op.execute('ALTER TABLE jobs ADD COLUMN last_failure_at TIMESTAMPTZ')
    op.execute('ALTER TABLE jobs ADD COLUMN manual_retries INTEGER NOT NULL DEFAULT 0')
    op.execute('ALTER TABLE document_jobs ADD COLUMN failure_retryable BOOLEAN NOT NULL DEFAULT false')
    op.execute('ALTER TABLE document_jobs ADD COLUMN first_failure_at TIMESTAMPTZ')
    op.execute('ALTER TABLE document_jobs ADD COLUMN last_failure_at TIMESTAMPTZ')
    op.execute('ALTER TABLE document_jobs ADD COLUMN manual_retries INTEGER NOT NULL DEFAULT 0')
    op.execute('\nCREATE TABLE review_actions (\n\treview_case_id UUID NOT NULL, \n\treview_version INTEGER NOT NULL, \n\ttransaction_version INTEGER NOT NULL, \n\tactor_id UUID NOT NULL, \n\taction VARCHAR(40) NOT NULL, \n\treason_code VARCHAR(80) NOT NULL, \n\tcomment VARCHAR(500) NOT NULL, \n\tevidence JSONB NOT NULL, \n\tdetails JSONB NOT NULL, \n\ttenant_id UUID NOT NULL, \n\tlegal_entity_id UUID NOT NULL, \n\tid UUID NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(tenant_id, legal_entity_id, review_case_id) REFERENCES review_cases (tenant_id, legal_entity_id, id), \n\tUNIQUE (tenant_id, legal_entity_id, review_case_id, review_version), \n\tCHECK (review_version > 1 AND transaction_version > 0), \n\tUNIQUE (tenant_id, legal_entity_id, id), \n\tFOREIGN KEY(tenant_id, legal_entity_id) REFERENCES legal_entities (tenant_id, id)\n)\n\n')
    op.execute('ALTER TABLE review_actions ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE review_actions FORCE ROW LEVEL SECURITY')
    op.execute("CREATE POLICY scope_isolation ON review_actions USING (tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid AND legal_entity_id = nullif(current_setting('app.legal_entity_id', true), '')::uuid) WITH CHECK (tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid AND legal_entity_id = nullif(current_setting('app.legal_entity_id', true), '')::uuid)")
    op.execute('CREATE TRIGGER immutable_fact BEFORE UPDATE OR DELETE ON review_actions FOR EACH ROW EXECUTE FUNCTION reject_fact_mutation()')
    op.execute('\nCREATE TABLE operation_records (\n\toperation_key VARCHAR(64) NOT NULL, \n\tkind VARCHAR(32) NOT NULL, \n\tobject_id UUID NOT NULL, \n\tactor_id UUID NOT NULL, \n\tdetails JSONB NOT NULL, \n\ttenant_id UUID NOT NULL, \n\tlegal_entity_id UUID NOT NULL, \n\tid UUID NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (tenant_id, legal_entity_id, operation_key), \n\tUNIQUE (tenant_id, legal_entity_id, id), \n\tFOREIGN KEY(tenant_id, legal_entity_id) REFERENCES legal_entities (tenant_id, id)\n)\n\n')
    op.execute('ALTER TABLE operation_records ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE operation_records FORCE ROW LEVEL SECURITY')
    op.execute("CREATE POLICY scope_isolation ON operation_records USING (tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid AND legal_entity_id = nullif(current_setting('app.legal_entity_id', true), '')::uuid) WITH CHECK (tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid AND legal_entity_id = nullif(current_setting('app.legal_entity_id', true), '')::uuid)")
    op.execute('CREATE TRIGGER immutable_fact BEFORE UPDATE OR DELETE ON operation_records FOR EACH ROW EXECUTE FUNCTION reject_fact_mutation()')

def downgrade():
    op.drop_table("operation_records")
    op.drop_table("review_actions")
    op.drop_index("ix_review_owner")
    op.drop_column('jobs','failure_retryable')
    op.drop_column('jobs','first_failure_at')
    op.drop_column('jobs','last_failure_at')
    op.drop_column('jobs','manual_retries')
    op.drop_column('document_jobs','failure_retryable')
    op.drop_column('document_jobs','first_failure_at')
    op.drop_column('document_jobs','last_failure_at')
    op.drop_column('document_jobs','manual_retries')
    op.drop_column("review_cases",'owner_id')
    op.drop_column("review_cases",'row_version')
    op.drop_column("review_cases",'updated_at')
