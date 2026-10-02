"""Retain complete immutable deterministic rule context for each new evaluation."""
from alembic import op
import sqlalchemy as sa
revision='0002_inputs'
down_revision='0001_phase1'
branch_labels=None
depends_on=None


def upgrade():
    op.create_table('evaluation_inputs',
        sa.Column('id',sa.Uuid(),primary_key=True),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),
        sa.Column('tenant_id',sa.Uuid(),nullable=False),sa.Column('legal_entity_id',sa.Uuid(),nullable=False),
        sa.Column('evaluation_id',sa.Uuid(),nullable=False),sa.Column('encoded',sa.Text(),nullable=False),sa.Column('content_digest',sa.String(64),nullable=False),
        sa.UniqueConstraint('tenant_id','legal_entity_id','id'),sa.UniqueConstraint('tenant_id','legal_entity_id','evaluation_id'),
        sa.ForeignKeyConstraint(['tenant_id','legal_entity_id'],['legal_entities.tenant_id','legal_entities.id']),
        sa.ForeignKeyConstraint(['tenant_id','legal_entity_id','evaluation_id'],['evaluations.tenant_id','evaluations.legal_entity_id','evaluations.id']))
    if op.get_bind().dialect.name=='postgresql':
        op.execute('ALTER TABLE evaluation_inputs ENABLE ROW LEVEL SECURITY')
        op.execute('ALTER TABLE evaluation_inputs FORCE ROW LEVEL SECURITY')
        op.execute("CREATE POLICY scope_isolation ON evaluation_inputs USING (tenant_id = nullif(current_setting('app.tenant_id',true),'')::uuid AND legal_entity_id = nullif(current_setting('app.legal_entity_id',true),'')::uuid) WITH CHECK (tenant_id = nullif(current_setting('app.tenant_id',true),'')::uuid AND legal_entity_id = nullif(current_setting('app.legal_entity_id',true),'')::uuid)")
        op.execute('CREATE TRIGGER immutable_fact BEFORE UPDATE OR DELETE ON evaluation_inputs FOR EACH ROW EXECUTE FUNCTION reject_fact_mutation()')


def downgrade():
    op.drop_table('evaluation_inputs')
