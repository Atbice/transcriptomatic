# transcribe_deepgram.py

import os
import glob
import asyncio
import functools
import tempfile
import logging
from datetime import datetime
from pydub import AudioSegment
from pydub.silence import split_on_silence
from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
    FileSource
)

# --- Configuration Constants ---
# Deepgram API Key -  MUST be set as an environment variable DEEPGRAM_API_KEY
# or directly here (not recommended for security)
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

INPUT_AUDIO_DIR = "./audio"  # Directory containing audio files
OUTPUT_TRANSCRIPTION_DIR = "./results/deepgram-api"
TARGET_LANGUAGE_CODE = "sv"  # Swedish

# pydub Audio Splitting Parameters
MIN_SILENCE_LEN_MS = 700  # Minimum length of silence to split on, in milliseconds
SILENCE_THRESH_DBFS = -35  # Silence threshold in dBFS (quieter than this is silence)
CHUNK_TARGET_DURATION_MS = 30000  # Target duration for chunks in ms (e.g., 30 seconds)
CHUNK_OVERLAP_MS = 500 # Overlap between chunks to avoid cutting words

# Deepgram API Parameters
DEEPGRAM_MODEL = "nova-2" # Or other models like "base", "enhanced"
DEEPGRAM_API_TIMEOUT_SECONDS = 300 # Timeout for API requests

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Authentication Module ---
def get_deepgram_client(api_key: str) -> DeepgramClient | None:
    """
    Initializes and returns a DeepgramClient.
    """
    if not api_key:
        logger.error("DEEPGRAM_API_KEY not found. Please set it as an environment variable.")
        return None
    try:
        deepgram = DeepgramClient(api_key)
        return deepgram
    except Exception as e:
        logger.error(f"Failed to initialize Deepgram client: {e}")
        return None

# --- Audio Processing Module (Leveraging existing logic) ---
def find_audio_files(input_dir: str) -> list[str]:
    """
    Finds all WAV, FLAC, and MP3 files in the specified directory.
    """
    supported_formats = ["*.wav", "*.flac", "*.mp3"]
    audio_files = []
    for fmt in supported_formats:
        audio_files.extend(glob.glob(os.path.join(input_dir, fmt)))
    logger.info(f"Found {len(audio_files)} audio files in {input_dir}.")
    return audio_files

def convert_mp3_to_wav(mp3_path: str) -> str | None:
    """
    Converts an MP3 file to a temporary WAV file.
    Returns the path to the temporary WAV file, or None if conversion fails.
    """
    try:
        logger.info(f"Converting MP3 '{os.path.basename(mp3_path)}' to WAV...")
        audio = AudioSegment.from_mp3(mp3_path)
        fd, temp_wav_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd) # close file descriptor
        audio.export(temp_wav_path, format="wav")
        logger.info(f"Successfully converted to temporary WAV: {temp_wav_path}")
        return temp_wav_path
    except Exception as e:
        logger.error(f"Error converting MP3 '{mp3_path}' to WAV: {e}")
        return None

def standardize_audio_segment(audio_segment: AudioSegment) -> AudioSegment:
    """
    Standardizes an audio segment to mono, 16kHz sample rate, 16-bit depth.
    Deepgram generally handles this well, but consistency can help.
    """
    audio_segment = audio_segment.set_channels(1)
    # Deepgram Nova-2 is trained on various sample rates, but explicit conversion can be good.
    # For other models, 16000Hz is often preferred.
    # audio_segment = audio_segment.set_frame_rate(16000)
    # audio_segment = audio_segment.set_sample_width(2) # 16-bit
    return audio_segment


