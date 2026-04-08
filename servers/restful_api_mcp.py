from __future__ import annotations

from typing import Any

import httpx
from fastmcp import FastMCP

BASE_URL = "https://api.restful-api.dev"
TIMEOUT_SECONDS = 30.0

mcp = FastMCP("restful-api-dev")


async def _request(method: str, path: str, *, params: list[tuple[str, str]] | None = None) -> Any:
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT_SECONDS) as client:
        response = await client.request(method, path, params=params)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            body = exc.response.text.strip()
            raise RuntimeError(
                f"{method} {exc.request.url} failed with {exc.response.status_code}: {body}"
            ) from exc

        try:
            return response.json()
        except ValueError:
            return {"text": response.text}


@mcp.tool
async def list_objects() -> list[dict[str, Any]]:
    """List all sample objects from restful-api.dev."""
    result = await _request("GET", "/objects")
    return result if isinstance(result, list) else [result]


@mcp.tool
async def get_object_by_id(object_id: str) -> dict[str, Any]:
    """Fetch a single object from restful-api.dev by id."""
    result = await _request("GET", f"/objects/{object_id}")
    return result if isinstance(result, dict) else {"items": result}


@mcp.tool
async def list_objects_by_ids(ids: list[str]) -> list[dict[str, Any]]:
    """Fetch multiple objects from restful-api.dev using repeated id query parameters."""
    params = [("id", object_id) for object_id in ids]
    result = await _request("GET", "/objects", params=params)
    return result if isinstance(result, list) else [result]


if __name__ == "__main__":
    mcp.run()
