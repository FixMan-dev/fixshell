import os

# FixShell Configuration
VERSION = "0.1.2"
DEBUG = os.getenv("FIXSHELL_DEBUG", "0") == "1"

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")

# Execution Defaults
MAX_RETRIES = 3
DRY_RUN_DEFAULT = False

# AI Settings (Optional/Roadmap)
LLM_MODEL = "ollama/llama3"
AI_EVIDENCE_THRESHOLD = 0.6
