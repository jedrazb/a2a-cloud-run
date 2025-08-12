from __future__ import annotations

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from .proxy import proxy_agent_card_request, proxy_agent_request
from .config import settings

app = FastAPI(title="A2A Proxy", version="0.1.0")


@app.get("/healthz", response_class=PlainTextResponse)
async def healthz() -> str:
    return "ok"


# Use a single configurable base for both routes
@app.get(f"{settings.AGENT_PROXY_PATH}.json")
async def elastic_agent_json(request: Request):
    return await proxy_agent_card_request(request)


@app.post(settings.AGENT_PROXY_PATH)
async def elastic_agent(request: Request):
    return await proxy_agent_request(request)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)
