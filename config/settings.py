import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

MIFY_API_KEY = os.getenv("MIFY_API_KEY", "")

# 支持多个知识库，逗号分隔
_dataset_ids_raw = os.getenv("MIFY_DATASET_IDS", os.getenv("MIFY_DATASET_ID", ""))
MIFY_DATASET_IDS: list[str] = [s.strip() for s in _dataset_ids_raw.split(",") if s.strip()]
# 向后兼容：取第一个作为默认
MIFY_DATASET_ID = MIFY_DATASET_IDS[0] if MIFY_DATASET_IDS else ""
MIFY_TOP_K = int(os.getenv("MIFY_TOP_K", "5"))
MIFY_BASE_URL = "https://service.mify.mioffice.cn/api/v1/datasets"

# MCP Transport
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "stdio")
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "8003"))

# RAG-Fusion
MIFY_RRF_K = int(os.getenv("MIFY_RRF_K", "60"))
MIFY_NUM_VARIANTS = int(os.getenv("MIFY_NUM_VARIANTS", "5"))
MIFY_RETRIEVE_WORKERS = int(os.getenv("MIFY_RETRIEVE_WORKERS", "3"))

# LLM 客户端（通过 Mify 代理调用）
LLM_API_KEY = os.getenv("LLM_API_KEY", MIFY_API_KEY)
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://service.mify.mioffice.cn/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "mimo-v2.5-pro")
