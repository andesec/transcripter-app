from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from .models import TranscriptionResponse
from .services import transcribe_audio_with_huggingface, generate_summary_and_notes

app = FastAPI(title="Transcriber API")

@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_and_summarize(
    audio_file: UploadFile = File(...),
    category: str = Form(...)
):
    """
    Receives an audio file and a category, transcribes the audio,
    and generates a summary and notes.
    """
    if not audio_file.content_type or not audio_file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an audio file.")

    transcription = transcribe_audio_with_huggingface(audio_file)
    if not transcription:
        raise HTTPException(status_code=422, detail="Transcription service returned no content.")

    summary, notes = generate_summary_and_notes(transcription, category)
    if not summary or not notes:
        raise HTTPException(status_code=422, detail="AI service failed to generate summary and notes.")

    return TranscriptionResponse(
        transcription=transcription,
        summary=summary,
        notes=notes
    )

@app.get("/")
def read_root():
    return {"message": "Welcome to the Transcriber API!"}
