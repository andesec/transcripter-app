from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from .models import TranscriptionResponse
from .services import transcribe_audio_with_huggingface, generate_summary_and_notes

app = FastAPI(title="Transcriber API")

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

@app.get("/")
def read_root():
    return {"message": "Welcome to the Transcriber API!"}
