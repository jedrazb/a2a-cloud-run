from __future__ import annotations

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


def build_target_url(kbn_base_url: str, agent_id: str, json_variant: bool) -> str:
    base = kbn_base_url.rstrip("/") + "/"
    path = f"api/chat/a2a/{agent_id}{'.json' if json_variant else ''}"
    return urljoin(base, path)


def filter_headers(headers: Iterable[Tuple[str, str]]) -> Dict[str, str]:
    forwarded: Dict[str, str] = {}
    for key, value in headers:
        lk = key.lower()
        if lk in HOP_BY_HOP_HEADERS or lk == "host" or lk == "authorization":
            continue
        forwarded[key] = value
    return forwarded


async def proxy_request(
    request: Request,
    json_variant: bool,
    client: Optional[httpx.AsyncClient] = None,
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

    try:
        # Validate host against optional allowlist
        settings.validate_kbn_host(str(kbn_url), settings.allowed_kbn_hosts)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    target_url = build_target_url(str(kbn_url), agent_id, json_variant)

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

    # Build downstream response
    content = upstream_resp.content
    media_type = upstream_resp.headers.get("content-type")

    # Expose a limited set of upstream headers
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
