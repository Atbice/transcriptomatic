import threading
import time
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import func
from database import Session, Meeting, Transcript, get_agent_outputs # Absolute import
from .white_hat_agent import WhiteHatAgent
from .blue_hat_agent import BlueHatAgent
from .red_hat_agent import RedHatAgent
from .yellow_hat_agent import YellowHatAgent
from .green_hat_agent import GreenHatAgent
from .black_hat_agent import BlackHatAgent
from .purple_hat_agent import PurpleHatAgent
from .miro_agent import MiroAgent
from constants import AVAILABLE_LLM_MODELS, DEFAULT_LLM_MODEL_KEY, DEFAULT_AGENT_RUN_INTERVAL_SECONDS # Absolute import

# Global variable to store the active meeting ID for agent processing
_active_meeting_id = None
_scheduler_thread = None
_stop_event = threading.Event()

def set_active_meeting(meeting_id):
    """Set the active meeting ID for agent processing."""
    global _active_meeting_id
    previous_meeting = _active_meeting_id
    _active_meeting_id = meeting_id
    logging.info(f"Active meeting set to {meeting_id} (previously {previous_meeting})")
    return _active_meeting_id

def get_active_meeting():
    """Get the current active meeting ID."""
    return _active_meeting_id

async def run_agent_suite(meeting_id, fetch_mode='recent'):
    """
    Run the suite of agents for the given meeting ID.

    Args:
        meeting_id: The ID of the meeting to process.
        fetch_mode: The mode of transcript fetching. 'recent' for recent transcripts, 'full' for all transcripts.
    """
    try:
        logging.info(f"Running agent suite for meeting {meeting_id} with fetch mode '{fetch_mode}'")
        session = Session()

        # Get meeting details to access custom configurations
        meeting = session.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            logging.error(f"Meeting {meeting_id} not found. Cannot run agents.")
            return

        # Determine LLM model to use, default if not set
        llm_model_key = getattr(meeting, 'llm_model_key', None) or DEFAULT_LLM_MODEL_KEY
        if llm_model_key not in AVAILABLE_LLM_MODELS:
            logging.warning(f"Invalid LLM model key {llm_model_key} for meeting {meeting_id}. Using default: {DEFAULT_LLM_MODEL_KEY}")
            llm_model_key = DEFAULT_LLM_MODEL_KEY

        llm_config = AVAILABLE_LLM_MODELS[llm_model_key]
        logging.info(f"Using LLM model {llm_model_key} for meeting {meeting_id}")

        # Determine interval_seconds for context fetching by agents, and for 'recent' transcript_input
        # This is the interval that get_transcription_context will use if fetch_mode is 'recent' for agent's additional_context
        # And also the interval for fetching the main transcript_input if fetch_mode is 'recent'
        interval_seconds_for_context_and_recent_input = meeting.agent_run_interval_seconds if meeting and meeting.agent_run_interval_seconds is not None else DEFAULT_AGENT_RUN_INTERVAL_SECONDS

        # Fetch transcripts for the main input based on mode
        logging.info(f"run_agent_suite: Called with fetch_mode='{fetch_mode}' for meeting_id={meeting_id}")
        if fetch_mode == 'full':
            transcripts = session.query(Transcript).filter(Transcript.meeting_id == meeting_id).order_by(Transcript.timestamp.asc()).all()
            logging.info(f"run_agent_suite: Fetched {len(transcripts)} transcripts for 'full' mode (main input) for meeting {meeting_id}.")
        else:  # 'recent' mode
            start_time = datetime.utcnow() - timedelta(seconds=interval_seconds_for_context_and_recent_input)
            logging.info(f"run_agent_suite: Fetching transcripts for 'recent' mode (main input) for meeting {meeting_id} since {start_time} (last {interval_seconds_for_context_and_recent_input} seconds).")
            transcripts = session.query(Transcript).filter(
                Transcript.meeting_id == meeting_id,
                Transcript.timestamp > start_time
            ).order_by(Transcript.timestamp.asc()).all()
            logging.info(f"run_agent_suite: Fetched {len(transcripts)} transcripts for 'recent' mode (main input) for meeting {meeting_id}.")

        if not transcripts:
            logging.info(f"run_agent_suite: No {fetch_mode} transcripts found for meeting {meeting_id} for main input. Skipping agent processing.")
            session.close() # Close session if returning early
            return

        # Prepare main input for agents by concatenating transcript texts
        transcript_texts = [t.text for t in transcripts]
        transcript_input = "\n".join(transcript_texts)
        transcript_input_snippet = (transcript_input[:200] + '...') if len(transcript_input) > 200 else transcript_input
        logging.info(f"run_agent_suite: Processing {len(transcripts)} transcripts for meeting {meeting_id} (main input, fetch_mode='{fetch_mode}'). Total length: {len(transcript_input)} chars. Snippet: {transcript_input_snippet}")

        # Initialize agents with the selected LLM configuration and correct fetch_mode for their context
        # The fetch_mode passed here will determine how get_transcription_context behaves for agent's additional_context
        # The interval_seconds_for_context_and_recent_input is used by get_transcription_context if fetch_mode is 'recent'
        logging.info(f"Initializing agents for meeting {meeting_id} with fetch_mode='{fetch_mode}' and interval_seconds='{interval_seconds_for_context_and_recent_input}' for their additional_context.")
        white_hat = WhiteHatAgent(llm_config=llm_config, meeting_id=meeting_id, fetch_mode=fetch_mode, interval_seconds=interval_seconds_for_context_and_recent_input)
        blue_hat = BlueHatAgent(llm_config=llm_config, meeting_id=meeting_id, fetch_mode=fetch_mode, interval_seconds=interval_seconds_for_context_and_recent_input)
        red_hat = RedHatAgent(llm_config=llm_config, meeting_id=meeting_id, fetch_mode=fetch_mode, interval_seconds=interval_seconds_for_context_and_recent_input)
        yellow_hat = YellowHatAgent(llm_config=llm_config, meeting_id=meeting_id, fetch_mode=fetch_mode, interval_seconds=interval_seconds_for_context_and_recent_input)
        green_hat = GreenHatAgent(llm_config=llm_config, meeting_id=meeting_id, fetch_mode=fetch_mode, interval_seconds=interval_seconds_for_context_and_recent_input)
        black_hat = BlackHatAgent(llm_config=llm_config, meeting_id=meeting_id, fetch_mode=fetch_mode, interval_seconds=interval_seconds_for_context_and_recent_input)
        purple_hat = PurpleHatAgent(llm_config=llm_config, meeting_id=meeting_id, fetch_mode=fetch_mode, interval_seconds=interval_seconds_for_context_and_recent_input)
        miro_agent = MiroAgent(llm_config=llm_config, meeting_id=meeting_id, fetch_mode=fetch_mode, interval_seconds=interval_seconds_for_context_and_recent_input)

        # Run agents with the transcript input and save outputs
        loop = asyncio.get_event_loop()

        # Run White, Red, Black, Yellow, Green agents simultaneously using run_in_executor
        logging.info(f"Running White, Red, Black, Yellow, Green agents simultaneously for meeting {meeting_id}")
        
        tasks_group1 = [
            loop.run_in_executor(None, white_hat.run, transcript_input, meeting_id),
            loop.run_in_executor(None, red_hat.run, transcript_input, meeting_id),
            loop.run_in_executor(None, yellow_hat.run, transcript_input, meeting_id),
            loop.run_in_executor(None, green_hat.run, transcript_input, meeting_id),
            loop.run_in_executor(None, black_hat.run, transcript_input, meeting_id)
        ]
        results_group1 = await asyncio.gather(*tasks_group1)
        white_output, red_output, yellow_output, green_output, black_output = results_group1
        
        logging.info(f"White, Red, Black, Yellow, Green agents completed for meeting {meeting_id}")

        # Prepare input for Blue Hat and Purple Hat Agents with outputs from the first group
        combined_output_for_blue_purple = f"Transcript:\n{transcript_input}\n\nAgent Outputs:\nWhite Hat (Facts):\n{white_output}\n\nRed Hat (Humor):\n{red_output}\n\nYellow Hat (Opportunities):\n{yellow_output}\n\nGreen Hat (Ideas):\n{green_output}\n\nBlack Hat (Risks):\n{black_output}"

        # Run Blue and Purple agents concurrently after the first group
        logging.info(f"Running Blue and Purple Hat Agents concurrently for meeting {meeting_id}")
        task_blue = loop.run_in_executor(None, blue_hat.run, combined_output_for_blue_purple, meeting_id)
        task_purple = loop.run_in_executor(None, purple_hat.run, combined_output_for_blue_purple, meeting_id) # Purple also uses the combined output
        
        results_group2 = await asyncio.gather(task_blue, task_purple)
        blue_output, purple_output = results_group2
        logging.info(f"Blue and Purple Hat Agents completed for meeting {meeting_id}")

        # Run Miro Agent with outputs from all other agents
        miro_input = f"Transcript:\n{transcript_input}\n\nAgent Outputs:\nWhite Hat (Facts):\n{white_output}\n\nRed Hat (Humor):\n{red_output}\n\nYellow Hat (Opportunities):\n{yellow_output}\n\nGreen Hat (Ideas):\n{green_output}\n\nBlack Hat (Risks):\n{black_output}\n\nPurple Hat (Emotions):\n{purple_output}\n\nBlue Hat (Synthesis):\n{blue_output}"
        logging.info(f"Running Miro Agent for meeting {meeting_id} with combined input")
        miro_output = await loop.run_in_executor(None, miro_agent.run, miro_input, meeting_id)

        logging.info(f"Agent suite completed for meeting {meeting_id}")
    except Exception as e:
        logging.error(f"Error running agent suite for meeting {meeting_id}: {e}", exc_info=True)
    finally:
        if 'session' in locals() and session and session.is_active: # Check if session is active
            session.close()

