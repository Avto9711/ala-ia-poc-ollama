from __future__ import annotations

import chainlit as cl

from agent_runtime import invoke_agent

WELCOME_MESSAGE = (
    "Local agent UI ready.\n\n"
    "Ask about `restful-api.dev` objects or ask questions grounded in `constitution.pdf`."
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
        thinking.content = f"Agent execution failed: {exc}"
        await thinking.update()
        return

    thinking.content = response
    await thinking.update()
