import asyncio
import logging
import os
import ssl
import time
from pathlib import Path
from typing import Any, Dict, Iterable, Optional
from urllib.parse import urljoin, urlparse, urlunparse

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

TRANSCRIPTION_STATUS_POLL_INTERVAL = float(
    os.getenv("TRANSCRIPTION_STATUS_POLL_INTERVAL", "2.0")
)
TRANSCRIPTION_STATUS_POLL_TIMEOUT = float(
    os.getenv("TRANSCRIPTION_STATUS_POLL_TIMEOUT", "120.0")
)
_raw_request_timeout = os.getenv("TRANSCRIPTION_REQUEST_TIMEOUT", "300.0")
if _raw_request_timeout.strip().lower() == "none":
    TRANSCRIPTION_REQUEST_TIMEOUT: Optional[float] = None
else:
    TRANSCRIPTION_REQUEST_TIMEOUT = float(_raw_request_timeout)

_PROCESSING_STATUSES = {
    "pending",
    "processing",
    "queued",
    "in_progress",
    "running",
    "started",
}
_SUCCESS_STATUSES = {
    "success",
    "succeeded",
    "completed",
    "done",
    "finished",
}
_FAILED_STATUSES = {
    "failed",
    "error",
    "cancelled",
    "canceled",
}


def _extract_transcription_text(payload: Dict[str, Any]) -> Optional[str]:
    """Extract transcription text from a payload, checking common keys."""

    if not isinstance(payload, dict):
        return None

    direct_text = payload.get("transcription") or payload.get("text")
    if isinstance(direct_text, str) and direct_text.strip():
        return direct_text

    result_section = payload.get("result")
    if isinstance(result_section, dict):
        return _extract_transcription_text(result_section)

    return None


def _normalize_transcription_payload(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Ensure the payload includes a `transcription` key if text was found."""

    transcription = _extract_transcription_text(payload)
    if transcription is None:
        return None

    normalized = dict(payload)
    normalized["transcription"] = transcription
    return normalized


def _resolve_status(payload: Dict[str, Any]) -> Optional[str]:
    """Return a normalized status string if available in the payload."""

    for key in ("status", "state", "phase"):
        raw_value = payload.get(key)
        if isinstance(raw_value, str):
            return raw_value.lower()
    return None


def _resolve_status_endpoint(
    base_endpoint: str, response: httpx.Response, payload: Dict[str, Any]
) -> Optional[str]:
    """Attempt to determine a status endpoint for asynchronous polling."""

    for key in ("status_url", "polling_url", "result_url", "statusEndpoint"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value

    location_header = response.headers.get("Location") or response.headers.get("location")
    if location_header:
        if location_header.startswith("http://") or location_header.startswith("https://"):
            return location_header
        return urljoin(base_endpoint.rstrip("/") + "/", location_header)

    return None


async def _poll_transcription_status(
    client: httpx.AsyncClient,
    status_endpoint: str,
) -> Dict[str, Any]:
    """Poll the provided status endpoint until a transcription is ready or timeout occurs."""

    logger.info(
        "Polling transcription status from %s every %ss (timeout %ss)",
        status_endpoint,
        TRANSCRIPTION_STATUS_POLL_INTERVAL,
        TRANSCRIPTION_STATUS_POLL_TIMEOUT,
    )

    deadline = time.monotonic() + TRANSCRIPTION_STATUS_POLL_TIMEOUT

    while True:
        response = await client.get(status_endpoint)
        response.raise_for_status()

        payload = response.json()

        normalized = _normalize_transcription_payload(payload)
        if normalized is not None:
            logger.info("Transcription completed via status polling.")
            return normalized

        status = _resolve_status(payload)
        if status in _FAILED_STATUSES:
            raise HTTPException(
                status_code=502,
                detail=(
                    "Transcription service reported a failure while processing the audio."
                ),
            )

        if status in _SUCCESS_STATUSES:
            raise HTTPException(
                status_code=502,
                detail=(
                    "Transcription service completed without returning transcription text."
                ),
            )

        if time.monotonic() >= deadline:
            raise HTTPException(
                status_code=504,
                detail="Timed out while waiting for the transcription service to finish processing.",
            )

        if status not in _PROCESSING_STATUSES:
            logger.debug(
                "Polling status endpoint %s returned unrecognized payload: %s",
                status_endpoint,
                payload,
            )

        await asyncio.sleep(TRANSCRIPTION_STATUS_POLL_INTERVAL)


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

    timeout = httpx.Timeout(
        TRANSCRIPTION_REQUEST_TIMEOUT,
        connect=10.0,
    )

    async with httpx.AsyncClient(
        verify=False,
        timeout=timeout,
    ) as client:  # Disable SSL verification for local development
        for endpoint in endpoints:
            try:
                logger.info("Attempting transcription via %s", endpoint)
                response = await client.post(endpoint, files=file_field)
                response.raise_for_status()

                try:
                    payload = response.json()
                except ValueError:
                    logger.debug(
                        "Transcription service returned non-JSON payload from %s: %r",
                        endpoint,
                        response.text,
                    )
                    payload = {}
                normalized = _normalize_transcription_payload(payload)
                if normalized is not None:
                    logger.info("Transcription completed on initial request to %s", endpoint)
                    return normalized

                status_endpoint = _resolve_status_endpoint(endpoint, response, payload)
                if status_endpoint:
                    logger.info(
                        "Transcription is still processing; polling status endpoint %s",
                        status_endpoint,
                    )
                    return await _poll_transcription_status(client, status_endpoint)

                status = _resolve_status(payload)
                if status in _PROCESSING_STATUSES:
                    raise HTTPException(
                        status_code=502,
                        detail=(
                            "Transcription service reported processing but did not provide a status endpoint to poll."
                        ),
                    )

                raise HTTPException(
                    status_code=502,
                    detail=(
                        "Transcription service responded without transcription text. "
                        "Enable asynchronous polling by including a status URL in the response."
                    ),
                )
            except httpx.HTTPStatusError as http_error:
                # The service responded but returned an error status. Surface the details immediately.
                detail = http_error.response.text
                raise HTTPException(
                    status_code=http_error.response.status_code,
                    detail=f"Transcription service error: {detail}",
                ) from http_error
            except httpx.TimeoutException as timeout_error:
                raise HTTPException(
                    status_code=504,
                    detail=(
                        "Timed out while waiting for the transcription service to respond. "
                        "Increase TRANSCRIPTION_REQUEST_TIMEOUT if longer processing is expected."
                    ),
                ) from timeout_error
            except (httpx.RequestError, ssl.SSLError) as request_error:
                last_request_error = request_error
                logger.warning(
                    "Request to transcription service at %s failed: %r", endpoint, request_error
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
