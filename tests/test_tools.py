import pytest
from agents.tools import LookupTools, ToolContext

CTX = ToolContext('synthetic-analyst', 'Analyst')


def build_tools(**overrides):
    calls = []
    services = dict(
        get_customer_service=lambda identifier: {'customer_id': identifier},
        get_accounts_service=lambda identifier: [{'account_id': 'SYN-1'}],
        get_complaint_service=lambda identifier: {'complaint_id': identifier, 'history': []},
        retrieval_service=lambda **kw: {'results': [{'chunk_id': 'KB-003-test', 'text': 'Approved synthetic evidence', 'metadata': {'source_id': 'KB-003'}}]},
        authorize=lambda ctx, tool, resource: ctx.role == 'Analyst',
        audit=lambda ctx, tool, status, code: calls.append((tool, status, code)) or 'audit-1',
        policy_filters=lambda ctx, filters: {'approval_status': 'Approved', 'access_label': 'Internal', 'version': 'current'},
    )
    services.update(overrides)
    return LookupTools(**services), calls


@pytest.mark.parametrize('tool,key', [('get_customer','customer_id'), ('get_accounts','customer_id'), ('get_complaint','complaint_id')])
def test_sql_success(tool, key):
    tools, calls = build_tools()
    result = getattr(tools, tool)(CTX, **{key:'SYN-101'})
    assert result['status'] == 'success'
    assert result['audit_event_id'] == 'audit-1'
    assert calls


def test_not_found():
    tools, _ = build_tools(get_complaint_service=lambda _: None)
    assert tools.get_complaint(CTX, complaint_id='missing')['status'] == 'not_found'


def test_invalid_id():
    tools, _ = build_tools()
    result = tools.get_customer(CTX, customer_id='')
    assert result['error']['code'] == 'INVALID_INPUT'


def test_unauthorized():
    tools, _ = build_tools(authorize=lambda *_: False)
    assert tools.get_accounts(CTX, customer_id='SYN-1')['error']['code'] == 'ACCESS_DENIED'


def test_sql_failure_is_controlled():
    def fail(_): raise RuntimeError('sensitive connection string')
    tools, _ = build_tools(get_customer_service=fail)
    result = tools.get_customer(CTX, customer_id='SYN-1')
    assert result['error']['code'] == 'LOOKUP_UNAVAILABLE'
    assert 'sensitive' not in str(result)


def test_rag_success_and_enforced_filters():
    received = {}
    def retrieve(**kwargs):
        received.update(kwargs)
        return {'results': [{'chunk_id':'KB-003', 'text':'synthetic', 'metadata':{}}]}
    tools, _ = build_tools(retrieval_service=retrieve)
    result = tools.search_policy(CTX, query='Fee investigation?', filters={'access_label':'Restricted'}, top_k=3)
    assert result['status'] == 'success'
    assert received['filters']['access_label'] == 'Internal'
    assert received['rerank'] is True


def test_rag_empty():
    tools, _ = build_tools(retrieval_service=lambda **_: {'results': []})
    assert tools.search_policy(CTX, query='Unknown?', filters={}, top_k=3)['status'] == 'not_found'


@pytest.mark.parametrize('query,filters,top_k', [('',{},3), ('hello',{},0), ('hello',{},21), ('hello',[],3), ('hello',{},True)])
def test_rag_bad_inputs(query, filters, top_k):
    tools, _ = build_tools()
    assert tools.search_policy(CTX, query=query, filters=filters, top_k=top_k)['error']['code'] == 'INVALID_INPUT'


def test_rag_failure():
    def fail(**_): raise RuntimeError('secret')
    tools, _ = build_tools(retrieval_service=fail)
    result = tools.search_policy(CTX, query='Policy?', filters={}, top_k=3)
    assert result['error']['code'] == 'RETRIEVAL_UNAVAILABLE'
    assert 'secret' not in str(result)


def test_audit_failure_fails_closed():
    tools, _ = build_tools(audit=lambda *_: None)
    result = tools.get_customer(CTX, customer_id='SYN-1')
    assert result['error']['code'] == 'AUDIT_UNAVAILABLE'
    assert result['data'] is None


def test_policy_filter_failure_fails_closed():
    def fail(*_): raise ValueError('Invalid access scope')
    tools, _ = build_tools(policy_filters=fail)
    result = tools.search_policy(CTX, query='Policy?', filters={}, top_k=3)
    assert result['status'] == 'error'
