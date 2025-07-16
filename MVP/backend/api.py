import uvicorn
import numpy as np
import base64
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, Body, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional, List, Any
from audio_transcribe import AudioTranscriber
from constants import SAMPLE_RATE, AVAILABLE_WHISPER_MODELS, AVAILABLE_LLM_MODELS, DEFAULT_LLM_MODEL_KEY, DEFAULT_AGENT_RUN_INTERVAL_SECONDS # Import available models, LLM config, and default interval
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
from database import get_agent_outputs, AgentOutput, Session, Meeting, Transcript
from datetime import datetime
import json # Keep json import
import asyncio # Keep asyncio import
from websocket_manager import manager # Import manager from the new file
from agents.agent_runner import start_agent_scheduler, stop_agent_scheduler, set_active_meeting, run_agent_suite # Import scheduler functions, active meeting setter, and run_agent_suite

# --- FastAPI App Setup ---

app = FastAPI()

# Add CORS middleware to allow requests from the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify in production to specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global transcriber instance
transcriber = None

# --- Application Lifecycle Events ---
@app.on_event("startup")
async def startup_event():
    """Start background tasks on application startup."""
    start_agent_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    """Stop background tasks on application shutdown."""
    stop_agent_scheduler()

# --- API Endpoints ---

class AudioChunkModel(BaseModel):
    """Model for receiving audio chunks from the frontend."""
    audio_data: str  # Base64 encoded audio data
    sample_rate: Optional[int] = SAMPLE_RATE

class StartSessionModel(BaseModel):
    """Model for starting a session, including STT model and other session configs."""
    stt_model_name: str # Renamed for clarity
    llm_model_key: Optional[str] = None # LLM model chosen for this session
    agent_run_interval_seconds: Optional[int] = None # Interval chosen for this session