def agent_scheduler():
    """
    Background thread function to run agents on the active meeting at regular intervals.
    """
    logging.info("Starting agent scheduler thread")
    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    while not _stop_event.is_set():
        run_start_time = time.monotonic() # Record start time of the cycle
        current_active_meeting_at_cycle_start = get_active_meeting() # Store active meeting at start of cycle

        try:
            if current_active_meeting_at_cycle_start is not None:
                logging.info(f"Scheduler: Active meeting detected: {current_active_meeting_at_cycle_start}. Running agent suite.")
                loop.run_until_complete(run_agent_suite(current_active_meeting_at_cycle_start, fetch_mode='recent'))
            else:
                logging.info("Scheduler: No active meeting to process at cycle start. Waiting...")

            # Determine base interval for the next run
            # This interval is the target time from the START of this run to the START of the next.
            target_interval = DEFAULT_AGENT_RUN_INTERVAL_SECONDS
            if current_active_meeting_at_cycle_start is not None:
                try:
                    with Session() as session:
                        meeting = session.query(Meeting).filter(Meeting.id == current_active_meeting_at_cycle_start).first()
                        if meeting and meeting.agent_run_interval_seconds:
                            target_interval = meeting.agent_run_interval_seconds
                            logging.info(f"Scheduler: Using meeting-specific target interval of {target_interval}s for meeting {current_active_meeting_at_cycle_start}")
                        else:
                            logging.info(f"Scheduler: Using default target interval of {target_interval}s for meeting {current_active_meeting_at_cycle_start}")
                except Exception as e:
                    logging.error(f"Error determining scheduler target interval for meeting {current_active_meeting_at_cycle_start}: {e}", exc_info=True)
                    target_interval = DEFAULT_AGENT_RUN_INTERVAL_SECONDS
                    logging.info(f"Scheduler: Falling back to default target interval of {target_interval}s due to error.")
            else:
                # If no active meeting, the loop still needs a sleep duration before checking again.
                # The 'target_interval' here will be used to calculate sleep if no agents ran.
                logging.info(f"Scheduler: No active meeting, base target interval for sleep is {target_interval}s")

            run_end_time = time.monotonic()
            duration_of_run = run_end_time - run_start_time
            
            if current_active_meeting_at_cycle_start is not None: # Only log agent suite duration if it actually ran
                logging.info(f"Scheduler: Agent suite processing (if run) took {duration_of_run:.2f} seconds.")

            sleep_time_needed = target_interval - duration_of_run
            
            if sleep_time_needed <= 0:
                if current_active_meeting_at_cycle_start is not None: # Only warn if agents ran and overran
                    logging.warning(f"Scheduler: Agent suite duration ({duration_of_run:.2f}s) exceeded or met target interval ({target_interval}s). Sleeping for 1s.")
                sleep_time_needed = 1 # Minimal sleep to prevent tight loop and yield control

            logging.info(f"Scheduler: Calculated sleep time is {sleep_time_needed:.2f} seconds. Polling for stop/active meeting changes every 5s within this.")
            
            # Sleep in shorter intervals to be more responsive
            actual_slept_time = 0
            while actual_slept_time < sleep_time_needed and not _stop_event.is_set():
                time_to_wait_short = min(5, sleep_time_needed - actual_slept_time)
                _stop_event.wait(time_to_wait_short) # This is a blocking wait from threading.Event
                actual_slept_time += time_to_wait_short
                
                # Check if the active meeting status changed during this short sleep
                new_active_meeting = get_active_meeting()
                if new_active_meeting != current_active_meeting_at_cycle_start:
                    logging.info(f"Scheduler: Active meeting status changed during sleep (was {current_active_meeting_at_cycle_start}, now {new_active_meeting}). Waking up early.")
                    break
            
            logging.info(f"Scheduler: Waking up for next cycle. Total time in this cycle: {time.monotonic() - run_start_time:.2f}s")

        except Exception as e:
            logging.error(f"Unhandled exception in agent scheduler loop: {e}", exc_info=True)
            _stop_event.wait(5) # Wait a short time before the next attempt in case of persistent errors

    loop.close()
    logging.info("Agent scheduler thread stopped")

def start_agent_scheduler():
    """Start the agent scheduler in a background thread."""
    global _scheduler_thread, _stop_event
    if _scheduler_thread is None or not _scheduler_thread.is_alive():
        _stop_event = threading.Event() # Ensure event is fresh
        _scheduler_thread = threading.Thread(target=agent_scheduler, daemon=True)
        _scheduler_thread.start()
        logging.info("Agent scheduler started")
    else:
        logging.warning("Agent scheduler already running")

def stop_agent_scheduler():
    """Stop the agent scheduler."""
    global _scheduler_thread, _stop_event
    if _scheduler_thread is not None and _scheduler_thread.is_alive():
        logging.info("Stopping agent scheduler...")
        _stop_event.set()
        _scheduler_thread.join(timeout=5.0) # Increased timeout
        if _scheduler_thread.is_alive():
            logging.warning("Agent scheduler thread did not terminate gracefully after 5s")
        else:
            logging.info("Agent scheduler stopped successfully")
    else:
        logging.warning("Agent scheduler not running or already stopped")
    _scheduler_thread = None # Clear thread reference