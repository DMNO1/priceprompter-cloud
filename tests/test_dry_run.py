"""
PricePrompter Cloud - 干运行测试脚本
测试核心功能，无需真实API调用
"""
import sys
import os
import json

# 确保可以导入src模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.logger import get_logger
from src.cache_manager import SemanticCacheManager
from src.smart_router import SmartRouter
from src.slop_detector import SlopDetector
from src.proxy_service import PricePrompterProxy
from src.config import load_config

logger = get_logger()


def test_semantic_cache():
    """测试语义缓存"""
    print("\n🧪 测试: 语义缓存管理器")
    
    cache = SemanticCacheManager(":memory:")  # 内存数据库
    
    test_messages = [
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm fine, thank you!"}
    ]
    
    test_response = {
        "id": "test-123",
        "choices": [{"message": {"content": "I'm fine!"}}],
        "usage": {"total_tokens": 10}
    }
    
    # 存储
    success = cache.store(test_messages, test_response, "gpt-3.5-turbo")
    print(f"   存储: {'✅' if success else '❌'}")
    
    # 搜索
    cached = cache.semantic_search(test_messages, threshold=0.9)
    print(f"   搜索: {'✅' if cached else '❌'}")
    
    # 统计
    stats = cache.get_stats()
    print(f"   统计: 总条目={stats['total_entries']}, 节省tokens={stats['tokens_saved']}")
    
    return success and cached is not None


def test_smart_router():
    """测试智能路由"""
    print("\n🧪 测试: 智能路由器")
    
    router = SmartRouter()
    
    # 简单查询
    decision = router.select_model('auto', [{"role": "user", "content": "hi"}])
    print(f"   简单查询: {decision.selected_model.id}")
    
    # 复杂查询
    decision = router.select_model('auto', [{"role": "user", "content": "Analyze and implement a complex algorithm"}])
    print(f"   复杂查询: {decision.selected_model.id}")
    
    # 成本计算
    cost = router.calculate_actual_cost('gpt-4-turbo', {'prompt_tokens': 100, 'completion_tokens': 50})
    print(f"   成本计算: ${cost:.6f}")
    
    return True


def test_slop_detector():
    """测试Slop检测器"""
    print("\n🧪 测试: AI Slop检测器")
    
    detector = SlopDetector()
    
    # AI生成文本
    ai_text = """
    In the ever-changing landscape of technology, we need to leverage the power of AI 
    to unlock the potential of our synergy. This is a game-changer that will 
    undoubtedly revolutionize our approach. We must think outside the box and 
    collaborate together to achieve our goals.
    """
    
    result = detector.analyze(ai_text)
    print(f"   AI文本分数: {result.score:.2f}")
    print(f"   发现问题: {len(result.issues)}")
    print(f"   建议: {result.suggestions[:2]}")
    
    # 人类文本
    human_text = "The project is complete. We deployed the changes and everything works."
    human_result = detector.analyze(human_text)
    print(f"   人类文本分数: {human_result.score:.2f}")
    
    return result.score >= 0.25 and human_result.score < 0.3


def test_proxy_service():
    """测试代理服务"""
    print("\n🧪 测试: 代理服务")
    
    try:
        config = load_config()
        proxy = PricePrompterProxy(config)
        
        # 测试请求
        messages = [
            {"role": "user", "content": "Explain quantum computing in simple terms."}
        ]
        
        response = proxy.proxy_request(
            provider="auto",
            messages=messages,
            user_id="test-user"
        )
        
        print(f"   请求成功: {response.success}")
        print(f"   命中缓存: {response.cached}")
        print(f"   成本: ${response.cost:.6f}")
        print(f"   Slop分数: {response.slop_score:.2f}")
        print(f"   路由模型: {response.routing_info.get('model', 'N/A')}")
        
        # 获取统计
        stats = proxy.get_stats()
        print(f"   缓存条目: {stats['cache']['total_entries']}")
        print(f"   请求总数: {stats['cost']['total_requests']}")
        
        return response.success
        
    except Exception as e:
        print(f"   测试失败: {str(e)}")
        return False


def test_dry_run():
    """干运行测试"""
    print("=" * 50)
    print("PricePrompter Cloud 干运行测试")
    print("=" * 50)
    
    tests = [
        ("语义缓存", test_semantic_cache),
        ("智能路由", test_smart_router),
        ("Slop检测", test_slop_detector),
        ("代理服务", test_proxy_service),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"   ❌ 异常: {str(e)}")
            results.append((name, False))
    
    # 输出总结
    print("\n" + "=" * 50)
    print("📊 测试结果汇总")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {name}: {status}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！")
        return 0
    else:
        print("⚠️ 部分测试失败，请检查日志")
        return 1


if __name__ == '__main__':
    exit_code = test_dry_run()
    sys.exit(exit_code)
