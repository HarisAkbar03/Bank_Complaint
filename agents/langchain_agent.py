
import json
import logging
import uuid

from langchain.agents import create_agent
from langchain.tools import tool, ToolRuntime
from langchain_ollama import ChatOllama

from agents.tools import LookupTools, ToolContext
from agents.live_services import (
    get_customer_service,
    get_accounts_service,
    get_complaint_service,
    search_policy_service,
)

MODEL = "qwen2.5:7b"


# -------- SYSTEM PROMPT --------

SYSTEM_PROMPT = """
You are a banking complaint investigation assistant.

Available tools:
1. get_customer
2. get_accounts
3. get_complaint
4. search_policy

Rules:
- Use tools whenever information is needed.
- For policy questions, always call search_policy.
- Answer policy questions only using retrieved evidence.
- Cite policy source IDs from document metadata.
- Never invent customer, account, complaint, or policy details.
- If retrieval fails, explain that the policy cannot be verified.
- Never substitute general banking practices for policy evidence.
- Do not perform database updates.
- Respect authorization failures.
"""


# -------- LOCAL TEST SECURITY --------
# Development only: synthetic data and a trusted local user.
# Replace with real server-side security before production.

logging.basicConfig(
    filename="agent_audit.log",
    level=logging.INFO,
)


def authorize(ctx, tool, resource):
    allowed_tools = {
        "get_customer",
        "get_accounts",
        "get_complaint",
        "search_policy",
    }

    return (
        isinstance(ctx, ToolContext)
        and ctx.actor_id == "demo_analyst"
        and ctx.role == "Analyst"
        and tool in allowed_tools
    )


def audit(ctx, tool, status, code):
    audit_id = str(uuid.uuid4())

    logging.info(
        "audit_id=%s actor=%s tool=%s status=%s code=%s",
        audit_id,
        ctx.actor_id,
        tool,
        status,
        code,
    )

    return audit_id


def policy_filters(ctx, filters):
    # Empty filters preserve existing retrieval behavior.
    # This does NOT enforce approved-document restrictions.
    # Production must apply mandatory metadata/access filters.
    return dict(filters)


# -------- INITIALIZE LOOKUP TOOLS --------

lookup_tools = LookupTools(
    get_customer_service=get_customer_service,
    get_accounts_service=get_accounts_service,
    get_complaint_service=get_complaint_service,
    retrieval_service=search_policy_service,
    authorize=authorize,
    audit=audit,
    policy_filters=policy_filters,
)


# -------- LANGCHAIN TOOLS --------

@tool
def get_customer(
    customer_id: str,
    runtime: ToolRuntime[ToolContext],
) -> dict:
    """Retrieve customer details using customer ID."""

    return lookup_tools.get_customer(
        runtime.context,
        customer_id=customer_id,
    )


@tool
def get_accounts(
    customer_id: str,
    runtime: ToolRuntime[ToolContext],
) -> dict:
    """Retrieve accounts belonging to a customer."""

    return lookup_tools.get_accounts(
        runtime.context,
        customer_id=customer_id,
    )


@tool
def get_complaint(
    complaint_id: str,
    runtime: ToolRuntime[ToolContext],
) -> dict:
    """Retrieve complaint details using complaint ID."""

    return lookup_tools.get_complaint(
        runtime.context,
        complaint_id=complaint_id,
    )


@tool
def search_policy(
    query: str,
    runtime: ToolRuntime[ToolContext],
) -> dict:
    """Search banking policy documents using RAG."""

    return lookup_tools.search_policy(
        runtime.context,
        query=query,
        filters={},
        top_k=3,
    )


# -------- INITIALIZE LLM --------

llm = ChatOllama(
    model=MODEL,
    temperature=0,
)


# -------- CREATE LANGCHAIN AGENT --------

agent = create_agent(
    model=llm,
    tools=[
        get_customer,
        get_accounts,
        get_complaint,
        search_policy,
    ],
    system_prompt=SYSTEM_PROMPT,
    context_schema=ToolContext,
)


# -------- RUN AGENT --------

def run_agent(question, ctx):

    response = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": question,
                }
            ]
        },
        context=ctx,
        config={
            "recursion_limit": 20,
        },
    )

    # Display tool calls and results
    for message in response["messages"]:

        if message.type == "ai" and message.tool_calls:
            for call in message.tool_calls:
                print("\nTOOL CALLED:", call["name"])
                print("ARGUMENTS:", call["args"])

        if message.type == "tool":
            print("\nTOOL RESULT:")
            print(message.content)

    print("\nMODEL ANSWER:")
    print(response["messages"][-1].content)

    return response


# -------- INTERACTIVE TESTING --------

if __name__ == "__main__":

    print("Banking Complaint LangChain AI Assistant")
    print("Type 'exit' to quit.")

    # Local synthetic-data testing only
    ctx = ToolContext(
        actor_id="demo_analyst",
        role="Analyst",
    )

    while True:

        question = input("\nAsk a question: ").strip()

        if question.lower() in ("exit", "quit"):
            break

        if not question:
            continue

        try:
            run_agent(question, ctx)

        except Exception as error:
            print(
                "\nAgent error:",
                type(error).__name__,
                str(error),
            )
