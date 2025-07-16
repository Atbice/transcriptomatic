# transcribe_elevenlabs.py
'''Python script to automate audio transcription using the ElevenLabs Speech-to-Text API.
This script processes local audio files (WAV, FLAC, MP3), converts them if necessary,
splits long audio files into smaller chunks based on silence, transcribes them using
ElevenLabs API, and saves the transcriptions to a structured output directory.
'''

import os
from pathlib import Path

# Get the directory of the current script
SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
import glob
import tempfile
import httpx
import logging
import time # Added import for time
from pydub import AudioSegment
from pydub.silence import split_on_silence
from elevenlabs.client import ElevenLabs
# from elevenlabs import save # save is for TTS, not directly used for STT response saving to text file
# import dotenv
from dotenv import load_dotenv
load_dotenv() # Load environment variables from .env file if needed

# --- Configuration ---
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
if not ELEVENLABS_API_KEY:
    logging.warning("ElevenLabs API Key not found in environment variables. "
                    "Please set ELEVENLABS_API_KEY or hardcode it in the script (not recommended).")
    # exit(1) # Consider exiting if API key is crucial and not found

INPUT_AUDIO_DIR = SCRIPT_DIR / ".." / "audio"
OUTPUT_DIR_BASE = SCRIPT_DIR / ".." / "results" / "elevenlabs-api"
TARGET_LANGUAGE_CODE = "sv" # Swedish (primarily for reference, Scribe auto-detects)

# Use the official model ID for Scribe.
ELEVENLABS_STT_MODEL_ID = "scribe_v1" # Corrected/Verified STT model ID

# Audio processing parameters (relevant if using splitting and conversion)
TARGET_SAMPLE_RATE = 16000
TARGET_CHANNELS = 1
TARGET_SAMPLE_WIDTH = 2
MIN_SILENCE_LEN = 700
SILENCE_THRESH = -35
KEEP_SILENCE = 300

# Chunking parameters
CHUNK_DURATION_MS = 20 * 60 * 1000 # 20 minutes in milliseconds

# Retry parameters for transcription
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 10

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# For more detailed SDK communication, you can set elevenlabs client logging
# import httpx
# httpx_logger = logging.getLogger("httpx")
# httpx_logger.setLevel(logging.DEBUG) # or INFO


# --- Helper Functions ---
def ensure_dir(directory_path):
    Path(directory_path).mkdir(parents=True, exist_ok=True)

# --- Authentication Module ---
def get_elevenlabs_client(api_key: str) -> ElevenLabs | None:
    if not api_key:
        logging.error("ElevenLabs API Key is missing.")
        return None
    try:
        client = ElevenLabs(api_key=api_key)
        logging.info("ElevenLabs client initialized with custom timeout settings.")
        return client
    except Exception as e:
        logging.error(f"Failed to initialize ElevenLabs client: {e}")
        return None

# --- Audio Processing Module (Leveraging existing logic from plan) ---
# These functions (find_audio_files, convert_to_standard_wav, split_audio_on_silence_wrapper)
# are kept for completeness but are bypassed in the current direct MP3 test logic in main().

def find_audio_files(input_dir: str) -> list[str]:
    supported_formats = ["*.wav", "*.mp3", "*.flac"]
    audio_files = []
    for fmt in supported_formats:
        audio_files.extend(glob.glob(os.path.join(input_dir, fmt)))
    logging.info(f"Found {len(audio_files)} audio files in {input_dir}.")
    return audio_files

def convert_to_standard_wav(audio_path: str, target_path: str) -> bool:
    try:
        logging.info(f"Loading audio file: {audio_path}")
        audio = AudioSegment.from_file(audio_path)
        logging.info(f"Original audio: {audio.frame_rate}Hz, {audio.channels} channels, {audio.sample_width*8}-bit")
        audio = audio.set_channels(TARGET_CHANNELS)
        audio = audio.set_frame_rate(TARGET_SAMPLE_RATE)
        audio = audio.set_sample_width(TARGET_SAMPLE_WIDTH)
        audio.export(target_path, format="wav")
        logging.info(f"Successfully converted and standardized {audio_path} to {target_path}")
        return True
    except Exception as e:
        logging.error(f"Error converting {audio_path} to WAV: {e}")
        return False

def split_audio_on_silence_wrapper(
    audio_segment: AudioSegment,
    min_silence_len_ms: int,
    silence_thresh_dbfs: int,
    keep_silence_ms: int
) -> list[AudioSegment]:
    logging.info(f"Splitting audio: min_silence_len={min_silence_len_ms}ms, "
                 f"silence_thresh={silence_thresh_dbfs}dBFS, keep_silence={keep_silence_ms}ms")
    chunks = split_on_silence(
        audio_segment,
        min_silence_len=min_silence_len_ms,
        silence_thresh=silence_thresh_dbfs,
        keep_silence=keep_silence_ms,
        seek_step=1
    )
    if not chunks:
        logging.warning("No silence detected, treating as a single chunk.")
        return [audio_segment]
    logging.info(f"Audio split into {len(chunks)} chunks.")
    return chunks

