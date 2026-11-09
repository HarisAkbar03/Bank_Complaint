
import json
import os

import requests
from dotenv import load_dotenv

from rag.answer_prompt import (
    SYSTEM_PROMPT,
    build_answer_prompt,
)


load_dotenv()


class LocalLLMError(RuntimeError):
    pass


def generate_answer(question, evidence):
    base_url = os.getenv(
        "OLLAMA_BASE_URL",
        "http://127.0.0.1:11434"
    ).rstrip("/")

    model = os.getenv(
        "OLLAMA_MODEL",
        "qwen2.5:7b"
    )

    payload = {
        "model": model,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0,
            "num_ctx": 8192,
        },
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": build_answer_prompt(
                    question,
                    evidence,
                ),
            },
        ],
    }

    try:
        response = requests.post(
            f"{base_url}/api/chat",
            json=payload,
            timeout=(5, 180),
        )

        response.raise_for_status()

        data = response.json()

        content = data["message"]["content"]

        result = json.loads(content)

    except (
        requests.RequestException,
        KeyError,
        ValueError,
        TypeError,
    ) as error:
        raise LocalLLMError(
            "Local Ollama generation failed. "
            "Check that Ollama is running and "
            f"the model '{model}' is installed."
        ) from error

    if not isinstance(result, dict):
        raise LocalLLMError(
            "Ollama returned an invalid answer object"
        )

    required = {
        "answer",
        "state",
        "confidence",
        "cited_chunk_ids",
    }

    if not required.issubset(result):
        raise LocalLLMError(
            "Ollama response is missing required fields"
        )

    if (
        not isinstance(result["answer"], str)
        or not isinstance(result["cited_chunk_ids"], list)
        or not all(
            isinstance(item, str)
            for item in result["cited_chunk_ids"]
        )
        or result["state"] not in {
            "supported",
            "partially_supported",
            "abstained",
        }
        or result["confidence"] not in {
            "high",
            "medium",
            "low",
        }
    ):
        raise LocalLLMError(
            "Ollama returned an invalid answer format"
        )

    return result
