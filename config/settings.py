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
    # ---- SDC / 时序约束 ----
    "b26e181e-fc6c-4371-8a11-3e19580afd85": {
        "name": "SDC 知识库",
        "keywords": ["sdc", "constraint", "input_delay", "output_delay", "false_path",
                     "multicycle", "set_max", "set_min", "驱动", "约束", "设计约束"],
    },
    "dce185be-b1c9-4a86-bd4d-7e6d43346255": {
        "name": "SDC Part2",
        "keywords": ["sdc", "constraint", "input_delay", "output_delay", "false_path",
                     "multicycle", "set_max", "set_min", "驱动", "约束", "设计约束",
                     "case_analysis", "clock_group", "generated_clock"],
    },
    # ---- 时序分析 ----
    "bb4d9587-8010-46b1-b8cf-8798b0c6a0eb": {
        "name": "时序分析",
        "keywords": ["timing", "sta", "primetime", "pt", "slack", "setup", "hold", "clock",
                     "cts", "uncertainty", "latency", "skew", "pte", "uite", "rc", "sel",
                     "lnk", "mc", "时序", "时序分析", "时序检查", "时钟", "建立时间", "保持时间"],
    },
    # ---- Memory ----
    "fa43ebb5-0333-4e8f-9351-33952daafaec": {
        "name": "Memory Part1",
        "keywords": ["memory", "mem", "sram", "rom", "dram", "register", "reg", "flip_flop",
                     "ff", "latch", "锁存器", "触发器", "存储器", "mem_wrapper", "spyglass",
                     "mick", "vclint", "vprune", "defck", "paramchk", "rdc", "bw", "broadway",
                     "lauda", "luada", "libset", "wrapper"],
    },
    "52dfe94f-507e-4cff-a172-6d86d90bc582": {
        "name": "Memory Part2",
        "keywords": ["memory", "mem", "sram", "rom", "dram", "register", "reg", "flip_flop",
                     "ff", "latch", "锁存器", "触发器", "存储器", "mem_wrapper", "spyglass",
                     "mick", "vclint", "vprune", "defck", "paramchk", "rdc", "bw", "broadway",
                     "lauda", "luada", "libset", "wrapper", "mem2reg", "mcp2", "mcp3"],
    },
    # ---- 低功耗 ----
    "99d29d7f-bd5a-491d-b34f-3cb1cef5eac7": {
        "name": "低功耗领域",
        "keywords": ["low_power", "upf", "clp", "power", "isolation", "level_shifter",
                     "power_domain", "power_switch", "always_on", "aon", "retention",
                     "功耗", "低功耗", "隔离", "电平转换", "电源域", "电源开关",
                     "crossover", "crossing", "iso", "lsh", "pd", "psw"],
    },
    "e7c1e746-e1d0-4bb3-b378-d36e6fe08291": {
        "name": "低功耗 Part 2",
        "keywords": ["low_power", "upf", "clp", "power", "isolation", "level_shifter",
                     "power_domain", "power_switch", "always_on", "aon", "retention",
                     "功耗", "低功耗", "隔离", "电平转换", "电源域", "电源开关",
                     "crossover", "crossing", "iso", "lsh", "pd", "psw",
                     "pst", "mtcmos", "power_state"],
    },
    # ---- 后端 / 物理实现 ----
    "5c906757-2747-4718-9522-bd17852035ab": {
        "name": "DFT",
        "keywords": ["dft", "atpg", "scan", "scan_chain", "bist", "mbist", "jtag", "tap",
                     "testability", "compression", "occ", "test_mode", "扫描链", "可测性"],
    },
    "39a13266-3e70-43bb-9e38-32c7ff6e5eea": {
        "name": "PPA",
        "keywords": ["ppa", "qor", "area", "power", "performance", "utilization",
                     "congestion", "面积", "性能", "优化", "density"],
    },
    "fb33c54a-42ea-45ae-8b1a-668d6c71d8c4": {
        "name": "LEC",
        "keywords": ["lec", "formality", "conformal", "equivalence", "等价性检查",
                     "逻辑等价", "formal_verification", "eco_verify"],
    },
    "acc7250a-026f-437f-86bc-28c45f2b383f": {
        "name": "Signoff",
        "keywords": ["signoff", "sign_off", "sign-off", "release", "交付检查", "签核"],
    },
    "82a67a2c-f83c-41be-9fa8-d8646bdad631": {
        "name": "穿线",
        "keywords": ["穿线", "feedthrough", "feed_through", "port_punch", "打洞", "穿孔"],
    },
    # ---- 综合 / 项目 / 流程类 ----
    "2fb30098-e238-4daa-992c-d7b9d735e87c": {
        "name": "综合策略",
        "keywords": ["synthesis", "genus", "dc", "design_compiler", "综合", "综合策略",
                     "综合流程", "综合脚本", "compile", "elaborate", "ungroup", "flatten",
                     "exc", "gca", "cpi"],
    },
    "86fdcf82-e017-4069-bcbc-b38565f3ba46": {
        "name": "项目经验",
        "keywords": ["项目经验", "项目总结", "经验", "案例", "case_study", "lessons",
                     "踩坑", "avoid", "pitfall"],
    },
    "a7851884-20e8-47f8-a46f-2492de614646": {
        "name": "交付",
        "keywords": ["交付", "delivery", "release", "netlist", "gds", "handoff",
                     "交付清单", "交付规范", "交付流程"],
    },
    "e4821655-d759-41ce-ad6d-7d09ee6de943": {
        "name": "复盘",
        "keywords": ["复盘", "review", "retro", "retrospective", "postmortem",
                     "问题复盘", "项目复盘", "周报", "月报"],
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
