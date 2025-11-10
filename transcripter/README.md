# Transcripter & Summarizer (Unified)

Transform your audio into text, summaries, and notes. This is a unified application that runs both the Streamlit UI and the FastAPI backend in a single container.

## Features

- **Unified Architecture**: A single application serving both the UI and API.
- **Modular Codebase**: Code is organized into modules for clarity and maintainability.
- **Modern UI**: A clean and user-friendly interface built with Streamlit.
- **AI-Powered**: Utilizes Hugging Face for transcription and Gemini for summarization and note-taking.
- **Dockerized**: Easy to set up and run locally with a single Docker command.

## Prerequisites

- Docker

## How to Run

1.  **Clone the repository** (or download the files).

2.  **Set up your environment variables**:
    - Navigate to the `transcripter` directory.
    - You will find a `.env` file. Open it and replace the placeholder values with your actual API keys:
      ```env
      GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"
      HUGGING_FACE_API_URL="YOUR_HUGGING_FACE_API_URL_HERE"
      ```

3.  **Run the application with Docker Compose**:
    - Open your terminal, navigate to the `transcripter` directory, and run:
      ```bash
      docker-compose up --build
      ```
    - The application will be built and started. The `--build` flag is only necessary the first time or after code changes.

4.  **Access the application**:
    - Open your web browser and go to `http://localhost:8501`.
    - The API documentation is available at `http://localhost:8000/docs`.

## Project Structure

```
transcripter/
├── src/
│   ├── __init__.py
│   ├── api.py            # FastAPI application
│   ├── main.py           # Main entrypoint (runs UI and API)
│   ├── models.py         # Pydantic models
│   ├── services.py       # External service interactions
│   └── ui.py             # Streamlit application
├── .env                  # Your secret keys
├── .gitignore
├── Dockerfile            # Single Dockerfile for the application
├── requirements.txt
└── README.md
```
