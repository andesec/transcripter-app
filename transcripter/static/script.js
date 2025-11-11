document.addEventListener('DOMContentLoaded', () => {
    const audioFile = document.getElementById('audioFile');
    const categorySelect = document.getElementById('category');
    const transcribeButton = document.getElementById('transcribeButton');
    const summarizeButton = document.getElementById('summarizeButton');
    const resetButton = document.getElementById('resetButton');
    const transcriptionOutput = document.getElementById('transcriptionOutput');
    const summaryOutput = document.getElementById('summaryOutput');
    const notesOutput = document.getElementById('notesOutput');
    const notificationArea = document.getElementById('notificationArea'); // Assuming this element exists in index.html

    let transcribedText = ""; // To store transcription temporarily

    // --- Helper Functions ---
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notificationArea.innerHTML = ''; // Clear previous notifications
        notificationArea.appendChild(notification);

        // Show and then hide after a few seconds
        setTimeout(() => {
            notification.classList.add('show');
        }, 10); // Small delay to trigger CSS transition

        setTimeout(() => {
            notification.classList.remove('show');
            notification.addEventListener('transitionend', () => notification.remove(), { once: true });
        }, 5000);
    }

    function resetUI() {
        categorySelect.value = 'meeting';
        transcribeButton.disabled = true;
        summarizeButton.disabled = true;
        transcriptionOutput.value = '';
        summaryOutput.innerHTML = '';
        notesOutput.innerHTML = '';
        transcribedText = "";
        showNotification('UI has been reset.', 'info');
    }

    // --- Event Listeners ---
    audioFile.addEventListener('change', () => {
        const file = audioFile.files[0];
        if (file) {
            // Client-side file type validation
            const allowedTypes = ['audio/wav', 'audio/mpeg', 'audio/x-m4a', 'audio/mp4', 'audio/vnd.wav', 'audio/aac']; // mp3 is audio/mpeg, m4a can be audio/x-m4a or audio/mp4, also added audio/vnd.wav for broader WAV support and audio/aac for m4a
            if (!allowedTypes.includes(file.type)) {
                showNotification('Invalid file type. Please upload WAV, MP3, or M4A.', 'error');
                audioFile.value = ''; // Clear selected file
                transcribeButton.disabled = true;
                return;
            }

            // Client-side file size validation (10 MB limit)
            const maxSizeMB = 10;
            if (file.size > maxSizeMB * 1024 * 1024) {
                showNotification(`File size exceeds ${maxSizeMB} MB limit.`, 'error');
                audioFile.value = ''; // Clear selected file
                transcribeButton.disabled = true;
                return;
            }

            transcribeButton.disabled = false;
        } else {
            transcribeButton.disabled = true;
        }
            transcriptionOutput.value = '';
            summaryOutput.innerHTML = '';
            notesOutput.innerHTML = '';
            transcribedText = "";
    });

    transcribeButton.addEventListener('click', async () => {
        const file = audioFile.files[0];
        if (!file) {
            showNotification('Please select an audio file first.', 'error');
            return;
        }

        transcribeButton.disabled = true;
        summarizeButton.disabled = true;
        transcriptionOutput.value = 'Transcribing... Please wait.';
        summaryOutput.innerHTML = '';
        notesOutput.innerHTML = '';
        showNotification('Transcription started...', 'info');

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(window.TRANSCRIPTION_SERVICE_URL, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            transcribedText = data.transcription;
            transcriptionOutput.value = transcribedText;
            summarizeButton.disabled = false;
            showNotification('Transcription complete!', 'success');

        } catch (error) {
            console.error('Transcription error:', error);
            transcriptionOutput.value = `Error during transcription: ${error.message}`;
            showNotification(`Error during transcription: ${error.message}`, 'error');
        } finally {
            transcribeButton.disabled = false;
        }
    });

    summarizeButton.addEventListener('click', async () => {
        if (!transcribedText) {
            showNotification('Please transcribe audio first.', 'error');
            return;
        }

        summarizeButton.disabled = true;
        summaryOutput.innerHTML = 'Generating summary... Please wait.';
        notesOutput.innerHTML = 'Generating notes... Please wait.';
        showNotification('Generating summary and notes...', 'info');

        const category = categorySelect.value;
        const formData = new FormData();
        formData.append('transcribed_text', transcribedText);
        formData.append('category', category);

        try {
            const response = await fetch('/summarize_and_notes', {
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
            showNotification('Summary and notes generated!', 'success');

        } catch (error) {
            console.error('Summarization error:', error);
            summaryOutput.innerHTML = `Error during summarization: ${error.message}`;
            notesOutput.innerHTML = '';
            showNotification(`Error during summarization: ${error.message}`, 'error');
        } finally {
            summarizeButton.disabled = false;
        }
    });

    resetButton.addEventListener('click', () => {
        resetUI();
    });

    // Initial state
    resetUI();
});