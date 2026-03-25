#!/usr/bin/env python3
"""
PricePrompter Cloud - Vercel WSGI adapter
使Flask app兼容Vercel Python runtime
"""
import sys
import os

# 确保src在路径中
sys.path.insert(0, os.path.dirname(__file__))

# Set serverless mode for components before import
if os.getenv("VERCEL") or os.getenv("VERCEL_ENV"):
    os.environ["PRICEPROMPTER_SERVERLESS"] = "1"

from src.api_server import app as application, init_app

# 初始化 (可能返回False如果组件不可用，但我们仍然导出app)
try:
    init_app()
except Exception as e:
    import logging
    logging.error(f"PricePrompter init_app failed: {e}")
    # Still export app, but it may have limited functionality

# Vercel期望的入口
app = application
