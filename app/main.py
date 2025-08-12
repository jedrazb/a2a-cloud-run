from __future__ import annotations

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from .proxy import proxy_request

app = FastAPI(title="A2A Proxy", version="0.1.0")


@app.get("/healthz", response_class=PlainTextResponse)
async def healthz() -> str:
    return "ok"


@app.get("/elastic/agent.json")
async def elastic_agent_json(request: Request):
    return await proxy_request(request, json_variant=True)


@app.post("/elastic/agent")
async def elastic_agent(request: Request):
    return await proxy_request(request, json_variant=False)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)
