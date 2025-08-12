#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if required environment variables are set
if [ -z "$PROJECT_ID" ] || [ -z "$SERVICE_NAME" ] || [ -z "$KBN_URL" ] || [ -z "$API_KEY" ] || [ -z "$AGENT_ID" ]; then
    echo "Error: Required environment variables not set."
    echo "Please either:"
    echo "1. Set them in a .env file, or"
    echo "2. Pass them as command line arguments"
    echo ""
    echo "Usage: $0 [PROJECT_ID] [SERVICE_NAME] [KBN_URL] [API_KEY] [AGENT_ID]"
    echo "Example: $0 my-project a2a-proxy https://kibana.example.com my-api-key my-agent-id"
    echo ""
    echo "Or create a .env file with:"
    echo "PROJECT_ID=my-project"
    echo "SERVICE_NAME=a2a-proxy"
    echo "KBN_URL=https://kibana.example.com"
    echo "API_KEY=my-api-key"
    echo "AGENT_ID=my-agent-id"
    exit 1
fi

# Use command line arguments if provided (overrides .env values)
PROJECT_ID=${1:-$PROJECT_ID}
SERVICE_NAME=${2:-$SERVICE_NAME}
KBN_URL=${3:-$KBN_URL}
API_KEY=${4:-$API_KEY}
AGENT_ID=${5:-$AGENT_ID}

# The region to deploy to
REGION="us-central1"

# The memory to allocate to the service
MEMORY="256Mi"

# The CPU to allocate to the service (minimum is 1)
CPU="1"

# --- Deployment ---

echo "Starting deployment of service '$SERVICE_NAME' to project '$PROJECT_ID' in region '$REGION'..."

# Deploy to Cloud Run from source code (using Procfile instead of Dockerfile)
gcloud run deploy "$SERVICE_NAME" \
  --source . \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --memory "$MEMORY" \
  --cpu "$CPU" \
  --no-allow-unauthenticated \
  --set-env-vars=GOOGLE_CLOUD_PROJECT="$PROJECT_ID",GOOGLE_CLOUD_LOCATION="$REGION",KBN_URL="$KBN_URL",API_KEY="$API_KEY",AGENT_ID="$AGENT_ID"

echo "Deployment complete."
echo "Service URL: $(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --project $PROJECT_ID --format 'value(status.url)')"

# After the initial deployment, get the service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --project="$PROJECT_ID" --region="$REGION" --format='value(status.url)')

# Update the service to set the PROXY_BASE_URL environment variable
echo "Updating service with its public URL: $SERVICE_URL"
gcloud run services update "$SERVICE_NAME" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --update-env-vars=PROXY_BASE_URL=$SERVICE_URL

echo "Deployment and configuration complete!"
echo "Service is available at: $SERVICE_URL"
