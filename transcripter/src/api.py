import logging
import os
import ssl
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, urlunparse

import httpx
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .models import TranscriptionResponse
from .services import generate_summary_and_notes


logger = logging.getLogger(__name__)

app = FastAPI(title="Transcriber API")

# Mount static files
app.mount("/static", StaticFiles(directory=Path(__file__).parent.parent / "static"), name="static")

TRANSCRIPTION_SERVICE_URL_BASE = os.getenv(
    "TRANSCRIPTION_SERVICE_URL",
    "https://andenate-transcription-service.hf.space"  # Default fallback Base URL
)


def _build_transcription_endpoint(base_url: str) -> str:
    """Return a normalized transcription endpoint with a trailing /transcribe."""
    normalized_base = base_url.rstrip("/")
    return f"{normalized_base}/transcribe"


def _fallback_to_http(url: str) -> Optional[str]:
    """Return the HTTP version of a URL if the scheme is HTTPS."""
    parsed = urlparse(url)
    if parsed.scheme.lower() != "https":
        return None

    return urlunparse(parsed._replace(scheme="http"))

@app.get("/", response_class=HTMLResponse)
async def read_root():
    index_html_path = Path(__file__).parent.parent / "static" / "index.html"
    with open(index_html_path, "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.post("/summarize_and_notes", response_model=TranscriptionResponse)
async def summarize_and_notes(
    transcribed_text: str = Form(...),
    category: str = Form(...)
):
    """
    Receives transcribed text and a category, then generates a summary and notes.
    """
    summary, notes = generate_summary_and_notes(transcribed_text, category)
    if not summary or not notes:
        raise HTTPException(status_code=422, detail="AI service failed to generate summary and notes.")

    return TranscriptionResponse(
        transcription=transcribed_text, # Return the input text as transcription
        summary=summary,
        notes=notes
    )

@app.post("/transcribe_audio")
async def transcribe_audio(
    file: UploadFile = File(...)
):
    """
    Receives an audio file and transcribes it using an external service.
    Returns the transcribed text.
    """
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an audio file.")

    try:
        print(1)
        audio_content = await file.read()

        transcription_endpoint = _build_transcription_endpoint(TRANSCRIPTION_SERVICE_URL_BASE)

        # Forward the audio file to the external transcription service
        async with httpx.AsyncClient(verify=False) as client:  # Disable SSL verification for local development
            try:
                response = await client.post(
                    transcription_endpoint,
                    files={"file": (file.filename, audio_content, file.content_type)}
                )
                response.raise_for_status()  # Raise an exception for HTTP errors
            except (httpx.UnsupportedProtocol, httpx.LocalProtocolError, ssl.SSLError) as protocol_error:
                fallback_endpoint = _fallback_to_http(transcription_endpoint)
                if not fallback_endpoint:
                    raise protocol_error

                logger.warning(
                    "HTTPS request to %s failed (%s). Retrying over HTTP at %s.",
                    transcription_endpoint,
                    protocol_error,
                    fallback_endpoint,
                )
                response = await client.post(
                    fallback_endpoint,
                    files={"file": (file.filename, audio_content, file.content_type)}
                )
                response.raise_for_status()

            transcription_data = response.json()
            transcribed_text = transcription_data.get("transcription")
            print(7, transcribed_text)
        if not transcribed_text:
            raise HTTPException(status_code=500, detail="Transcription service did not return text.")
        print(8)
        return {"transcription": transcribed_text}

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Transcription service error: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
