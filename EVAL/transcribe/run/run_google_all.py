import os
import glob
from google.cloud import speech
import google.api_core.exceptions # Explicitly import for GoogleAPIError
from pydub import AudioSegment # For MP3 to WAV conversion and splitting
from pydub.silence import split_on_silence # For splitting
import tempfile # For creating temporary WAV files

# --- Configuration ---

AUDIO_DIR = "./audio"  # Directory containing audio files to transcribe
import os
from dotenv import load_dotenv
SUPPORTED_EXTENSIONS = ("*.wav", "*.flac", "*.mp3")
RESULTS_BASE_DIR = "./results/google-api" # Base directory for saving transcriptions

TARGET_SAMPLE_RATE = 16000  # Desired sample rate for WAV conversion

# Parameters for splitting audio on silence
MIN_SILENCE_LEN_MS = 700  # Minimum length of a silence to be used for splitting (milliseconds)
SILENCE_THRESH_DBFS_OFFSET = -14 # Offset from average dBFS to consider as silence (e.g., -14 means 14dB below average)
KEEP_SILENCE_MS = 250     # Amount of silence to leave at the beginning and end of chunks (milliseconds)
MAX_CHUNK_DURATION_S = 55 # Maximum duration for a chunk in seconds to be safe for API limit

# --- Authentication ---

# --- Audio File Handling ---
def find_audio_files(directory):
    audio_files = []
    if not os.path.exists(directory):
        print(f"Audio directory not found: {directory}")
        try:
            os.makedirs(directory) 
            print(f"Created directory: {directory}. Please add audio files to it.")
        except OSError as e:
            print(f"Error creating directory {directory}: {e}")
            return [] 
        return [] 
        
    for ext in SUPPORTED_EXTENSIONS:
        audio_files.extend(glob.glob(os.path.join(directory, ext)))
    
    if not audio_files:
        print(f"No audio files found in {directory} with supported extensions ({', '.join(SUPPORTED_EXTENSIONS)}).")
    return audio_files

# --- MP3 to WAV Conversion ---
def convert_mp3_to_wav(mp3_path, target_sample_rate=TARGET_SAMPLE_RATE):
    try:
        print(f"Converting {os.path.basename(mp3_path)} to WAV...")
        audio = AudioSegment.from_mp3(mp3_path)
        audio = audio.set_frame_rate(target_sample_rate)
        audio = audio.set_channels(1) # Mono
        audio = audio.set_sample_width(2) # 16-bit

        temp_wav_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_wav_path = temp_wav_file.name
        temp_wav_file.close() 

        audio.export(temp_wav_path, format="wav")
        print(f"Converted to temporary WAV: {temp_wav_path}")
        return temp_wav_path
    except Exception as e:
        print(f"Error converting MP3 to WAV for {mp3_path}: {e}")
        print("Make sure FFmpeg is installed and accessible in your system's PATH.")
        return None

# --- Audio Splitting ---
def split_audio_on_silence_wrapper(audio_segment, min_silence_len=MIN_SILENCE_LEN_MS, 
                                   silence_thresh_offset=SILENCE_THRESH_DBFS_OFFSET, 
                                   keep_silence=KEEP_SILENCE_MS):
    """
    Splits an AudioSegment object based on silence.
    Returns a list of AudioSegment objects (chunks).
    """
    dynamic_silence_thresh = audio_segment.dBFS + silence_thresh_offset
    print(f"Splitting audio on silence (min_silence_len={min_silence_len}ms, "
          f"silence_thresh={dynamic_silence_thresh:.2f}dBFS, keep_silence={keep_silence}ms)...")
    
    chunks = split_on_silence(
        audio_segment,
        min_silence_len=min_silence_len,
        silence_thresh=dynamic_silence_thresh,
        keep_silence=keep_silence,
        seek_step=1 # Check every ms for silence for finer granularity
    )
    
    if not chunks:
        print("No silence found to split on, processing the audio as a single chunk.")
        return [audio_segment] # Return the original segment as a single chunk
    
    print(f"Audio initially split into {len(chunks)} chunks based on silence.")
    return chunks

