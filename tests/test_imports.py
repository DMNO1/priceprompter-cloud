import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
try:
    from src import config, logger, cache_manager, smart_router, slop_detector, proxy_service
    print("All module imports OK")
    print(f"  config: loaded")
    print(f"  cache_manager: loaded")
    print(f"  smart_router: loaded")
    print(f"  slop_detector: loaded")
    print(f"  proxy_service: loaded")
except Exception as e:
    print(f"IMPORT ERROR: {e}")
    sys.exit(1)
