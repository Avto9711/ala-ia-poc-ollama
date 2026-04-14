from __future__ import annotations

import asyncio
import sys

from agent_runtime import invoke_agent


async def main() -> None:
    prompt = " ".join(sys.argv[1:]).strip()
    if not prompt:
        raise SystemExit(
            "Uso: uv run python main.py <pregunta>  "
            "(restful-api.dev, constitution.pdf o coopnama-servicios.pdf)"
        )

    result = await invoke_agent([{"role": "user", "content": prompt}])
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
