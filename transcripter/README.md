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

3.  **Build the Docker image**:
    - Open your terminal, navigate to the `transcripter` directory, and run:
      ```bash
      docker build -t transcripter-app .
      ```

4.  **Run the Docker container**:
    - After the build is complete, run the container with:
      ```bash
      docker run -p 8501:8501 -p 8000:8000 transcripter-app
      ```

5.  **Access the application**:
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
