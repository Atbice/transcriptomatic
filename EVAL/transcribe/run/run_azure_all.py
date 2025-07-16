# run_azure_all.py

import os
from pathlib import Path
import glob
import tempfile
import logging
from datetime import datetime
import requests # Added for HTTP requests
from dotenv import load_dotenv # Added for .env loading

# Get the directory of the current script
SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
dotenv_path = SCRIPT_DIR.parent.parent / ".env"
load_dotenv(dotenv_path=dotenv_path, override=True)

# Third-party libraries
try:
    from pydub import AudioSegment
    from pydub.utils import make_chunks # For creating fixed-duration chunks
    from pydub.exceptions import CouldntDecodeError
except ImportError:
    print("pydub or its utilities not found. Please install with: pip install pydub")
    exit()

# --- Configuration Constants ---
# Azure OpenAI Configuration - Fetched from environment variables
AZURE_OPENAI_ENDPOINT_URL = os.environ.get("AZURE_ENDPOINT_URL")
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_KEY")

# Audio Processing Configuration
AUDIO_DIR = SCRIPT_DIR / ".." / "audio"
RESULTS_DIR = SCRIPT_DIR / ".." / "results" / "azure-api"
SUPPORTED_EXTENSIONS = ["*.wav", "*.mp3", "*.flac"]

# Audio Standardization
TARGET_SAMPLE_RATE = 16000  # Hz
TARGET_CHANNELS = 1         # Mono
MODEL_MAX_CHUNK_DURATION_SECONDS = 300 # Max duration per chunk (23m 50s), safely below 1500s limit
API_REQUEST_TIMEOUT_SECONDS = 1600 # Timeout for API call, should be > chunk duration (e.g., 26m 40s)

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

# --- Audio Processing Module (Leveraging pydub) ---
def find_audio_files(directory, extensions):
    """
    Finds all audio files with specified extensions in the given directory.
    """
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(directory, ext)))
    logger.info(f"Found {len(files)} audio files in {directory}.")
    return files

def convert_to_compatible_wav(input_path, output_path, target_sample_rate, target_channels):
    """
    Converts an audio file to a WAV format compatible with transcription requirements.
    """
    try:
        logger.info(f"Converting '{Path(input_path).name}' to compatible WAV format at '{Path(output_path).name}'.")
        audio = AudioSegment.from_file(input_path)
        audio = audio.set_frame_rate(target_sample_rate)
        audio = audio.set_channels(target_channels)
        audio.export(output_path, format="wav")
        logger.info(f"Successfully converted '{Path(input_path).name}' to '{Path(output_path).name}'.")
        return True
    except CouldntDecodeError as e:
        logger.error(f"Pydub CouldntDecodeError for '{Path(input_path).name}': {e}. Ensure FFmpeg/libav is installed and in PATH if handling non-WAV files.")
        return False
    except Exception as e:
        logger.error(f"Error converting '{Path(input_path).name}' to WAV: {e}")
        return False

# --- Transcription Core Module (Using Azure OpenAI Endpoint) ---
def transcribe_audio_openai(api_key, endpoint_url, audio_chunk_path, model_name="gpt-40-transcribe"):
    """
    Transcribes a single audio chunk using the Azure OpenAI-style transcription endpoint.
    """
    logger.debug(f"Transcribing audio file via OpenAI endpoint: {Path(audio_chunk_path).name}")
    if not api_key or not endpoint_url:
        logger.error("Azure OpenAI API key or endpoint URL is missing.")
        raise ValueError("Missing Azure OpenAI API key or endpoint URL.")

    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": model_name
        # If your model 'gpt-40-transcribe' requires a language parameter, add it here:
        # "language": "sv-SE" # Example
    }
    try:
        with open(audio_chunk_path, 'rb') as audio_file:
            files = {
                'file': (os.path.basename(audio_chunk_path), audio_file, 'audio/wav')
            }
            response = requests.post(endpoint_url, headers=headers, data=data, files=files, timeout=API_REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()

            response_json = response.json()
            transcribed_text = response_json.get('text', '')
            if not transcribed_text and response_json:
                logger.warning(f"Transcription result for {Path(audio_chunk_path).name} was empty. Full response: {response_json}")
            elif not response_json:
                 logger.warning(f"Empty JSON response for {Path(audio_chunk_path).name}")
            return transcribed_text

    except requests.exceptions.Timeout:
        logger.error(f"HTTP Request timed out for {Path(audio_chunk_path).name} after {API_REQUEST_TIMEOUT_SECONDS}s.")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP Request failed for {Path(audio_chunk_path).name}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response status: {e.response.status_code}")
            try:
                logger.error(f"Response content: {e.response.text}")
            except Exception:
                logger.error("Could not decode response content.")
        return None
    except ValueError as e: # For JSON decoding errors
        logger.error(f"Error decoding JSON response for {Path(audio_chunk_path).name}: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during transcription of {Path(audio_chunk_path).name}: {e}")
        return None

# --- Response Parsing & Output ---
def save_transcription(output_base_dir, original_filename, transcription_text):
    """
    Saves the transcription text to a structured output directory.
    """
    filename_no_ext = os.path.splitext(original_filename)[0]
    safe_filename_no_ext = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in filename_no_ext).rstrip()
    results_dir = os.path.join(output_base_dir, safe_filename_no_ext)
    os.makedirs(results_dir, exist_ok=True)

    output_filename = f"azure-api_{safe_filename_no_ext}_transcription_result.txt"
    full_output_path = os.path.join(results_dir, output_filename)

    try:
        with open(full_output_path, "w", encoding="utf-8") as f:
            f.write(transcription_text)
        logger.info(f"Transcription saved to: {full_output_path}")
    except IOError as e:
        logger.error(f"Failed to save transcription to {full_output_path}: {e}")

