from __future__ import annotations

import json
from typing import Dict, Iterable, Optional, Tuple
from urllib.parse import urljoin

import httpx
from fastapi import HTTPException, Request
from starlette.responses import Response

from .config import settings


HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


def build_agent_url(base_url: str, agent_proxy_path: str) -> str:
    """Construct the agent POST URL exposed in the agent card JSON.

    Always returns the non-JSON endpoint, e.g. `${base}/elastic/agent`.
    """
    return f"{base_url.rstrip('/')}{agent_proxy_path}"


def filter_headers(headers: Iterable[Tuple[str, str]]) -> Dict[str, str]:
    forwarded: Dict[str, str] = {}
    for key, value in headers:
        lk = key.lower()
        if lk in HOP_BY_HOP_HEADERS or lk == "host" or lk == "authorization":
            continue
        forwarded[key] = value
    return forwarded


def remap_agent_json_urls(content: bytes, agent_post_url: str) -> bytes:
    """Replace only the top-level `url` field in the agent card JSON with the provided agent POST URL."""
    try:
        data = json.loads(content.decode("utf-8"))
        if isinstance(data, dict) and isinstance(data.get("url"), str):
            data["url"] = agent_post_url
        return json.dumps(data, separators=(",", ":")).encode("utf-8")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return content


async def proxy_agent_card_request(
    request: Request, client: Optional[httpx.AsyncClient] = None
) -> Response:
    # Read strictly from service config (environment), no header overrides
    agent_id = settings.AGENT_ID
    kbn_url = settings.KBN_URL
    api_key = settings.API_KEY

    if not agent_id:
        raise HTTPException(
            status_code=500, detail="Server misconfigured: missing AGENT_ID"
        )
    if not kbn_url:
        raise HTTPException(
            status_code=500, detail="Server misconfigured: missing KBN_URL"
        )
    if not api_key:
        raise HTTPException(
            status_code=500, detail="Server misconfigured: missing API_KEY"
        )

    base = str(kbn_url).rstrip("/") + "/"
    target_url = urljoin(base, f"{settings.KIBANA_A2A_ENDPOINT}/{agent_id}.json")

    body = await request.body()
    method = request.method

    headers_out = filter_headers(request.headers.items())
    headers_out["Authorization"] = f"ApiKey {api_key}"

    close_client = False
    if client is None:
        client = httpx.AsyncClient(timeout=settings.TIMEOUT_SECONDS)
        close_client = True

    try:
        upstream_resp = await client.request(
            method=method,
            url=target_url,
            headers=headers_out,
            content=body if body else None,
        )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Upstream timeout")
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=502, detail=f"Upstream request failed: {e}"
        ) from e
    finally:
        if close_client:
            await client.aclose()

    content = upstream_resp.content
    media_type = upstream_resp.headers.get("content-type")

    if media_type and "application/json" in media_type:
        content = remap_agent_json_urls(
            content,
            build_agent_url(settings.PROXY_BASE_URL, settings.AGENT_PROXY_PATH),
        )

    response_headers: Dict[str, str] = {}
    for key in ("content-type", "cache-control", "etag"):
        if key in upstream_resp.headers:
            response_headers[key] = upstream_resp.headers[key]

    return Response(
        content=content,
        status_code=upstream_resp.status_code,
        headers=response_headers,
        media_type=media_type,
    )


async def proxy_agent_request(
    request: Request, client: Optional[httpx.AsyncClient] = None
) -> Response:
    agent_id = settings.AGENT_ID
    kbn_url = settings.KBN_URL
    api_key = settings.API_KEY

    if not agent_id:
        raise HTTPException(
            status_code=500, detail="Server misconfigured: missing AGENT_ID"
        )
    if not kbn_url:
        raise HTTPException(
            status_code=500, detail="Server misconfigured: missing KBN_URL"
        )
    if not api_key:
        raise HTTPException(
            status_code=500, detail="Server misconfigured: missing API_KEY"
        )

    base = str(kbn_url).rstrip("/") + "/"
    target_url = urljoin(base, f"{settings.KIBANA_A2A_ENDPOINT}/{agent_id}")

    body = await request.body()
    method = request.method

    headers_out = filter_headers(request.headers.items())
    headers_out["Authorization"] = f"ApiKey {api_key}"

    close_client = False
    if client is None:
        client = httpx.AsyncClient(timeout=settings.TIMEOUT_SECONDS)
        close_client = True

    try:
        upstream_resp = await client.request(
            method=method,
            url=target_url,
            headers=headers_out,
            content=body if body else None,
        )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Upstream timeout")
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=502, detail=f"Upstream request failed: {e}"
        ) from e
    finally:
        if close_client:
            await client.aclose()

    media_type = upstream_resp.headers.get("content-type")

    response_headers: Dict[str, str] = {}
    for key in ("content-type", "cache-control", "etag"):
        if key in upstream_resp.headers:
            response_headers[key] = upstream_resp.headers[key]

    return Response(
        content=upstream_resp.content,
        status_code=upstream_resp.status_code,
        headers=response_headers,
        media_type=media_type,
    )
