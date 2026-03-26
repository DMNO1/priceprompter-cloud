#!/usr/bin/env python3
"""
PricePrompter Cloud - Vercel Serverless Adapter
Flask app adapter for Vercel Python runtime
"""
import sys
import os
import logging

logger = logging.getLogger("priceprompter.vercel")

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Set serverless mode for components before import
if os.getenv("VERCEL") or os.getenv("VERCEL_ENV"):
    os.environ["PRICEPROMPTER_SERVERLESS"] = "1"

try:
    from src.api_server import app as application, init_app

    # Initialize (may return False if DB unavailable, but app still works)
    try:
        init_app()
        logger.info("PricePrompter init_app succeeded")
    except Exception as init_err:
        logger.warning(f"PricePrompter init_app warning: {init_err}")

    app = application
    logger.info("PricePrompter app exported successfully")

except Exception as e:
    logger.error(f"PricePrompter app import failed: {e}", exc_info=True)
    # Fallback: create a minimal Flask app that reports the error
    from flask import Flask, jsonify
    app = Flask(__name__)

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def error_handler(path):
        return jsonify({
            "error": "App failed to initialize",
            "detail": str(e),
            "hint": "Check Vercel function logs for full traceback"
        }), 503
