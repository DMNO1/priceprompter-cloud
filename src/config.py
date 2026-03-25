"""
PricePrompter Cloud - 配置管理模块
"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelConfig:
    """AI模型配置"""
    id: str
    provider: str
    cost_per_1k_input: float
    cost_per_1k_output: float
    context_window: int
    strengths: list


@dataclass
class AppConfig:
    """应用配置"""
    # 服务配置
    host: str = "0.0.0.0"
    port: int = 3000
    debug: bool = False
    
    # 数据库配置
    database_url: str = "sqlite:///./priceprompter.db"
    chroma_url: str = "http://localhost:8000"
    redis_url: str = "redis://localhost:6379"
    
    # API密钥 (从环境变量读取)
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    
    # 缓存配置
    cache_ttl: int = 7 * 24 * 60 * 60  # 7天
    similarity_threshold: float = 0.95
    
    # 日志配置
    log_level: str = "INFO"
    log_file: str = "./logs/priceprompter.log"


def load_config() -> AppConfig:
    """加载配置"""
    # Detect serverless environment
    is_serverless = os.getenv("PRICEPROMPTER_SERVERLESS") == "1" or os.getenv("VERCEL") == "1"
    db_url = os.getenv("DATABASE_URL", "sqlite:///./priceprompter.db")
    if is_serverless:
        db_url = "sqlite:///:memory:"
    return AppConfig(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "3000")),
        debug=os.getenv("DEBUG", "false").lower() == "true",
        database_url=db_url,
        chroma_url=os.getenv("CHROMA_URL", "http://localhost:8000"),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        cache_ttl=int(os.getenv("CACHE_TTL", str(7 * 24 * 60 * 60))),
        similarity_threshold=float(os.getenv("SIMILARITY_THRESHOLD", "0.95")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_file=os.getenv("LOG_FILE", "./logs/priceprompter.log"),
    )


# 预定义模型配置
MODELS = [
    ModelConfig(
        id="gpt-4-turbo",
        provider="openai",
        cost_per_1k_input=0.01,
        cost_per_1k_output=0.03,
        context_window=128000,
        strengths=["complex", "coding", "analysis"]
    ),
    ModelConfig(
        id="gpt-3.5-turbo",
        provider="openai",
        cost_per_1k_input=0.0005,
        cost_per_1k_output=0.0015,
        context_window=16385,
        strengths=["simple", "fast", "cheap"]
    ),
    ModelConfig(
        id="claude-3-opus",
        provider="anthropic",
        cost_per_1k_input=0.015,
        cost_per_1k_output=0.075,
        context_window=200000,
        strengths=["long-context", "analysis", "writing"]
    ),
    ModelConfig(
        id="claude-3-haiku",
        provider="anthropic",
        cost_per_1k_input=0.00025,
        cost_per_1k_output=0.00125,
        context_window=200000,
        strengths=["fast", "cheap", "simple"]
    ),
]
