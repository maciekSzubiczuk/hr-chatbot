from pathlib import Path
from dotenv import load_dotenv
import os

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL   = os.getenv("GROQ_MODEL", "llama3-70b-8192")