import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Thư mục gốc dự án
ROOT = Path(__file__).resolve().parents[2]

# Load file .env (tìm trong thư mục dự án hoặc thư mục cha)
env_path = ROOT / ".env"
if not env_path.exists() and (ROOT.parent / ".env").exists():
    env_path = ROOT.parent / ".env"
load_dotenv(env_path, override=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
JINA_API_KEY = os.getenv("JINA_API_KEY", "").strip()

# Đường dẫn dữ liệu bài giảng & chỉ mục
DATA_DIR = ROOT / "data"
INDEX_PATH = DATA_DIR / "index.json"

# Cấu hình LLM & Agent
MODEL = os.getenv("LLM_MODEL", "qwen/qwen3.8-27b")
MAX_STEPS = 10
OBS_MAX_CHARS = 1500

# Trọng số hybrid search
TOP_K = 3
W_BM25 = 0.3
W_VECTOR = 0.7
SEARCH_MODE = os.getenv("SEARCH_MODE", "hybrid")

# Ngưỡng điểm tối thiểu để lọc bớt kết quả không liên quan
MIN_SCORE = {
    "dense": float(os.getenv("MIN_SCORE_DENSE", "0.45")),
    "hybrid": float(os.getenv("MIN_SCORE_HYBRID", "0.30")),
    "bm25": float(os.getenv("MIN_SCORE_BM25", "1.50")),
}

def check_keys() -> None:
    if not GROQ_API_KEY:
        sys.exit("Thiếu GROQ_API_KEY trong file .env")
