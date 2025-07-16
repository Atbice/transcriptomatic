# Transcriptomatic

## Description

Transcriptomatic is a comprehensive project for speech-to-text transcription and evaluation. The main application, located in the `MVP/` directory, provides a user-friendly interface for transcribing audio using various APIs and models. The evaluation framework in the `EVAL/` directory allows for comparing and assessing the performance of different transcription models.

## Technologies Used

- Frontend: React
- Backend: FastAPI
- Containerization: Docker, Docker Compose
- Programming Language: Python
- Transcription APIs/Models: Various services like Azure, Deepgram, Elevenlabs, and local models such as Whisper
- AI Agents: Custom agents for enhanced transcription capabilities

## Getting Started

For detailed setup and usage instructions, please refer to the specific README files:

- [MVP/README.md](MVP/README.md) for the main application
- [EVAL/README.md](EVAL/README.md) for the evaluation framework

## Project Structure

- `MVP/`: Contains the minimum viable product with the React frontend, FastAPI backend, Docker configurations, and AI agents.
- `EVAL/`: Houses scripts and data for evaluating transcription models, including comparison tools and result plots.
- `PRESENTATION/`: Contains presentation materials such as images and Markdown files.
- `RAPPORT/`: Contains report files in Markdown format.

Detailed file structure representation can be generated using the `tree` command.

```bash
    tree
```