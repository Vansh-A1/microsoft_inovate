"""Printed heading geometry: measured cells, missing slots and unsafe fragments."""
from copy import deepcopy
import pytest
from app.extraction.layout import groups,table_columns,printed_layout
from test_clearledger_layout import span


def page():
    headings=[span('Description',.03,.409,.08,.022),span('Qty',.52,.400,.03,.026),
              span('Unit price',.66,.399,.06,.024),span('Amount',.81,.396,.05,.023)]
    rows=[span('Canvas routing folders',.03,.462,.14,.024),span('3',.52,.458,.013,.023),
          span('18.50',.66,.454,.04,.025),span('55.50',.81,.452,.04,.025),
          span('Oak seal carriers',.03,.540,.11,.022),span('18.00',.81,.529,.04,.025)]
    return {'spans':headings+rows}


def test_measured_heading_fragments_map_distinct_rows_and_keep_blank_cells_unknown():
    original=page();saved=deepcopy(original)
    assert len(groups(original)[0])==3  # Generic rows remain conservative.
    assert table_columns(original)==('description','quantity','unit_price','amount')
    headers,rows,notes=printed_layout(original)
    assert not headers and notes==['TABLE_CELL_UNREAD'] and len(rows)==2
    assert {f:v for f,v,_ in rows[0]}=={'description':'Canvas routing folders','quantity':'3','unit_price':'18.50','amount':'55.50'}
    assert {f:v for f,v,_ in rows[1]}=={'description':'Oak seal carriers','quantity':None,'unit_price':None,'amount':'18.00'}
    boxes={f:b for f,_,b in rows[1]}
    assert boxes['quantity'] is boxes['unit_price'] is None
    assert boxes['description']==original['spans'][8]['bbox']
    assert boxes['amount']==original['spans'][9]['bbox'] and original==saved


@pytest.mark.parametrize('unsafe',['duplicate','unrelated','separate_rows','crossing','nonlinear'])
def test_unsafe_heading_fragments_never_establish_table_ownership(unsafe):
    value=page()
    if unsafe=='duplicate':value['spans'].insert(1,span('Qty',.2,.409,.03,.022))
    elif unsafe=='unrelated':value['spans'].insert(1,span('Approval instruction',.2,.409,.14,.022))
    elif unsafe=='separate_rows':value['spans'][0]['bbox'].update(y1=.43,y2=.452)
    elif unsafe=='crossing':value['spans'][0]['bbox']['x2']=.54
    elif unsafe=='nonlinear':value['spans'][2]['bbox'].update(y1=.41,y2=.434)
    assert table_columns(value) is None
    assert printed_layout(value)[1]==[]