# --- Transcription Core Module ---
def transcribe_chunk_elevenlabs(
    elevenlabs_client: ElevenLabs,
    audio_chunk_path: str,
    model_id: str = ELEVENLABS_STT_MODEL_ID
) -> dict | None:
    """
    Transcribes a single audio chunk using the ElevenLabs STT API with retry logic for timeouts.
    Relies on the 'eleven_scribe_v1' model which auto-detects language.
    """
    if not elevenlabs_client:
        logging.error("ElevenLabs client not available for transcription.")
        return None

    for attempt in range(MAX_RETRIES):
        try:
            logging.info(f"Attempt {attempt + 1}/{MAX_RETRIES}: Transcribing chunk: {audio_chunk_path} with model '{model_id}'")

            with open(audio_chunk_path, "rb") as audio_file:
                stt_response = elevenlabs_client.speech_to_text.convert(
                    file=audio_file,
                    model_id=model_id
                )

            logging.info(f"STT API response object type: {type(stt_response)}")

            if hasattr(stt_response, 'text') and isinstance(stt_response.text, str):
                full_text = stt_response.text
                logging.info(f"Successfully transcribed chunk on attempt {attempt + 1}. Raw text length: {len(full_text)}")
                stripped_text = full_text.strip()
                if not stripped_text:
                    logging.warning(f"Transcription resulted in empty or whitespace-only text for model '{model_id}' using file '{audio_chunk_path}' on attempt {attempt + 1}.")
                    try:
                        vars_stt_response = vars(stt_response) # Use a variable to avoid potential issues in f-string
                        logging.debug(f"STT Response object details (when text is empty): {vars_stt_response}")
                    except TypeError:
                        logging.debug(f"STT Response object (could not get vars): {stt_response}")
                return {"text": stripped_text}
            else:
                logging.error(f"Attempt {attempt + 1}/{MAX_RETRIES}: Unexpected response structure from ElevenLabs STT. Expected .text attribute on response object.")
                logging.debug(f"Raw STT response object type: {type(stt_response)}")
                logging.debug(f"Raw STt response object content (first 1000 chars): {str(stt_response)[:1000]}")
                # If the structure is unexpected, it's likely not a transient timeout, so don't retry this specific error.
                return None

        except Exception as e:
            error_message = str(e)
            logging.error(f"Attempt {attempt + 1}/{MAX_RETRIES}: Error during ElevenLabs STT for chunk {audio_chunk_path} with model {model_id}: {error_message}")
            if hasattr(e, 'body'):
                logging.error(f"API Error Body: {e.body}")

            # Check if the error is a timeout and if retries are available
            if "timed out" in error_message.lower() and attempt < MAX_RETRIES - 1:
                logging.warning(f"Timeout detected. Retrying in {RETRY_DELAY_SECONDS} seconds...")
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                # If it's not a timeout or no retries left, log and return None
                if "timed out" in error_message.lower():
                     logging.error(f"Timeout error persisted after {MAX_RETRIES} attempts for {audio_chunk_path}.")
                else:
                     logging.error(f"Non-timeout error occurred or retries exhausted for {audio_chunk_path}.")
                return None # Return None after exhausting retries or for non-timeout errors

    # This part should ideally not be reached if MAX_RETRIES > 0, but as a fallback:
    logging.error(f"Transcription failed after {MAX_RETRIES} attempts for {audio_chunk_path}.")
    return None


# --- Response Parsing & Output ---
def extract_transcription_text_elevenlabs(response: dict | None) -> str | None:
    if response and "text" in response:
        return response["text"] # This will be the stripped text
    # logging.warning("Could not extract transcription text from response dict.") # Already logged if text is empty
    return None

def save_transcription(output_filepath: str, transcription_text: str):
    try:
        with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(transcription_text)
        logging.info(f"Transcription successfully saved to {output_filepath}")
    except IOError as e:
        logging.error(f"Error saving transcription to {output_filepath}: {e}")

