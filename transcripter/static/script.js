document.addEventListener('DOMContentLoaded', () => {
    const audioFile = document.getElementById('audioFile');
    const categorySelect = document.getElementById('category');
    const transcribeButton = document.getElementById('transcribeButton');
    const summarizeButton = document.getElementById('summarizeButton');
    const resetButton = document.getElementById('resetButton');
    const transcriptionOutput = document.getElementById('transcriptionOutput');
    const summaryOutput = document.getElementById('summaryOutput');
    const notesOutput = document.getElementById('notesOutput');

    let transcribedText = ""; // To store transcription temporarily

    // --- Event Listeners ---
    audioFile.addEventListener('change', () => {
        // Enable/disable transcribe button based on file selection
        transcribeButton.disabled = !audioFile.files.length;
        resetUI(); // Reset UI when a new file is selected
    });

    transcribeButton.addEventListener('click', async () => {
        const file = audioFile.files[0];
        if (!file) {
            alert('Please select an audio file first.');
            return;
        }

        transcribeButton.disabled = true;
        summarizeButton.disabled = true;
        transcriptionOutput.value = 'Transcribing...';
        summaryOutput.innerHTML = '';
        notesOutput.innerHTML = '';

        const formData = new FormData();
        formData.append('file', file); // Key 'file' as per previous fix

        try {
            const response = await fetch('https://andenate-transcription-service.hf.space/transcribe', {
                method: 'POST',
                body: formData,
                // No 'Content-Type' header needed for FormData, browser sets it
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            transcribedText = data.transcription;
            transcriptionOutput.value = transcribedText;
            summarizeButton.disabled = false; // Enable summarize button after transcription
            alert('Transcription complete!');

        } catch (error) {
            console.error('Transcription error:', error);
            transcriptionOutput.value = `Error during transcription: ${error.message}`;
            alert(`Error during transcription: ${error.message}`);
        } finally {
            transcribeButton.disabled = false;
        }
    });

    summarizeButton.addEventListener('click', async () => {
        if (!transcribedText) {
            alert('Please transcribe audio first.');
            return;
        }

        summarizeButton.disabled = true;
        summaryOutput.innerHTML = 'Generating summary...';
        notesOutput.innerHTML = 'Generating notes...';

        const category = categorySelect.value;
        const formData = new FormData();
        formData.append('transcribed_text', transcribedText);
        formData.append('category', category);

        try {
            const response = await fetch('/summarize_and_notes', { // Call local FastAPI
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            summaryOutput.innerHTML = data.summary;
            notesOutput.innerHTML = data.notes.map(note => `<li>${note}</li>`).join('');
            alert('Summary and notes generated!');

        } catch (error) {
            console.error('Summarization error:', error);
            summaryOutput.innerHTML = `Error during summarization: ${error.message}`;
            notesOutput.innerHTML = '';
            alert(`Error during summarization: ${error.message}`);
        } finally {
            summarizeButton.disabled = false;
        }
    });

    resetButton.addEventListener('click', () => {
        resetUI();
        alert('UI has been reset.');
    });

    function resetUI() {
        audioFile.value = ''; // Clear file input
        categorySelect.value = 'meeting';
        transcribeButton.disabled = true;
        summarizeButton.disabled = true;
        transcriptionOutput.value = '';
        summaryOutput.innerHTML = '';
        notesOutput.innerHTML = '';
        transcribedText = "";
    }

    // Initial state
    resetUI();
});
