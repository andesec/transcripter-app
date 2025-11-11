import os
import httpx
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from .models import TranscriptionResponse
from .services import generate_summary_and_notes

app = FastAPI(title="Transcriber API")

# Mount static files
app.mount("/static", StaticFiles(directory=Path(__file__).parent.parent / "static"), name="static")

TRANSCRIPTION_SERVICE_URL_BASE = os.getenv(
    "TRANSCRIPTION_SERVICE_URL",
    "https://andenate-transcription-service.hf.space" # Default fallback Base URL
)

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
        audio_content = await file.read()
        
        # Forward the audio file to the external transcription service
        async with httpx.AsyncClient(verify=False) as client: # Disable SSL verification for local development
            transcription_endpoint = f"{TRANSCRIPTION_SERVICE_URL_BASE}/transcribe"
            response = await client.post(
                transcription_endpoint,
                files={"file": (file.filename, audio_content, file.content_type)}
            )
            response.raise_for_status() # Raise an exception for HTTP errors
            try:
                transcription_data = response.json()
            except json.JSONDecodeError:
                raise HTTPException(status_code=500, detail="Transcription service returned invalid JSON.")
            
            transcribed_text = transcription_data.get("transcription")

        if not transcribed_text:
            raise HTTPException(status_code=500, detail="Transcription service did not return text.")

        return {"transcription": transcribed_text}

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Transcription service error: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
