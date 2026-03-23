"""
PricePrompter Cloud - 简单测试
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.logger import get_logger
from src.config import load_config
from src.smart_router import SmartRouter

print("开始测试...")

try:
    # 测试配置加载
    config = load_config()
    print("1. 配置加载: OK")
    
    # 测试路由器
    router = SmartRouter()
    decision = router.select_model('auto', [{"role": "user", "content": "hello"}])
    print(f"2. 智能路由: OK - 选择了 {decision.selected_model.id}")
    
    print("\n所有基础测试通过!")
    
except Exception as e:
    print(f"测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
