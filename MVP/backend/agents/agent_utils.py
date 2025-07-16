import os
from dotenv import load_dotenv
from agno.models.azure import AzureOpenAI
from agno.models.azure import AzureAIFoundry
from sqlalchemy.orm import sessionmaker
from database import Transcript, Session # Changed to absolute import
from datetime import datetime, timedelta # Add this import
from constants import DEFAULT_AGENT_RUN_INTERVAL_SECONDS # Add this import
import logging # Import logging

load_dotenv()

def create_azure_model(llm_config: dict):
    """Create and return an Azure model instance based on the provided configuration.

    Args:
        llm_config: A dictionary containing the LLM configuration, including 'provider',
                    'api_key', 'endpoint', 'model_identifier', and optionally 'api_version'.

    Returns:
        Instance of OpenAIChat or AzureAIFoundry based on the specified provider.

    Raises:
        ValueError: If an unsupported provider is specified in llm_config.
    """
    provider = llm_config.get('provider')

    if provider == "azure_openai":
        return AzureOpenAI(
            id=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version=os.getenv("OPENAI_API_VERSION", "2024-12-01-preview")
        )
    elif provider == "azure_ai_inference":
        return AzureAIFoundry(
            api_key=os.getenv("AZURE_AI_API_KEY", llm_config.get('api_key')),
            endpoint=os.getenv("AZURE_AI_ENDPOINT", llm_config.get('endpoint')),
            deployment_name=os.getenv("AZURE_DEPLOYMENT_NAME", llm_config.get('model_identifier')),
            api_version=os.getenv("OPENAI_API_VERSION", llm_config.get('api_version'))
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}. Must be 'azure_openai' or 'azure_ai_inference'.")

def get_transcription_context(meeting_id: int, fetch_mode: str = 'recent', interval_seconds: int = None) -> str:
    """Fetch transcription data for a given meeting ID to be used as context for agents,
    respecting the fetch_mode.

    Args:
        meeting_id: The ID of the meeting for which to retrieve transcriptions.
        fetch_mode: 'recent' or 'full'. Determines how much transcript to fetch.
        interval_seconds: Used when fetch_mode is 'recent'. Defines the window for recent transcripts.
                          Defaults to DEFAULT_AGENT_RUN_INTERVAL_SECONDS if None.

    Returns:
        A string containing the concatenated text of the transcriptions,
        or a default message if no transcriptions are found or in case of an error.
    """
    if interval_seconds is None:
        interval_seconds = DEFAULT_AGENT_RUN_INTERVAL_SECONDS
    
    logging.info(f"get_transcription_context called for meeting_id: {meeting_id}, fetch_mode: {fetch_mode}, interval_seconds: {interval_seconds}")

    try:
        session = Session()
        query = session.query(Transcript).filter(Transcript.meeting_id == meeting_id)

        if fetch_mode == 'full':
            transcripts = query.order_by(Transcript.timestamp.asc()).all()
            context_label = "Full meeting transcriptions"
            logging.info(f"Fetched {len(transcripts)} transcripts for 'full' mode for meeting {meeting_id}.")
        elif fetch_mode == 'recent':
            start_time = datetime.utcnow() - timedelta(seconds=interval_seconds)
            transcripts = query.filter(Transcript.timestamp > start_time).order_by(Transcript.timestamp.asc()).all()
            context_label = f"Meeting transcriptions from the last {interval_seconds} seconds"
            logging.info(f"Fetched {len(transcripts)} transcripts for 'recent' mode (since {start_time}) for meeting {meeting_id}.")
        else:
            session.close() # Ensure session is closed if returning early
            logging.error(f"Invalid fetch_mode '{fetch_mode}' specified for transcription context for meeting {meeting_id}.")
            return "Invalid fetch_mode specified for transcription context."

        if transcripts:
            context = "\n".join([t.text for t in transcripts])
            # Log a snippet of the context
            context_snippet = (context[:200] + '...') if len(context) > 200 else context
            logging.info(f"Returning context for meeting {meeting_id} (mode: {fetch_mode}): {context_snippet}")
            return f"{context_label}:\n{context}"
        else:
            logging.info(f"No transcriptions available for meeting {meeting_id} (mode: {fetch_mode}).")
            return f"No transcriptions available for this meeting (mode: {fetch_mode})."
    except Exception as e:
        logging.error(f"Error fetching transcription context for meeting {meeting_id} (mode: {fetch_mode}): {e}", exc_info=True)
        return "Unable to retrieve transcription data due to an error."
    finally:
        if 'session' in locals() and session.is_active: # Ensure session is closed if it was opened
            session.close()

def save_agent_output(meeting_id: int, agent_id: int, agent_name: str, output_text: str) -> bool:
    """Save the output of an agent to the database for a specific meeting.
    
    Args:
        meeting_id: The ID of the meeting associated with the output.
        agent_id: The unique identifier for the agent.
        agent_name: The name of the agent (e.g., 'Blue Hat').
        output_text: The text output generated by the agent.
    
    Returns:
        bool: True if the output was successfully saved, False otherwise.
    """
    try:
        from database import save_agent_output_to_db # Changed to absolute import
        result = save_agent_output_to_db(meeting_id, agent_id, agent_name, output_text)
        if result:
            print(f"Successfully saved output for {agent_name} in meeting {meeting_id}")
            return True
        else:
            print(f"Failed to save output for {agent_name} in meeting {meeting_id}")
            return False
    except Exception as e:
        print(f"Error saving agent output for {agent_name} in meeting {meeting_id}: {e}")
        return False

def get_agent_outputs(meeting_id: int, agent_name: str = None) -> list:
    """Retrieve agent outputs for a specific meeting from the database.
    
    Args:
        meeting_id: The ID of the meeting to retrieve outputs for.
        agent_name: Optional. The name of the agent to filter outputs by. If None, returns outputs from all agents.
    
    Returns:
        list: A list of AgentOutput objects ordered by timestamp in descending order.
    """
    try:
        from ..database import get_agent_outputs as db_get_agent_outputs
        outputs = db_get_agent_outputs(meeting_id, agent_name)
        print(f"Retrieved {len(outputs)} outputs for meeting {meeting_id}" + (f" and agent {agent_name}" if agent_name else ""))
        return outputs
    except Exception as e:
        print(f"Error retrieving agent outputs for meeting {meeting_id}: {e}")
        return []