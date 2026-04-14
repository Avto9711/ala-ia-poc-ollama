from __future__ import annotations

import chainlit as cl

from agent_runtime import invoke_agent

WELCOME_MESSAGE = (
    "Interfaz local del agente lista.\n\n"
    "Haz preguntas sobre objetos de `restful-api.dev`, sobre `constitution.pdf` o sobre `coopnama-servicios.pdf` en español."
)


@cl.on_chat_start
async def on_chat_start() -> None:
    await cl.Message(content=WELCOME_MESSAGE).send()


@cl.on_message
async def on_message(message: cl.Message) -> None:
    thinking = cl.Message(content="")
    await thinking.send()

    try:
        response = await invoke_agent(cl.chat_context.to_openai())
    except Exception as exc:
        thinking.content = f"Falló la ejecución del agente: {exc}"
        await thinking.update()
        return

    thinking.content = response
    await thinking.update()