# --- Recognition Configuration ---
def get_recognition_config(audio_file_path_is_wav, language_code="sv-SE"): # Expects path to a WAV
    diarization_settings = speech.SpeakerDiarizationConfig(
        enable_speaker_diarization=False
    )
    config = speech.RecognitionConfig(
        language_code=language_code,
        enable_word_time_offsets=False,
        diarization_config=diarization_settings,
        enable_automatic_punctuation=True,
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16, # All chunks are WAV
        sample_rate_hertz=TARGET_SAMPLE_RATE # All chunks are set to this rate
    )
    # No need to check extension as we ensure chunks/converted files are WAV
    return config

# --- Transcription ---
def transcribe_chunk(client, audio_chunk_path, log_prefix, config):
    if config is None: # Should not happen if get_recognition_config is robust
        print(f"Skipping transcription for {log_prefix} due to missing recognition config.")
        return None
    try:
        with open(audio_chunk_path, "rb") as audio_file_content:
            content = audio_file_content.read()
        
        audio_input = speech.RecognitionAudio(content=content)
        
        print(f"Transcribing {log_prefix} (Language: {config.language_code}, Source: {os.path.basename(audio_chunk_path)})...")
        response = client.recognize(config=config, audio=audio_input)
        return response
    except FileNotFoundError:
        print(f"Error: Audio file not found at {audio_chunk_path}")
        return None
    except google.api_core.exceptions.GoogleAPIError as e:
        print(f"Google API error during transcription of {log_prefix}: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during transcription of {log_prefix}: {e}")
        return None

# --- Response Processing ---
def extract_transcription_text(response):
    full_transcript_parts = []
    if response and response.results:
        for result in response.results:
            if result.alternatives and len(result.alternatives) > 0:
                full_transcript_parts.append(result.alternatives[0].transcript)
    return "\n".join(full_transcript_parts).strip() # Return stripped single string from chunk

# --- Output Saving ---
def save_transcription(original_audio_file_path, full_transcription_text):
    if not full_transcription_text:
        print(f"No transcription text to save for {os.path.basename(original_audio_file_path)}.")
        return

    audio_file_name_with_ext = os.path.basename(original_audio_file_path)
    audio_file_name_no_ext, _ = os.path.splitext(audio_file_name_with_ext)

    output_dir_for_file = os.path.join(RESULTS_BASE_DIR, audio_file_name_no_ext)
    output_file_name = f"google-api_{audio_file_name_no_ext}_transcription_result.txt"
    output_file_path = os.path.join(output_dir_for_file, output_file_name)

    try:
        os.makedirs(output_dir_for_file, exist_ok=True)
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(full_transcription_text)
        print(f"Transcription saved to: {output_file_path}")
    except IOError as e:
        print(f"Error writing transcription to file {output_file_path}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while saving transcription for {os.path.basename(original_audio_file_path)}: {e}")