# --- Main Execution Logic ---
def main():
    logger.info(f"Starting Azure OpenAI Speech-to-Text script with chunking for audio longer than {MODEL_MAX_CHUNK_DURATION_SECONDS}s.")

    os.makedirs(AUDIO_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)

    if not AZURE_OPENAI_ENDPOINT_URL or not AZURE_OPENAI_API_KEY:
        logger.error("AZURE_OPENAI_ENDPOINT_URL or AZURE_OPENAI_API_KEY environment variables not set.")
        return

    audio_files = find_audio_files(AUDIO_DIR, SUPPORTED_EXTENSIONS)
    if not audio_files:
        logger.warning(f"No audio files found in '{AUDIO_DIR}'. Please add audio files to process.")
        return

    for audio_file_path in audio_files:
        original_filename = os.path.basename(audio_file_path)
        logger.info(f"\nProcessing file: {original_filename}")

        temp_wav_for_processing = None
        created_temp_wav = False
        final_transcription = "[PROCESSING_NOT_ATTEMPTED]"

        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_f:
                temp_wav_for_processing = tmp_f.name
            
            if not convert_to_compatible_wav(audio_file_path, temp_wav_for_processing, TARGET_SAMPLE_RATE, TARGET_CHANNELS):
                logger.error(f"Skipping file {original_filename} due to conversion error.")
                final_transcription = "[CONVERSION_FAILED]"
                if os.path.exists(temp_wav_for_processing):
                     try: os.remove(temp_wav_for_processing)
                     except OSError: pass
                temp_wav_for_processing = None
                save_transcription(RESULTS_DIR, original_filename, final_transcription) # Save error status
                continue
            created_temp_wav = True

            try:
                audio_segment = AudioSegment.from_wav(temp_wav_for_processing)
            except Exception as e:
                logger.error(f"Could not load converted WAV {Path(temp_wav_for_processing).name} with pydub: {e}")
                final_transcription = "[FAILED_TO_LOAD_CONVERTED_AUDIO]"
                save_transcription(RESULTS_DIR, original_filename, final_transcription)
                continue

            duration_seconds = len(audio_segment) / 1000.0
            logger.info(f"Duration of '{original_filename}': {duration_seconds:.2f} seconds.")

            chunk_length_ms = MODEL_MAX_CHUNK_DURATION_SECONDS * 1000

            if duration_seconds > MODEL_MAX_CHUNK_DURATION_SECONDS:
                logger.info(f"'{original_filename}' is longer than {MODEL_MAX_CHUNK_DURATION_SECONDS}s. Splitting into chunks of up to {MODEL_MAX_CHUNK_DURATION_SECONDS}s.")
                
                audio_chunks = make_chunks(audio_segment, chunk_length_ms)
                transcribed_parts = []
                total_chunks = len(audio_chunks)
                logger.info(f"Splitting '{original_filename}' into {total_chunks} chunks.")

                for i, chunk_data in enumerate(audio_chunks):
                    chunk_part_name = f"chunk_{i+1}_of_{total_chunks}"
                    temp_chunk_wav = None
                    try:
                        with tempfile.NamedTemporaryFile(suffix=f"_{chunk_part_name}.wav", delete=False) as tmp_chunk_f:
                            temp_chunk_wav = tmp_chunk_f.name
                        
                        # Ensure chunk is not empty (can happen with make_chunks if total duration is small multiple)
                        if len(chunk_data) == 0:
                            logger.warning(f"Skipping empty chunk {chunk_part_name} for '{original_filename}'.")
                            continue

                        chunk_data.export(temp_chunk_wav, format="wav")
                        logger.info(f"Transcribing {chunk_part_name} for '{original_filename}' (duration: {len(chunk_data)/1000.0:.2f}s)")
                        
                        transcription_part = transcribe_audio_openai(
                            AZURE_OPENAI_API_KEY,
                            AZURE_OPENAI_ENDPOINT_URL,
                            temp_chunk_wav
                        )
                        if transcription_part is None:
                            transcribed_parts.append(f"[{chunk_part_name.upper()}_TRANSCRIPTION_FAILED_API_ERROR]")
                        elif not transcription_part.strip():
                            transcribed_parts.append(f"[{chunk_part_name.upper()}_NO_SPEECH_RECOGNIZED]")
                        else:
                            transcribed_parts.append(transcription_part)
                    except Exception as e_chunk:
                        logger.error(f"Error processing {chunk_part_name} for '{original_filename}': {e_chunk}", exc_info=True)
                        transcribed_parts.append(f"[{chunk_part_name.upper()}_PROCESSING_ERROR]")
                    finally:
                        if temp_chunk_wav and os.path.exists(temp_chunk_wav):
                            try:
                                os.remove(temp_chunk_wav)
                                logger.debug(f"Deleted temporary chunk WAV: {temp_chunk_wav}")
                            except OSError as e_del_chunk:
                                logger.warning(f"Could not delete temp chunk WAV {temp_chunk_wav}: {e_del_chunk}")
                
                final_transcription = "\n\n".join(transcribed_parts)
            
            else: # Audio is not longer than MODEL_MAX_CHUNK_DURATION_SECONDS
                logger.info(f"Transcribing entire file '{original_filename}' (<= {MODEL_MAX_CHUNK_DURATION_SECONDS}s).")
                transcription_result = transcribe_audio_openai(
                    AZURE_OPENAI_API_KEY,
                    AZURE_OPENAI_ENDPOINT_URL,
                    temp_wav_for_processing
                )
                if transcription_result is None:
                    final_transcription = "[TRANSCRIPTION_FAILED_API_ERROR]"
                elif not transcription_result.strip():
                    final_transcription = "[No speech recognized in the audio]"
                else:
                    final_transcription = transcription_result
            
            log_snippet = final_transcription[:100].replace('\n', ' ') + ('...' if len(final_transcription) > 100 else '')
            logger.info(f"Saving transcription for {original_filename}. Snippet: {log_snippet}")
            save_transcription(RESULTS_DIR, original_filename, final_transcription)

        except Exception as e:
            logger.error(f"An unexpected error occurred while processing {original_filename}: {e}", exc_info=True)
            if final_transcription == "[PROCESSING_NOT_ATTEMPTED]" or not (final_transcription.startswith("[") and final_transcription.endswith("]")):
                 final_transcription = "[OVERALL_PROCESSING_ERROR_UNEXPECTED]"
            save_transcription(RESULTS_DIR, original_filename, final_transcription)
        finally:
            if created_temp_wav and temp_wav_for_processing and os.path.exists(temp_wav_for_processing):
                try:
                    os.remove(temp_wav_for_processing)
                    logger.debug(f"Deleted temporary processing WAV: {temp_wav_for_processing}")
                except OSError as e_del:
                    logger.warning(f"Could not delete temporary file {temp_wav_for_processing}: {e_del}")
    
    logger.info("Script finished.")

if __name__ == "__main__":
    # FFmpeg check (basic)
    # A more robust check would involve trying to invoke ffmpeg directly or checking its version.
    try:
        # Try to load a tiny dummy segment. If pydub can't find ffmpeg for common formats, it might error here.
        AudioSegment.silent(duration=10).export("dummy_check.wav", format="wav") # wav export itself doesn't need ffmpeg
        # The real test is often when 'from_file' is called with mp3/flac in convert_to_compatible_wav
        logger.debug("Pydub basic audio segment creation successful.")
        if os.path.exists("dummy_check.wav"): os.remove("dummy_check.wav")
    except Exception as e:
        logger.warning(
            f"Pydub/FFmpeg check encountered an issue: {e}. "
            "If you are processing MP3 or FLAC files, ensure FFmpeg is installed and in your system's PATH. "
            "WAV file processing should still work."
        )
    main()