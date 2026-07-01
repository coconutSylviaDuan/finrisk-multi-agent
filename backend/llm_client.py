import json
import os
from typing import Any

from langchain_openai import ChatOpenAI


def build_llm() -> ChatOpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Copy .env.example to .env and fill it first.")

    kwargs: dict[str, Any] = {
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "api_key": api_key,
        "temperature": float(os.getenv("OPENAI_TEMPERATURE", "0.2")),
    }
    base_url = os.getenv("OPENAI_BASE_URL")
    if base_url:
        kwargs["base_url"] = base_url
    return ChatOpenAI(**kwargs)


def parse_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.removeprefix("json").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end > start:
        cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)
