might need to use these commands with podman 

Change Ownership:
sudo chown -R $(id -u):$(id -g) /home/bice/dev/eghed/1_transcriptomatic/transcriptomatic/MVP/data/

Change Permissions:
chmod -R u+rwX /home/bice/dev/eghed/1_transcriptomatic/transcriptomatic/MVP/data/
---

# Audio Transcription System with React Frontend

This project is an audio transcription system featuring a React frontend for recording audio and a FastAPI backend for processing and transcribing it.

## System Overview

The system consists of two main components:

1. **React Frontend**: Captures audio from your microphone or system, processes it into chunks, and sends it to the backend API.
2. **FastAPI Backend**: Receives audio data, transcribes it using the KBLab/kb-whisper models, stores transcripts in a database, and processes them with agents.

## Setup Instructions

The application is deployed using a single script (`docker-start.sh`) that leverages Docker and Docker Compose to build and run both the frontend and backend. You can change which model you wanna use in the constants.py file, deafult right now is KBLab/kb-whisper-small. Follow these steps to get started: 

1. **Ensure Prerequisites are Installed**:
   - **Docker**: Required to build and run the application containers.
   - **Docker Compose**: Required to manage the multi-container setup.

   Verify Docker is installed and running by executing:
   ```bash
   docker info
   ```
   If you see an error, install Docker and ensure the Docker daemon is active.

2. **Run the Setup Script**:
   Execute the provided script to build and deploy the application:
   ```bash
   ./docker-start.sh
   ```

   The script will:
   - Check if Docker is running.
   - Create a sample `.env` file if one doesn’t exist.
   - Prompt you to edit the `.env` file with your API keys and settings.
   - Build and start the Docker containers for the frontend and backend.
   - Display URLs to access the application once it’s running.

3. **Access the Application**:
   After the script completes successfully, you can access:
   - **Frontend**: `http://localhost` or `http://<your-ip-address>`
   - **Backend API**: `http://localhost:8000` or `http://<your-ip-address>:8000`

4. **View Logs** (optional):
   To monitor the application in real-time:
   ```bash
   docker-compose logs -f
   ```

5. **Stop the Application**:
   To shut down the services:
   ```bash
   docker-compose down
   ```

## Configuration

The script generates a sample `backend/.env` file if it doesn’t exist. You must edit this file to provide necessary configurations for the backend, primarily API keys for Azure services. The sample `.env` looks like this:

```
# Azure AI API Keys and Endpoints (for potential future use or specific models)
AZURE_AI_API_KEY=your_azure_ai_api_key_here
AZURE_AI_ENDPOINT=your_azure_ai_endpoint_here
AZURE_DEPLOYMENT_NAME=your_azure_ai_deployment_name_here

# Azure OpenAI API Keys and Endpoints (Primary for LLM agents)
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint_here # e.g., https://your-resource.openai.azure.com/openai/deployments/your-deployment/chat/completions?api-version=YYYY-MM-DD
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
OPENAI_API_VERSION=your_api_version_here # e.g., 2024-02-01
AZURE_OPENAI_DEPLOYMENT_NAME=your_azure_openai_deployment_name_here # e.g., gpt-4o-mini
```

### What You Need to Provide:
- **Azure AI Variables**: Replace the placeholders (`your_azure_ai...`) with your actual Azure AI service credentials if you intend to use specific Azure AI models directly.
- **Azure OpenAI Variables**: Replace the placeholders (`your_azure_openai...`, `your_api_version...`) with your actual Azure OpenAI service credentials. This is required for the agent processing functionality.
  - `AZURE_OPENAI_ENDPOINT`: The full endpoint URL for your deployed model, including the API version.
  - `AZURE_OPENAI_API_KEY`: Your API key for the Azure OpenAI service.
  - `OPENAI_API_VERSION`: The API version your deployment uses (e.g., `2024-02-01`).
  - `AZURE_OPENAI_DEPLOYMENT_NAME`: The name you gave your model deployment in Azure.

After editing the `.env` file, press **Enter** when prompted by the script to proceed with the deployment.

## Requirements

To run this application, ensure your system has:
- **Docker**: For containerization.
- **Docker Compose**: For managing the multi-container setup.
- **Azure OpenAI Credentials**: For agent processing functionality.

No manual installation of Python, Node.js, or other dependencies is required, as Docker handles everything.

## How It Works

### Frontend
- Click the "Start Recording" button.
- Grant microphone access when prompted by the browser.
- Chose either microphone or system (it is like when you share your screen, use the tab where the meeting is)
- Audio is captured, split into chunks, and sent to the backend.
- Transcriptions appear in real-time on the interface.

### Backend
- Receives audio chunks via API endpoints.
- Transcribes them using the KBLab/kb-whisper models.
- Stores transcriptions in a database.
- Periodically processes transcriptions with agents.

## API Endpoints

- **`POST /start_session/{meeting_id}`**: Starts a new transcription session.
- **`POST /transcribe/{meeting_id}`**: Processes and transcribes an audio chunk.
- **`POST /end_session`**: Ends the current transcription session.

## Files Structure

### Backend
- `api.py`: FastAPI server with endpoints.
- `audio_transcribe.py`: Manages audio transcription with the ML model.
- `constants.py`: Configuration constants.

### Frontend
- `index.html`: HTML entry point.
- `index.jsx`: React entry point.
- `App.jsx`: Main React component.
- `AudioRecorder.jsx`: Handles audio recording and transmission.
- `App.css`: Application styling.

## Troubleshooting

### Microphone Access
- Ensure your browser has microphone permissions.
- Use HTTPS in production (localhost works in development).

### Audio Quality
- Minimize background noise.
- Speak clearly and consistently.
- Adjust `MIN_CHUNK_DURATION` in the `.env` file if chunks are too short or long.

### Service Issues
- If the script reports issues, check logs with:
  ```bash
  docker-compose logs
  ```
- Verify Docker is running and the `.env` file is correctly configured.

---
