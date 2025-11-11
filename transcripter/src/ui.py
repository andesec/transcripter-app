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

    # Initialize session state variables
    if "uploaded_file" not in st.session_state:
        st.session_state.uploaded_file = None
    if "transcription" not in st.session_state:
        st.session_state.transcription = ""
    if "category" not in st.session_state:
        st.session_state.category = "meeting"
    if "results" not in st.session_state:
        st.session_state.results = None

    with st.sidebar:
        st.header("Controls")
        st.session_state.uploaded_file = st.file_uploader(
            "Upload your audio file",
            type=["wav", "mp3", "m4a"]
        )
        st.session_state.category = st.selectbox(
            "Select the audio category",
            ("meeting", "conversation", "study lecture", "fiction", "think aloud"),
            help="Select the category that best describes your audio to get a better summary."
        )

        transcribe_button = st.button("Transcribe Audio", type="primary", disabled=st.session_state.uploaded_file is None)
        summarize_button = st.button("Generate Summary & Notes", disabled=st.session_state.transcription == "")

        st.markdown("---")
        if st.button("Reset"):
            st.session_state.clear()
            st.experimental_rerun()

    if transcribe_button and st.session_state.uploaded_file is not None:
        with st.spinner("🚀 Launching the AI magic... Please wait."):
            try:
                files = {"file": (st.session_state.uploaded_file.name, st.session_state.uploaded_file, st.session_state.uploaded_file.type)}
                
                st.info("Step 1/3: Uploading audio file and transcribing...")
                
                # Always call the configured TRANSCRIPTION_SERVICE_URL for transcription
                response = requests.post(TRANSCRIPTION_SERVICE_URL, files=files, timeout=300)
                
                response.raise_for_status()
                
                st.info("Step 2/3: Analyzing response...")
                data = response.json()
                
                # Assume external service always returns transcription
                st.session_state.transcription = data.get("transcription", "")
                st.success("✅ Transcription complete! Now generate summary and notes.")
                
                st.toast("Processing complete!", icon="🎉")

            except requests.exceptions.Timeout as e:
                display_error("The request timed out after 5 minutes", e)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 422:
                    display_error("The transcription service failed to process the content", e)
                else:
                    display_error(f"A server error occurred (Code: {e.response.status_code})", e)
            except requests.exceptions.RequestException as e:
                display_error("Failed to connect to the transcription service", e)
            except Exception as e:
                display_error("An unexpected error occurred", e)

    if summarize_button and st.session_state.transcription != "":
        with st.spinner("✨ Generating summary and notes..."):
            try:
                st.info("Step 3/3: Generating summary and notes...")
                response = requests.post(
                    f"{API_URL}/summarize_and_notes",
                    data={"transcribed_text": st.session_state.transcription, "category": st.session_state.category},
                    timeout=300
                )
                response.raise_for_status()
                st.session_state.results = response.json()
                st.success("✅ Summary and notes complete!")
                st.toast("Processing complete!", icon="🎉")
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

    if st.session_state.results:
        display_results(st.session_state.results)
    elif st.session_state.transcription:
        st.subheader("📝 Transcription")
        st.text_area("Full transcription text", st.session_state.transcription, height=250)

if __name__ == "__main__":
    main()