# --- Main Execution Logic ---
def main():
    logging.info("Starting ElevenLabs Transcription Process...")

    if not ELEVENLABS_API_KEY:
        logging.error("ELEVENLABS_API_KEY is not set. Exiting.")
        return

    elevenlabs_client = get_elevenlabs_client(ELEVENLABS_API_KEY)
    if not elevenlabs_client:
        logging.error("Failed to initialize ElevenLabs client. Exiting.")
        return

    ensure_dir(INPUT_AUDIO_DIR)
    ensure_dir(OUTPUT_DIR_BASE)

    # Get all audio files from the input directory
    audio_files_to_process = find_audio_files(INPUT_AUDIO_DIR)
    if not audio_files_to_process:
        logging.warning("No audio files found to process. Exiting.")
        return
    logging.info(f"Found {len(audio_files_to_process)} audio files to process.")

    for i, audio_file_path in enumerate(audio_files_to_process):
        logging.info(f"--- Processing file: {audio_file_path} ---")
        file_name_no_ext = Path(audio_file_path).stem
        file_output_dir = os.path.join(OUTPUT_DIR_BASE, f"{file_name_no_ext}")
        ensure_dir(file_output_dir)
        output_transcription_path = os.path.join(
            file_output_dir,
            f"elevenlabs-api_{file_name_no_ext}_transcription_result.txt"
        )

        # --- Check for existing transcription ---
        if os.path.exists(output_transcription_path):
            try:
                with open(output_transcription_path, "r", encoding="utf-8") as f:
                    existing_content = f.read().strip()
                if existing_content != "[No transcription result or empty text returned by API]":
                    logging.info(f"Skipping transcription for {audio_file_path}: Valid transcription already exists at {output_transcription_path}")
                    # Add delay even if skipped, unless it's the last file
                    if i < len(audio_files_to_process) - 1:
                        logging.info(f"Waiting 120 seconds before processing next file...")
                        time.sleep(120)
                    continue # Skip to the next file
                else:
                    logging.info(f"Existing transcription file found for {audio_file_path} but content indicates no result. Re-processing.")
            except IOError as e:
                logging.warning(f"Could not read existing transcription file {output_transcription_path}: {e}. Proceeding with transcription.")
        # --- End Check ---

        try:
            logging.info(f"Loading audio file for duration check: {audio_file_path}")
            audio = AudioSegment.from_file(audio_file_path)
            duration_ms = len(audio)
            logging.info(f"Audio duration: {duration_ms} ms")

            full_transcription = ""

            if duration_ms > CHUNK_DURATION_MS:
                logging.info(f"Audio duration ({duration_ms} ms) exceeds chunk limit ({CHUNK_DURATION_MS} ms). Splitting into chunks.")
                start_ms = 0
                chunk_index = 0
                while start_ms < duration_ms:
                    end_ms = min(start_ms + CHUNK_DURATION_MS, duration_ms)
                    chunk = audio[start_ms:end_ms]

                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                        temp_audio_path = tmp_file.name
                        chunk.export(temp_audio_path, format="wav")
                        logging.info(f"Saved chunk {chunk_index} to temporary file: {temp_audio_path}")

                    try:
                        logging.info(f"Transcribing chunk {chunk_index} ({start_ms}-{end_ms} ms)")
                        transcription_response_dict = transcribe_chunk_elevenlabs(
                            elevenlabs_client,
                            temp_audio_path,
                            model_id=ELEVENLABS_STT_MODEL_ID
                        )
                        transcribed_text = extract_transcription_text_elevenlabs(transcription_response_dict)

                        if transcribed_text:
                            full_transcription += transcribed_text + " " # Concatenate with a space
                            logging.info(f"Chunk {chunk_index} transcription successful.")
                        else:
                            logging.warning(f"Transcription yielded no text for chunk {chunk_index}.")
                            full_transcription += "[No transcription result for this chunk] "

                    finally:
                        # Clean up the temporary file
                        os.remove(temp_audio_path)
                        logging.info(f"Cleaned up temporary file: {temp_audio_path}")

                    start_ms = end_ms
                    chunk_index += 1

                # Save the concatenated transcription
                if full_transcription.strip():
                     save_transcription(output_transcription_path, full_transcription.strip())
                else:
                     save_transcription(output_transcription_path, "[No transcription result or empty text returned by API]")


            else:
                logging.info(f"Audio duration ({duration_ms} ms) is within chunk limit. Processing as a single file.")
                transcription_response_dict = transcribe_chunk_elevenlabs(
                    elevenlabs_client,
                    audio_file_path,
                    model_id=ELEVENLABS_STT_MODEL_ID
                )

                transcribed_text = extract_transcription_text_elevenlabs(transcription_response_dict)

                if transcribed_text:
                    logging.info(f"Transcription successful. Text preview: '{transcribed_text[:100]}...'")
                    save_transcription(output_transcription_path, transcribed_text)
                else:
                    logging.warning(f"Transcription yielded no text for {audio_file_path}.")
                    save_transcription(output_transcription_path, "[No transcription result or empty text returned by API]")


        except Exception as e_file:
            logging.error(f"An unhandled error occurred processing file {audio_file_path}: {e_file}")
        finally:
            pass

        logging.info(f"--- Finished processing for file: {audio_file_path} ---")

        # --- Add delay after processing ---
        # Add delay unless it's the last file
        if i < len(audio_files_to_process) - 1:
            logging.info(f"Waiting 120 seconds before processing next file...")
            time.sleep(120)
        # --- End Add delay ---


    logging.info("ElevenLabs Transcription Process Completed.")

if __name__ == "__main__":
    main()