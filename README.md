# A2A Proxy (FastAPI, Cloud Run ready)

Minimal proxy exposing:
- `GET /elastic/agent.json` → `{kbnUrl}/api/chat/a2a/{agentId}.json`
- `POST /elastic/agent` → `{kbnUrl}/api/chat/a2a/{agentId}`

Authentication to Kibana is done via `Authorization: ApiKey <apiKey>`.

## Service configuration
Configure via environment (no request header overrides):
- `AGENT_ID`: agent id
- `KBN_URL`: base Kibana URL, e.g. `https://kibana.example.com`
- `API_KEY`: Kibana API key

Optional safety allowlist via env: `ALLOWED_KBN_HOSTS=kibana.example.com,other.host`

## Run locally

Using uv:

```bash
# from repo root
uv sync
# create .env with required values or copy from .env.example
cp .env.example .env
uv run uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Test health:

```bash
curl -i http://127.0.0.1:8080/healthz
```

Test proxy (no headers needed once .env is set):

```bash
curl -i http://127.0.0.1:8080/elastic/agent.json
```

Or set env defaults (Cloud Run style):

```bash
export DEFAULT_AGENT_ID=<AGENT_ID>
export DEFAULT_KBN_URL=https://<KIBANA_HOST>
export DEFAULT_API_KEY=<API_KEY>
uv run uvicorn app.main:app --host 0.0.0.0 --port 8080
```

## Container build and run

```bash
docker build -t a2a-proxy:local .
docker run --rm -p 8080:8080 \
  -e AGENT_ID=<AGENT_ID> \
  -e KBN_URL=https://<KIBANA_HOST> \
  -e API_KEY=<API_KEY> \
  a2a-proxy:local
```

## Deploy to Cloud Run

Prereqs: `gcloud` installed and configured, a Google Cloud project selected.

```bash
# Enable required services (one-time):
gcloud services enable run.googleapis.com cloudbuild.googleapis.com

# Build and push with Cloud Build
PROJECT_ID=$(gcloud config get-value project)
REGION=us-central1
IMAGE="gcr.io/${PROJECT_ID}/a2a-proxy:latest"

gcloud builds submit --tag "$IMAGE" .

# Deploy to Cloud Run
# Set environment variables for defaults and allowlist as needed
gcloud run deploy a2a-proxy \
  --image "$IMAGE" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --cpu 1 \
  --memory 512Mi \
  --max-instances 10 \
  --port 8080 \
  --set-env-vars AGENT_ID=<AGENT_ID>,KBN_URL=https://<KIBANA_HOST>,API_KEY=<API_KEY>,ALLOWED_KBN_HOSTS=<HOST_ALLOWLIST>
```

No manual clicks are required; everything can be done via CLI.

## Notes
- The proxy forwards most headers except hop-by-hop and `Authorization` (it injects Kibana `ApiKey`).
- Timeouts default to 30s, configurable via `TIMEOUT_SECONDS` env.
- Health endpoint: `GET /healthz`.
