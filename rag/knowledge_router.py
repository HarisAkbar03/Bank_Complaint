
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from rag.knowledge_service import answer_question
from rag.local_llm import LocalLLMError
from rag.vector_index import VectorStoreUnavailableError


router = APIRouter(
    prefix="/rag",
    tags=["RAG Knowledge Service"],
)


class PolicyQueryRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    filters: dict[str, str] = Field(
        default_factory=dict
    )
    rerank: bool = True


@router.post("/policy/query")
def policy_query(request: PolicyQueryRequest):
    try:
        return answer_question(
            query=request.query,
            top_k=request.top_k,
            filters=request.filters,
            rerank=request.rerank,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except (
        VectorStoreUnavailableError,
        LocalLLMError,
        RuntimeError,
    ) as error:
        raise HTTPException(
            status_code=503,
            detail="RAG knowledge service unavailable",
        ) from error