# --- Main Execution Logic ---
def main():
    # Determine the correct path to the .env file relative to the script
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(dotenv_path=dotenv_path)

    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        print("Error: GOOGLE_API_KEY not found in .env file or environment. Please ensure it is set.")
        print(f"Attempted to load .env from: {dotenv_path}")
        return

    print("API key loaded successfully.")
    try:
        speech_client = speech.SpeechClient(client_options={'api_key': api_key})
    except Exception as e:
        print(f"Failed to create SpeechClient: {e}")
        return


    audio_files_to_process = find_audio_files(AUDIO_DIR)

    if not audio_files_to_process:
        print(f"Exiting as no audio files were found or directory could not be accessed in '{AUDIO_DIR}'.")
        return

    print(f"Found {len(audio_files_to_process)} audio file(s) to process.")

    for original_audio_path in audio_files_to_process:
        print(f"\nProcessing original file: {original_audio_path}")
        
        path_to_process_as_wav = original_audio_path
        is_converted_mp3_temp_file = False
        original_filename_for_logging = os.path.basename(original_audio_path)

        file_extension = os.path.splitext(original_audio_path)[1].lower()

        if file_extension == ".mp3":
            temp_wav_path = convert_mp3_to_wav(original_audio_path)
            if temp_wav_path:
                path_to_process_as_wav = temp_wav_path
                is_converted_mp3_temp_file = True
            else:
                print(f"Skipping {original_audio_path} due to MP3 conversion error.")
                continue 
        elif file_extension not in [".wav", ".flac"]:
             # If FLAC, it will be loaded by AudioSegment directly.
             # If other unsupported type, AudioSegment.from_file might fail later.
            pass


        all_chunk_transcriptions = []
        try:
            # Load the audio file (should be WAV or FLAC, or converted WAV from MP3)
            print(f"Loading audio for splitting: {path_to_process_as_wav}")
            # Determine format for pydub if not WAV
            audio_format = "wav" # Default, as MP3s are converted to WAV
            if os.path.splitext(path_to_process_as_wav)[1].lower() == ".flac":
                audio_format = "flac"
            
            sound = AudioSegment.from_file(path_to_process_as_wav, format=audio_format)
            # Ensure sound is in the target format for consistency before splitting
            sound = sound.set_frame_rate(TARGET_SAMPLE_RATE).set_channels(1).set_sample_width(2)

        except Exception as e:
            print(f"Error loading audio segment from {path_to_process_as_wav}: {e}")
            if is_converted_mp3_temp_file and os.path.exists(path_to_process_as_wav):
                try:
                    os.remove(path_to_process_as_wav)
                    print(f"Deleted temporary WAV file: {path_to_process_as_wav}")
                except Exception as e_del:
                    print(f"Error deleting temporary WAV file {path_to_process_as_wav}: {e_del}")
            continue

        # Split audio into chunks
        audio_chunks = split_audio_on_silence_wrapper(sound)
        
        if not audio_chunks:
            print(f"Audio splitting did not produce chunks for {original_filename_for_logging}. Skipping.")
        else:
            for i, chunk_segment in enumerate(audio_chunks):
                log_chunk_prefix = f"{original_filename_for_logging} (chunk {i+1}/{len(audio_chunks)})"
                
                if chunk_segment.duration_seconds == 0:
                    print(f"Skipping zero duration chunk {i+1} for {original_filename_for_logging}.")
                    continue

                if chunk_segment.duration_seconds > MAX_CHUNK_DURATION_S:
                    print(f"WARNING: {log_chunk_prefix} is {chunk_segment.duration_seconds:.2f}s long. "
                          f"This might exceed the API's synchronous limit and result in an error. "
                          f"Consider adjusting silence splitting parameters or using GCS for very long segments.")
                
                temp_chunk_file = None # Ensure it's defined for finally block
                try:
                    # Export chunk to a temporary WAV file
                    temp_chunk_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                    temp_chunk_path = temp_chunk_file.name
                    temp_chunk_file.close() # Close it so pydub can write

                    print(f"Exporting {log_chunk_prefix} to {temp_chunk_path} ({chunk_segment.duration_seconds:.2f}s)")
                    chunk_segment.export(temp_chunk_path, format="wav")

                    # Get recognition config (always for WAV now)
                    recognition_config_chunk = get_recognition_config(True, language_code="sv-SE") 
                    
                    api_response_chunk = transcribe_chunk(
                        speech_client, 
                        temp_chunk_path, 
                        log_chunk_prefix, 
                        recognition_config_chunk
                    )
                    if api_response_chunk:
                        transcribed_text_chunk = extract_transcription_text(api_response_chunk)
                        if transcribed_text_chunk:
                            all_chunk_transcriptions.append(transcribed_text_chunk)
                
                except Exception as e_chunk_proc:
                    print(f"Error processing {log_chunk_prefix}: {e_chunk_proc}")
                finally:
                    if temp_chunk_file and os.path.exists(temp_chunk_file.name):
                        try:
                            os.remove(temp_chunk_file.name)
                        except Exception as e_del_chunk:
                            print(f"Error deleting temp chunk {temp_chunk_file.name}: {e_del_chunk}")
            
            # Combine transcriptions from all chunks for the original file
            final_transcribed_text = " ".join(all_chunk_transcriptions).strip()

            if final_transcribed_text:
                save_transcription(original_audio_path, final_transcribed_text)
            else:
                print(f"No transcription result after processing all chunks for {original_filename_for_logging}.")

        # Delete the main temporary WAV file if it was created from an MP3
        if is_converted_mp3_temp_file and os.path.exists(path_to_process_as_wav):
            try:
                os.remove(path_to_process_as_wav)
                print(f"Deleted converted MP3 temp file: {path_to_process_as_wav}")
            except Exception as e_del_main_temp:
                print(f"Error deleting converted MP3 temp file {path_to_process_as_wav}: {e_del_main_temp}")
            
    print("\nAll processing finished.")

if __name__ == "__main__":
    main()
