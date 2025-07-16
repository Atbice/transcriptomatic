# download_models.py
import os
import torch
from transformers import WhisperProcessor, WhisperForConditionalGeneration, pipeline
# Assuming constants.py is in the same directory or accessible via PYTHONPATH
# from constants import AVAILABLE_WHISPER_MODELS

# For standalone testing, define it here or ensure constants.py is available
AVAILABLE_WHISPER_MODELS = [
    "KBLab/kb-whisper-tiny",
    # "KBLab/kb-whisper-base",
    # "KBLab/kb-whisper-small",
    # "KBLab/kb-whisper-medium",
    # "KBLab/kb-whisper-large",
]


# Get paths
path_to_this_file = os.path.dirname(os.path.abspath(__file__))
# This should resolve to /app/data/stt_model_cache inside the container
path_to_stt_model_cache = os.path.join(path_to_this_file, "data", "stt_model_cache")

print(f"INFO: Script location: {path_to_this_file}")
print(f"INFO: Attempting to use cache directory: {path_to_stt_model_cache}")

# Ensure the cache directory exists and is writable
try:
    os.makedirs(path_to_stt_model_cache, exist_ok=True)
    print(f"INFO: Ensured cache directory exists or was created: {path_to_stt_model_cache}")
    
    # Explicitly test writability
    test_file_path = os.path.join(path_to_stt_model_cache, ".permission_test.txt")
    with open(test_file_path, "w") as f:
        f.write("test")
    os.remove(test_file_path)
    print(f"INFO: Successfully created and deleted a test file in {path_to_stt_model_cache}. Write permissions seem OK at this level.")

except Exception as e:
    print(f"ERROR: Could not create or write to cache directory {path_to_stt_model_cache}. Error: {e}")
    print("ERROR: This is likely a volume mount permission issue from the host, or an issue with SELinux if you're using it.")
    print("ERROR: Please check the permissions of the host directory mounted to /app/data inside the container.")
    raise # Stop if we can't even write here

# Set device
device = "cuda:0" if torch.cuda.is_available() else "cpu"
print(f"INFO: Using device: {device}")
if device == "cuda:0":
    print(f"INFO: CUDA device name: {torch.cuda.get_device_name(0)}")

for model_name in AVAILABLE_WHISPER_MODELS:
    print(f"\nINFO: === Processing model: {model_name} ===")
    transcriber = None  # Initialize to None for each model
    model = None
    processor = None
    try:
        print(f"INFO: Loading processor for {model_name}...")
        processor = WhisperProcessor.from_pretrained(model_name, cache_dir=path_to_stt_model_cache)
        
        print(f"INFO: Loading model {model_name}...")
        model = WhisperForConditionalGeneration.from_pretrained(model_name, cache_dir=path_to_stt_model_cache)
        
        # Move model to device
        print(f"INFO: Moving model {model_name} to {device}...")
        model.to(device)

        print(f"INFO: Initializing pipeline for {model_name}...")
        transcriber = pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            chunk_length_s=30,
            device=device # Note: model is already on device, so this might be redundant but is often used
        )
        print(f"SUCCESS: Model {model_name} loaded and pipeline initialized successfully.")
    except Exception as e:
        print(f"ERROR: Error loading model {model_name}: {e}")
        # The original script re-raised, which stops the container CMD.
        # For debugging all models, you might comment out 'raise' temporarily.
        raise
    finally:
        # Clean up to free memory
        if transcriber is not None:
            print(f"INFO: Cleaning up transcriber for {model_name}.")
            del transcriber
        if model is not None:
            print(f"INFO: Cleaning up model {model_name}.")
            del model
        if processor is not None:
            print(f"INFO: Cleaning up processor for {model_name}.")
            del processor
        
        if device == "cuda:0":
            torch.cuda.empty_cache()
            print(f"INFO: Emptied CUDA cache after {model_name}.")
        print(f"INFO: === Finished processing for model: {model_name} ===")

print("\nINFO: Finished attempting to download all models specified in AVAILABLE_WHISPER_MODELS.")