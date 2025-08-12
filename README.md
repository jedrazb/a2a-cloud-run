# A2A Proxy

A lightweight proxy that wraps Elastic OneChat agents exposed in Kibana and makes them available for A2A (Agent-to-Agent) communication.

## What it does

The proxy exposes two endpoints that forward requests to Kibana's OneChat API:
- `GET /elastic/agent.json` → Returns agent configuration with URLs remapped to proxy endpoints
- `POST /elastic/agent` → Forwards chat requests to the Kibana agent

Authentication to Kibana is handled automatically via API key injection.

## Configuration

Set these environment variables:
- `AGENT_ID`: The OneChat agent ID in Kibana
- `KBN_URL`: Base Kibana URL (e.g., `https://kibana.example.com`)
- `API_KEY`: Kibana API key for authentication
- `PROXY_BASE_URL`: Public URL of this proxy (auto-set during deployment)

## Quick Start

### Local Development
```bash
# Install dependencies
uv sync

# Set environment variables
export AGENT_ID=your-agent-id
export KBN_URL=https://your-kibana.com
export API_KEY=your-api-key

# Run locally
uv run uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### Deploy to Cloud Run
```bash
# Run the deployment script
./deploy.sh [PROJECT_ID] [SERVICE_NAME] [KBN_URL] [API_KEY] [AGENT_ID]

# Or create a .env file and run:
./deploy.sh
```

The deployment script:
1. Builds and deploys the service to Cloud Run
2. Sets required environment variables
3. Automatically configures the `PROXY_BASE_URL` with the service's public URL
4. Returns the service URL for use

### Note about dependencies on Cloud Run
- **Buildpacks require `requirements.txt`**: When deploying with `--source .` (buildpacks), Google Cloud Run installs Python dependencies from `requirements.txt`. Keeping only `pyproject.toml` is not sufficient for the buildpack to install dependencies. This repo includes `requirements.txt` for that reason.

## Usage

Once deployed, your OneChat agent is available at:
- `https://your-service-url/elastic/agent.json` - Get agent config
- `https://your-service-url/elastic/agent` - Send chat messages

The proxy automatically handles authentication and URL remapping, making your Kibana OneChat agent accessible for A2A integrations.
