import subprocess
import threading
import os
import sys

# Get the absolute path to the project root directory
project_root = os.path.dirname(os.path.abspath(__file__))

def run_fastapi():
    cmd = [
        sys.executable, "-m", "uvicorn",
        "ai_tutor_platform.main_api:app",
        "--port", "8000",
        "--reload"
    ]
    env = os.environ.copy()
    env['PYTHONPATH'] = project_root + os.pathsep + env.get('PYTHONPATH', '')
    print(f"Starting FastAPI with PYTHONPATH: {env['PYTHONPATH']}")
    subprocess.run(cmd, env=env)

def run_streamlit():
    # *** CRUCIAL CHANGE HERE ***
    # Run streamlit as a module, pointing to the 'ai_tutor_platform' package
    # and its 'main.py' file. This makes Python resolve imports correctly.
    cmd = [
        sys.executable, "-m", "streamlit",
        "run",
        # Pass the module path relative to the PYTHONPATH
        "ai_tutor_platform.main" # This tells streamlit to look for main.py inside ai_tutor_platform package
        # Optional Streamlit server options
        # "--server.port", "8501",
        # "--server.enableCORS", "false",
        # "--server.enableXsrfProtection", "false"
    ]
    env = os.environ.copy()
    env['PYTHONPATH'] = project_root + os.pathsep + env.get('PYTHONPATH', '')
    print(f"Starting Streamlit with PYTHONPATH: {env['PYTHONPATH']}")
    subprocess.run(cmd, env=env)

if __name__ == "__main__":
    print(f"Project root detected: {project_root}")

    # Ensure the current working directory is the project root for consistent path resolution
    os.chdir(project_root)
    print(f"Changed current working directory to: {os.getcwd()}")

    t1 = threading.Thread(target=run_fastapi)
    t2 = threading.Thread(target=run_streamlit)

    t1.start()
    t2.start()

    t1.join()
    t2.join()