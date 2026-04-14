from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_ollama import ChatOllama

from rag.retriever import (
    build_coopnama_servicios_retrieval_tool,
    build_constitution_retrieval_tool,
)

MODEL_NAME = "gemma4-e4b-m1-16gb"
SERVER_PATH = Path(__file__).resolve().parent / "servers" / "restful_api_mcp.py"

SYSTEM_PROMPT = (
    "Eres un asistente útil con acceso a dos fuentes de herramientas locales. "
    "Responde siempre en español. "
    "Usa las herramientas MCP de restful_api_dev para preguntas sobre objetos de restful-api.dev. "
    "Usa retrieve_constitution_context para preguntas sobre constitution.pdf o la Constitución de la República Dominicana. "
    "Usa retrieve_coopnama_servicios_context para preguntas sobre coopnama-servicios.pdf o los servicios de COOPNAMA. "
    "Si una herramienta no devuelve evidencia suficiente para responder, dilo con claridad y no inventes hechos."
)


def _coerce_text_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    parts.append(text)
        return "\n".join(parts)
    return str(content)


def normalize_messages(messages: list[dict[str, Any]]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for message in messages:
        role = str(message.get("role", "user"))
        content = _coerce_text_content(message.get("content", ""))
        if not content.strip():
            continue
        normalized.append({"role": role, "content": content})
    return normalized


def render_result(result: Any) -> str:
    if isinstance(result, dict):
        messages = result.get("messages")
        if messages:
            final_message = messages[-1]
            content = getattr(final_message, "content", None)
            if content is not None:
                return _coerce_text_content(content)
            return str(final_message)

        for key in ("output", "content", "response"):
            if key in result and result[key] is not None:
                return _coerce_text_content(result[key])

    content = getattr(result, "content", None)
    if content is not None:
        return _coerce_text_content(content)

    return str(result)


async def build_agent() -> tuple[Any, MultiServerMCPClient]:
    model = ChatOllama(model=MODEL_NAME, temperature=0.2)

    client = MultiServerMCPClient(
        {
            "restful_api_dev": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [str(SERVER_PATH)],
            }
        }
    )

    mcp_tools = await client.get_tools()
    rag_tools = [
        build_constitution_retrieval_tool(),
        build_coopnama_servicios_retrieval_tool(),
    ]
    agent = create_agent(model=model, tools=[*mcp_tools, *rag_tools], system_prompt=SYSTEM_PROMPT)
    return agent, client


async def invoke_agent(messages: list[dict[str, Any]]) -> str:
    agent, _client = await build_agent()
    normalized_messages = normalize_messages(messages)
    result = await agent.ainvoke({"messages": normalized_messages})
    return render_result(result)
