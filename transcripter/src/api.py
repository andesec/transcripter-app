import os
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from .models import TranscriptionResponse
from .services import generate_summary_and_notes

app = FastAPI(title="Transcriber API")

# Mount static files
app.mount("/static", StaticFiles(directory=Path(__file__).parent.parent / "static"), name="static")

TRANSCRIPTION_SERVICE_URL_PLACEHOLDER = "__TRANSCRIPTION_SERVICE_URL_PLACEHOLDER__"

@app.get("/", response_class=HTMLResponse)
async def read_root():
    transcription_service_url = os.getenv(
        "TRANSCRIPTION_SERVICE_URL",
        "https://andenate-transcription-service.hf.space/transcribe" # Default fallback URL
    )
    
    index_html_path = Path(__file__).parent.parent / "static" / "index.html"
    with open(index_html_path, "r") as f:
        html_content = f.read()
    
    # Replace the placeholder with the actual URL
    html_content = html_content.replace(TRANSCRIPTION_SERVICE_URL_PLACEHOLDER, transcription_service_url)
    
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
