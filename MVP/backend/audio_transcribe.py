import os
import torch
import numpy as np
import threading
import time
from transformers import WhisperProcessor, WhisperForConditionalGeneration, pipeline
from constants import AVAILABLE_WHISPER_MODELS, SAMPLE_RATE, DEFAULT_AGENT_RUN_INTERVAL_SECONDS # Import list of models, use renamed default interval
import asyncio
from agents.agent_runner import run_agent_suite, set_active_meeting # Import scheduler control
from database import save_transcript_to_db # Ensure this import is present

class AudioTranscriber:
    def __init__(self,
                 device="cuda:0" if torch.cuda.is_available() else "cpu"):
        """Initializes the transcriber with device preference but defers model loading."""
        self.device = device
        self.model_name = None
        self.meeting_id = None
        self.transcriber = None # Model pipeline will be loaded on session start
        print(f"AudioTranscriber initialized on device: {self.device}. Model will be loaded on session start.")
        import logging
        logging.info(f"AudioTranscriber initialized on device: {self.device}. Model will be loaded on session start.")

    def initialize_session(self, meeting_id: int, model_name: str):
        """Sets the meeting ID, loads the specified model if needed, and notifies the scheduler."""
        import logging
        if model_name not in AVAILABLE_WHISPER_MODELS:
            error_msg = f"Invalid model name: {model_name}. Available models: {AVAILABLE_WHISPER_MODELS}"
            logging.error(error_msg)
            raise ValueError(error_msg)

        # Load or reload model only if it's different or not yet loaded
        if self.transcriber is None or self.model_name != model_name:
            logging.info(f"Loading transcription model: {model_name} on device: {self.device}...")
            try:
                # Define the path to the model cache directory
                path_to_this_file = os.path.dirname(os.path.abspath(__file__))
                path_to_stt_model_cache = os.path.join(path_to_this_file, "data/stt_model_cache")
                # Ensure the cache directory exists
                os.makedirs(path_to_stt_model_cache, exist_ok=True)

                # Load processor and model manually with cache_dir
                processor = WhisperProcessor.from_pretrained(model_name, cache_dir=path_to_stt_model_cache)
                model = WhisperForConditionalGeneration.from_pretrained(model_name, cache_dir=path_to_stt_model_cache)

                # Initialize pipeline with pre-loaded model and processor
                self.transcriber = pipeline(
                    "automatic-speech-recognition",
                    model=model,
                    tokenizer=processor.tokenizer,
                    feature_extractor=processor.feature_extractor,
                    chunk_length_s=30,
                    device=self.device
                )
                self.model_name = model_name
                logging.info(f"Model {self.model_name} loaded successfully.")
            except Exception as e:
                logging.error(f"Error loading model {model_name}: {e}", exc_info=True)
                self.transcriber = None # Ensure transcriber is None if loading failed
                raise # Re-raise the exception to signal failure

        self.meeting_id = meeting_id
        set_active_meeting(self.meeting_id) # Inform the central scheduler
        logging.info(f"AudioTranscriber: Session initialized for meeting ID {self.meeting_id} with model {self.model_name}. Scheduler notified.")

    async def process_audio_chunk(self, audio_data, sample_rate=SAMPLE_RATE):
        """Transcribes the given audio data using the configured model and saves it."""
        import logging
        if self.transcriber is None or self.meeting_id is None:
             logging.error(f"Transcriber not initialized or no meeting_id set. Cannot process audio chunk. Transcriber: {self.transcriber is not None}, Meeting ID: {self.meeting_id}")
             return None # Or raise an error?

        try:
            # Ensure meeting_id is an integer
            meeting_id = self.meeting_id
            try:
                if not isinstance(meeting_id, int):
                    meeting_id = int(meeting_id)
                    self.meeting_id = meeting_id  # Update the instance variable too
                    logging.info(f"Converted meeting_id to int: {meeting_id}")
            except (ValueError, TypeError) as e:
                logging.error(f"Invalid meeting_id: {meeting_id}, cannot convert to int: {e}")
                return None

            logging.info(f"Transcribing audio chunk for meeting {meeting_id}...")
            # Ensure audio_data is a numpy array
            if not isinstance(audio_data, np.ndarray):
                audio_data = np.array(audio_data)
                logging.info(f"Converted audio data to numpy array, shape: {audio_data.shape}")

            # Handle different audio shapes (from frontend or system recorder)
            if len(audio_data.shape) == 2:
                if audio_data.shape[1] > 1:
                    audio_data = audio_data.mean(axis=1)
                    logging.info("Converted stereo to mono by averaging channels")
                else:
                    audio_data = audio_data[:, 0]
                    logging.info("Extracted first channel from multi-channel audio")
            elif len(audio_data.shape) > 2:
                error_msg = f"Audio data has more than 2 dimensions: {audio_data.shape}"
                logging.error(error_msg)
                raise ValueError(error_msg)

            # Ensure correct data type
            if audio_data.dtype != np.float32:
                logging.info(f"Converting audio data from {audio_data.dtype} to float32")
                audio_data = audio_data.astype(np.float32)

            logging.info(f"Audio data prepared: shape={audio_data.shape}, dtype={audio_data.dtype}, sample_rate={sample_rate}")

            # Use 'raw' key as specified by the runtime error message - REMOVED THIS
            # audio_input = {'raw': audio_data, 'sampling_rate': sample_rate} # REMOVED DICT WRAPPER
            # The pipeline should handle the conversion from raw audio to features
            logging.info("Starting transcription with Whisper model...")
            transcription = self.transcriber(audio_data, # Pass numpy array directly
                                            chunk_length_s=30,
                                            batch_size=16,
                                            return_timestamps=False)
            logging.info("Transcription complete.")

            # Validate transcription result
            if not isinstance(transcription, dict) or 'text' not in transcription:
                logging.error(f"Invalid transcription result format: {type(transcription)}")
                return None

            # Get the transcript text and clean it
            transcript_text = transcription['text'].strip()

            # Log a preview of the transcription result
            if transcript_text and len(transcript_text) > 0:
                preview = transcript_text[:50] + "..." if len(transcript_text) > 50 else transcript_text
                logging.info(f"Transcription result for meeting {meeting_id}: {preview}")

                # Make sure the meeting is set as active for agent processing
                set_active_meeting(meeting_id)
                logging.info(f"Set meeting {meeting_id} as active for agent processing")

                # Save transcript to DB and verify success
                print(f"\nSaving transcript to database for meeting {meeting_id}\n")
                save_result = save_transcript_to_db(meeting_id, transcript_text)
                if save_result:
                    logging.info(f"Successfully saved transcript to database for meeting {meeting_id}")
                else:
                    logging.error(f"Failed to save transcript to database for meeting {meeting_id}")
            else:
                logging.warning(f"Empty transcription result for meeting {meeting_id}, not saving to database")

            return transcript_text
        except Exception as e:
            logging.error(f"Error during transcription for meeting {self.meeting_id}: {e}", exc_info=True)
            print(f"ERROR in process_audio_chunk: {e}")
            # Consider raising the exception or returning a specific error indicator
            return None

    async def stop(self):
        """Stop transcription, notify scheduler, and run final agent suite."""
        import logging
        current_meeting_id = self.meeting_id # Store before potentially clearing
        logging.info(f"Attempting to stop transcription for meeting ID: {current_meeting_id}")

        # Trigger final agent processing with the full transcript
        if current_meeting_id is not None:
            # Validate meeting_id is an integer
            try:
                if not isinstance(current_meeting_id, int):
                    current_meeting_id = int(current_meeting_id)
                    logging.info(f"Converted meeting_id to int: {current_meeting_id}")
            except (ValueError, TypeError) as e:
                logging.error(f"Invalid meeting_id: {current_meeting_id}, cannot convert to int: {e}")
                current_meeting_id = None

            if current_meeting_id is not None:
                logging.info(f"Triggering FINAL agent suite processing (full) for meeting ID: {current_meeting_id}")
                try:
                    # Explicitly call out that we're running the agent suite
                    print(f"\nRUNNING FINAL AGENT SUITE FOR MEETING {current_meeting_id}\n")
                    # Run agents on the full transcript in a separate thread
                    await asyncio.to_thread(run_agent_suite, current_meeting_id, fetch_mode='full')
                    logging.info(f"Final agent suite processing completed for meeting ID: {current_meeting_id}")
                    print(f"\nFINAL AGENT SUITE COMPLETED FOR MEETING {current_meeting_id}\n")
                except Exception as e:
                    logging.error(f"Error during final agent suite processing for meeting {current_meeting_id}: {e}", exc_info=True)
        else:
            logging.warning("No meeting ID was set, skipping final agent processing.")

        # Clear meeting ID after stopping and notify the scheduler
        self.meeting_id = None
        set_active_meeting(None) # Inform the central scheduler the meeting ended
        logging.info("Transcription stopped and final processing triggered (if applicable).")

        # Optionally clear the model too, or keep it loaded for the next session
        # self.transcriber = None
        # self.model_name = None


if __name__ == '__main__':
    print("AudioTranscribe class initialized. Requires audio data to transcribe.")
    # Add example usage if needed for standalone testing