def split_audio_on_silence_deepgram(
    audio_segment: AudioSegment,
    min_silence_len: int = MIN_SILENCE_LEN_MS,
    silence_thresh: int = SILENCE_THRESH_DBFS,
    keep_silence: int = 100, # Amount of silence to keep at edges of chunks
    max_chunk_duration_ms: int = CHUNK_TARGET_DURATION_MS,
    overlap_ms: int = CHUNK_OVERLAP_MS
) -> list[AudioSegment]:
    """
    Splits an AudioSegment into smaller chunks based on silence.
    Attempts to keep chunks under max_chunk_duration_ms.
    """
    logger.info(f"Splitting audio: min_silence_len={min_silence_len}ms, silence_thresh={silence_thresh}dBFS, max_chunk_duration={max_chunk_duration_ms}ms")

    # First, split by silence
    initial_chunks = split_on_silence(
        audio_segment,
        min_silence_len=min_silence_len,
        silence_thresh=silence_thresh,
        keep_silence=keep_silence
    )

    if not initial_chunks:
        logger.warning("No silence detected for splitting, using the whole audio as one chunk if it's short enough.")
        if len(audio_segment) <= max_chunk_duration_ms:
            return [audio_segment]
        else: # if it's too long and no silence, we have to split it bluntly
            logger.warning(f"Audio is longer than {max_chunk_duration_ms}ms and no silence detected. Splitting by max duration.")


    final_chunks = []
    current_chunk = None

    for segment in initial_chunks:
        if current_chunk is None:
            current_chunk = segment
        elif len(current_chunk) + len(segment) <= max_chunk_duration_ms:
            current_chunk += segment
        else:
            final_chunks.append(current_chunk)
            current_chunk = segment # Start new chunk

    if current_chunk is not None:
        final_chunks.append(current_chunk)

    # If any chunk is still too long, split it hard
    processed_chunks = []
    for chunk in final_chunks:
        if len(chunk) > max_chunk_duration_ms:
            start_time = 0
            while start_time < len(chunk):
                end_time = min(start_time + max_chunk_duration_ms, len(chunk))
                sub_chunk = chunk[start_time:end_time]
                processed_chunks.append(sub_chunk)
                start_time += max_chunk_duration_ms - overlap_ms # Apply overlap for subsequent chunks
                if start_time >= len(chunk): # ensure we don't create tiny overlaps at the very end
                    break
        else:
            processed_chunks.append(chunk)

    logger.info(f"Audio split into {len(processed_chunks)} chunks.")
    return processed_chunks


# --- Transcription Core Module ---
async def transcribe_chunk_deepgram(
    deepgram_client: DeepgramClient,
    audio_chunk_path: str,
    language_code: str = TARGET_LANGUAGE_CODE
) -> dict | None:
    """
    Transcribes a single audio chunk using Deepgram API.
    Returns the API response as a dictionary.
    """
    if not os.path.exists(audio_chunk_path):
        logger.error(f"Audio chunk path does not exist: {audio_chunk_path}")
        return None

    try:
        with open(audio_chunk_path, 'rb') as audio_file:
            buffer_data = audio_file.read()

        payload: FileSource = {
            "buffer": buffer_data,
        }

        options = PrerecordedOptions(
            model=DEEPGRAM_MODEL,
            language=language_code,
            smart_format=True,
            punctuate=True,
            diarize=False, # Set to True if diarization is needed
            # Add other features as needed:
            # numerals=True,
            # profanity_filter=True,
        )
        
        logger.info(f"Sending chunk '{os.path.basename(audio_chunk_path)}' to Deepgram for transcription...")

        # Get the current event loop
        loop = asyncio.get_running_loop()

        # Get the synchronous transcribe_file method
        transcribe_method = deepgram_client.listen.prerecorded.v("1").transcribe_file

        # Create a partial function for the blocking call
        blocking_call = functools.partial(transcribe_method, payload, options=options, timeout=DEEPGRAM_API_TIMEOUT_SECONDS)

        # Run the blocking call in the default executor
        response = await loop.run_in_executor(None, blocking_call)

        logger.info(f"Received transcription for chunk '{os.path.basename(audio_chunk_path)}'.")
        return response.to_dict() # Convert Deepgram's response object to dict

    except Exception as e:
        logger.error(f"Error transcribing chunk '{os.path.basename(audio_chunk_path)}' with Deepgram: {e}")
        return None

