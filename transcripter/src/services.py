import os
import requests
import google.generativeai as genai
from fastapi import UploadFile, HTTPException
from pydantic import ValidationError
import logging
import json

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
HUGGING_FACE_API_URL = os.getenv("HUGGING_FACE_API_URL")

def configure_services():
    """Checks and configures the external services."""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        logger.error("GEMINI_API_KEY environment variable not set or is a placeholder.")
        return False
    if not HUGGING_FACE_API_URL or HUGGING_FACE_API_URL == "YOUR_HUGGING_FACE_API_URL_HERE":
        logger.error("HUGGING_FACE_API_URL environment variable not set or is a placeholder.")
        return False
    
    genai.configure(api_key=GEMINI_API_KEY)
    return True

# --- Service Functions ---
def transcribe_audio_with_huggingface(audio_file: UploadFile):
    """Sends audio file to Hugging Face for transcription."""
    if not HUGGING_FACE_API_URL or HUGGING_FACE_API_URL == "YOUR_HUGGING_FACE_API_URL_HERE":
        raise HTTPException(status_code=500, detail="Hugging Face API URL is not configured.")
    try:
        files = {'file': (audio_file.filename, audio_file.file, audio_file.content_type)}
        logger.info(f"Sending audio file to Hugging Face API: {audio_file.filename}")
        response = requests.post(HUGGING_FACE_API_URL, files=files, timeout=120)
        response.raise_for_status()
        logger.info("Received successful response from Hugging Face API.")
        return response.json().get("text")
    except requests.exceptions.Timeout:
        logger.error("Request to Hugging Face API timed out.")
        raise HTTPException(status_code=504, detail="Request to transcription service timed out.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Hugging Face API: {e}")
        raise HTTPException(status_code=502, detail=f"Error communicating with transcription service: {e}")

def generate_summary_and_notes(transcription: str, category: str):
    """Generates summary and notes using the Gemini API."""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        raise HTTPException(status_code=500, detail="Gemini API Key is not configured.")
    
    model = genai.GenerativeModel('gemini-pro')
    prompt = f"""
    You are an expert in summarizing and taking notes.
    Given the following transcription from a '{category}', please generate a concise summary and a list of key notes.
    The output MUST be a valid JSON object with two keys: "summary" (a string) and "notes" (a list of strings).

    Transcription:
    {transcription}
    """
    try:
        logger.info("Sending request to Gemini API.")
        response = model.generate_content(prompt)
        
        cleaned_response = response.text.strip().replace('`', '')
        if cleaned_response.startswith('json'):
            cleaned_response = cleaned_response[4:]

        logger.info("Received response from Gemini API.")
        data = json.loads(cleaned_response)
        
        if "summary" not in data or "notes" not in data or not isinstance(data["notes"], list):
            raise ValueError("Invalid JSON structure from Gemini API.")
            
        return data.get("summary"), data.get("notes")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from Gemini API response: {e}")
        logger.error(f"Gemini response text: {response.text}")
        raise HTTPException(status_code=500, detail="Failed to parse summary from AI service.")
    except (ValueError, ValidationError) as e:
        logger.error(f"Invalid data structure from Gemini API: {e}")
        raise HTTPException(status_code=500, detail=f"Received invalid data structure from AI service: {e}")
    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred with the AI service: {e}")
