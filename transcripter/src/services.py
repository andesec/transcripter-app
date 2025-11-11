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

def configure_services():
    """Checks and configures the external services."""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        logger.error("GEMINI_API_KEY environment variable not set or is a placeholder.")
        return False
    
    genai.configure(api_key=GEMINI_API_KEY)
    return True

# --- Service Functions ---
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
