#!/bin/bash

# Move to project root
cd "$(dirname "$0")/.."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting Podman build and deployment for the Audio Transcription App...${NC}"

# Check if Podman is installed and running/available
if ! podman info > /dev/null 2>&1; then
  echo -e "${RED}Error: Podman is not running or not installed/configured correctly.${NC}"
  echo "Please install Podman and ensure it is operational."
  echo "If using Podman machine on macOS or Windows, ensure it's started."
  exit 1
fi

# Default ports (adjusted to avoid conflict with sound-saver-portal)
BACKEND_PORT=8000
FRONTEND_PORT=8080 # Assumed to match podman-compose.yml host port mapping

# Check CUDA availability
USE_GPU=false
if command -v nvidia-smi > /dev/null 2>&1 && nvidia-smi > /dev/null 2>&1; then
  echo -e "${YELLOW}NVIDIA GPU with CUDA support detected.${NC}"
  echo -e "${YELLOW}Would you like to use the GPU? (y/N)${NC}"
  read -r response
  if [[ "$response" =~ ^[Yy]$ ]]; then
    USE_GPU=true
    echo -e "${GREEN}Configuring to use GPU...${NC}"
    echo -e "${YELLOW}Note: GPU usage with Podman requires nvidia-container-toolkit and Podman configured for the NVIDIA runtime.${NC}"
    echo -e "${YELLOW}Ensure your docker/docker-compose.gpu.yml sets appropriate environment variables (e.g., NVIDIA_VISIBLE_DEVICES=all).${NC}"
  else
    echo -e "${YELLOW}Proceeding with CPU only...${NC}"
  fi
else
  echo -e "${YELLOW}No CUDA-capable GPU detected. Using CPU...${NC}"
fi

# Check if ports are already in use
if lsof -i :$BACKEND_PORT > /dev/null 2>&1; then
  echo -e "${RED}Error: Port $BACKEND_PORT is already in use.${NC}"
  echo "Please free the port or edit your compose file (e.g., docker/docker-compose.yml) to use a different backend port."
  exit 1
fi
if lsof -i :$FRONTEND_PORT > /dev/null 2>&1; then
  echo -e "${RED}Error: Port $FRONTEND_PORT is already in use.${NC}"
  echo "Please free the port or edit your compose file (e.g., docker/docker-compose.yml) to use a different frontend port."
  exit 1
fi

# Create .env file if it doesn't exist in the backend directory
if [ ! -f backend/.env ]; then
  echo -e "${YELLOW}Creating sample .env file in backend/.env...${NC}"
  cat > backend/.env << 'EOF'
# Azure AI API Keys and Endpoints (for potential future use or specific models)
AZURE_AI_API_KEY=your_azure_ai_api_key_here
AZURE_AI_ENDPOINT=your_azure_ai_endpoint_here
AZURE_DEPLOYMENT_NAME=your_azure_ai_deployment_name_here

# Azure OpenAI API Keys and Endpoints (Primary for LLM agents)
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint_here # e.g., https://your-resource.openai.azure.com/openai/deployments/your-deployment/chat/completions?api-version=YYYY-MM-DD
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
OPENAI_API_VERSION=your_api_version_here # e.g., 2024-02-01
AZURE_OPENAI_DEPLOYMENT_NAME=your_azure_openai_deployment_name_here # e.g., gpt-4o-mini
EOF
  echo -e "${GREEN}Created .env file in backend/.env. Please edit it to add your actual API keys and settings.${NC}"
  echo -e "${YELLOW}Press Enter to continue after editing the .env file, or Ctrl+C to exit...${NC}"
  read
fi

# Build and start containers
echo -e "${YELLOW}Building and starting Podman containers...${NC}"
# Ensure you have podman-compose installed (e.g., pip install podman-compose)
if [ "$USE_GPU" = true ]; then
  # Use both the base compose file and the GPU override file
  echo -e "${YELLOW}Starting containers with GPU support (ensure docker/docker-compose.gpu.yml is Podman compatible)...${NC}"
  podman-compose -f docker/docker-compose.yml -f docker/docker-compose.gpu.yml up --build -d
else
  # Use only the base compose file for CPU mode
  echo -e "${YELLOW}Starting containers with CPU only...${NC}"
  podman-compose -f docker/docker-compose.yml up --build -d
fi

# Wait for services to start
echo -e "${YELLOW}Waiting for services to start...${NC}"
sleep 5 # Adjust sleep time if necessary

# Check if services are running
# podman-compose ps status can be 'Running' or include 'Up'.
# This checks the main compose file; GPU override might affect service names if not careful.
# awk 'NR>1 && NF>0' skips header and empty lines before grepping.
if podman-compose -f docker/docker-compose.yml ps | awk 'NR>1 && NF>0' | grep -Eiq 'running|up'; then
  echo -e "${GREEN}Services are up and running!${NC}"

  # Get host IP (localhost on macOS, IP on Linux)
  # For rootless Podman on Linux, 'localhost' is often the correct address from the host.
  if [[ "$OSTYPE" == "darwin"* ]]; then
    HOST_IP="localhost"
  else
    # For Linux, if using rootless Podman, localhost is generally preferred for host access.
    # If you know you're using rootful Podman or have specific network setups, hostname -I might be appropriate.
    # Consider advising 'localhost' for Linux too, or let user decide.
    HOST_IP=$(hostname -I | awk '{print $1}')
    if podman info --format '{{.Host.RemoteSocket.Exists}}' 2>/dev/null | grep -q 'true' && [[ -z "$SSH_CONNECTION" ]]; then # Basic check for podman machine like setup or rootless
        IS_ROOTLESS_OR_VM=$(podman info --format '{{range .Store.GraphRoot}}{{.}}{{end}}' | grep -c "$HOME")
        if [ "$IS_ROOTLESS_OR_VM" -gt 0 ]; then
            echo -e "${YELLOW}Detected rootless Podman or Podman Machine like environment on Linux. Services might be best accessed via localhost.${NC}"
            echo -e "${YELLOW}Using detected IP: $HOST_IP. If this doesn't work, try localhost.${NC}"
        fi
    fi
  fi

  echo -e "${GREEN}===== Application URLs =====${NC}"
  echo -e "Frontend: ${GREEN}http://$HOST_IP:$FRONTEND_PORT${NC}"
  echo -e "Backend API: ${GREEN}http://$HOST_IP:$BACKEND_PORT${NC}"
  echo ""
  echo -e "${YELLOW}Use the following command to view logs:${NC}"
  echo "podman-compose -f docker/docker-compose.yml logs -f"
  echo ""
  echo -e "${YELLOW}To stop the services:${NC}"
  echo "podman-compose -f docker/docker-compose.yml down"
else
  echo -e "${RED}There was an issue starting the services.${NC}"
  echo "Please check the logs with: podman-compose -f docker/docker-compose.yml logs"
fi