# --- Response Parsing & Output ---
def extract_transcription_text_deepgram(response: dict) -> str | None:
    """
    Extracts the transcription text from Deepgram's API response.
    """
    try:
        if response and response.get("results") and response["results"]["channels"]:
            transcript = response["results"]["channels"][0]["alternatives"][0]["transcript"]
            if transcript.strip(): # Ensure it's not just whitespace
                return transcript
            else:
                logger.warning("Received an empty transcript string from Deepgram.")
                return None
        else:
            logger.warning(f"Transcription result seems empty or malformed: {response}")
            return None
    except (KeyError, IndexError, TypeError) as e:
        logger.error(f"Error parsing Deepgram transcription response: {e}. Response: {response}")
        return None

def save_transcription(output_dir: str, original_filename: str, transcription_text: str):
    """
    Saves the transcription text to a .txt file in the output directory.
    """
    base_filename = os.path.splitext(original_filename)[0]
    # Construct the new nested output directory
    nested_output_dir = os.path.join(output_dir, base_filename)

    # Ensure the nested directory exists
    if not os.path.exists(nested_output_dir):
        os.makedirs(nested_output_dir, exist_ok=True)
        logger.info(f"Created output directory: {nested_output_dir}")

    # Construct the new output filepath
    output_filename = f"deepgram-api_{base_filename}_transcription_result.txt"
    output_filepath = os.path.join(nested_output_dir, output_filename)

    try:
        with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(transcription_text)
        logger.info(f"Transcription saved to: {output_filepath}")
    except IOError as e:
        logger.error(f"Error saving transcription to file '{output_filepath}': {e}")


# --- Main Execution Logic ---
async def process_single_audio_file(deepgram_client: DeepgramClient, audio_path: str):
    """
    Processes a single audio file: converts, splits, transcribes, and saves.
    """
    logger.info(f"--- Starting processing for: {os.path.basename(audio_path)} ---")
    original_filename = os.path.basename(audio_path)
    temp_wav_path = None
    processed_audio_path = audio_path # Path to the audio file that will be processed (WAV or FLAC)

    if audio_path.lower().endswith(".mp3"):
        temp_wav_path = convert_mp3_to_wav(audio_path)
        if not temp_wav_path:
            logger.error(f"Skipping {original_filename} due to MP3 conversion failure.")
            return
        processed_audio_path = temp_wav_path

    try:
        logger.info(f"Loading audio file: {processed_audio_path}")
        audio_segment = AudioSegment.from_file(processed_audio_path)
    except Exception as e:
        logger.error(f"Error loading audio file '{processed_audio_path}': {e}")
        if temp_wav_path and os.path.exists(temp_wav_path):
            os.remove(temp_wav_path)
            logger.info(f"Cleaned up temporary WAV: {temp_wav_path}")
        return

    audio_segment = standardize_audio_segment(audio_segment)
    audio_chunks = split_audio_on_silence_deepgram(audio_segment)

    if not audio_chunks:
        logger.warning(f"No audio chunks to process for {original_filename}. Skipping.")
        if temp_wav_path and os.path.exists(temp_wav_path):
            os.remove(temp_wav_path)
            logger.info(f"Cleaned up temporary WAV: {temp_wav_path}")
        return

    all_chunk_transcriptions = []
    chunk_temp_files = []

    for i, chunk_segment in enumerate(audio_chunks):
        fd, chunk_temp_path = tempfile.mkstemp(suffix=f"_chunk{i}.wav")
        os.close(fd)
        chunk_temp_files.append(chunk_temp_path)
        
        try:
            logger.info(f"Exporting chunk {i+1}/{len(audio_chunks)} to temporary WAV: {chunk_temp_path}")
            # Ensure chunk is WAV for Deepgram if not already
            chunk_segment.export(chunk_temp_path, format="wav")
            
            transcription_response = await transcribe_chunk_deepgram(deepgram_client, chunk_temp_path)
            if transcription_response:
                transcript_text = extract_transcription_text_deepgram(transcription_response)
                if transcript_text:
                    all_chunk_transcriptions.append(transcript_text)
                else:
                    logger.warning(f"Chunk {i+1} of {original_filename} yielded no valid transcript.")
            else:
                logger.warning(f"Transcription failed for chunk {i+1} of {original_filename}.")

        except Exception as e:
            logger.error(f"Error processing chunk {i+1} of {original_filename}: {e}")
        finally:
            if os.path.exists(chunk_temp_path):
                os.remove(chunk_temp_path)
                # logger.debug(f"Deleted temporary chunk WAV: {chunk_temp_path}")
    
    logger.info(f"Collected {len(all_chunk_transcriptions)} transcriptions for {original_filename}.")

    if all_chunk_transcriptions:
        final_transcription = " ".join(all_chunk_transcriptions)
        save_transcription(OUTPUT_TRANSCRIPTION_DIR, original_filename, final_transcription)
    else:
        logger.warning(f"No transcriptions were generated for {original_filename}.")

    if temp_wav_path and os.path.exists(temp_wav_path):
        os.remove(temp_wav_path)
        logger.info(f"Cleaned up temporary WAV: {temp_wav_path}")
    
    logger.info(f"--- Finished processing for: {original_filename} ---")


