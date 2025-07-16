# database.py
from sqlalchemy import create_engine, Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class Meeting(Base):
    __tablename__ = 'meetings'
    id = Column(Integer, primary_key=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    title = Column(Text, nullable=False)
    agenda = Column(Text, nullable=True)
    llm_model_key = Column(Text, nullable=True) # Store the key of the selected LLM model (e.g., "gpt-4o-mini")
    agent_run_interval_seconds = Column(Integer, nullable=True) # Store custom agent run interval per meeting
    transcripts = relationship('Transcript', backref='meeting')
    outputs = relationship('AgentOutput', backref='meeting')

class MeetingRelation(Base):
    __tablename__ = 'meeting_relations'
    id = Column(Integer, primary_key=True)
    meeting_id = Column(Integer, ForeignKey('meetings.id'), nullable=False)
    previous_meeting_id = Column(Integer, ForeignKey('meetings.id'), nullable=False)

class Transcript(Base):
    __tablename__ = 'transcripts'
    id = Column(Integer, primary_key=True)
    meeting_id = Column(Integer, ForeignKey('meetings.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    text = Column(Text, nullable=False)

class AgentOutput(Base):
    __tablename__ = 'agents_output'
    id = Column(Integer, primary_key=True)
    meeting_id = Column(Integer, ForeignKey('meetings.id'), nullable=False)
    agent_id = Column(Integer, nullable=False)
    agent_name = Column(Text, nullable=False)
    output_text = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False)

# Hardcode the database path to project_root/data/trans_agents.db
DB_PATH = "/app/data/trans_agents.db"

# Ensure the 'data' directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Create the engine with the hardcoded path
engine = create_engine(f'sqlite:///{DB_PATH}')
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

def save_transcript_to_db(meeting_id, text):
    """Saves the transcript to the SQLite database."""
    import logging  # Import here for direct access
    import traceback  # For detailed error tracing
    
    print(f"\n=== SAVE_TRANSCRIPT_TO_DB CALLED ===")
    print(f"Meeting ID: {meeting_id}, Type: {type(meeting_id)}")
    print(f"Text length: {len(text) if text else 0}")
    
    # Validate and convert meeting_id to integer if needed
    try:
        if not isinstance(meeting_id, int):
            meeting_id = int(meeting_id)
            print(f"Converted meeting_id to int: {meeting_id}")
            logging.info(f"Converted meeting_id to int: {meeting_id}")
    except (ValueError, TypeError) as e:
        error_msg = f"Invalid meeting_id: {meeting_id}, cannot convert to int: {e}"
        logging.error(error_msg)
        print(f"ERROR: {error_msg}")
        return False
        
    # Validate text is not empty
    if not text or not isinstance(text, str) or text.strip() == "":
        error_msg = f"Empty or invalid text provided for meeting {meeting_id}. Not saving to database."
        logging.warning(error_msg)
        print(f"WARNING: {error_msg}")
        return False
    
    try:
        print(f"Creating database session...")
        session = Session()
        print(f"Database session created successfully")
        
        # Check if the meeting exists
        print(f"Querying for meeting {meeting_id}...")
        meeting = session.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            error_msg = f"Meeting with ID {meeting_id} not found. Cannot save transcript."
            logging.error(error_msg)
            print(f"ERROR: {error_msg}")
            return False
        print(f"Found meeting: {meeting.id} - {meeting.title if hasattr(meeting, 'title') else 'No title'}")

        # Create a new transcript object
        # Use UTC time to match the filtering logic in agent_runner.py
        timestamp = datetime.utcnow()
        print(f"Creating transcript with timestamp: {timestamp}")
        transcript = Transcript(meeting_id=meeting_id, timestamp=timestamp, text=text)

        # Add the transcript to the session and commit the changes
        print(f"Adding transcript to session...")
        session.add(transcript)
        print(f"Committing changes to database...")
        session.commit()
        print(f"Database commit successful")

        # Get the ID of the saved transcript for logging
        transcript_id = transcript.id
        success_msg = f"Transcript saved to database with ID {transcript_id} for meeting ID: {meeting_id}"
        logging.info(success_msg)
        print(f"SUCCESS: {success_msg}")
        
        # Double-check that the transcript was actually saved
        verification = session.query(Transcript).filter(Transcript.id == transcript_id).first()
        if verification:
            print(f"Verified transcript ID {transcript_id} exists in database")
        else:
            print(f"WARNING: Could not verify transcript ID {transcript_id} in database after save")
        
        return True

    except Exception as e:
        error_msg = f"Error saving transcript to database for meeting {meeting_id}: {e}"
        logging.error(error_msg, exc_info=True)
        print(f"EXCEPTION: {error_msg}")
        print(traceback.format_exc())
        return False
    finally:
        if 'session' in locals() and session:
            print(f"Closing database session...")
            session.close()
            print(f"Database session closed")
        print("=== SAVE_TRANSCRIPT_TO_DB COMPLETED ===\n")

def save_agent_output_to_db(meeting_id, agent_id, agent_name, output_text):
    """Saves the agent output to the SQLite database."""
    try:
        session = Session()

        # Create a new agent output object
        agent_output = AgentOutput(
            meeting_id=meeting_id,
            agent_id=agent_id,
            agent_name=agent_name,
            output_text=output_text,
            timestamp=datetime.now()
        )

        # Add the agent output to the session and commit the changes
        session.add(agent_output)
        session.commit()
        session.refresh(agent_output) # Load attributes like ID before session closes

        print(f"Agent output saved to database for meeting ID: {meeting_id}, agent: {agent_name}")
        return agent_output  # Return the created object instead of a boolean

    except Exception as e:
        print(f"Error saving agent output to database: {e}")
        return False
    finally:
        session.close()

def get_agent_outputs(meeting_id, agent_name=None):
    """Retrieves agent outputs for a meeting from the database."""
    try:
        session = Session()
        query = session.query(AgentOutput).filter(AgentOutput.meeting_id == meeting_id)
        
        if agent_name:
            query = query.filter(AgentOutput.agent_name == agent_name)
            
        outputs = query.order_by(AgentOutput.timestamp.desc()).all()
        return outputs
    
    except Exception as e:
        print(f"Error retrieving agent outputs from database: {e}")
        return []
    finally:
        session.close()