# Speech-to-Text Evaluation Framework

This framework is designed to evaluate various Speech-to-Text (STT) models and APIs, comparing their performance on different audio files using metrics like WER, CER, BERTScore, and more.

## Setup

To set up the environment, use `uv` for managing the Python environment. Ensure you have `uv` installed (install via `pip install uv` if needed). Then, navigate to the EVAL directory and run:

```
uv sync
```

This command will create a virtual environment and install all dependencies listed in `pyproject.toml`, including packages such as `deepgram-sdk`, `elevenlabs`, `google-cloud-speech`, `openai`, `evaluate`, `bert-score`, `jiwer`, `levenshtein`, `matplotlib`, `pandas`, `stanza`, and `whisper-live`. It uses Python 3.12 by default, but you can specify a different version if needed via `.python-version`.

## Configuration

API keys are required for accessing external services. Configure them using the `.env` file located in the EVAL directory. Create or edit the `.env` file with the following entries, replacing the placeholders with your actual API keys:

```
DEEPGRAM_API_KEY=your_deepgram_key
AZURE_API_KEY=your_azure_key
ELEVENLABS_API_KEY=your_elevenlabs_key
GOOGLE_API_KEY=your_google_key
AZURE_OPENAI_API_KEY=your_azure_openai_key
```

Ensure this file is kept secure and not committed to version control. Add it to `.gitignore` if it isn't already listed.

## Main Scripts and Directories

- `compare_files.py`: A Python script that compares two text files and calculates the Word Error Rate (WER).
- `how_to_improve_stt_using_google_cloud.md`: A Markdown guide providing tips and steps for enhancing STT performance using Google Cloud Speech-to-Text and Storage services.
- `evaluat/`: Directory containing evaluation scripts, such as `evaluator.py` for metric calculations, `plot_evaluation_results.py` for generating visualizations, and `llm_eval.py` for advanced evaluations using language models.
- `transcribe/`: Directory with transcription scripts and results storage. It includes subdirectories like `run/` (e.g., `run_azure_all.py`, `run_deepgram_all.py`) for executing transcriptions with different models, and `results/` for storing output files.

## Running Evaluation Scripts

To run transcriptions, use the scripts in the `transcribe/run/` directory. For example, to transcribe all audio files using the Azure API:

```
uv run python transcribe/run/run_azure_all.py
```

Similar scripts are available for other models (e.g., `run_deepgram_all.py`, `run_elevenlabs_all.py`). After transcription, use scripts in the `evaluat/` directory to process results, such as running `uv run python evaluat/evaluator.py` to compute metrics or `uv run python evaluat/plot_evaluation_results.py` to create plots.

## Dependencies

All project dependencies are defined in `pyproject.toml`. This file specifies packages for API interactions, metric evaluations, and data processing. Key dependencies include:

- `deepgram-sdk` for Deepgram API support
- `elevenlabs` for ElevenLabs API
- `google-cloud-speech` for Google Cloud Speech-to-Text
- `openai` for OpenAI-based evaluations
- `evaluate`, `bert-score`, `jiwer`, `levenshtein` for performance metrics
- `matplotlib`, `pandas` for data visualization and handling
- `stanza`, `whisper-live` for additional NLP and STT capabilities

Install them automatically with `uv sync`.

## Troubleshooting

- **API Key Errors**: If you encounter authentication issues, double-check the keys in your `.env` file for correctness and ensure the script is loading environment variables (e.g., using `python-dotenv`). Common issues include typos in key names or missing variables.
- **Environment Setup Problems**: Verify that `uv` is installed and that your Python version matches `.python-version` (default is 3.12). If `uv sync` fails, ensure you have internet access and no package conflicts; try clearing the cache with `uv cache clear`.
- **Script Execution Failures**: Check for missing audio files in the project directory or incorrect paths in scripts. Review error messages in the console for details, and ensure all dependencies are installed. If using external APIs, confirm they are accessible and rate limits are not exceeded.