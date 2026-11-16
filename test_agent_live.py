
import json
from ollama import chat

from agents.live_services import (
    get_customer_service,
    get_accounts_service,
    get_complaint_service,
    search_policy_service,
)

MODEL = "qwen2.5:7b"


# -------- SQL TOOLS --------

def get_customer(customer_id: str) -> dict:
    """Retrieve a synthetic customer by customer ID."""
    return get_customer_service(customer_id)


def get_accounts(customer_id: str) -> list:
    """Retrieve accounts belonging to a synthetic customer."""
    return get_accounts_service(customer_id)


def get_complaint(complaint_id: str) -> dict:
    """Retrieve a synthetic complaint by complaint ID."""
    return get_complaint_service(complaint_id)


# -------- RAG TOOL --------

def search_policy(query: str) -> dict:
    """Search approved banking complaint policies."""
    return search_policy_service(
        query=query,
        top_k=3,
        candidate_k=20,
        rerank=True,
    )


# -------- AVAILABLE TOOLS --------

available_tools = {
    "get_customer": get_customer,
    "get_accounts": get_accounts,
    "get_complaint": get_complaint,
    "search_policy": search_policy,
}


# -------- SYSTEM PROMPT --------

SYSTEM_PROMPT = """
You are a banking complaint investigation assistant.

You have access to four tools:

1. get_customer - Retrieve customer details.
2. get_accounts - Retrieve customer accounts.
3. get_complaint - Retrieve complaint details.
4. search_policy - Retrieve approved policy evidence.

Rules:
- Use tools when information is needed.
- Never invent customer, account, or complaint details.
- For complaint questions, retrieve the complaint first.
- Retrieve customer information only when needed.
- Use search_policy for policy questions.
- Cite policy source IDs.
- If information is unavailable, say so.
- Do not perform any database updates.
"""


def run_agent(question):
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": question,
        },
    ]

    for round_number in range(1, 9):
        response = chat(
            model=MODEL,
            messages=messages,
            tools=list(available_tools.values()),
        )

        messages.append(response.message)

        # No tool calls means the model has finished.
        if not response.message.tool_calls:
            print("\nMODEL ANSWER:")
            print(response.message.content)
            return

        # Execute every tool requested in this round.
        for call in response.message.tool_calls:
            name = call.function.name
            args = call.function.arguments

            print(f"\nTOOL CALLED: {name}")
            print("ARGUMENTS:", args)

            if name not in available_tools:
                result = {
                    "error": "Tool not allowed"
                }
            else:
                try:
                    result = available_tools[name](**args)

                    if result is None:
                        result = {
                            "status": "not_found"
                        }

                except Exception as error:
                    # Keep internal exception details out of the model.
                    print("TOOL ERROR:", type(error).__name__)
                    result = {
                        "error": "Tool execution failed"
                    }

            print("\nTOOL RESULT:")
            print(json.dumps(result, indent=2, default=str))

            messages.append({
                "role": "tool",
                "tool_name": name,
                "content": json.dumps(result, default=str),
            })

    print("\nAgent stopped: maximum tool rounds reached.")


# -------- INTERACTIVE TESTING --------

if __name__ == "__main__":
    print("Banking Complaint AI Assistant")
    print("Type 'exit' to quit.")

    while True:
        question = input("\nAsk a question: ").strip()

        if question.lower() in ("exit", "quit"):
            break

        if not question:
            continue

        run_agent(question)
