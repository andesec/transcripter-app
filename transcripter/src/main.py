import multiprocessing
import uvicorn
import subprocess
import os
from .services import configure_services
from .api import app as fastapi_app

def run_fastapi():
    """Runs the FastAPI application."""
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000, log_level="info")

def run_streamlit():
    """Runs the Streamlit application."""
    os.environ["API_URL"] = "http://localhost:8000"
    command = [
        "streamlit",
        "run",
        "src/ui.py",
        "--server.port=80",
        "--server.address=0.0.0.0"
    ]
    subprocess.run(command)

if __name__ == "__main__":
    # Check and configure services. The services will log errors if keys are missing.
    configure_services()

    # Create and start the processes
    fastapi_process = multiprocessing.Process(target=run_fastapi)
    streamlit_process = multiprocessing.Process(target=run_streamlit)

    fastapi_process.start()
    streamlit_process.start()

    fastapi_process.join()
    streamlit_process.join()
