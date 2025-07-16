# MVP/backend/agno_agents/model_chooser.py

import os
import sys

# Ensure the backend directory is in the Python path
# Adjust the path depth ('../..') as necessary based on your project structure
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Now import constants from the correct location
try:
    from constants import (
        ACTIVE_LLM_PROVIDER,
        AZURE_AI_INFERENCE_ENDPOINT,
        AZURE_AI_INFERENCE_API_KEY,
        AZURE_AI_INFERENCE_MODEL,
        AZURE_OPENAI_ENDPOINT,
        AZURE_OPENAI_API_KEY,
        AZURE_OPENAI_DEPLOYMENT_NAME,
        AZURE_OPENAI_API_VERSION,
    )
except ImportError as e:
    print(f"Error importing constants in model_chooser.py: {e}")
    print(f"Current sys.path: {sys.path}")
    # If you see this error, adjust the sys.path manipulation above
    raise

def get_active_llm_config():
    """
    Returns the configuration details for the currently active LLM provider.

    Returns:
        A dictionary containing:
        - 'provider': The name of the active provider ('azure_ai_inference' or 'azure_openai').
        - 'endpoint': The endpoint URL for the active provider.
        - 'api_key': The API key for the active provider.
        - 'model_identifier': The model/deployment name for the active provider.
        - 'api_version': The API version (only for 'azure_openai').
    """
    provider = ACTIVE_LLM_PROVIDER

    if provider == "azure_ai_inference":
        return {
            "provider": provider,
            "endpoint": AZURE_AI_INFERENCE_ENDPOINT,
            "api_key": AZURE_AI_INFERENCE_API_KEY,
            "model_identifier": AZURE_AI_INFERENCE_MODEL,
            "api_version": None, # Not applicable for this client
        }
    elif provider == "azure_openai":
        return {
            "provider": provider,
            "endpoint": AZURE_OPENAI_ENDPOINT,
            "api_key": AZURE_OPENAI_API_KEY,
            "model_identifier": AZURE_OPENAI_DEPLOYMENT_NAME,
            "api_version": AZURE_OPENAI_API_VERSION,
        }
    else:
        # This case should ideally be caught by the validation in constants.py
        raise ValueError(f"Invalid ACTIVE_LLM_PROVIDER configured: '{provider}'")

# Example of direct usage (optional)
if __name__ == "__main__":
    active_config = get_active_llm_config()
    print(f"Active LLM Configuration:")
    for key, value in active_config.items():
        print(f"  {key}: {value}")