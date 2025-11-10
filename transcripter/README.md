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

## Understanding the Application Architecture

This application is built as a unified service, meaning both the user interface (UI) and the backend API run together within a single Docker container. This design offers simplicity in deployment while maintaining a clear separation of concerns in the codebase.

### How the UI Works (Streamlit)

The interactive web interface you'll use is built with **Streamlit**. Streamlit allows us to create rich, data-driven web applications purely in Python.

*   **Accessing the UI:** Once the Docker container is running (after `docker-compose up --build`), you can access the Streamlit UI by opening your web browser and navigating to **`http://localhost:8501`**. This is where you will upload audio files, select categories, and view the generated transcriptions, summaries, and notes.

### How the Backend API Works (FastAPI)

The core logic for processing audio, interacting with Hugging Face for transcription, and calling the Gemini API for summarization and note-taking is handled by a **FastAPI** application.

*   **Why an API Endpoint?** While the UI and backend are unified in deployment, they still communicate with each other. When you upload an audio file and click "Generate Insights" in the Streamlit UI, the UI needs a way to send that audio file and your chosen category to the backend processing logic. This is precisely the role of the FastAPI endpoint (`/transcribe`).
    *   The Streamlit UI (your web browser) makes an HTTP request to the FastAPI backend (running on `http://localhost:8000`) to send the audio data.
    *   The FastAPI backend then takes this data, processes it (sends to Hugging Face, then Gemini), and returns the results to the Streamlit UI.

This internal API communication is a standard and robust way for different parts of a web application to interact, even when they are deployed together. It ensures that the UI remains responsive while complex, potentially long-running tasks are handled efficiently by the backend.

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
