import streamlit as st
import requests
import os

# --- Page Configuration ---
st.set_page_config(
    page_title="Transcriber & Summarizer",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Configuration ---
API_URL = os.getenv("API_URL", "http://localhost:8000")
TRANSCRIPTION_SERVICE_URL = os.getenv("TRANSCRIPTION_SERVICE_URL", f"{API_URL}/transcribe")

# --- UI Components ---
def display_error(message: str, error: Exception):
    """Displays a user-friendly error message."""
    st.error(f"{message}. Please try again.")
    with st.expander("See error details"):
        st.exception(error)

def display_results(data: dict):
    """Displays the transcription, summary, and notes."""
    st.subheader("📝 Transcription")
    st.text_area("Full transcription text", data["transcription"], height=250)
    
    st.subheader("✨ AI-Generated Summary")
    st.markdown(data["summary"])
    
    st.subheader("📌 Key Notes")
    for note in data["notes"]:
        st.markdown(f"- {note}")

# --- Main App ---
def main():
    """Main function to run the Streamlit app."""
    st.title("Transcriber & Summarizer")
    st.markdown(
        "Transform your audio into text, summaries, and notes. "
        "Powered by Hugging Face and Gemini."
    )

    with st.sidebar:
        st.header("Controls")
        uploaded_file = st.file_uploader(
            "Upload your audio file",
            type=["wav", "mp3", "m4a"]
        )
        category = st.selectbox(
            "Select the audio category",
            ("meeting", "conversation", "study lecture", "fiction", "think aloud"),
            help="Select the category that best describes your audio to get a better summary."
        )
        submit_button = st.button("Generate Insights", type="primary")

        st.markdown("---")
        if st.button("Reset"):
            st.session_state.clear()
            st.experimental_rerun()

    if submit_button:
        if uploaded_file is not None:
            with st.spinner("🚀 Launching the AI magic... Please wait."):
                try:
                    files = {"audio_file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                    params = {"category": category}
                    
                    st.info("Step 1/3: Uploading audio file...")
                    response = requests.post(TRANSCRIPTION_SERVICE_URL, files=files, data=params, timeout=300)
                    
                    st.info("Step 2/3: Analyzing response...")
                    response.raise_for_status()
                    
                    st.info("Step 3/3: Generating results...")
                    data = response.json()
                    
                    st.success("✅ Success! Here are your results.")
                    st.toast("Processing complete!", icon="🎉")
                    display_results(data)

                except requests.exceptions.Timeout as e:
                    display_error("The request timed out after 5 minutes", e)
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 422:
                        display_error("The AI service failed to process the content", e)
                    else:
                        display_error(f"A server error occurred (Code: {e.response.status_code})", e)
                except requests.exceptions.RequestException as e:
                    display_error("Failed to connect to the backend service", e)
                except Exception as e:
                    display_error("An unexpected error occurred", e)
        else:
            st.warning("Please upload an audio file first.")
            st.toast("No file selected.", icon="⚠️")

if __name__ == "__main__":
    main()
