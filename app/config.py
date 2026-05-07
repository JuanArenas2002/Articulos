import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

DEBUG = os.getenv("DEBUG", "False") == "True"

# ── URLs de microservicios externos ─────────────────────────────────────────
REVISTA_SERVICE_URL = os.getenv("REVISTA_SERVICE_URL", "http://localhost:8002")
