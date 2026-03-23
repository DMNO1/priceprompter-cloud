"""
PricePrompter Cloud - AI成本优化工具
"""

__version__ = "1.0.0"
__author__ = "PricePrompter Team"

from .config import load_config, AppConfig, MODELS
from .logger import get_logger, log_execution_start, log_execution_end
from .cache_manager import SemanticCacheManager, CacheEntry
from .smart_router import SmartRouter, RoutingDecision
from .slop_detector import SlopDetector, SlopAnalysisResult
from .proxy_service import PricePrompterProxy, ProxyResponse

__all__ = [
    'load_config',
    'AppConfig',
    'MODELS',
    'get_logger',
    'log_execution_start',
    'log_execution_end',
    'SemanticCacheManager',
    'CacheEntry',
    'SmartRouter',
    'RoutingDecision',
    'SlopDetector',
    'SlopAnalysisResult',
    'PricePrompterProxy',
    'ProxyResponse',
]