async def main():
    """
    Main asynchronous function to orchestrate the transcription process.
    """
    if not DEEPGRAM_API_KEY:
        logger.critical("DEEPGRAM_API_KEY environment variable is not set. Exiting.")
        print("Error: DEEPGRAM_API_KEY is not set. Please set it in your environment or .env file.")
        return

    deepgram_client = get_deepgram_client(DEEPGRAM_API_KEY)
    if not deepgram_client:
        logger.critical("Failed to initialize Deepgram client. Exiting.")
        return

    if not os.path.exists(INPUT_AUDIO_DIR):
        logger.warning(f"Input directory '{INPUT_AUDIO_DIR}' does not exist. Creating it.")
        os.makedirs(INPUT_AUDIO_DIR, exist_ok=True)
        logger.info(f"Please add audio files to '{INPUT_AUDIO_DIR}' and re-run the script.")
        return

    audio_files_to_process = find_audio_files(INPUT_AUDIO_DIR)

    if not audio_files_to_process:
        logger.info(f"No audio files found in '{INPUT_AUDIO_DIR}'. Exiting.")
        return

    logger.info(f"Starting transcription process for {len(audio_files_to_process)} files...")

    # Create output directory if it doesn't exist
    if not os.path.exists(OUTPUT_TRANSCRIPTION_DIR):
        os.makedirs(OUTPUT_TRANSCRIPTION_DIR, exist_ok=True)
        logger.info(f"Created output directory: {OUTPUT_TRANSCRIPTION_DIR}")

    for audio_file_path in audio_files_to_process:
        await process_single_audio_file(deepgram_client, audio_file_path)

    logger.info("All audio files processed.")


if __name__ == "__main__":
    # To load .env file if present (for local development)
    try:
        from dotenv import load_dotenv
        load_dotenv()
        DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", DEEPGRAM_API_KEY) # Re-assign if loaded from .env
        logger.info(".env file loaded (if present).")
    except ImportError:
        logger.info("dotenv library not found, skipping .env load. Ensure DEEPGRAM_API_KEY is set in environment.")
        pass # dotenv is optional

    if DEEPGRAM_API_KEY is None: # Final check after attempting to load .env
        print("CRITICAL: DEEPGRAM_API_KEY is not set. Please refer to README.md for configuration.")
        logger.critical("CRITICAL: DEEPGRAM_API_KEY is not set after checking environment and .env. Exiting.")
    else:
        asyncio.run(main())