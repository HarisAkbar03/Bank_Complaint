"""Exercise 5.2.1: bounded read-only lookup adapters for existing services.

Adapters are injected, not reimplemented. Trusted security and audit callbacks are
mandatory; no LLM-supplied role or access decision is accepted.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping


@dataclass(frozen=True)
class ToolContext:
    """Trusted server-created identity, never constructed from model arguments."""
    actor_id: str
    role: str


class LookupTools:
    def __init__(
        self,
        *,
        get_customer_service: Callable[[str], Any],
        get_accounts_service: Callable[[str], Any],
        get_complaint_service: Callable[[str], Any],
        retrieval_service: Callable[..., Mapping[str, Any]],
        authorize: Callable[[ToolContext, str, str | None], bool],
        audit: Callable[[ToolContext, str, str, str], str],
        policy_filters: Callable[[ToolContext, Mapping[str, Any]], Mapping[str, Any]],
    ):
        self._services = {
            'get_customer': get_customer_service,
            'get_accounts': get_accounts_service,
            'get_complaint': get_complaint_service,
        }
        self._retrieve = retrieval_service
        self._authorize = authorize
        self._audit = audit
        self._policy_filters = policy_filters

    def _result(self, ctx, tool, status, data=None, code=None, message=None):
        # Audit is mandatory; if audit fails, return no potentially sensitive data.
        try:
            audit_id = self._audit(ctx, tool, status, code or '')
            if not isinstance(audit_id, str) or not audit_id.strip():
                raise ValueError('Missing audit identifier')
        except Exception:
            return {'status': 'error', 'data': None,
                    'error': {'code': 'AUDIT_UNAVAILABLE', 'message': 'Audit unavailable'},
                    'audit_event_id': None}
        return {'status': status, 'data': data,
                'error': {'code': code, 'message': message} if code else None,
                'audit_event_id': audit_id}

    def _guard(self, ctx, tool, resource):
        if not isinstance(ctx, ToolContext) or not ctx.actor_id or ctx.role not in ('Analyst', 'Supervisor'):
            return False
        try:
            return self._authorize(ctx, tool, resource) is True
        except Exception:
            return False

    def _sql(self, ctx, tool, identifier):
        if not isinstance(identifier, str) or not identifier.strip():
            return self._result(ctx, tool, 'error', code='INVALID_INPUT', message='Nonempty string ID required')
        if not self._guard(ctx, tool, identifier):
            return self._result(ctx, tool, 'error', code='ACCESS_DENIED', message='Access denied')
        try:
            value = self._services[tool](identifier)
            if value is None or (tool == 'get_accounts' and value == []):
                return self._result(ctx, tool, 'not_found')
            return self._result(ctx, tool, 'success', data=value)
        except Exception:
            return self._result(ctx, tool, 'error', code='LOOKUP_UNAVAILABLE', message='Lookup unavailable')

    def get_customer(self, ctx: ToolContext, *, customer_id: str) -> dict:
        return self._sql(ctx, 'get_customer', customer_id)

    def get_accounts(self, ctx: ToolContext, *, customer_id: str) -> dict:
        # authorize callback must enforce verified customer and account scope.
        return self._sql(ctx, 'get_accounts', customer_id)

    def get_complaint(self, ctx: ToolContext, *, complaint_id: str) -> dict:
        # Existing complaint service must include authorized status history.
        return self._sql(ctx, 'get_complaint', complaint_id)

    def search_policy(self, ctx: ToolContext, *, query: str, filters: dict, top_k: int) -> dict:
        tool = 'search_policy'
        if not isinstance(query, str) or not query.strip() or len(query) > 2000 or not isinstance(filters, dict) or type(top_k) is not int or not 1 <= top_k <= 20:
            return self._result(ctx, tool, 'error', code='INVALID_INPUT', message='Invalid search arguments')
        if not self._guard(ctx, tool, None):
            return self._result(ctx, tool, 'error', code='ACCESS_DENIED', message='Access denied')
        try:
            # Must validate caller filters and enforce access/current-version constraints.
            safe_filters = self._policy_filters(ctx, filters)
            if not isinstance(safe_filters, Mapping):
                raise ValueError('Invalid effective filters')
            response = self._retrieve(query=query, filters=dict(safe_filters), top_k=top_k,
                                      candidate_k=max(20, top_k), rerank=True)
            chunks = response['results']
            if not isinstance(chunks, list):
                raise ValueError('Malformed retrieval response')
            # Defensive check; real document ACL enforcement belongs in retrieval layer.
            for chunk in chunks:
                if not isinstance(chunk, dict) or not all(k in chunk for k in ('chunk_id', 'text', 'metadata')):
                    raise ValueError('Malformed evidence')
            return self._result(ctx, tool, 'success' if chunks else 'not_found', data=chunks if chunks else None)
        except Exception:
            return self._result(ctx, tool, 'error', code='RETRIEVAL_UNAVAILABLE', message='Policy lookup unavailable')