@app.post("/api/start_session/{meeting_id}")
async def start_session(meeting_id: int, session_data: StartSessionModel):
    """Initialize a new transcription session with a specified model."""
    global transcriber
    session = None # Define session variable for finally block
    try:
        # 1. Update Meeting record with selected LLM and Interval
        session = Session()
        meeting = session.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found to start session for.")

        # Update LLM and Interval if provided in the request
        if session_data.llm_model_key and session_data.llm_model_key in AVAILABLE_LLM_MODELS:
            meeting.llm_model_key = session_data.llm_model_key
            logging.info(f"Updated meeting {meeting_id} LLM model to: {meeting.llm_model_key}")
        elif not meeting.llm_model_key: # Set default only if not already set
             meeting.llm_model_key = DEFAULT_LLM_MODEL_KEY
             logging.info(f"Set meeting {meeting_id} LLM model to default: {meeting.llm_model_key}")

        if session_data.agent_run_interval_seconds is not None and session_data.agent_run_interval_seconds >= 30: # Basic validation
            meeting.agent_run_interval_seconds = session_data.agent_run_interval_seconds
            logging.info(f"Updated meeting {meeting_id} agent interval to: {meeting.agent_run_interval_seconds}s")
        elif not meeting.agent_run_interval_seconds: # Set default only if not already set
            meeting.agent_run_interval_seconds = DEFAULT_AGENT_RUN_INTERVAL_SECONDS
            logging.info(f"Set meeting {meeting_id} agent interval to default: {meeting.agent_run_interval_seconds}s")

        session.commit()
        
        # Check if there are any existing transcripts for this meeting
        transcript_count = session.query(Transcript).filter(Transcript.meeting_id == meeting_id).count()
        logging.info(f"Found {transcript_count} existing transcripts for meeting {meeting_id}")
        
        session.close() # Close session after update

        # 2. Start Transcription Session
        # Ensure only one transcriber session is active globally
        if transcriber is not None:
            if hasattr(transcriber, 'stop') and callable(transcriber.stop):
                logging.info(f"Stopping existing transcription session before starting new one for meeting {meeting_id}.")
                try:
                    await transcriber.stop() # Stop previous session if any
                    logging.info("Previous transcriber stopped successfully")
                except Exception as e:
                    logging.error(f"Error stopping previous transcriber: {e}", exc_info=True)

        # Initialize the transcriber with the chosen Whisper model
        model_name = session_data.stt_model_name
        if model_name not in AVAILABLE_WHISPER_MODELS:
            raise HTTPException(status_code=400, detail=f"Invalid model name: {model_name}. Available models: {AVAILABLE_WHISPER_MODELS}.")
        
        # Create a new transcriber instance
        transcriber = AudioTranscriber()
        # Initialize the transcriber with the meeting ID and chosen model
        transcriber.initialize_session(meeting_id, model_name)
        logging.info(f"Successfully initialized transcriber for meeting {meeting_id} with model {model_name}")
        
        # Set the meeting as active for agent processing
        set_active_meeting(meeting_id)
        logging.info(f"Set meeting {meeting_id} as active for agent processing")
        
        # Return confirmation with details about the selected configuration
        return {
            "message": "Session started successfully", 
            "model": model_name,
            "meeting_id": meeting_id
        }
    except ValueError as ve: # Catch specific error for invalid model or loading failure
        print(f"Error starting session {meeting_id}: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logging.error(f"Unexpected error starting session {meeting_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")
    finally:
        if session and session.is_active:
            session.close()

@app.post("/api/transcribe/{meeting_id}")
async def transcribe_audio(meeting_id: int, data: AudioChunkModel):
    """Receive audio chunk and transcribe it."""
    global transcriber
    print(f"\n=== TRANSCRIBE API CALLED for meeting_id: {meeting_id} ===")
    print(f"Transcriber exists: {transcriber is not None}")
    if transcriber:
        print(f"Transcriber meeting_id: {transcriber.meeting_id}")
    
    # Check if a transcriber exists AND if its meeting ID matches the request
    if not transcriber or transcriber.meeting_id != meeting_id:
        error_msg = f"Error: No active transcription session found for meeting ID: {meeting_id} during transcribe call."
        print(error_msg)
        logging.error(error_msg)
        raise HTTPException(status_code=400, detail=f"No active transcription session found for meeting ID: {meeting_id}. Please start a session first.")

    try:
        # Decode the base64 audio data
        print(f"Audio data length (base64): {len(data.audio_data)}")
        audio_bytes = base64.b64decode(data.audio_data)
        print(f"Decoded audio bytes length: {len(audio_bytes)}")
        audio_array = np.frombuffer(audio_bytes, dtype=np.float32)
        print(f"Audio array shape: {audio_array.shape}, dtype: {audio_array.dtype}, sample_rate: {data.sample_rate}")

        # Verify we have a non-empty audio array
        if audio_array.size == 0:
            logging.error(f"Empty audio array received for meeting {meeting_id}")
            print("ERROR: Empty audio array")
            return {"transcription": "", "message": "Empty audio received"}
            
        # Transcribe the audio
        print(f"Calling transcriber.process_audio_chunk for meeting {meeting_id}...")
        result = await transcriber.process_audio_chunk(audio_array, data.sample_rate)
        print(f"process_audio_chunk returned: {result[:50] if result else None}")
        
        # Check the database directly to verify save happened
        with Session() as session:
            # Count transcripts before this call
            transcript_count = session.query(Transcript).filter(Transcript.meeting_id == meeting_id).count()
            print(f"Transcript count for meeting {meeting_id} in database: {transcript_count}")
        
        # Verify transcription was properly saved
        if result:
            logging.info(f"Transcription saved for meeting {meeting_id}: {result[:50]}...")
            print(f"SUCCESS: Transcription for meeting {meeting_id}: {result[:50]}...")
            
            # Explicitly set active meeting just to be sure
            set_active_meeting(meeting_id)
            logging.info(f"Reinforced meeting {meeting_id} as active for agent processing")
        else:
            error_msg = f"Empty transcription result for meeting {meeting_id}"
            logging.warning(error_msg)
            print(f"WARNING: {error_msg}")

        return {
            "transcription": result if result else "",
            "message": "Audio chunk processed successfully" if result else "No transcription result"
        }
    except Exception as e:
        error_msg = f"Transcription error for meeting {meeting_id}: {str(e)}"
        logging.error(error_msg, exc_info=True)
        print(f"EXCEPTION: {error_msg}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")
    finally:
        print("=== TRANSCRIBE API CALL COMPLETED ===\n")

@app.post("/api/end_session")
async def end_session():
    """End the current transcription session and trigger agent processing."""
    global transcriber
    try:
        if transcriber is None:
            logging.warning("No active transcription session to end.")
            return {"message": "No active session to end."}
            
        # Store meeting ID before stopping
        meeting_id = transcriber.meeting_id
        logging.info(f"Ending session for meeting ID: {meeting_id}")
        
        # Call the transcriber's stop method
        if hasattr(transcriber, 'stop') and callable(transcriber.stop):
            logging.info("Calling transcriber.stop()")
            await transcriber.stop()
            logging.info("Transcriber stopped successfully")
        else:
            logging.error("Transcriber does not have a valid stop method")

        # Store meeting ID before clearing transcriber reference
        meeting_id_to_process = meeting_id

        # Now clear the transcriber reference and set active meeting to None
        transcriber = None
        set_active_meeting(None)
        logging.info("Transcriber reference cleared and active meeting set to None")

        # Trigger a final agent run with the full transcript
        logging.info(f"Triggering final agent run with full transcript for meeting {meeting_id_to_process}")
        # Run this in a separate task to avoid blocking the API response
        asyncio.create_task(run_agent_suite(meeting_id_to_process, fetch_mode='full'))

        return {"message": "Session ended successfully and final agent processing triggered"}
    except Exception as e:
        logging.error(f"Failed to end session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to end session: {str(e)}")

class MeetingModel(BaseModel):
    """Model for creating a new meeting."""
    title: str
    agenda: Optional[str] = None
    llm_model_key: Optional[str] = None # Add field for selected LLM model
    agent_run_interval_seconds: Optional[int] = None # Add field for agent interval

class AgentOutputModel(BaseModel):
    """Model for agent output data."""
    id: int
    agent_id: int
    agent_name: str
    output_text: str
    timestamp: str

@app.get("/api/meetings")
async def list_meetings():
    """Get a list of all meetings."""
    try:
        session = Session()
        meetings = session.query(Meeting).order_by(Meeting.start_time.desc()).all()

        # Convert SQLAlchemy objects to dictionaries
        result = []
        for meeting in meetings:
            result.append({
                "id": meeting.id,
                "title": meeting.title,
                "agenda": meeting.agenda,
                "start_time": meeting.start_time.isoformat(),
                "end_time": meeting.end_time.isoformat() if meeting.end_time else None,
                # Safely access llm_model_key, defaulting to None if attribute doesn't exist
                "llm_model_key": getattr(meeting, 'llm_model_key', None)
            })

        return {"meetings": result}
    except Exception as e:
        logging.error(f"Error fetching meetings: {e}", exc_info=True) # Log the full exception traceback
        raise HTTPException(status_code=500, detail=f"Failed to fetch meetings: {str(e)}")
    finally:
        # Ensure session exists and is closed
        if 'session' in locals() and session:
             session.close()

@app.post("/api/meetings")
async def create_meeting(meeting: MeetingModel):
    """Create a new meeting."""
    try:
        session = Session()

        # Create a new meeting record
        new_meeting = Meeting(
            title=meeting.title,
            agenda=meeting.agenda,
            start_time=datetime.now(),
            llm_model_key=meeting.llm_model_key, # Add this field
            agent_run_interval_seconds=meeting.agent_run_interval_seconds # Add this field
        )
        session.add(new_meeting)
        session.commit()
        meeting_id = new_meeting.id
        session.close()
        
        # Don't automatically set as active yet - wait for session start
        # This will happen when the user starts recording

        return {"message": "Meeting created successfully", "meeting_id": meeting_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create meeting: {str(e)}")

@app.get("/api/meetings/{meeting_id}")
async def get_meeting_details(meeting_id: int):
    """Get details for a specific meeting."""
    try:
        session = Session()
        meeting = session.query(Meeting).filter(Meeting.id == meeting_id).first()
        session.close()

        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        return {
            "id": meeting.id,
            "title": meeting.title,
            "agenda": meeting.agenda,
            "start_time": meeting.start_time.isoformat(),
            "end_time": meeting.end_time.isoformat() if meeting.end_time else None,
            # Safely access llm_model_key, defaulting to None if attribute doesn't exist or is null
            # Safely access llm_model_key, defaulting to None if attribute doesn't exist or is null
            "llm_model_key": getattr(meeting, 'llm_model_key', None),
            # Safely access interval, defaulting to None if attribute doesn't exist or is null
            "agent_run_interval_seconds": getattr(meeting, 'agent_run_interval_seconds', None)
        }
    except Exception as e:
        # Log the exception details here if possible
        raise HTTPException(status_code=500, detail=f"Failed to fetch meeting details: {str(e)}")


@app.get("/api/agent_outputs/{meeting_id}")
async def get_meeting_agent_outputs(meeting_id: int):
    """Get all agent outputs for a specific meeting."""
    try:
        # Fetch agent outputs from the database
        outputs = get_agent_outputs(meeting_id)

        # Convert SQLAlchemy objects to dictionaries
        result = []
        for output in outputs:
            result.append({
                "id": output.id,
                "agent_id": output.agent_id,
                "agent_name": output.agent_name,
                "output_text": output.output_text,
                "timestamp": output.timestamp.isoformat()
            })

        return {"agent_outputs": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch agent outputs: {str(e)}")

@app.get("/api/stt_models") # Renamed endpoint
async def get_available_stt_models() -> Dict[str, List[str]]:
    """Returns the list of available Speech-to-Text (Whisper) models."""
    # Ensure the constant is accessible
    if not AVAILABLE_WHISPER_MODELS:
         raise HTTPException(status_code=500, detail="STT Model list configuration error.")
    return {"models": AVAILABLE_WHISPER_MODELS}

@app.get("/api/llm_models")
async def get_available_llm_models() -> Dict[str, List[str]]:
    """Returns the list of available LLM model keys."""
    if not AVAILABLE_LLM_MODELS:
        raise HTTPException(status_code=500, detail="LLM Model list configuration error.")
    # Return only the keys (user-facing names)
    return {"models": list(AVAILABLE_LLM_MODELS.keys())}

# --- WebSocket Endpoint ---

@app.websocket("/ws/{meeting_id}")
async def websocket_endpoint(websocket: WebSocket, meeting_id: int):
    await manager.connect(websocket, meeting_id)
    try:
        while True:
            # Keep the connection alive, listening for messages (optional)
            # data = await websocket.receive_text()
            # print(f"Received message from client for meeting {meeting_id}: {data}")
            # For now, just keep alive by waiting
            await asyncio.sleep(60) # Check connection status periodically
    except WebSocketDisconnect:
        manager.disconnect(websocket, meeting_id)
    except Exception as e:
        print(f"WebSocket error for meeting {meeting_id}: {e}")
        manager.disconnect(websocket, meeting_id)


if __name__ == "__main__":
    # Start the FastAPI server
    # Note: Ensure asyncio is available if not already imported at the top
    import asyncio # Make sure asyncio is imported
    uvicorn.run(app, host="0.0.0.0", port=8000)