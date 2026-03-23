#!/usr/bin/env python3
"""
PricePrompter Cloud - Vercel WSGI adapter
使Flask app兼容Vercel Python runtime
"""
import sys
import os

# 确保src在路径中
sys.path.insert(0, os.path.dirname(__file__))

from src.api_server import app as application, init_app

# 初始化
init_app()

# Vercel期望的入口
app = application
