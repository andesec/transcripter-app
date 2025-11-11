# Transcripter App

This repository contains the code for **Transcripter**, a web application that uses WhisperX to transcribe audio files and then generates notes and summaries from the transcript.

## Repository Structure

The production application lives in the [`transcripter/`](transcripter/) directory. It includes the Streamlit user interface, the FastAPI backend, and Docker tooling for running everything together.

```
transcripter/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── src/
└── static/
```

The subdirectory also provides an in-depth [README](transcripter/README.md) with setup steps, environment configuration, and architectural details.

## Getting Started

1. Navigate to the [`transcripter/`](transcripter/) directory.
2. Follow the environment configuration instructions in the subproject README to create a `.env` file with your API credentials.
3. Launch the application with Docker Compose:

   ```bash
   docker-compose up --build
   ```

For more detailed information about features, architecture, and usage, see the [Transcripter README](transcripter/README.md).
