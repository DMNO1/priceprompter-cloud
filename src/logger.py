"""
PricePrompter Cloud - 日志管理模块
"""
import logging
import os
import sys
from datetime import datetime
from typing import Optional


class PricePrompterLogger:
    """统一的日志管理器"""
    
    def __init__(self, name: str = "priceprompter", log_file: str = "./logs/priceprompter.log", level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # 清除已有处理器
        self.logger.handlers = []
        
        # 确保日志目录存在
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # 文件处理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, level.upper()))
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        # 设置Windows控制台编码
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        self.logger.addHandler(console_handler)
    
    def info(self, message: str):
        """记录信息日志"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """记录警告日志"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """记录错误日志"""
        self.logger.error(message)
    
    def debug(self, message: str):
        """记录调试日志"""
        self.logger.debug(message)
    
    def critical(self, message: str):
        """记录严重错误日志"""
        self.logger.critical(message)


# 全局日志实例
_logger: Optional[PricePrompterLogger] = None


def get_logger(log_file: str = "./logs/priceprompter.log", level: str = "INFO") -> PricePrompterLogger:
    """获取日志实例"""
    global _logger
    if _logger is None:
        _logger = PricePrompterLogger(log_file=log_file, level=level)
    return _logger


def log_execution_start(task_name: str, log_file: str = "./logs/execution.log"):
    """记录任务开始"""
    logger = get_logger(log_file=log_file)
    logger.info(f"=" * 60)
    logger.info(f"任务开始: {task_name}")
    logger.info(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return logger


def log_execution_end(task_name: str, success: bool, message: str = "", log_file: str = "./logs/execution.log"):
    """记录任务结束"""
    logger = get_logger(log_file=log_file)
    status = "成功" if success else "失败"
    logger.info(f"任务结束: {task_name} - {status}")
    if message:
        logger.info(f"结果: {message}")
    logger.info(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"=" * 60)
