import subprocess
import time
import webbrowser


python_path = r"C:\Users\lucca\Documents\GitHub\projeto-ciencia-tecnologia\venv\Scripts\python.exe"


backend = subprocess.Popen(
    [
        python_path,
        "-m",
        "uvicorn",
        "main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000"
    ],
    cwd=r"C:\Users\lucca\Documents\GitHub\projeto-ciencia-tecnologia"
)


time.sleep(3)


webbrowser.open(
    "http://localhost:8000"
)


backend.wait()