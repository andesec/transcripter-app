import logging
import os
import ssl
from pathlib import Path
from typing import Any, Dict, Iterable, Optional
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


async def _attempt_transcription(
    file_field: Dict[str, tuple],
    endpoints: Iterable[str],
) -> Dict[str, Any]:
    """Try each endpoint until one succeeds or raise an informative HTTPException."""

    last_request_error: Optional[Exception] = None

    async with httpx.AsyncClient(verify=False) as client:  # Disable SSL verification for local development
        for endpoint in endpoints:
            try:
                logger.info("Attempting transcription via %s", endpoint)
                response = await client.post(endpoint, files=file_field)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as http_error:
                # The service responded but returned an error status. Surface the details immediately.
                detail = http_error.response.text
                raise HTTPException(
                    status_code=http_error.response.status_code,
                    detail=f"Transcription service error: {detail}",
                ) from http_error
            except (httpx.RequestError, ssl.SSLError) as request_error:
                last_request_error = request_error
                logger.warning(
                    "Request to transcription service at %s failed: %s", endpoint, request_error
                )
                continue

    if last_request_error is not None:
        raise HTTPException(
            status_code=502,
            detail=(
                "Unable to reach the transcription service. "
                "Ensure the service is reachable over HTTP or HTTPS."
            ),
        ) from last_request_error

    raise HTTPException(status_code=502, detail="Transcription service is unavailable.")

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

@app.post("/transcribe_and_summarize", response_model=TranscriptionResponse)
async def transcribe_and_summarize(
    file: UploadFile = File(...),
    category: str = Form(...)
):
    """
    Receives an audio file, transcribes it using an external service,
    then generates a summary and notes based on the transcription.
    """
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an audio file.")

    try:
        audio_content = await file.read()

        transcription_endpoint = _build_transcription_endpoint(TRANSCRIPTION_SERVICE_URL_BASE)

        # Forward the audio file to the external transcription service
        file_field = {
            "file": (
                file.filename or "audio",
                audio_content,
                file.content_type or "application/octet-stream",
            )
        }

        endpoints = [transcription_endpoint]
        fallback_endpoint = _fallback_to_http(transcription_endpoint)
        if fallback_endpoint:
            endpoints.append(fallback_endpoint)

        transcription_data = await _attempt_transcription(file_field, endpoints)
        transcribed_text = transcription_data.get("transcription")

        if not transcribed_text:
            raise HTTPException(status_code=500, detail="Transcription service did not return text.")

        summary, notes = generate_summary_and_notes(transcribed_text, category)
        if not summary or not notes:
            raise HTTPException(status_code=422, detail="AI service failed to generate summary and notes.")

        return TranscriptionResponse(
            transcription=transcribed_text,
            summary=summary,
            notes=notes
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Transcription service error: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
