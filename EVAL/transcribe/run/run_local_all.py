import os
from pathlib import Path

# Get the directory of the current script
SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
import shutil
import wave
import logging
import numpy as np
# import pyaudio # We will import conditionally later
import threading
import json
import websocket
import uuid
import time
import av # Used for RTSP/HLS streams, might not be strictly needed for file-only transcription

# Configure logging early
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Assume whisper_live.utils is accessible or replace with equivalent logic
class DummyUtils:
    def clear_screen(self):
        pass
    def print_transcript(self, text):
        print("\n--- Transcription ---")
        for line in text:
            print(line)
        print("--------------------")
    def create_srt_file(self, transcript, output_path):
         print(f"Dummy: Writing SRT to {output_path}")
         # Simple dummy SRT output (matches structure of the provided example)
         try:
             with open(output_path, "w", encoding="utf-8") as f:
                 for i, segment in enumerate(transcript):
                     f.write(f"{i+1}\n")
                     # Simple time format (HH:MM:SS,ms) - adjust if needed
                     start_time_ms = int(float(segment.get('start', 0)) * 1000)
                     end_time_ms = int(float(segment.get('end', 0)) * 1000)

                     start_h, start_rem_s = divmod(start_time_ms // 1000, 3600)
                     start_m, start_s = divmod(start_rem_s, 60)
                     start_ms = start_time_ms % 1000

                     end_h, end_rem_s = divmod(end_time_ms // 1000, 3600)
                     end_m, end_s = divmod(end_rem_s, 60)
                     end_ms = end_time_ms % 1000

                     f.write(f"{start_h:02}:{start_m:02}:{start_s:02},{start_ms:03} --> {end_h:02}:{end_m:02}:{end_s:02},{end_ms:03}\n")
                     f.write(f"{segment.get('text', '').strip()}\n\n")
             print(f"Dummy: SRT file written to {output_path}")
         except Exception as e:
              print(f"Dummy: Error writing SRT file {output_path}: {e}")


    def resample(self, audio_path, sr=16000):
        logging.info(f"DummyUtils.resample: Called with audio_path='{audio_path}', sr={sr}")
        
        # Log details about the TEMP_DIR global variable
        try:
            logging.info(f"DummyUtils.resample: TEMP_DIR type is {type(TEMP_DIR)}, value is '{TEMP_DIR}'")
            if isinstance(TEMP_DIR, Path) and TEMP_DIR.is_absolute():
                logging.info(f"DummyUtils.resample: TEMP_DIR is an absolute Path: '{TEMP_DIR}'")
            else:
                logging.warning(f"DummyUtils.resample: TEMP_DIR is NOT an absolute Path or not a Path object! Value: '{TEMP_DIR}', Type: {type(TEMP_DIR)}")
        except NameError:
            logging.error("DummyUtils.resample: TEMP_DIR global variable is not defined!")
            return audio_path # Cannot proceed without TEMP_DIR

        # Ensure the TEMP_DIR directory exists (it should have been created by main_async)
        try:
            TEMP_DIR.mkdir(parents=True, exist_ok=True)
            logging.info(f"DummyUtils.resample: Ensured TEMP_DIR exists at '{TEMP_DIR}'")
        except Exception as e_mkdir:
            logging.error(f"DummyUtils.resample: Failed to ensure TEMP_DIR '{TEMP_DIR}' exists: {e_mkdir}")
            return audio_path # Return original if temp dir cannot be assured

        path_obj_audio = Path(audio_path)
        # Ensure the output filename has a .wav extension for the dummy resample
        resampled_filename = f"{path_obj_audio.stem}_resampled.wav"
        logging.info(f"DummyUtils.resample: Calculated resampled_filename='{resampled_filename}' (forced .wav extension)")
        
        dummy_resampled_path_obj = TEMP_DIR / resampled_filename
        # Convert to string for shutil.copy and logging
        dummy_resampled_path_str = str(dummy_resampled_path_obj)
        
        logging.info(f"DummyUtils.resample: Destination path object is '{dummy_resampled_path_obj}'")
        logging.info(f"DummyUtils.resample: Destination path string is '{dummy_resampled_path_str}'")
        
        try:
            shutil.copy(str(audio_path), dummy_resampled_path_str) # Ensure audio_path is also a string for shutil.copy
            logging.info(f"Dummy: Created dummy resampled file at '{dummy_resampled_path_str}'")
            return dummy_resampled_path_str
        except Exception as e:
            logging.error(f"Dummy resample failed to copy file from '{str(audio_path)}' to '{dummy_resampled_path_str}': {e}")
            # Log current working directory if copy fails, might give a clue
            try:
                logging.error(f"DummyUtils.resample: Current working directory is '{os.getcwd()}'")
            except:
                pass # Intentionally ignore errors from os.getcwd() in this context
            return audio_path # Return original path if copy fails

utils = None  # Initialize utils

try:
    import whisper_live.utils as wl_utils
    logging.info("Successfully imported 'whisper_live.utils'.")
    utils = wl_utils  # Use the real utils if import succeeds

    # Check if the real utils has a resample method and log which one is active
    if hasattr(utils, 'resample'):
        logging.info("The 'utils.resample' method will use the 'whisper_live.utils' library's REAL implementation.")
    else:
        logging.warning("'whisper_live.utils' was imported but does not have a 'resample' method.")
        logging.info("Falling back to DummyUtils for 'resample' and other utils functions as 'resample' is critical and missing.")
        utils = DummyUtils() # Fallback if resample is missing from the imported module
        logging.info("The 'utils.resample' method will now use the local DUMMY implementation.")

except ImportError:
    logging.warning("Failed to import 'whisper_live.utils'. Will use local DummyUtils as a fallback.")
    utils = DummyUtils()
    logging.info("The 'utils.resample' method will use the local DUMMY implementation.")
except Exception as e:
    logging.error(f"An unexpected error occurred during 'whisper_live.utils' import: {e}. Will use local DummyUtils as a fallback.")
    utils = DummyUtils()
    logging.info("The 'utils.resample' method will use the local DUMMY implementation due to an import error.")

# Final check to ensure utils is assigned (should not happen with current logic but good for safety)
if utils is None:
    logging.critical("CRITICAL: 'utils' was not assigned. This indicates a flaw in the import logic. Defaulting to DummyUtils to prevent a crash.")
    utils = DummyUtils()
    logging.info("The 'utils.resample' method will use the local DUMMY implementation due to a critical fallback.")


class Client:
    """
    Handles communication with a server using WebSocket.
    """
    INSTANCES = {}
    END_OF_AUDIO = "END_OF_AUDIO"

    def __init__(
        self,
        host=None,
        port=None,
        lang=None,
        translate=False,
        model="small",
        srt_file_path="output.srt",
        use_vad=True,
        log_transcription=True,
        max_clients=4,
        max_connection_time=7200,  # Log the value for debugging
        send_last_n_segments=10,
        no_speech_thresh=0.45,
        clip_audio=False,
        same_output_threshold=10,
    ):
        logging.info("\033[91mMax connection time set to %d seconds\033[0m" % max_connection_time)  # Fixed formatting to use %d for integer
        """
        Initializes a Client instance for audio recording and streaming to a server.

        If host and port are not provided, the WebSocket connection will not be established.
        When translate is True, the task will be set to "translate" instead of "transcribe".
        he audio recording starts immediately upon initialization.

        Args:
            host (str): The hostname or IP address of the server.
            port (int): The port number for the WebSocket server.
            lang (str, optional): The selected language for transcription. Default is None.
            translate (bool, optional): Specifies if the task is translation. Default is False.
            model (str, optional): The whisper model to use (e.g., "small", "medium", "large"). Default is "small".
            srt_file_path (str, optional): The file path to save the output SRT file. Default is "output.srt".
            use_vad (bool, optional): Whether to enable voice activity detection. Default is True.
            log_transcription (bool, optional): Whether to log transcription output to the console. Default is True.
            max_clients (int, optional): Maximum number of client connections allowed. Default is 4.
            max_connection_time (int, optional): Maximum allowed connection time in seconds. Default is 600.
            send_last_n_segments (int, optional): Number of most recent segments to send to the client. Defaults to 10.
            no_speech_thresh (float, optional): Segments with no speech probability above this threshold will be discarded. Defaults to 0.45.
            clip_audio (bool, optional): Whether to clip audio with no valid segments. Defaults to False.
            same_output_threshold (int, optional): Number of repeated outputs before considering it as a valid segment. Defaults to 10.
        """
        self.recording = False
        self.task = "transcribe"
        self.uid = str(uuid.uuid4())
        self.waiting = False
        self.last_response_received = None
        self.disconnect_if_no_response_for = 10800  # Increased to 3 hours to accommodate longer audio files and prevent premature disconnections
        self.language = lang
        self.model = model
        self.server_error = False
        self.srt_file_path = srt_file_path
        self.use_vad = use_vad
        self.last_segment = None
        self.last_received_segment = None
        self.log_transcription = log_transcription
        self.max_clients = max_clients
        self.max_connection_time = max_connection_time
        self.send_last_n_segments = send_last_n_segments
        self.no_speech_thresh = no_speech_thresh
        self.clip_audio = clip_audio
        self.same_output_threshold = same_output_threshold

        if translate:
            self.task = "translate"

        self.audio_bytes = None

        if host is not None and port is not None:
            socket_url = f"ws://{host}:{port}"
            self.client_socket = websocket.WebSocketApp(
                socket_url,
                on_open=lambda ws: self.on_open(ws),
                on_message=lambda ws, message: self.on_message(ws, message),
                on_error=lambda ws, error: self.on_error(ws, error),
                on_close=lambda ws, close_status_code, close_msg: self.on_close(
                    ws, close_status_code, close_msg
                ),
            )
        else:
            print("[ERROR]: No host or port specified.")
            # Set server_error to prevent waiting loop in __call__
            self.server_error = True
            self.error_message = "No host or port specified."
            return # Exit init if no connection details

        Client.INSTANCES[self.uid] = self

        # start websocket client in a thread
        self.ws_thread = threading.Thread(target=self.client_socket.run_forever)
        self.ws_thread.daemon = True # Allow thread to exit when main program exits
        self.ws_thread.start()

        self.transcript = [] 

    def handle_status_messages(self, message_data):
        """Handles server status messages."""
        status = message_data["status"]
        if status == "WAIT":
            self.waiting = True
            # Ensure message is a number before rounding
            wait_time = message_data.get('message', 0)
            if isinstance(wait_time, (int, float)):
                 print(f"[INFO]: Client {self.uid}: Server is full. Estimated wait time {round(wait_time)} minutes.")
            else:
                 print(f"[INFO]: Client {self.uid}: Server is full. Received unexpected message: {wait_time}")

        elif status == "ERROR":
            print(f"[ERROR]: Client {self.uid}: Message from Server: {message_data.get('message', 'Unknown Error')}")
            self.server_error = True
            self.error_message = message_data.get('message', 'Unknown server error.')
            # Trigger disconnect
            try: self.client_socket.close()
            except: pass # Ignore errors if socket is already closed
        elif status == "WARNING":
            print(f"[WARNING]: Client {self.uid}: Message from Server: {message_data.get('message', 'Unknown Warning')}")
        else:
             print(f"[INFO]: Client {self.uid}: Received unknown status: {status}")


    def process_segments(self, segments):
        """Processes transcript segments."""
        text = []
        # Ensure segments is a list
        if not isinstance(segments, list):
            logging.warning(f"[WARNING]: Client {self.uid}: Received non-list segments: {segments}")
            return

        for i, seg in enumerate(segments):
             # Ensure seg is a dictionary and has 'text' key
             if not isinstance(seg, dict) or 'text' not in seg:
                 logging.warning(f"[WARNING]: Client {self.uid}: Received invalid segment format: {seg}")
                 continue

             segment_text = seg.get("text", "") # Use get with default

             if not text or text[-1] != segment_text:
                 text.append(segment_text)

             # Append completed segments to the full transcript list
             # Check if server_backend exists and is 'faster_whisper' before accessing seg.get("completed")
             if hasattr(self, 'server_backend') and self.server_backend == "faster_whisper" and seg.get("completed", False):
                  # Check if this segment is already the last one in the transcript or overlaps/is before
                  # This basic check prevents simple duplicates but might not handle complex overlaps
                  if not self.transcript or (
                      'start' in seg and 'end' in seg and 'end' in self.transcript[-1] and
                       float(seg['start']) >= float(self.transcript[-1]['end']) - 0.01 # Allow tiny overlaps
                  ):
                      # Deep copy segment if it's mutable, though dictionaries are usually fine here
                      self.transcript.append(seg) # Appending complete segments here
                      logging.debug(f"[DEBUG]: Client {self.uid}: Appended completed segment: {segment_text[:50]}...")
                  else:
                      logging.debug(f"[DEBUG]: Client {self.uid}: Skipping append of completed segment (overlaps or duplicate): {segment_text[:50]}...")

             # Update last segment if it's the very last one in the list and not completed by server
             # This is typically for the current "unstable" segment
             if i == len(segments) - 1 and not seg.get("completed", False):
                  self.last_segment = seg # This seems to store the last received *incomplete* segment


        # update last received segment and last valid response time
        if segments: # Only update if segments list is not empty
            last_seg_text = segments[-1].get("text", "")
            if self.last_received_segment is None or self.last_received_segment != last_seg_text:
                self.last_response_received = time.time()
                self.last_received_segment = last_seg_text
                logging.debug(f"[DEBUG]: Client {self.uid}: Updated last received segment: {last_seg_text[:50]}...")

        if self.log_transcription and text: # Only log if logging is enabled and there is text
            # Truncate to last few entries for brevity.
            # text = text[-5:] # Log last 5 segments
            try:
                utils.clear_screen() # Might not work in all terminals
                utils.print_transcript(text) # print_transcript expects a list of strings
            except Exception as e:
                 logging.warning(f"[WARNING]: Error during console transcription logging: {e}")


    def on_message(self, ws, message):
        """
        Callback function called when a message is received from the server.

        It updates various attributes of the client based on the received message, including
        recording status, language detection, and server messages. If a disconnect message
        is received, it sets the recording status to False.

        Args:
            ws (websocket.WebSocketApp): The WebSocket client instance.
            message (str): The received message from the server.

        """
        try:
            message = json.loads(message)
        except json.JSONDecodeError:
            logging.error(f"[ERROR]: Client {self.uid}: Failed to parse JSON message: {message[:100]}...")
            return

        if self.uid != message.get("uid"):
            print(f"[ERROR]: Client {self.uid}: Received message with invalid client uid: {message.get('uid')}")
            return

        if "status" in message.keys():
            self.handle_status_messages(message)
            return

        if "message" in message.keys():
            msg_content = message["message"]
            if msg_content == "DISCONNECT":
                print(f"[INFO]: Client {self.uid}: Server disconnected due to overtime.")
                self.recording = False
            elif msg_content == "SERVER_READY":
                self.last_response_received = time.time()
                self.recording = True
                self.server_backend = message.get("backend", "unknown") # Use .get for safety
                print(f"[INFO]: Client {self.uid}: Server Running with backend {self.server_backend}")
            else:
                 # Log other server messages if needed
                 logging.info(f"[INFO]: Client {self.uid}: Server message: {msg_content}")

            return # Handled message, return


        if "language" in message.keys():
            self.language = message.get("language")
            lang_prob = message.get("language_prob")
            print(
                f"[INFO]: Client {self.uid}: Server detected language {self.language} with probability {lang_prob:.4f}"
            )
            return # Handled message, return


        if "segments" in message.keys():
            self.process_segments(message["segments"])
            # Do not return here, as message might contain other keys besides segments

        # Process any other keys in the message if necessary


    def on_error(self, ws, error):
        # Check if the error is a connection closed error, which is expected during shutdown
        if isinstance(error, websocket.WebSocketConnectionClosedException):
             logging.info(f"[INFO]: Client {self.uid}: WebSocket connection closed (expected).")
        else:
             print(f"[ERROR] Client {self.uid}: WebSocket Error: {error}")
             self.server_error = True
             self.error_message = str(error)
             # Set recording to False on error
             self.recording = False
             self.waiting = False


    def on_close(self, ws, close_status_code, close_msg):
        print(f"[INFO]: Client {self.uid}: Websocket connection closed: {close_status_code}: {close_msg}")
        self.recording = False
        self.waiting = False
        # Ensure last response time is updated or handled so wait_before_disconnect doesn't block indefinitely
        # If closed, no more responses are coming.
        if self.last_response_received is None:
             self.last_response_received = time.time() # Set it now to allow wait_before_disconnect to proceed


    def on_open(self, ws):
        """
        Callback function called when the WebSocket connection is successfully opened.

        Sends an initial configuration message to the server, including client UID,
        language selection, and task type.

        Args:
            ws (websocket.WebSocketApp): The WebSocket client instance.

        """
        print(f"[INFO]: Client {self.uid}: Opened connection")
        config_message = {
            "uid": self.uid,
            "language": self.language,
            "task": self.task,
            "model": self.model,
            "use_vad": self.use_vad,
            "max_clients": self.max_clients,
            "max_connection_time": self.max_connection_time,
            "send_last_n_segments": self.send_last_n_segments,
            "no_speech_thresh": self.no_speech_thresh,
            "clip_audio": self.clip_audio,
            "same_output_threshold": self.same_output_threshold,
        }
        try:
            ws.send(json.dumps(config_message))
            logging.debug(f"[DEBUG]: Client {self.uid}: Sent config message: {config_message}")
        except Exception as e:
            logging.error(f"[ERROR]: Client {self.uid}: Failed to send config message on open: {e}")
            # Optionally close the socket if config cannot be sent
            try: ws.close()
            except: pass


    def send_packet_to_server(self, message):
        """
        Send an audio packet to the server using WebSocket.

        Args:
            message (bytes): The audio data packet in bytes to be sent to the server.

        """
        # Check if the socket is still open and connected before sending
        if not hasattr(self, 'client_socket') or self.client_socket is None or \
           not hasattr(self.client_socket, 'sock') or self.client_socket.sock is None or \
           not self.client_socket.sock.connected:
            # logging.warning(f"[WARNING]: Client {self.uid}: WebSocket not connected. Cannot send packet.")
            return # Do not attempt to send if socket is not ready

        try:
            self.client_socket.send(message, websocket.ABNF.OPCODE_BINARY)
            # logging.debug(f"[DEBUG]: Client {self.uid}: Sent {len(message)} bytes.") # Log only in debug
        except websocket.WebSocketConnectionClosedException:
             logging.warning(f"[WARNING]: Client {self.uid}: WebSocket connection closed. Cannot send packet.")
             self.recording = False # Ensure recording stops if connection closes
        except Exception as e:
            # Suppress frequent logging for send errors unless in debug mode
            # logging.debug(f"[DEBUG]: Client {self.uid}: Error sending packet: {e}")
            pass


    def close_websocket(self):
        """
        Close the WebSocket connection and join the WebSocket thread.

        First attempts to close the WebSocket connection using `self.client_socket.close()`. After
        closing the connection, it joins the WebSocket thread to ensure proper termination.

        """
        # Check if client_socket exists and is not None before trying to close
        if hasattr(self, 'client_socket') and self.client_socket:
            try:
                logging.info(f"[INFO]: Client {self.uid}: Attempting to close WebSocket connection.")
                # The close() method sends the close frame and waits for the server's close frame
                self.client_socket.close()
                logging.info(f"[INFO]: Client {self.uid}: WebSocket close method called.")
            except Exception as e:
                logging.error(f"[ERROR]: Client {self.uid}: Error calling WebSocket close(): {e}")
        else:
             logging.debug(f"[DEBUG]: Client {self.uid}: WebSocket client socket not initialized or already processed close.")


        # Check if ws_thread exists and is alive before trying to join
        if hasattr(self, 'ws_thread') and self.ws_thread and self.ws_thread.is_alive():
            try:
                logging.debug(f"[DEBUG]: Client {self.uid}: Joining WebSocket thread.")
                # Give the thread a moment to process pending events before joining
                self.ws_thread.join(timeout=5.0) # Increased timeout slightly
                if self.ws_thread.is_alive():
                    logging.warning(f"[WARNING]: Client {self.uid}: WebSocket thread did not terminate after join timeout.")
                else:
                    logging.debug(f"[DEBUG]: Client {self.uid}: WebSocket thread joined successfully.")
            except Exception as e:
                logging.error(f"[ERROR:] Client {self.uid}: Error joining WebSocket thread: {e}")
        else:
             logging.debug(f"[DEBUG]: Client {self.uid}: WebSocket thread not initialized or not alive.")

        # Remove instance from the global dict after closing
        if self.uid in Client.INSTANCES:
            del Client.INSTANCES[self.uid]
            logging.debug(f"[DEBUG]: Removed Client {self.uid} from INSTANCES.")


    def get_client_socket(self):
        """
        Get the WebSocket client socket instance.

        Returns:
            WebSocketApp: The WebSocket client socket instance currently in use by the client.
            None: If the client_socket is not initialized.
        """
        return getattr(self, 'client_socket', None)


    def write_srt_file(self, output_path="output.srt"):
        """
        Writes out the transcript in .srt format.

        Args:
            output_path (str, optional): The path to the target file.  Default is "output.srt".

        """
        # Ensure transcript is not empty before writing
        # Also include the last_segment if it exists and wasn't added as a completed segment
        final_transcript_for_srt = list(self.transcript) # Make a copy
        if self.last_segment and 'text' in self.last_segment and self.last_segment.get("text") and \
           (not final_transcript_for_srt or (
                'text' in final_transcript_for_srt[-1] and final_transcript_for_srt[-1]['text'] != self.last_segment['text']
            )):
             # Add last segment if it's different from the last completed segment
             # Ensure it has valid time info before adding
             if 'start' in self.last_segment and 'end' in self.last_segment:
                  # Basic check to avoid adding segments that clearly precede the last completed one
                   if not final_transcript_for_srt or float(self.last_segment['start']) >= float(final_transcript_for_srt[-1]['end']) - 0.01:
                        final_transcript_for_srt.append(self.last_segment)
                        logging.debug(f"[DEBUG]: Client {self.uid}: Appended last unstable segment for SRT.")
                   else:
                        logging.debug(f"[DEBUG]: Client {self.uid}: Skipping append of last unstable segment for SRT (time mismatch).")
             else:
                  logging.debug(f"[DEBUG]: Client {self.uid}: Last segment has no time info, skipping append for SRT.")


        if final_transcript_for_srt:
            try:
                # Ensure the output directory exists
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                utils.create_srt_file(final_transcript_for_srt, output_path)
                logging.info(f"[INFO]: Client {self.uid}: SRT file written to {output_path}")
            except Exception as e:
                logging.error(f"[ERROR]: Client {self.uid}: Error writing SRT file {output_path}: {e}")
        else:
            logging.warning(f"[WARNING]: Client {self.uid}: No transcript segments available to write SRT file to {output_path}.")


    def wait_before_disconnect(self):
        """Waits a bit before disconnecting in order to process pending responses."""
        # Only wait if the client is still marked as recording or waiting,
        # AND we have received at least one response to set last_response_received,
        # AND the socket is still open.
        is_socket_open = hasattr(self, 'client_socket') and self.client_socket and hasattr(self.client_socket, 'sock') and self.client_socket.sock and self.client_socket.sock.connected

        if not (self.recording or self.waiting) or self.last_response_received is None or not is_socket_open:
            logging.debug(f"[DEBUG]: Client {self.uid}: Skipping wait_before_disconnect. Recording: {self.recording}, Waiting: {self.waiting}, LastResponse: {self.last_response_received is not None}, SocketOpen: {is_socket_open}")
            return # No need to wait if already done or no responses ever received on an open socket


        logging.info(f"[INFO]: Client {self.uid}: Waiting up to {self.disconnect_if_no_response_for} seconds for final server responses...")
        start_wait_time = time.time()

        while (self.recording or self.waiting) and \
              (time.time() - self.last_response_received) < self.disconnect_if_no_response_for and \
              is_socket_open: # Also check socket status inside the loop

             time.sleep(0.1) # Add a small sleep to prevent busy-waiting
             # Re-check socket status
             is_socket_open = hasattr(self, 'client_socket') and self.client_socket and hasattr(self.client_socket, 'sock') and self.client_socket.sock and self.client_socket.sock.connected

             # Add a hard timeout based on the start of the wait
             if time.time() - start_wait_time > self.disconnect_if_no_response_for + 5: # Add a small buffer
                 logging.warning(f"[WARNING]: Client {self.uid}: Waited for over {self.disconnect_if_no_response_for} seconds, forcing continuation.")
                 break # Exit loop after a hard timeout

        logging.info(f"[INFO]: Client {self.uid}: Finished waiting for final server responses.")


class TranscriptionTeeClient:
    """
    Client for handling audio recording, streaming, and transcription tasks via one or more
    WebSocket connections.

    Acts as a high-level client for audio transcription tasks using a WebSocket connection. It can be used
    to send audio data for transcription to one or more servers, and receive transcribed text segments.
    Args:
        clients (list): one or more previously initialized Client instances

    Attributes:
        clients (list): the underlying Client instances responsible for handling WebSocket connections.
    """
    def __init__(self, clients, save_output_recording=False, output_recording_filename="./output_recording.wav", mute_audio_playback=False):
        self.clients = clients
        if not self.clients:
            raise Exception("At least one client is required.")

        # Define core audio parameters independent of PyAudio availability
        self.chunk = 4096
        # Use the numeric value for 16-bit signed integer PCM format (paInt16)
        self.format = 8 # Corresponds to pyaudio.paInt16 (if pyaudio is used)
        self.channels = 1
        self.rate = 16000 # Expected sample rate by Whisper models

        self.record_seconds = 60000 # Duration limit for microphone recording
        self.save_output_recording = save_output_recording
        self.output_recording_filename = output_recording_filename
        self.mute_audio_playback = mute_audio_playback

        self.frames = b"" # Buffer for recorded audio frames

        self.p = None # PyAudio instance (initialized conditionally)
        self.stream = None # PyAudio stream (initialized conditionally)

        # --- PyAudio Conditional Initialization ---
        # Only attempt PyAudio setup if audio playback is NOT muted (e.g., playing files or streams with sound)
        # OR if microphone recording is explicitly requested (though this script only uses files/streams).
        # Since this script uses mute_audio_playback=True and file input, this block will be skipped.
        # This prevents the ALSA/JACK errors if pyaudio cannot initialize.
        if not self.mute_audio_playback: # Only initialize PyAudio if we intend to produce sound or record from mic
            try:
                import pyaudio
                self.p = pyaudio.PyAudio()
                logging.info("PyAudio imported and initialized.")

                # Attempt to open a stream only if playback is NOT muted
                # The stream will be used for playing back files/streams.
                # If microphone recording were desired, we'd also need input=True here or in a separate stream.
                try:
                    # Use the numeric format defined earlier, and reference pyaudio constant if import succeeded
                    pyaudio_format = pyaudio.paInt16 # Use the constant from the imported module

                    self.stream = self.p.open(
                        format=pyaudio_format,
                        channels=self.channels,
                        rate=self.rate,
                        input=False, # Set input=False as we only need output for playback
                        output=True,
                        frames_per_buffer=self.chunk,
                    )
                    logging.info("PyAudio playback stream successfully opened.")
                except OSError as error:
                    logging.warning(f"[WARN]: TranscriptionTeeClient: Unable to access audio device for playback. {error}. Playback disabled.")
                    self.stream = None
                    self.mute_audio_playback = True # Force mute if playback stream fails
                except Exception as e:
                     logging.warning(f"[WARN]: TranscriptionTeeClient: Error opening PyAudio playback stream: {e}. Playback disabled.")
                     self.stream = None
                     self.mute_audio_playback = True

            except ImportError:
                logging.warning("[WARN]: TranscriptionTeeClient: pyaudio not installed. Audio playback/recording from microphone disabled.")
                self.p = None
                self.stream = None
                self.mute_audio_playback = True # Cannot play back without pyaudio
            except Exception as e:
                 logging.warning(f"[WARN]: TranscriptionTeeClient: Error initializing PyAudio: {e}. Audio playback/recording from microphone disabled.")
                 self.p = None
                 self.stream = None
                 self.mute_audio_playback = True
        else:
             logging.info("PyAudio initialization skipped because mute_audio_playback is True.")
        # --- End PyAudio Conditional Initialization ---


    def __call__(self, audio=None, rtsp_url=None, hls_url=None, save_file=None):
        """
        Start the transcription process.

        Initiates the transcription process by connecting to the server via a WebSocket. It waits for the server
        to be ready to receive audio data and then sends audio for transcription. If an audio file is provided, it
        will be played and streamed to the server; otherwise, it will perform live recording.

        Args:
            audio (str, optional): Path to an audio file for transcription. Default is None, which triggers live recording.
            rtsp_url (str, optional): RTSP stream URL.
            hls_url (str, optional): HLS stream URL.
            save_file (str, optional): Local path to save the network stream (only for HLS/RTSP).

        """
        assert sum(
            source is not None for source in [audio, rtsp_url, hls_url]
        ) <= 1, 'You must provide only one selected source (audio file, RTSP, or HLS)'

        logging.info("[INFO]: TranscriptionTeeClient: Waiting for all clients ready ...")

        # Check if ANY client connection failed early during their init
        if any(client.server_error for client in self.clients):
             error_messages = [client.error_message for client in self.clients if client.server_error]
             self.close_all_clients() # Close any clients that might have partially connected
             raise RuntimeError(f"One or more clients failed during initialization or connection. Errors: {', '.join(error_messages)}")


        # Wait for ALL clients to report SERVER_READY state
        # This ensures all connections are open and the server is ready to receive audio
        all_clients_ready = False
        while not all_clients_ready:
            all_clients_ready = True
            for client in self.clients:
                if client.server_error:
                     error_message = client.error_message if client.server_error else "Server error"
                     self.close_all_clients()
                     raise RuntimeError(f"Server error occurred for client {client.uid} while waiting for ready: {error_message}")

                if client.waiting:
                     logging.info(f"[INFO]: Client {client.uid} is waiting for a slot on the server. Waiting...")
                     all_clients_ready = False
                     time.sleep(2) # Wait longer if any client is waiting
                     break # Check all clients again after waiting

                if not client.recording: # 'recording' becomes True upon receiving SERVER_READY
                    logging.debug(f"[DEBUG]: Client {client.uid} not ready yet. Status: recording={client.recording}, waiting={client.waiting}, error={client.server_error}")
                    all_clients_ready = False
                    time.sleep(0.5) # Wait a bit before re-checking

            if all_clients_ready:
                 logging.info("[INFO]: All Clients Ready!")
                 break # Exit the outer while loop

            # Add a timeout to prevent infinite waiting if server never sends SERVER_READY
            # This requires tracking how long we've been waiting since the start
            if not hasattr(self, '_wait_start_time'):
                 self._wait_start_time = time.time()
            elif time.time() - self._wait_start_time > 30: # Example timeout: 30 seconds
                 self.close_all_clients()
                 raise RuntimeError("Timeout waiting for all clients to become ready.")


        try:
            if hls_url is not None:
                self.process_hls_stream(hls_url, save_file)
            elif audio is not None:
                # Ensure resampling handles non-wav files if needed
                # The utils.resample function is assumed to return a path to a 16kHz WAV file
                try:
                    resampled_file = utils.resample(audio, sr=self.rate)
                    logging.info(f"Resampled audio file prepared: {resampled_file}")
                    self.play_file(resampled_file)
                except Exception as e:
                     logging.error(f"[ERROR]: Failed during audio resampling or file playback: {e}")
                     # Decide whether to continue or raise error
                     raise RuntimeError(f"Audio file processing failed: {e}") from e

                # Clean up the resampled file if it's temporary and created by utils.resample
                # A simple check if path is different and exists might not be enough,
                # ideally utils.resample should return a flag if a temporary file was created.
                # For now, a basic check:
                if resampled_file and resampled_file != audio and Path(resampled_file).exists():
                    try:
                        os.remove(resampled_file)
                        logging.info(f"Removed temporary resampled file: {resampled_file}")
                    except Exception as e:
                         logging.warning(f"[WARNING]: Failed to remove temporary resampled file {resampled_file}: {e}")

            elif rtsp_url is not None:
                self.process_rtsp_stream(rtsp_url)
            else:
                 # This path is not used by the batch script, but kept for completeness of the class
                 if self.stream is None:
                      logging.error("[ERROR]: Cannot record from microphone: PyAudio stream failed to initialize.")
                      raise RuntimeError("Microphone recording requested but PyAudio stream is not available.")
                 self.record() # Call the record method for microphone input

        except Exception as e:
            # Errors during audio processing (file read, stream, etc.) will be caught here
            logging.error(f"An error occurred during audio processing: {e}")
            # Re-raise the exception after logging
            raise e
        finally:
            # --- Finalization Steps ---
            logging.info("TranscriptionTeeClient: Starting finalization steps.")

            # 1. Send END_OF_AUDIO signal to all clients
            # This signals the server that no more audio is coming for this task.
            self.multicast_packet(Client.END_OF_AUDIO.encode('utf-8'), unconditional=True)
            logging.info("TranscriptionTeeClient: Sent END_OF_AUDIO to all clients.")

            # 2. Wait for servers to process final audio and send last responses
            # This gives servers time to finalize segments based on the END_OF_AUDIO signal.
            # The wait_before_disconnect method handles the timeout logic.
            logging.info("TranscriptionTeeClient: Waiting for final server responses and processing...")
            for client in self.clients:
                 # Wait for each client individually
                 client.wait_before_disconnect()
            logging.info("TranscriptionTeeClient: Finished waiting for final server responses.")


            # 3. Write SRT files for all clients based on collected transcripts
            self.write_all_clients_srt()
            logging.info("TranscriptionTeeClient: Wrote all client SRT files.")

            # 4. Close all WebSocket client connections
            self.close_all_clients()
            logging.info("TranscriptionTeeClient: Closed all client WebSocket connections.")

            # 5. Clean up PyAudio resources if they were initialized
            if self.stream:
                try:
                    logging.debug("TranscriptionTeeClient: Stopping and closing PyAudio stream.")
                    self.stream.stop_stream()
                    self.stream.close()
                except Exception as e:
                    logging.warning(f"[WARNING]: TranscriptionTeeClient: Error stopping/closing PyAudio stream: {e}")
            if self.p:
                try:
                   logging.debug("TranscriptionTeeClient: Terminating PyAudio instance.")
                   self.p.terminate()
                except Exception as e:
                   logging.warning(f"[WARNING]: TranscriptionTeeClient: Error terminating PyAudio instance: {e}")
            logging.info("TranscriptionTeeClient: PyAudio resources cleaned up.")

            # 6. If recording was used and saved, combine chunks (handled in record's finalization)


            logging.info("TranscriptionTeeClient: Finalization complete.")


    def close_all_clients(self):
        """Closes all client websockets."""
        logging.info("TranscriptionTeeClient: Closing all client WebSocket connections.")
        # Iterate over a copy of the list in case closing affects the list
        for client in list(self.clients):
            # Check if the client object still exists and has the method
            if client and hasattr(client, 'close_websocket'):
                client.close_websocket()
            else:
                logging.warning(f"TranscriptionTeeClient: Client object invalid or missing close_websocket method during cleanup.")


    def write_all_clients_srt(self):
        """Writes out .srt files for all clients."""
        logging.info("TranscriptionTeeClient: Writing SRT files for all clients.")
        for client in self.clients:
            # The client.write_srt_file method checks if there's a transcript to write
             if client and hasattr(client, 'write_srt_file'):
                 # The client's srt_file_path was set during its initialization
                 client.write_srt_file(client.srt_file_path)
             else:
                  logging.warning(f"TranscriptionTeeClient: Client object invalid or missing write_srt_file method.")


    def multicast_packet(self, packet, unconditional=False):
        """
        Sends an identical packet via all clients.

        Args:
            packet (bytes): The audio data packet in bytes to be sent.
            unconditional (bool, optional): If true, send regardless of whether clients are recording.  Default is False.
        """
        # Filter clients to only send to those that are recording (SERVER_READY state), unless unconditional
        # Check if the client object is valid before accessing its attributes
        active_clients = [client for client in self.clients if client and (unconditional or client.recording)]

        if not active_clients and not unconditional:
             # logging.debug("TranscriptionTeeClient: No active clients to send packet.")
             return # Don't attempt to send if no clients are ready or unconditional send isn't requested

        # Check if packet is END_OF_AUDIO and print info
        if isinstance(packet, bytes) and packet == Client.END_OF_AUDIO.encode('utf-8'):
             logging.info(f"TranscriptionTeeClient: Sending END_OF_AUDIO signal to {len(active_clients)} client(s).")
        elif isinstance(packet, bytes):
            # logging.debug(f"TranscriptionTeeClient: Sending audio packet ({len(packet)} bytes) to {len(active_clients)} client(s).")
            pass # Suppress debug log for every audio packet
        else:
             logging.warning(f"TranscriptionTeeClient: Attempted to send non-byte packet: {type(packet)}. Skipping.")
             return


        for client in active_clients:
             # The client's send_packet_to_server method should handle socket status checks
             if client and hasattr(client, 'send_packet_to_server'):
                client.send_packet_to_server(packet)
             else:
                 logging.warning(f"TranscriptionTeeClient: Client object invalid or missing send_packet_to_server method.")


    def play_file(self, filename):
        """
        Play an audio file and send it to the server for processing.

        Reads an audio file, plays it through the audio output (if not muted), and simultaneously sends
        the audio data to the server for processing.

        Args:
            filename (str): The path to the audio file to be played and sent to the server.
        """
        logging.info(f"[INFO]: TranscriptionTeeClient: Processing audio file: {filename}")
        wavfile = None # Initialize wavfile outside try block
        try:
            # Read audio file using the wave module
            try:
                 wavfile = wave.open(filename, "rb")
                 logging.info(f"TranscriptionTeeClient: Successfully opened WAV file: {filename}")
            except wave.Error as e:
                 logging.error(f"[ERROR]: TranscriptionTeeClient: Could not open audio file {filename} using wave module: {e}")
                 # Check if file exists but is not a valid WAV file
                 if Path(filename).is_file():
                      logging.error(f"[ERROR]: TranscriptionTeeClient: File {filename} exists but appears not to be a valid WAV format.")
                      logging.info("TranscriptionTeeClient: The wave module only supports WAV files. Ensure utils.resample converts to WAV.")

                 raise RuntimeError(f"Failed to open audio file {filename}") from e # Re-raise as RuntimeError


            logging.info(f"TranscriptionTeeClient: Audio file details: Channels={wavfile.getnchannels()}, FrameRate={wavfile.getframerate()}, SampleWidth={wavfile.getsampwidth()}")

            # Check if the file format is compatible with expected 16-bit PCM
            if wavfile.getsampwidth() != 2 or wavfile.getnchannels() != 1 or wavfile.getframerate() != self.rate:
                 logging.warning(f"[WARNING]: TranscriptionTeeClient: Audio file format ({wavfile.getnchannels()} ch, {wavfile.getframerate()} Hz, {wavfile.getsampwidth() * 8}-bit) does not match expected ({self.channels} ch, {self.rate} Hz, 16-bit). Assuming utils.resample handled this or server can adapt.")
                 # This warning is okay *if* utils.resample guarantees the output format
                 # If utils.resample outputs a temporary file with the correct format, this check should be on the *resampled* file.


            # Attempt to open PyAudio stream for playback if needed and not muted
            # This block is only reached if mute_audio_playback was False during __init__
            if not self.mute_audio_playback and self.stream is None and self.p is not None:
                 logging.info("TranscriptionTeeClient: Re-attempting PyAudio stream open for playback...")
                 try:
                     import pyaudio # Import again just in case (should already be imported if self.p is not None)
                     pyaudio_format = pyaudio.paInt16
                     # Use file properties if they match expected rate/channels, otherwise use instance defaults
                     stream_rate = wavfile.getframerate() if wavfile.getframerate() == self.rate else self.rate
                     stream_channels = wavfile.getnchannels() if wavfile.getnchannels() == self.channels else self.channels
                     stream_format = self.p.get_format_from_width(wavfile.getsampwidth()) # Use PyAudio method to get format from width

                     self.stream = self.p.open(
                         format=stream_format,
                         channels=stream_channels,
                         rate=stream_rate,
                         input=False, # Only output for playback
                         output=True,
                         frames_per_buffer=self.chunk,
                     )
                     logging.info("TranscriptionTeeClient: PyAudio playback stream successfully opened for file.")
                 except OSError as e:
                     logging.error(f"[ERROR]: TranscriptionTeeClient: Could not open PyAudio stream for playback: {e}. Audio playback will be muted.")
                     self.stream = None
                     self.mute_audio_playback = True # Force mute if playback fails
                 except ImportError: # Should not happen if self.p is not None
                      logging.error("[ERROR]: TranscriptionTeeClient: PyAudio import failed during playback stream open attempt.")
                      self.stream = None
                      self.mute_audio_playback = True
                 except Exception as e:
                     logging.error(f"[ERROR]: TranscriptionTeeClient: Unexpected error opening PyAudio stream for playback: {e}. Audio playback will be muted.")
                     self.stream = None
                     self.mute_audio_playback = True


            # Check if any client is recording before starting to send data
            if not any(client.recording for client in self.clients):
                 logging.warning("TranscriptionTeeClient: No clients are in recording state (SERVER_READY). Skipping file playback and sending.")
                 wavfile.close()
                 return # Exit if no clients are ready to receive audio


            logging.info("TranscriptionTeeClient: Starting audio file stream to server...")
            frame_index = 0
            bytes_per_frame = wavfile.getsampwidth() * wavfile.getnchannels()

            while True:
                data = wavfile.readframes(self.chunk)
                if data == b"":
                    logging.info("TranscriptionTeeClient: End of audio file reached.")
                    break # End of audio file

                # Check if any client is still recording before sending the chunk
                if not any(client.recording for client in self.clients):
                     logging.warning("TranscriptionTeeClient: Clients stopped recording mid-file. Stopping file playback and sending.")
                     break # Stop sending if clients disconnect

                # Convert audio data to float array (expected by server)
                try:
                     # The bytes_to_float_array expects 16-bit mono bytes
                     # If the source WAV is not 16-bit mono, resampling is essential before this point.
                     # Assuming `utils.resample` handles this.
                     audio_array = self.bytes_to_float_array(data)
                     self.multicast_packet(audio_array.tobytes()) # Send audio packet
                except Exception as e:
                     logging.error(f"[ERROR]: TranscriptionTeeClient: Error processing or sending audio packet at frame {frame_index}: {e}")
                     # Decide whether to continue or stop on send error
                     pass # Continue for now


                # Playback audio if stream is open and not muted
                if not self.mute_audio_playback and self.stream:
                    try:
                        # Write the raw bytes read from the WAV file for playback
                        self.stream.write(data)
                    except Exception as e:
                        logging.error(f"[ERROR]: TranscriptionTeeClient: Error during audio playback at frame {frame_index}: {e}")
                        # Optionally set mute_audio_playback = True if playback fails
                        self.mute_audio_playback = True
                        if self.stream:
                             try:
                                  self.stream.stop_stream()
                                  self.stream.close()
                             except Exception as close_e:
                                  logging.error(f"TranscriptionTeeClient: Error closing stream after playback error: {close_e}")
                             self.stream = None


                # Simulate real-time by sleeping for the duration of the chunk
                # Calculate duration based on the actual file's frame rate
                actual_chunk_duration = self.chunk / float(wavfile.getframerate())
                time.sleep(actual_chunk_duration)
                frame_index += self.chunk

            wavfile.close()
            logging.info("TranscriptionTeeClient: Finished sending audio data for file.")

            # Finalization steps (sending END_OF_AUDIO, waiting, closing clients, writing SRT)
            # are handled in the finally block of the main __call__ method.

        except KeyboardInterrupt:
            logging.info("[INFO]: TranscriptionTeeClient: Keyboard interrupt received during file playback.")
            if wavfile: wavfile.close()
            # PyAudio and clients cleanup handled in finally of __call__
            raise # Re-raise the interrupt

        except Exception as e:
            logging.error(f"[ERROR]: TranscriptionTeeClient: Error during file playback process: {e}")
            if wavfile: wavfile.close()
            # Clients cleanup handled in finally of __call__
            raise # Re-raise the exception


    def process_rtsp_stream(self, rtsp_url):
        """
        Connect to an RTSP source, process the audio stream, and send it for transcription.

        Args:
            rtsp_url (str): The URL of the RTSP stream source.
        """
        print("[INFO]: TranscriptionTeeClient: Connecting to RTSP stream...")
        container = None
        try:
            # Use tcp transport explicitly for better reliability
            container = av.open(rtsp_url, format="rtsp", options={"rtsp_transport": "tcp"}, timeout=15) # Increased timeout
            self.process_av_stream(container, stream_type="RTSP")
        except av.AVError as e:
            print(f"[ERROR]: TranscriptionTeeClient: Failed to open or process RTSP stream: {e}")
            # Handle specific AV errors
            raise RuntimeError(f"RTSP stream processing failed: {e}") from e
        except Exception as e:
            print(f"[ERROR]: TranscriptionTeeClient: An unexpected error occurred processing RTSP stream: {e}")
            raise RuntimeError(f"RTSP stream processing failed: {e}") from e
        finally:
            if container:
                try:
                    container.close()
                    logging.debug("TranscriptionTeeClient: Closed AV container for RTSP.")
                except Exception as e:
                    logging.warning(f"TranscriptionTeeClient: Error closing AV container for RTSP: {e}")
            # Wait and close clients/write SRTs - handled in finally of __call__
        print("[INFO]: TranscriptionTeeClient: RTSP stream processing finished.")

    def process_hls_stream(self, hls_url, save_file=None):
        """
        Connect to an HLS source, process the audio stream, and send it for transcription.

        Args:
            hls_url (str): The URL of the HLS stream source.
            save_file (str, optional): Local path to save the network stream.
        """
        print("[INFO]: TranscriptionTeeClient: Connecting to HLS stream...")
        container = None
        output_container = None
        try:
            container = av.open(hls_url, format="hls", timeout=15) # Increased timeout
            self.process_av_stream(container, stream_type="HLS", save_file=save_file)
        except av.AVError as e:
            print(f"[ERROR]: TranscriptionTeeClient: Failed to open or process HLS stream: {e}")
            # Handle specific AV errors
            raise RuntimeError(f"HLS stream processing failed: {e}") from e
        except Exception as e:
            print(f"[ERROR]: TranscriptionTeeClient: An unexpected error occurred processing HLS stream: {e}")
            raise RuntimeError(f"HLS stream processing failed: {e}") from e
        finally:
            if container:
                try:
                    container.close()
                    logging.debug("TranscriptionTeeClient: Closed AV container for HLS.")
                except Exception as e:
                    logging.warning(f"TranscriptionTeeClient: Error closing AV container for HLS: {e}")
            if output_container:
                 try:
                     output_container.close()
                     logging.debug("TranscriptionTeeClient: Closed output AV container for HLS save.")
                 except Exception as e:
                      logging.warning(f"TranscriptionTeeClient: Error closing output AV container for HLS save: {e}")
            # Wait and close clients/write SRTs - handled in finally of __call__
        print("[INFO]: TranscriptionTeeClient: HLS stream processing finished.")


    def process_av_stream(self, container, stream_type, save_file=None):
        """
        Process an AV container stream (RTSP/HLS) and send audio packets to the server.

        Args:
            container (av.container.InputContainer): The input container to process.
            stream_type (str): The type of stream being processed ("RTSP" or "HLS").
            save_file (str, optional): Local path to save the stream. Default is None.
        """
        # Prefer finding an audio stream
        audio_stream = next((s for s in container.streams if s.type == "audio"), None)
        if not audio_stream:
            print(f"[ERROR]: TranscriptionTeeClient: No audio stream found in {stream_type} source.")
            raise RuntimeError(f"No audio stream found in {stream_type} source.")


        # Set up Resampler if needed (e.g., if stream is not 16kHz, s16le, mono)
        # WhisperLive expects 16kHz, 16-bit PCM, mono (s16 format, mono layout, 16000 rate)
        resampler = None
        expected_format = 's16' # Corresponds to 16-bit signed PCM
        expected_layout = 'mono' # Mono channel
        expected_rate = self.rate # 16000 Hz (self.rate is 16000)

        # Check if resampling is required
        needs_resampling = (audio_stream.format.name != expected_format or
                            audio_stream.layout.name != expected_layout or
                            audio_stream.rate != expected_rate)

        if needs_resampling:
            logging.info(f"TranscriptionTeeClient: Input {stream_type} audio stream format mismatch (format: {audio_stream.format.name}, layout: {audio_stream.layout.name}, rate: {audio_stream.rate}). Setting up resampler...")
            try:
                # Create resampler to convert to the expected format
                resampler = av.AudioResampler(
                    format=expected_format,
                    layout=expected_layout,
                    rate=expected_rate
                )
                logging.info("TranscriptionTeeClient: Audio resampler created.")
            except Exception as e:
                logging.error(f"[ERROR]: TranscriptionTeeClient: Failed to create audio resampler: {e}. Cannot process stream with incompatible format.")
                raise RuntimeError(f"Failed to set up audio resampler: {e}") from e
        else:
            logging.info(f"TranscriptionTeeClient: Input {stream_type} audio stream format is compatible ({audio_stream.format.name}, {audio_stream.layout.name}, {audio_stream.rate} Hz). No resampling needed.")


        output_container = None
        output_audio_stream = None
        if save_file:
            try:
                # Ensure output directory exists
                Path(save_file).parent.mkdir(parents=True, exist_ok=True)

                # Use a WAV container and pcm_s16le codec for direct compatibility with expected WhisperLive format
                output_container = av.open(save_file, mode="w", format="wav")
                output_audio_stream = output_container.add_stream("pcm_s16le", rate=expected_rate)
                output_audio_stream.channels = 1 # Ensure mono if saving processed stream
                logging.info(f"TranscriptionTeeClient: Saving processed audio stream to {save_file} (WAV/pcm_s16le)")

            except Exception as e:
                logging.error(f"[ERROR]: TranscriptionTeeClient: Failed to set up output container for saving stream: {e}. Saving will be disabled.")
                if output_container:
                     try: output_container.close()
                     except: pass
                output_container = None
                output_audio_stream = None


        try:
            logging.info(f"TranscriptionTeeClient: Starting to decode and send {stream_type} audio stream...")

            # Check if any client is recording before starting to send data
            if not any(client.recording for client in self.clients):
                 logging.warning(f"TranscriptionTeeClient: No clients are in recording state for {stream_type}. Skipping stream processing.")
                 return # Exit if no clients are ready

            processed_packet_count = 0
            for packet in container.demux(audio_stream):
                # Check if any client is still recording before processing the packet
                if not any(client.recording for client in self.clients):
                     logging.warning(f"TranscriptionTeeClient: Clients stopped recording mid-{stream_type}. Stopping stream processing.")
                     break # Stop processing if clients disconnect

                try:
                    # Decode audio packets into frames
                    for frame in packet.decode():
                         # Process the frame (resample if necessary)
                         processed_frames = [frame]
                         if resampler:
                             try:
                                 processed_frames = resampler.resample(frame)
                             except Exception as e:
                                 logging.error(f"[ERROR]: TranscriptionTeeClient: Error during audio resampling: {e}. Skipping frame.")
                                 continue # Skip this frame if resampling fails

                         for p_frame in processed_frames:
                              # Ensure the processed frame is in the expected format (s16, mono, 16000 Hz)
                              if p_frame.format.name == expected_format and \
                                 p_frame.layout.name == expected_layout and \
                                 p_frame.rate == expected_rate:

                                 # Convert processed frame to bytes (16-bit signed PCM)
                                 audio_data_bytes = p_frame.to_ndarray().tobytes()

                                 # Send the audio data to the server
                                 self.multicast_packet(audio_data_bytes)

                                 # Save the processed frame if output saving is enabled
                                 if output_container and output_audio_stream:
                                     try:
                                         # Ensure the frame has a valid presentation timestamp (PTS) for muxing
                                         # If frame.pts is None, generate one based on rate/index
                                         if p_frame.pts is None:
                                             # This requires tracking frame index, which is complex with resampling.
                                             # It's often better if the decoder provides PTS.
                                             # For simplicity, let's assume PTS is usually available or not strictly needed for raw PCM save.
                                             # If saving fails here due to PTS, you might need a more robust PTS generation.
                                             pass # Assume frame has PTS or it's not critical for this codec/container

                                         # Mux the frame into the output container. encode() might return multiple packets.
                                         for out_packet in output_audio_stream.encode(p_frame):
                                              output_container.mux(out_packet)
                                     except Exception as e:
                                         logging.error(f"[ERROR]: TranscriptionTeeClient: Error muxing frame for saving: {e}. Saving might be incomplete.")
                                         # Decide whether to continue saving or disable it on error
                                         # For robustness, one might disable saving after an error
                                         # output_container = None # Example: disable further saving
                                         pass # Continue trying for now

                              else:
                                 logging.warning(f"[WARNING]: TranscriptionTeeClient: Processed frame not in expected format for sending (format: {p_frame.format.name}, layout: {p_frame.layout.name}, rate: {p_frame.rate}). Skipping frame.")


                except av.AVError as e:
                    logging.error(f"[ERROR]: TranscriptionTeeClient: Error decoding packet in {stream_type}: {e}. Skipping packet.")
                    # Decide whether to continue or stop on decoding error
                    pass # Continue processing next packets
                except Exception as e:
                    logging.error(f"[ERROR]: TranscriptionTeeClient: An unexpected error occurred decoding/processing packet in {stream_type}: {e}. Skipping packet.")
                    pass # Continue processing next packets

                processed_packet_count += 1
                # Add a small sleep to avoid overwhelming the system/server
                # This simulates real-time processing speed based on the stream's rate
                # A better approach would be to base sleep on PTS difference, but this is simpler.
                time.sleep(packet.time_base * packet.duration if packet.duration else 0.01)


            # --- Flushing ---
            # Flush the decoder to get any remaining buffered frames
            try:
                 for frame in container.decode(audio_stream):
                     # Process remaining frames (resample if needed)
                     processed_frames = [frame]
                     if resampler:
                          processed_frames = resampler.resample(frame)
                     for p_frame in processed_frames:
                           if p_frame.format.name == expected_format and p_frame.layout.name == expected_layout and p_frame.rate == expected_rate:
                               audio_data_bytes = p_frame.to_ndarray().tobytes()
                               self.multicast_packet(audio_data_bytes)
                               if output_container and output_audio_stream:
                                     for out_packet in output_audio_stream.encode(p_frame):
                                          output_container.mux(out_packet)
            except Exception as e:
                 logging.error(f"[ERROR]: TranscriptionTeeClient: Error flushing decoder: {e}. Some audio might be missing.")

            # Flush the resampler if used
            if resampler:
                 try:
                     for p_frame in resampler.flush():
                          if p_frame.format.name == expected_format and p_frame.layout.name == expected_layout and p_frame.rate == expected_rate:
                               audio_data_bytes = p_frame.to_ndarray().tobytes()
                               self.multicast_packet(audio_data_bytes)
                               if output_container and output_audio_stream:
                                     for out_packet in output_audio_stream.encode(p_frame):
                                          output_container.mux(out_packet)
                 except Exception as e:
                     logging.error(f"[ERROR]: TranscriptionTeeClient: Error flushing resampler: {e}. Some audio might be missing.")


            # Flush the output encoder/muxer if saving
            if output_container and output_audio_stream:
                 try:
                      # Pass no frame to encode() to signal flushing
                      for out_packet in output_audio_stream.encode():
                           output_container.mux(out_packet)
                      # Flush the muxer
                      output_container.flush()
                      logging.info(f"TranscriptionTeeClient: Flushed output container for {stream_type}.")
                 except Exception as e:
                      logging.error(f"[ERROR]: TranscriptionTeeClient: Error flushing output container: {e}. Saved file might be incomplete.")


            logging.info(f"TranscriptionTeeClient: Finished decoding and sending {stream_type} stream.")

        except Exception as e:
            logging.error(f"[ERROR]: TranscriptionTeeClient: An error occurred during {stream_type} stream processing loop: {e}")
            raise # Re-raise the exception


        finally:
            # Finalization steps (sending END_OF_AUDIO, waiting, closing clients, writing SRT)
            # are handled in the finally block of the main __call__ method.
             logging.debug(f"TranscriptionTeeClient: AV stream processing finally block reached for {stream_type}.")
            # Close AV containers - Handled in the outer process_rtsp/hls_stream finally block.
            # Wait and close clients/write SRTs - Handled in finally of __call__.


    def save_chunk(self, n_audio_file):
        """
        Saves the current audio frames (from microphone recording) to a WAV file in a separate thread.

        Args:
        n_audio_file (int): The index of the audio file which determines the filename.
                            This helps in maintaining the order and uniqueness of each chunk.
        """
        # Ensure 'chunks' directory exists
        chunks_dir = TEMP_DIR / "mic_chunks"
        if not os.path.exists(chunks_dir):
             os.makedirs(chunks_dir, exist_ok=True)

        chunk_filename = os.path.join(chunks_dir, f"{n_audio_file}.wav")

        logging.debug(f"TranscriptionTeeClient: Saving audio chunk {n_audio_file} to {chunk_filename}")

        t = threading.Thread(
            target=self.write_audio_frames_to_file,
            args=(self.frames[:], chunk_filename,),
        )
        t.start()

    def finalize_recording(self, n_audio_file):
        """
        Finalizes the microphone recording process by saving any remaining audio frames,
        closing the audio stream, and terminating the process.

        Args:
        n_audio_file (int): The file index to be used if there are remaining audio frames to be saved.
                            This index is incremented before use if the last chunk is saved.
        """
        # This method is only called when using the microphone recording path (`record()` method)
        logging.info("TranscriptionTeeClient: Finalizing microphone recording...")
        chunks_dir = TEMP_DIR / "mic_chunks"
        total_chunks_saved = n_audio_file # Start with the count of chunks already saved periodically

        if self.save_output_recording and len(self.frames):
            # Save the last remaining buffer
            final_chunk_filename = os.path.join(chunks_dir, f"{total_chunks_saved}.wav")
            self.write_audio_frames_to_file(
                self.frames[:], final_chunk_filename
            )
            total_chunks_saved += 1 # Increment total count as the last buffer was saved as one chunk

        elif self.save_output_recording and not len(self.frames):
             logging.warning("TranscriptionTeeClient: No audio frames recorded in the final buffer to save.")

        else: # Not saving output recording, so no chunks were saved
             total_chunks_saved = 0


        # PyAudio stream/instance close and client cleanup/SRT writing are handled
        # in the finally block of the main __call__ method after `record()` returns.
        # self.stream.stop_stream()
        # self.stream.close()
        # self.p.terminate()
        # self.close_all_clients()


        if self.save_output_recording and total_chunks_saved > 0:
            # Combine the saved chunks into the final output file
            self.write_output_recording(total_chunks_saved) # Pass the total count of chunks to combine
        elif self.save_output_recording and total_chunks_saved == 0:
             logging.warning("TranscriptionTeeClient: Output recording was requested, but no audio chunks were saved.")
             # Clean up the empty chunks directory if it exists
             if os.path.exists(chunks_dir):
                 try: shutil.rmtree(chunks_dir)
                 except: pass


        # Write all clients SRTs - Handled in finally of __call__
        # self.write_all_clients_srt()

        logging.info("TranscriptionTeeClient: Microphone recording finalized.")


    def record(self):
        """
        Record audio data from the input stream (microphone) and save it if configured.

        Continuously records audio data from the microphone, sends it to the server via a WebSocket
        connection, and simultaneously saves it to multiple WAV files in chunks if `save_output_recording`
        is True. It stops recording when the `record_seconds` duration is reached or when no clients
        are in the `recording` state.
        """
        # This method is only intended for microphone input, which requires PyAudio.
        if self.stream is None or self.p is None:
             logging.error("[ERROR]: TranscriptionTeeClient: Microphone recording requested but PyAudio is not available or stream failed to open.")
             # Signal error to clients? Or just exit? Exiting is safer.
             # Set server_error on clients? Or raise an exception? Raising exception is cleaner.
             raise RuntimeError("Microphone recording requires PyAudio and a working audio input stream.")

        logging.info(f"TranscriptionTeeClient: Starting microphone recording (duration limit: {self.record_seconds} seconds)...")

        n_audio_file = 0 # Counter for saved chunk files
        chunks_dir = TEMP_DIR / "mic_chunks" # Directory to save temporary chunks

        if self.save_output_recording:
            if os.path.exists(chunks_dir):
                try:
                    shutil.rmtree(chunks_dir)
                    logging.info(f"TranscriptionTeeClient: Cleaned up temporary directory: {chunks_dir}")
                except Exception as e:
                    logging.warning(f"[WARNING]: TranscriptionTeeClient: Failed to clean up temporary directory {chunks_dir}: {e}. Output recording might be incomplete.")
            try:
                os.makedirs(chunks_dir, exist_ok=True)
                logging.info(f"TranscriptionTeeClient: Created temporary directory: {chunks_dir}")
            except Exception as e:
                 logging.error(f"[ERROR]: TranscriptionTeeClient: Failed to create temporary directory {chunks_dir}: {e}. Output recording will not be saved.")
                 self.save_output_recording = False # Disable saving if dir creation fails


        try:
            logging.info("TranscriptionTeeClient: Recording...")
            frames_recorded = 0
            # Total number of frames to record before hitting record_seconds limit
            max_frames = int(self.rate * self.record_seconds)

            # Check if any client is recording before starting the read loop
            if not any(client.recording for client in self.clients):
                 logging.warning("TranscriptionTeeClient: No clients are in recording state (SERVER_READY). Skipping microphone recording.")
                 # Still need to finalize recording to handle cleanup logic
                 # This case falls through to the finally block which calls finalize_recording
                 # Ensure finalize_recording handles 0 chunks saved correctly.
                 return # Exit recording if no clients are ready

            # Start recording loop
            while any(client.recording for client in self.clients) and frames_recorded < max_frames:
                try:
                    # Read audio data from the microphone stream
                    # exception_on_overflow=False prevents crashes if the read buffer is full
                    data = self.stream.read(self.chunk, exception_on_overflow=False)
                    self.frames += data
                    frames_recorded += len(data) // (self.p.get_sample_size(self.format)) # frames = bytes / bytes_per_frame

                    # Convert audio data chunk to float array (expected by server)
                    try:
                         # Assumes microphone input is 16-bit PCM (self.format is paInt16, sample size is 2)
                         audio_array = self.bytes_to_float_array(data)
                         self.multicast_packet(audio_array.tobytes()) # Send audio packet
                    except Exception as e:
                         logging.error(f"[ERROR]: TranscriptionTeeClient: Error processing or sending microphone audio packet: {e}")
                         pass # Continue recording despite send error


                    # Save buffer to a chunk file if it exceeds a certain size (e.g., 60 seconds)
                    # Size check: bytes > 60 seconds * bytes_per_second (rate * sample_size * channels)
                    bytes_per_second = self.rate * self.p.get_sample_size(self.format) * self.channels
                    if self.save_output_recording and len(self.frames) > 60 * bytes_per_second:
                        self.save_chunk(n_audio_file)
                        n_audio_file += 1
                        self.frames = b"" # Clear buffer after saving chunk

                except IOError as e:
                    logging.error(f"[ERROR]: TranscriptionTeeClient: IOError during audio recording: {e}. Stream might be disconnected.")
                    # On IOError, assume microphone input failed critically and stop recording
                    break
                except Exception as e:
                     logging.error(f"[ERROR]: TranscriptionTeeClient: An unexpected error occurred during recording loop: {e}. Continuing...")
                     # For other unexpected errors, try to continue recording


            logging.info("TranscriptionTeeClient: Microphone recording loop finished.")

            # Finalize recording (save remaining frames, etc.)
            # This is handled in the outer try/except/finally block of __call__ after this method returns.
            # The count `n_audio_file` reflects the number of chunks saved *periodically*.
            # Any remaining frames in `self.frames` will be saved as chunk `n_audio_file` in finalize_recording.


        except KeyboardInterrupt:
            logging.info("[INFO]: TranscriptionTeeClient: Keyboard interrupt received during recording.")
            # Finalization handled in the outer try/except/finally block of __call__
            raise # Re-raise the interrupt

        except Exception as e:
            logging.error(f"[ERROR]: TranscriptionTeeClient: An error occurred during microphone recording: {e}")
            # Finalization handled in the outer try/except/finally block of __call__
            raise # Re-raise the exception


    def write_audio_frames_to_file(self, frames, file_name):
        """
        Write audio frames to a WAV file.

        The WAV file is created or overwritten with the specified name. The audio frames should be
        in the correct format and match the specified channel, sample width, and sample rate.

        Args:
            frames (bytes): The audio frames to be written to the file.
            file_name (str): The name of the WAV file to which the frames will be written.

        """
        # This method is only called when saving microphone recordings using PyAudio.
        if self.p is None:
             logging.error(f"[ERROR]: TranscriptionTeeClient: Cannot write WAV file chunk {file_name}: PyAudio not available.")
             return

        try:
            with wave.open(file_name, "wb") as wavfile:
                wavfile: wave.Wave_write
                wavfile.setnchannels(self.channels)
                # Use PyAudio's sample size method, as self.format is the PyAudio constant
                wavfile.setsampwidth(self.p.get_sample_size(pyaudio.paInt16)) # Assume 16-bit for saving
                wavfile.setframerate(self.rate)
                wavfile.writeframes(frames)
            logging.debug(f"TranscriptionTeeClient: Successfully wrote audio chunk to {file_name}")
        except Exception as e:
             logging.error(f"[ERROR]: TranscriptionTeeClient: Error writing audio chunk to {file_name}: {e}")


    def write_output_recording(self, num_chunks_saved):
        """
        Combine and save recorded microphone audio chunks into a single WAV file.

        Args:
            num_chunks_saved (int): The total number of audio chunk files that were saved.

        """
        logging.info(f"TranscriptionTeeClient: Combining {num_chunks_saved} audio chunks into {self.output_recording_filename}")
        chunks_dir = TEMP_DIR / "mic_chunks"
        # List files based on the expected naming convention from save_chunk/finalize_recording
        input_files = [
            os.path.join(chunks_dir, f"{i}.wav")
            for i in range(num_chunks_saved)
            # Only include files that actually exist
            if os.path.exists(os.path.join(chunks_dir, f"{i}.wav"))
        ]

        if not input_files:
             logging.warning(f"TranscriptionTeeClient: No chunk files found in {chunks_dir} to combine.")
             # Clean up the chunks directory even if empty or no files were found
             if os.path.exists(chunks_dir):
                  try: shutil.rmtree(chunks_dir)
                  except: pass
             return # Nothing to combine

        # Ensure output directory exists
        try:
            Path(self.output_recording_filename).parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logging.error(f"[ERROR]: TranscriptionTeeClient: Failed to create output directory for final recording: {e}. Skipping combining.")
            # Clean up chunks directory even if combining failed
            if os.path.exists(chunks_dir):
                 try: shutil.rmtree(chunks_dir)
                 except: pass
            return


        try:
            with wave.open(self.output_recording_filename, "wb") as wavfile_out:
                wavfile_out: wave.Wave_write
                # Assume all chunks have the same properties as the first chunk
                if input_files:
                    try:
                        with wave.open(input_files[0], "rb") as first_wav:
                             wavfile_out.setnchannels(first_wav.getnchannels())
                             wavfile_out.setsampwidth(first_wav.getsampwidth())
                             wavfile_out.setframerate(first_wav.getframerate())
                        logging.debug(f"TranscriptionTeeClient: Set WAV header from {input_files[0]}")
                    except Exception as e:
                         logging.error(f"[ERROR]: TranscriptionTeeClient: Failed to read header from first chunk {input_files[0]}: {e}. Cannot combine files.")
                         # Clean up chunks directory if reading header failed
                         if os.path.exists(chunks_dir):
                              try: shutil.rmtree(chunks_dir)
                              except: pass
                         return # Stop if we can't even read the header


                for in_file in input_files:
                    try:
                        with wave.open(in_file, "rb") as wav_in:
                            # Read chunks from the input file and write to the output file
                            while True:
                                data = wav_in.readframes(self.chunk)
                                if data == b"":
                                    break # End of input chunk file
                                wavfile_out.writeframes(data)
                        # Remove the processed chunk file
                        os.remove(in_file)
                        logging.debug(f"TranscriptionTeeClient: Combined and removed chunk: {in_file}")
                    except Exception as e:
                         logging.error(f"[ERROR]: TranscriptionTeeClient: Error processing or removing chunk file {in_file}: {e}. Skipping.")
                         # Continue processing other files even if one fails


            logging.info(f"TranscriptionTeeClient: Final recording saved to {self.output_recording_filename}")

        except Exception as e:
            logging.error(f"[ERROR]: TranscriptionTeeClient: Error combining audio chunks or writing final output file: {e}")
        finally:
            # clean up temporary directory to store chunks
            if os.path.exists(chunks_dir):
                try:
                    shutil.rmtree(chunks_dir)
                    logging.info(f"TranscriptionTeeClient: Cleaned up temporary chunks directory: {chunks_dir}")
                except Exception as e:
                    logging.warning(f"TranscriptionTeeClient: Failed to remove chunks directory {chunks_dir}: {e}")

    @staticmethod
    def bytes_to_float_array(audio_bytes):
        """
        Convert audio data from bytes (assuming 16-bit PCM) to a NumPy float array.

        It assumes that the audio data is in 16-bit PCM format (2 bytes per sample).
        The audio data is normalized to have values between -1 and 1.

        Args:
            audio_bytes (bytes): Audio data in bytes.

        Returns:
            np.ndarray: A NumPy array containing the audio data as float values normalized between -1 and 1.
        """
        # Check if audio_bytes is empty or not enough bytes for a 16-bit sample
        if not audio_bytes or len(audio_bytes) < 2:
             # logging.warning(f"bytes_to_float_array received less than 2 bytes ({len(audio_bytes)}). Returning empty array.")
             return np.array([], dtype=np.float32)

        # Ensure the length is a multiple of 2 for 16-bit samples
        if len(audio_bytes) % 2 != 0:
             # logging.warning(f"Audio bytes length ({len(audio_bytes)}) is not a multiple of 2. Truncating last byte.")
             audio_bytes = audio_bytes[:-1]

        # Use frombuffer to create a numpy array from the bytes, specifying int16 data type
        raw_data = np.frombuffer(buffer=audio_bytes, dtype=np.int16)
        # Convert to float32 and normalize to the range [-1, 1]
        return raw_data.astype(np.float32) / 32768.0 # Max value for int16 is 32767


class TranscriptionClient(TranscriptionTeeClient):
    """
    Client for handling audio transcription tasks via a single WebSocket connection.

    Acts as a high-level client for audio transcription tasks using a WebSocket connection. It can be used
    to send audio data for transcription to a server and receive transcribed text segments.

    Args:
        host (str): The hostname or IP address of the server.
        port (int): The port number to connect to on the server.
        lang (str, optional): The primary language for transcription. Default is None, which defaults to English ('en').
        translate (bool, optional): If True, the task will be translation instead of transcription. Default is False.
        model (str, optional): The whisper model to use (e.g., "small", "base"). Default is "small".
        use_vad (bool, optional): Whether to enable voice activity detection. Default is True.
        save_output_recording (bool, optional): Whether to save the microphone recording. Default is False.
        output_recording_filename (str, optional): Path to save the output recording WAV file. Default is "./output_recording.wav".
        output_transcription_path (str, optional): File path to save the output transcription (SRT file). Default is "./output.srt".
        log_transcription (bool, optional): Whether to log transcription output to the console. Default is True.
        max_clients (int, optional): Maximum number of client connections allowed. Default is 4.
        max_connection_time (int, optional): Maximum allowed connection time in seconds. Default is 600.
        mute_audio_playback (bool, optional): If True, mutes audio playback during file playback. Default is False.
        send_last_n_segments (int, optional): Number of most recent segments to send to the client. Defaults to 10.
        no_speech_thresh (float, optional): Segments with no speech probability above this threshold will be discarded. Defaults to 0.45.
        clip_audio (bool, optional): Whether to clip audio with no valid segments. Defaults to False.
        same_output_threshold (int, optional): Number of repeated outputs before considering it as a valid segment. Defaults to 10.

    Attributes:
        client (Client): An instance of the underlying Client class responsible for handling the WebSocket connection.

    Example:
        To create a TranscriptionClient and start transcription on microphone audio:
        ```python
        transcription_client = TranscriptionClient(host="localhost", port=9090)
        transcription_client()
        ```
    """
    def __init__(
        self,
        host,
        port,
        lang=None,
        translate=False,
        model="small",
        use_vad=True,
        save_output_recording=False,
        output_recording_filename="./output_recording.wav",
        output_transcription_path="./output.srt",
        log_transcription=True,
        max_clients=4,
        max_connection_time=7200,
        mute_audio_playback=False,
        send_last_n_segments=10,
        no_speech_thresh=0.45,
        clip_audio=False,
        same_output_threshold=10,
    ):
        # Validate file extensions upfront
        if save_output_recording and not output_recording_filename.lower().endswith(".wav"):
            raise ValueError(f"Please provide a valid `output_recording_filename`. It must end with `.wav`: {output_recording_filename}")
        # Allow None for output_transcription_path if SRT is not desired
        if output_transcription_path is not None and not output_transcription_path.lower().endswith(".srt"):
             raise ValueError(f"Please provide a valid `output_transcription_path`. It must end with `.srt` or be None: {output_transcription_path}")


        # Initialize the core Client instance
        self.client = Client(
            host,
            port,
            lang,
            translate,
            model,
            srt_file_path=output_transcription_path, # Pass the desired SRT path here (can be None)
            use_vad=use_vad,
            log_transcription=log_transcription,
            max_clients=max_clients,
            max_connection_time=max_connection_time,
            send_last_n_segments=send_last_n_segments,
            no_speech_thresh=no_speech_thresh,
            clip_audio=clip_audio,
            same_output_threshold=same_output_threshold,
        )

        # Initialize the parent TranscriptionTeeClient
        # Pass a list containing only this client instance
        TranscriptionTeeClient.__init__(
            self,
            [self.client],
            save_output_recording=save_output_recording,
            output_recording_filename=output_recording_filename,
            mute_audio_playback=mute_audio_playback # Pass mute setting to parent
        )

    # Override write_all_clients_srt if you want to prevent SRT writing entirely
    # def write_all_clients_srt(self):
    #     logging.info("Skipping SRT file writing as per TranscriptionClient override.")
    #     pass # Do nothing


# --- Corrected FullTranscriptionClient (Paste starts here) ---
class FullTranscriptionClient(TranscriptionClient):
    """
    A specialized TranscriptionClient that extends whisper_live.client.TranscriptionClient.
    It enables robust retrieval and persistence of the full transcription text
    from audio file inputs.
    """
    def __init__(self, *args, **kwargs):
        """
        Initializes the FullTranscriptionClient.
        All arguments are passed directly to the parent TranscriptionClient.
        """
        super().__init__(*args, **kwargs)
        # The 'self.client' attribute (from TranscriptionClient's __init__)
        # is the actual Client instance which holds the 'transcript' list.
        # No need to initialize a new list here.

    def transcribe_and_get_full_text(self, audio_file_path: str, output_text_filepath: str = None) -> str:
        """
        Transcribes the specified audio file and returns the full, aggregated
        transcription text. Optionally saves it to a plain text file.

        This method leverages the existing transcription logic of the parent class
        but ensures the final aggregated text is retrieved from the internal
        Client instance.

        Args:
            audio_file_path (str): The path to the audio file to transcribe.
            output_text_filepath (str, optional): Path to save the full transcription
                                                  as a plain text file. If None,
                                                  the text is not saved to a file.

        Returns:
            str: The full, aggregated transcription text, or an empty string if
                 transcription failed or yielded no results. Returns None if a
                 critical error prevented transcription from starting or completing.
        """
        file_path_obj = Path(audio_file_path)
        if not file_path_obj.is_file():
            logging.error(f"[ERROR]: Provided path is not a valid file: {audio_file_path}")
            return "" # Return empty string for invalid input path

        logging.info(f"[INFO]: Starting transcription for audio file: {audio_file_path}")

        # Reset transcript list in the underlying client instance for this new job
        if hasattr(self.client, 'transcript') and isinstance(self.client.transcript, list):
             self.client.transcript = []
             logging.debug(f"[DEBUG]: Client transcript list reset for {audio_file_path}")
        else:
             logging.warning("[WARNING]: Underlying client does not have a 'transcript' list attribute. Cannot reset.")


        try:
            # Call the parent's __call__ method with the audio file path.
            # This triggers the audio processing, sending to server, and collecting segments
            # into self.client.transcript. It also handles waiting for SERVER_READY,
            # sending END_OF_AUDIO, waiting for final responses, closing the connection,
            # and writing the SRT file (if output_transcription_path was provided).
            super().__call__(audio=str(file_path_obj))

            # After super().__call__() returns, the transcription process for the file
            # should be complete. The client.transcript list should contain the segments.

            full_transcription_segments = []
            if hasattr(self.client, 'transcript') and isinstance(self.client.transcript, list):
                for segment in self.client.transcript:
                    if "text" in segment and segment["text"] is not None: # Ensure text key exists and is not None
                         # Append the text, removing any leading/trailing whitespace from the segment
                         segment_text = segment["text"].strip()
                         if segment_text: # Only append if not empty after stripping
                             full_transcription_segments.append(segment_text)

            else:
                 logging.warning("[WARNING]: Client transcript list not found or is not a list after transcription.")

            # Join segments. Add a space between segments unless the last character of the previous
            # segment is punctuation that should be followed by a new segment directly (like . or !?)
            # A simple space join is usually sufficient for basic text output.
            # Using " ".join would add a space even if a segment ends with punctuation.
            # A more sophisticated approach would check punctuation, but simple join is ok for raw text.
            # Let's just join them directly as consecutive text chunks.
            # If segments are like ["Hello.", "How are you?"], joining directly is "Hello.How are you?".
            # Joining with space: "Hello. How are you?"
            # Joining with empty string: "Hello.How are you?".
            # Given the example output is continuous text, joining with "" is correct.
            final_text = " ".join(full_transcription_segments).strip()

            if not final_text and file_path_obj.is_file():
                logging.warning(f"[WARNING]: Transcription for {file_path_obj.name} resulted in empty text. Check audio file, server logs, or model compatibility.")

            # Save the final, combined text to the specified plain text file
            if output_text_filepath:
                self.save_text_to_file(final_text, output_text_filepath)

            return final_text # Return the plain text string

        except RuntimeError as e:
            # These are errors potentially raised by the parent's __call__ (e.g., server full/error)
            logging.error(f"[ERROR]: Transcription failed for {file_path_obj.name} due to server or client error: {e}")
            # Client closure is handled in the finally block of the parent's __call__
            return None # Return None to indicate a critical failure

        except Exception as e:
            logging.error(f"[ERROR]: An unexpected error occurred during transcription for {file_path_obj.name}: {e}")
            # Client closure is handled in the finally block of the parent's __call__
            return None # Return None to indicate a critical failure

        # finally:
            # Client closure and SRT writing are handled by the finally block
            # in TranscriptionTeeClient.__call__. No need to duplicate here.
            # logging.info("[INFO]: Transcription process finished.")


    def save_text_to_file(self, text: str, output_filepath: str):
        """
        Saves the given transcription text to a specified plain text file.

        Args:
            text (str): The transcription text to save.
            output_filepath (str): The path to the output file.
        """
        # It's okay to save an empty string if transcription yielded no text.
        # if not text:
        #     logging.warning("No text provided to save. Skipping file write.")
        #     return

        try:
            # Ensure directory exists before writing
            output_dir = Path(output_filepath).parent
            output_dir.mkdir(parents=True, exist_ok=True)

            with open(output_filepath, "w", encoding="utf-8") as f:
                f.write(text)
            logging.info(f"[INFO]: Full transcription text successfully saved to '{output_filepath}'")
        except IOError as e:
            logging.error(f"[ERROR]: Could not write transcription text to file '{output_filepath}': {e}")
        except Exception as e:
            logging.error(f"[ERROR]: An unexpected error occurred while saving transcription text: {e}")

# --- Corrected FullTranscriptionClient (Paste ends here) ---


import asyncio
from pathlib import Path
import re # To sanitize model names for filenames

# Logging is configured at the top of the script now.

# --- Configuration ---
AUDIO_DIR = SCRIPT_DIR / ".." / "audio"
MODELS_JSON_PATH = SCRIPT_DIR / "local_models.json"
TEMP_DIR = SCRIPT_DIR / "temp_files"
RESULTS_DIR = SCRIPT_DIR / ".." / "results"
SERVER_HOST = "localhost" # Replace with your server host
SERVER_PORT = 8228        # Replace with your server port
DEFAULT_LANG = "sv"       # Set default language to Swedish
# ---------------------

class BatchTranscriptionManager:
    """
    Manages transcription of multiple audio files using multiple models.
    """
    def __init__(self, audio_dir: Path, models_json_path: Path, results_dir: Path, host: str, port: int, lang: str):
        self.audio_dir = audio_dir
        self.models_json_path = models_json_path
        self.results_dir = results_dir
        self.host = host
        self.port = port
        self.lang = lang
        self.models = self._load_models()

    def _load_models(self):
        """Loads the list of models from the JSON file, respecting the 'use_this_model' flag."""
        if not self.models_json_path.is_file():
            logging.error(f"Models JSON file not found: {self.models_json_path}")
            return []
        try:
            with open(self.models_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if "models" in data and isinstance(data["models"], list):
                loaded_models = []
                for model_entry in data["models"]:
                    if isinstance(model_entry, dict) and \
                       model_entry.get("use_this_model") is True and \
                       "name" in model_entry and \
                       isinstance(model_entry["name"], str) and \
                       model_entry["name"].strip():
                        loaded_models.append(model_entry["name"].strip())
                    elif isinstance(model_entry, dict) and model_entry.get("use_this_model") is not True:
                        logging.info(f"Skipping model '{model_entry.get('name', 'N/A')}' as 'use_this_model' is not true.")
                    else:
                        logging.warning(f"Skipping invalid model entry: {model_entry}")

                if not loaded_models:
                    logging.warning(f"No models marked with 'use_this_model: true' or no valid model entries found in '{self.models_json_path}'.")
                else:
                    logging.info(f"Loaded {len(loaded_models)} models to be used from {self.models_json_path}: {loaded_models}")
                return loaded_models
            else:
                logging.error(f"Invalid format in {self.models_json_path}. Expected {{'models': [{{'name': '...', 'use_this_model': true/false}}, ...]}}")
                return []
        except FileNotFoundError:
            logging.error(f"Models JSON file not found: {self.models_json_path}")
            return []
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON from {self.models_json_path}: {e}")
            return []
        except Exception as e:
            logging.error(f"An unexpected error occurred while loading models: {e}")
            return []

    def _sanitize_name(self, name: str) -> str:
        """Sanitizes a string to be safe for use in filenames and paths."""
        if name is None:
            return "unknown_name" # Handle None case

        # Replace invalid characters with underscores
        sanitized = re.sub(r'[<>:"/\\|?*_]', '-', name)
        # Replace spaces with underscores
        sanitized = sanitized.replace(' ', '-')
        # Remove leading/trailing underscores, spaces or dots that can cause issues on some filesystems
        sanitized = sanitized.strip('-. ')
        # Ensure it's not empty after sanitization
        if not sanitized:
            return "sanitized_empty" # Return a placeholder if sanitization results in empty string

        return sanitized

    def process_all(self):
        """
        Processes all audio files in the audio directory using all loaded models.
        """
        if not self.audio_dir.is_dir():
            logging.error(f"Audio directory not found: {self.audio_dir}")
            return
        if not self.models:
            logging.error("No models loaded. Cannot proceed with transcription.")
            return

        # Use rglob('*.mp3') or rglob('*.wav') if you want specific file types and recursive search
        # Using glob("*") for top level files only:
        audio_files = [f for f in self.audio_dir.iterdir() if f.is_file()]

        if not audio_files:
            logging.warning(f"No audio files found in {self.audio_dir}. Nothing to transcribe.")
            return

        logging.info(f"Found {len(audio_files)} audio file(s) in {self.audio_dir}")

        for audio_file_path in audio_files:
            audio_file_name = audio_file_path.stem # File name without extension
            sanitized_audio_file_name = self._sanitize_name(audio_file_name)

            for model_name in self.models:
                sanitized_model_name = self._sanitize_name(model_name)

                # Define output paths
                model_results_dir = self.results_dir / sanitized_model_name
                audio_specific_dir = model_results_dir / sanitized_audio_file_name
                # The plain text file will contain only the transcription text
                output_text_filepath = audio_specific_dir / f"{sanitized_model_name}_{sanitized_audio_file_name}_transcription_result.txt"
                 # The base class will still generate an SRT, give it a unique path.
                 # If you truly NEVER want an SRT, you could pass None to output_transcription_path
                 # in the client constructor, but the base class might still attempt to write.
                 # Providing a unique path is the safest way if the base class logic is fixed.
                output_srt_filepath = audio_specific_dir / f"{sanitized_model_name}_{sanitized_audio_file_name}_transcription_result.srt"

                # Create output directory for this audio file and model
                try:
                    audio_specific_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    logging.error(f"[ERROR]: Failed to create output directory {audio_specific_dir}: {e}. Skipping transcription for this file/model.")
                    continue # Skip to the next model/file combination


                logging.info(f"\n--- Transcribing '{audio_file_path.name}' with model '{model_name}' (Language: {self.lang}) ---")

                # Optional: Skip if the desired plain text output file already exists
                if output_text_filepath.exists():
                     logging.info(f"[INFO]: Plain text output file already exists: {output_text_filepath}. Skipping.")
                     continue # Skip to the next model/file combination


                client_instance = None # Initialize client_instance outside try block
                try:
                    # Initialize a new client for each transcription task
                    # Pass mute_audio_playback=True to prevent PyAudio errors in headless environments
                    # Pass output_transcription_path to give the base class a place to write the SRT
                    client_instance = FullTranscriptionClient(
                        host=self.host,
                        port=self.port,
                        model=model_name,      # Pass the specific model name
                        lang=self.lang,        # Explicitly set the language
                        translate=False,       # Set to True for translation if needed
                        use_vad=True,          # Use VAD by default
                        mute_audio_playback=True, # Crucial for headless/no audio environments
                        output_transcription_path=str(output_srt_filepath), # Pass unique SRT path for base class
                        log_transcription=False, # Disable live console logging for batch process
                        max_connection_time=7200  # Further increase if needed, based on file durations
                    )

                    # Check if the client successfully initialized its socket before proceeding
                    # This handles cases where host/port were None or connection failed immediately
                    if client_instance.client.server_error:
                        logging.error(f"[ERROR]: Client initialization failed for {audio_file_path.name} with {model_name}. Skipping.")
                        # No need to call close_all_clients here as the client init failed early
                        continue # Skip to the next model/file

                    # Call the new method to transcribe and get the full text
                    # This method calls the parent __call__ which handles the WS communication lifecycle
                    full_transcription = client_instance.transcribe_and_get_full_text(
                        audio_file_path=str(audio_file_path),
                        output_text_filepath=str(output_text_filepath) # Pass TXT output path
                    )

                    # Check the return value of transcribe_and_get_full_text
                    if full_transcription is not None: # Check against None to distinguish failure from empty result
                        logging.info(f"[INFO]: Transcription complete for '{audio_file_path.name}' with '{model_name}'. Result saved to {output_text_filepath}")
                        if output_srt_filepath.exists():
                             logging.info(f"[INFO]: SRT file also generated at {output_srt_filepath} (can be ignored).")
                    else:
                        # An error occurred during transcription if the return is None
                        logging.error(f"[ERROR]: Transcription process failed for '{audio_file_path.name}' with '{model_name}'. Check logs above.")


                except RuntimeError as e:
                    # These are errors potentially raised by the parent's __call__ (e.g., server full/error)
                    logging.error(f"[ERROR]: Transcription failed for '{audio_file_path.name}' with '{model_name}' due to server or client error: {e}")
                    # Client closure is handled in the finally block of the parent's __call__
                except Exception as e:
                     # Catch any other unexpected errors during the process
                     logging.error(f"[ERROR]: An unexpected error occurred during transcription for '{audio_file_path.name}' with '{model_name}': {e}")
                     # Client closure is handled in the finally block of the parent's __call__
                finally:
                    # Ensure the client is closed, even if errors occurred
                    # The FullTranscriptionClient's transcribe_and_get_full_text method's internal
                    # call to super().__call__() has a finally block that calls self.close_all_clients().
                    # However, if an exception happens *before* that inner finally block is reached,
                    # or if client_instance creation failed early, this final check is useful.
                    if client_instance:
                         try:
                             # Ensure the client socket and thread are properly terminated
                              # Check if close_all_clients method exists before calling
                              if hasattr(client_instance, 'close_all_clients'):
                                   client_instance.close_all_clients()
                                   logging.debug(f"[DEBUG]: Client for '{audio_file_path.name}' with '{model_name}' explicitly ensured closed.")
                              else:
                                   logging.warning(f"[WARNING]: Client instance {client_instance} lacks close_all_clients method.")
                         except Exception as close_e:
                             logging.error(f"[ERROR]: Error ensuring client closure after processing '{audio_file_path.name}' with '{model_name}': {close_e}")


        logging.info("\n--- Batch transcription process finished ---")


# --- Main Execution ---
async def main_async():
    if not TEMP_DIR.exists():
        logging.info(f"Temporary directory '{TEMP_DIR}' not found. Creating it.")
        TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # Create dummy directories and models.json if they don't exist for demonstration
    if not AUDIO_DIR.exists():
        logging.warning(f"Audio directory '{AUDIO_DIR}' not found. Creating dummy files.")
        AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        # Create dummy audio files (e.g., silence)
        dummy_audio1 = AUDIO_DIR / "sample1.wav"
        dummy_audio2 = AUDIO_DIR / "sample_two.mp3" # Use a different format
        dummy_audio3 = AUDIO_DIR / "sample with spaces & special chars!.wav" # Test sanitization

        if not dummy_audio1.exists():
             try:
                 with wave.open(str(dummy_audio1), 'wb') as wf:
                     wf.setnchannels(1)
                     wf.setsampwidth(2) # 16-bit audio (2 bytes)
                     wf.setframerate(16000) # 16kHz sample rate
                     wf.writeframes(b'\0\0' * 16000) # 1 second of silence (16000 frames * 2 bytes/frame)
                 logging.info(f"Created dummy audio file: {dummy_audio1}")
             except Exception as e:
                 logging.error(f"Failed to create dummy audio file {dummy_audio1}: {e}")

        # Creating a dummy MP3 requires an MP3 encoding library, which is more complex.
        # Just log a message if it doesn't exist and ensure utils.resample can handle it.
        if not dummy_audio2.exists():
             logging.warning(f"Dummy MP3 file '{dummy_audio2}' not found. Please provide it manually if needed for testing.")
             # Example of creating a dummy empty file to ensure it's picked up by glob
             try:
                  open(dummy_audio2, 'a').close()
                  logging.info(f"Created placeholder dummy MP3 file: {dummy_audio2}")
             except Exception as e:
                  logging.error(f"Failed to create placeholder dummy MP3 file {dummy_audio2}: {e}")


        if not dummy_audio3.exists():
             try:
                 with wave.open(str(dummy_audio3), 'wb') as wf:
                     wf.setnchannels(1)
                     wf.setsampwidth(2) # 16-bit audio (2 bytes)
                     wf.setframerate(16000) # 16kHz sample rate
                     wf.writeframes(b'\0\0' * 16000 * 3) # 3 seconds of silence
                 logging.info(f"Created dummy audio file (with special chars): {dummy_audio3}")
             except Exception as e:
                 logging.error(f"Failed to create dummy audio file {dummy_audio3}: {e}")


    if not MODELS_JSON_PATH.exists():
        logging.warning(f"Models JSON file '{MODELS_JSON_PATH}' not found. Creating a dummy file.")
        dummy_models = {
          "models": [
            "KBLab/kb-whisper-large",
            "small", # Example base model name
            "large-v3", # Another common model
            # "invalid/model" # Example of potential bad model name
            # None # Example of None entry
            # "" # Example of empty string entry
          ]
        }
        try:
            with open(str(MODELS_JSON_PATH), 'w', encoding='utf-8') as f:
                json.dump(dummy_models, f, indent=2)
            logging.info(f"Created dummy models file: {MODELS_JSON_PATH}")
        except Exception as e:
            logging.error(f"Failed to create dummy models file {MODELS_JSON_PATH}: {e}")


    # Check if pyaudio is available or handle the fact it's not needed for this use case
    # The conditional initialization in TranscriptionTeeClient handles the import errors.
    # We don't need to check here specifically unless we want to print a message
    # *before* any client initialization. The current logging in TranscriptionTeeClient
    # handles this fine.


    manager = BatchTranscriptionManager(
        audio_dir=AUDIO_DIR,
        models_json_path=MODELS_JSON_PATH,
        results_dir=RESULTS_DIR,
        host=SERVER_HOST,
        port=SERVER_PORT,
        lang=DEFAULT_LANG # Pass the default language here
    )

    manager.process_all()

if __name__ == "__main__":
    # Use asyncio.run to execute the main async function
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logging.info("\nBatch transcription interrupted by user.")
    except Exception as e:
        # Catch any exception not handled inside the manager
        logging.fatal(f"\nA fatal error occurred during batch processing: {e}", exc_info=True)
        # Ensure all active clients are closed in case of a top-level error
        logging.info("Attempting to close any remaining client connections.")
        for uid, client in list(Client.INSTANCES.items()):
            try:
                logging.info(f"Attempting to close client {uid}")
                client.close_websocket()
                # Give thread a moment to finish
                if client.ws_thread and client.ws_thread.is_alive():
                     client.ws_thread.join(timeout=2)
            except Exception as close_e:
                logging.error(f"Error during emergency client cleanup for {uid}: {close_e}")