# backend/constants.py

import os
from dotenv import load_dotenv

load_dotenv()

# --- LLM Model Definitions ---
# Maps user-facing model names to provider and deployment details.
# The frontend will send one of the keys (e.g., "DeepSeek-R1").
# The backend will then use this map to determine the provider and specific model/deployment.
AVAILABLE_LLM_MODELS = {
    "DeepSeek-R1": {
        "provider": "azure_ai_inference",
        "model_name": os.getenv("AZURE_AI_DEPLOYMENT_NAME_R1", "DeepSeek-R1"), # Use specific env var or default
        "endpoint": os.getenv("AZURE_AI_ENDPOINT", ""),
        "api_key": os.getenv("AZURE_AI_API_KEY", ""),
        "api_version": None # Not typically needed for AI Inference direct endpoint
    },
    "DeepSeek-V3": {
        "provider": "azure_ai_inference",
        "model_name": os.getenv("AZURE_AI_DEPLOYMENT_NAME_V3", "DeepSeek-V3"), # Use specific env var or default
        "endpoint": os.getenv("AZURE_AI_ENDPOINT", ""),
        "api_key": os.getenv("AZURE_AI_API_KEY", ""),
        "api_version": None
    },
    "gpt-4o-mini": {
        "provider": "azure_openai",
        "model_name": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME_4O_MINI", "gpt-4o-mini"), # Use specific env var or default
        "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT", ""),
        "api_key": os.getenv("AZURE_OPENAI_API_KEY", ""),
        "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    },
    "o3-mini": {
        "provider": "azure_openai",
        "model_name": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME_O3_MINI", "o3-mini"), # Use specific env var or default
        "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT", ""),
        "api_key": os.getenv("AZURE_OPENAI_API_KEY", ""),
        "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    },        
    "o4-mini": {
        "provider": "azure_openai",
        "model_name": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME_O3_MINI", "o3-mini"), # Use specific env var or default
        "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT", ""),
        "api_key": os.getenv("AZURE_OPENAI_API_KEY", ""),
        "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    },
    # Add more models here as needed
}

# --- Default LLM Choice (can be overridden by API call) ---
# Set a default model if none is specified by the frontend initially.
DEFAULT_LLM_MODEL_KEY = "o4-mini" # Or choose another default like "DeepSeek-R1"

# --- Azure AI Inference (DeepSeek) Configuration ---
# These are now primarily loaded within the AVAILABLE_LLM_MODELS dict,
# but we keep the old names for potential backward compatibility or other uses.
AZURE_AI_INFERENCE_ENDPOINT: str = os.getenv("AZURE_AI_ENDPOINT", "")
AZURE_AI_INFERENCE_API_KEY: str = os.getenv("AZURE_AI_API_KEY", "")
# AZURE_AI_INFERENCE_MODEL is now derived from AVAILABLE_LLM_MODELS

# --- Azure OpenAI (GPT) Configuration ---
# These are now primarily loaded within the AVAILABLE_LLM_MODELS dict,
# but we keep the old names for potential backward compatibility or other uses.
AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
# AZURE_OPENAI_DEPLOYMENT_NAME is now derived from AVAILABLE_LLM_MODELS
AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

# --- Azure AI Inference (DeepSeek) Configuration ---
AZURE_AI_INFERENCE_ENDPOINT: str = os.getenv("AZURE_AI_ENDPOINT", "") # Reuse existing env var
AZURE_AI_INFERENCE_API_KEY: str = os.getenv("AZURE_AI_API_KEY", "") # Reuse existing env var
# AZURE_AI_INFERENCE_MODEL: str = os.getenv("AZURE_AI_DEPLOYMENT_NAME", "DeepSeek-R1") # Model/Deployment name (Deprecated - use AVAILABLE_LLM_MODELS)

# --- Azure OpenAI (GPT) Configuration ---
AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "") # Can be the same or different endpoint
AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "") # Can be the same or different key
# AZURE_OPENAI_DEPLOYMENT_NAME: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "o3-mini") # Deployment name for the OpenAI model (Deprecated - use AVAILABLE_LLM_MODELS)
# AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview") # API version for Azure OpenAI (Deprecated - use AVAILABLE_LLM_MODELS)

# --- Whisper Model Settings ---
# List of available Whisper models for transcription
AVAILABLE_WHISPER_MODELS = [
    "KBLab/kb-whisper-tiny",
    "KBLab/kb-whisper-base",
    "KBLab/kb-whisper-small", # Default if none specified? Or handle in API
    "KBLab/kb-whisper-medium",
    "KBLab/kb-whisper-large",
    # Add other compatible models here if needed
]

# --- Audio Processing Settings (Existing) ---
MIN_CHUNK_DURATION = 4  # Minimum chunk size in seconds
SILENCE_THRESHOLD = 0.01  # Amplitude threshold for silence
SILENCE_DURATION = 0.2  # Seconds of silence to consider a break
SAMPLE_RATE = 16000  # Sample rate for audio recording, matches Whisper requirement

# --- Default Device (Existing) ---
DEFAULT_SYSTEM_DEVICE = 1

# --- Agent Processing Settings (Existing) ---
DEFAULT_AGENT_RUN_INTERVAL_SECONDS = 300 # Default 5 minutes (used if not specified per meeting)
AGENT_PROCESSING_TIMEOUT_SECONDS = 60 # Timeout for each agent run to prevent hanging
# AGENT_RECENT_SECONDS is now calculated dynamically in agent_runner.py based on the meeting's interval

# --- Validation (Optional but Recommended) ---
# --- Validation (Checks configuration for all defined models) ---
def validate_llm_configs():
    all_configs_valid = True
    for model_key, config in AVAILABLE_LLM_MODELS.items():
        provider = config["provider"]
        endpoint = config["endpoint"]
        api_key = config["api_key"]
        model_name = config["model_name"]
        api_version = config.get("api_version") # Use .get() as it might be None

        if not endpoint or not api_key or not model_name:
            print(f"Warning: Configuration missing for model '{model_key}' (provider: {provider}). Required: ENDPOINT, API_KEY, MODEL_NAME.")
            all_configs_valid = False
            continue # Check next model

        if provider == "azure_openai" and not api_version:
            print(f"Warning: Configuration missing API_VERSION for Azure OpenAI model '{model_key}'.")
            all_configs_valid = False

    if not all_configs_valid:
        print("--- Please check your .env file or environment variables for LLM configurations. ---")
    else:
        print("--- All defined LLM configurations seem present. ---")

# Run validation on import
validate_llm_configs()