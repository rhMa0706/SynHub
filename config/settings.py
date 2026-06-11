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

# 知识库领域映射：dataset_id -> 领域信息
# 用于搜索前的领域路由，判断查询该搜哪个库
DOMAIN_MAP = {
    "b26e181e-fc6c-4371-8a11-3e19580afd85": {
        "name": "SDC 知识库",
        "keywords": ["sdc", "constraint", "timing", "clock", "cts", "uncertainty", "latency",
                     "input_delay", "output_delay", "false_path", "multicycle", "set_max",
                     "set_min", "驱动", "约束", "时序约束", "设计约束"],
    },
    "fa43ebb5-0333-4e8f-9351-33952daafaec": {
        "name": "memory 领域",
        "keywords": ["memory", "mem", "sram", "rom", "dram", "register", "reg", "flip_flop",
                     "ff", "latch", "锁存器", "触发器", "存储器", "mem_wrapper", "spyglass",
                     "mick", "vclint", "vprune", "defck", "paramchk", "rdc", "bw", "broadway",
                     "lauda", "luada", "libset", "wrapper"],
    },
    "99d29d7f-bd5a-491d-b34f-3cb1cef5eac7": {
        "name": "低功耗领域",
        "keywords": ["low_power", "upf", "clp", "power", "isolation", "level_shifter",
                     "power_domain", "power_switch", "always_on", "aon", "retention",
                     "功耗", "低功耗", "隔离", "电平转换", "电源域", "电源开关",
                     "crossover", "crossing", "iso", "lsh", "pd", "psw"],
    },
}

# MCP Transport
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "stdio")
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "8003"))

# RAG-Fusion
MIFY_RRF_K = int(os.getenv("MIFY_RRF_K", "40"))
MIFY_NUM_VARIANTS = int(os.getenv("MIFY_NUM_VARIANTS", "5"))
MIFY_RETRIEVE_WORKERS = int(os.getenv("MIFY_RETRIEVE_WORKERS", "5"))

# LLM 客户端（通过 Mify 代理调用）
LLM_API_KEY = os.getenv("LLM_API_KEY", MIFY_API_KEY)
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://service.mify.mioffice.cn/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "mimo-v2.5-pro")

# 飞书配置（用于反馈写入多维表格）
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")
BITABLE_APP_TOKEN = os.getenv("BITABLE_APP_TOKEN", "")
BITABLE_TABLE_ID = os.getenv("BITABLE_TABLE_ID", "")
