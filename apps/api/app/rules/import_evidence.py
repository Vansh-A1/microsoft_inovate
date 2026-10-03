"""Attach actual mapped-cell provenance without changing finance results."""
from dataclasses import replace
from uuid import UUID
from app.domain.evidence import EvidenceReference,EvidenceKind,ImportCellLocator
from app.rules.engine import Decision


def mapped_evidence(decision,context):
    source=context.get('import_source');cells=context.get('import_cells',[])
    if not source or not cells:return decision
    rules=[]
    for rule in decision.results:
        references=tuple(r for r in rule.evidence if r.kind is not EvidenceKind.IMPORT_CELL)
        for cell in cells:
            references += (EvidenceReference(EvidenceKind.IMPORT_CELL,UUID(source['id']),1,UUID(context['tenant_id']),
                UUID(context['legal_entity_id']),field_path=cell['field_path'],snapshot_id=UUID(context['snapshot_id']),
                import_cell=ImportCellLocator(UUID(source['batch_id']),source['sheet'],source['row_number'],cell['column'])),)
        rules.append(replace(rule,evidence=references))
    return replace(decision,results=tuple(rules))
