from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping


@dataclass(frozen=True)
class ToolContext:
    """Trusted user information provided by the server."""
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
        policy_filters: Callable[
            [ToolContext, Mapping[str, Any]], Mapping[str, Any]
        ],
    ):
        # Store existing SQL services
        self._services = {
            "get_customer": get_customer_service,
            "get_accounts": get_accounts_service,
            "get_complaint": get_complaint_service,
        }

        self._retrieve = retrieval_service
        self._authorize = authorize
        self._audit = audit
        self._policy_filters = policy_filters

    def _result(self, ctx, tool, status, data=None, code=None, message=None):
        """Create a standard response and record an audit event."""

        try:
            audit_id = self._audit(ctx, tool, status, code or "")

            if not isinstance(audit_id, str) or not audit_id.strip():
                raise ValueError("Missing audit identifier")

        except Exception:
            return {
                "status": "error",
                "data": None,
                "error": {
                    "code": "AUDIT_UNAVAILABLE",
                    "message": "Audit unavailable",
                },
                "audit_event_id": None,
            }

        return {
            "status": status,
            "data": data,
            "error": (
                {"code": code, "message": message}
                if code else None
            ),
            "audit_event_id": audit_id,
        }

    def _guard(self, ctx, tool, resource):
        """Check whether the user is authorized."""

        if (
            not isinstance(ctx, ToolContext)
            or not ctx.actor_id
            or ctx.role not in ("Analyst", "Supervisor")
        ):
            return False

        try:
            return self._authorize(ctx, tool, resource) is True
        except Exception:
            return False

    def _sql(self, ctx, tool, identifier):
        """Handle SQL lookups with validation and authorization."""

        # Validate the ID
        if not isinstance(identifier, str) or not identifier.strip():
            return self._result(
                ctx, tool, "error",
                code="INVALID_INPUT",
                message="Nonempty string ID required",
            )

        # Check user permissions
        if not self._guard(ctx, tool, identifier):
            return self._result(
                ctx, tool, "error",
                code="ACCESS_DENIED",
                message="Access denied",
            )

        try:
            # Call the existing SQL service
            value = self._services[tool](identifier)

            if value is None or (tool == "get_accounts" and value == []):
                return self._result(ctx, tool, "not_found")

            return self._result(ctx, tool, "success", data=value)

        except Exception:
            return self._result(
                ctx, tool, "error",
                code="LOOKUP_UNAVAILABLE",
                message="Lookup unavailable",
            )

    def get_customer(self, ctx: ToolContext, *, customer_id: str) -> dict:
        """Retrieve a customer by ID."""
        return self._sql(ctx, "get_customer", customer_id)

    def get_accounts(self, ctx: ToolContext, *, customer_id: str) -> dict:
        """Retrieve accounts belonging to a customer."""
        return self._sql(ctx, "get_accounts", customer_id)

    def get_complaint(self, ctx: ToolContext, *, complaint_id: str) -> dict:
        """Retrieve a complaint by ID."""
        return self._sql(ctx, "get_complaint", complaint_id)

    def search_policy(
        self,
        ctx: ToolContext,
        *,
        query: str,
        filters: dict,
        top_k: int,
    ) -> dict:
        """Retrieve approved policy evidence using RAG."""

        tool = "search_policy"

        # Validate search inputs
        if (
            not isinstance(query, str)
            or not query.strip()
            or len(query) > 2000
            or not isinstance(filters, dict)
            or type(top_k) is not int
            or not 1 <= top_k <= 20
        ):
            return self._result(
                ctx, tool, "error",
                code="INVALID_INPUT",
                message="Invalid search arguments",
            )

        # Check authorization
        if not self._guard(ctx, tool, None):
            return self._result(
                ctx, tool, "error",
                code="ACCESS_DENIED",
                message="Access denied",
            )

        try:
            # Apply approved document filters
            safe_filters = self._policy_filters(ctx, filters)

            if not isinstance(safe_filters, Mapping):
                raise ValueError("Invalid effective filters")

            # Run existing RAG retrieval
            response = self._retrieve(
                query=query,
                filters=dict(safe_filters),
                top_k=top_k,
                candidate_k=max(20, top_k),
                rerank=True,
            )

            chunks = response["results"]

            if not isinstance(chunks, list):
                raise ValueError("Malformed retrieval response")

            # Validate retrieved evidence
            for chunk in chunks:
                if (
                    not isinstance(chunk, dict)
                    or not all(
                        key in chunk
                        for key in ("chunk_id", "text", "metadata")
                    )
                ):
                    raise ValueError("Malformed evidence")

            return self._result(
                ctx,
                tool,
                "success" if chunks else "not_found",
                data=chunks if chunks else None,
            )

        except Exception:
            return self._result(
                ctx, tool, "error",
                code="RETRIEVAL_UNAVAILABLE",
                message="Policy lookup unavailable",
            )
