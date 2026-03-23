"""
PricePrompter Cloud - API代理服务
核心代理层，拦截并转发AI请求
"""
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from .config import load_config, AppConfig
from .cache_manager import SemanticCacheManager
from .smart_router import SmartRouter, RoutingDecision
from .slop_detector import SlopDetector
from .logger import get_logger, log_execution_start, log_execution_end

logger = get_logger()


class ProxyResponse:
    """代理响应"""
    def __init__(self, success: bool, data: Any = None, cached: bool = False,
                 savings: int = 0, cost: float = 0.0, error: str = None,
                 slop_score: float = 0.0, routing_info: Dict = None):
        self.success = success
        self.data = data
        self.cached = cached
        self.savings = savings
        self.cost = cost
        self.error = error
        self.slop_score = slop_score
        self.routing_info = routing_info or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'success': self.success,
            'data': self.data,
            'cached': self.cached,
            'savings': self.savings,
            'cost': self.cost,
            'error': self.error,
            'slop_score': self.slop_score,
            'routing_info': self.routing_info
        }


class CostAnalyzer:
    """成本分析器"""
    
    def __init__(self):
        self.usage_log = []
        logger.info("成本分析器初始化完成")
    
    def log_usage(self, user_id: str, model_id: str, cost: float, 
                  tokens: Dict[str, int], cached: bool = False):
        """记录使用情况"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'model_id': model_id,
            'cost': cost,
            'tokens': tokens,
            'cached': cached
        }
        self.usage_log.append(entry)
        
        # 只保留最近1000条
        if len(self.usage_log) > 1000:
            self.usage_log = self.usage_log[-1000:]
    
    def get_stats(self, days: int = 7) -> Dict[str, Any]:
        """获取使用统计"""
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        recent = [e for e in self.usage_log 
                  if datetime.fromisoformat(e['timestamp']).timestamp() > cutoff]
        
        if not recent:
            return {
                'total_requests': 0,
                'total_cost': 0.0,
                'avg_cost': 0.0,
                'cache_hit_rate': 0.0
            }
        
        total_cost = sum(e['cost'] for e in recent)
        cached_count = sum(1 for e in recent if e['cached'])
        
        return {
            'total_requests': len(recent),
            'total_cost': round(total_cost, 6),
            'avg_cost': round(total_cost / len(recent), 6),
            'cache_hit_rate': round(cached_count / len(recent), 2)
        }


class PricePrompterProxy:
    """PricePrompter Cloud 核心代理服务"""
    
    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or load_config()
        self.cache = SemanticCacheManager()
        self.router = SmartRouter()
        self.slop_detector = SlopDetector()
        self.cost_analyzer = CostAnalyzer()
        
        logger.info("PricePrompter代理服务初始化完成")
    
    def proxy_request(
        self,
        provider: str,
        messages: List[Dict[str, str]],
        user_id: str = "anonymous",
        options: Optional[Dict[str, Any]] = None
    ) -> ProxyResponse:
        """代理AI请求"""
        options = options or {}
        start_time = time.time()
        
        try:
            logger.info(f"收到代理请求: provider={provider}, user={user_id}")
            
            # 1. 检查语义缓存
            cached = self.cache.semantic_search(
                messages, 
                threshold=self.config.similarity_threshold
            )
            
            if cached:
                logger.info(f"缓存命中: {cached.id[:8]}...")
                
                self.cost_analyzer.log_usage(
                    user_id=user_id,
                    model_id=cached.model,
                    cost=0.0,
                    tokens={'prompt': 0, 'completion': 0, 'total': 0},
                    cached=True
                )
                
                return ProxyResponse(
                    success=True,
                    data=cached.response,
                    cached=True,
                    savings=cached.tokens_saved,
                    cost=0.0,
                    routing_info={'source': 'cache', 'similarity': cached.similarity}
                )
            
            # 2. 智能路由选择模型
            routing = self.router.select_model(provider, messages, options)
            selected_model = routing.selected_model
            
            logger.info(f"路由决策: {selected_model.id}, 预估成本: ${routing.estimated_cost:.6f}")
            
            # 3. 模拟AI响应
            mock_response = self._mock_ai_response(selected_model.id, messages, options)
            
            # 4. AI Slop检测
            response_text = self._extract_response_text(mock_response)
            slop_result = self.slop_detector.analyze(response_text)
            
            if slop_result.score > 0.7:
                logger.warning(f"检测到AI Slop: score={slop_result.score:.2f}")
            
            # 5. 存入语义缓存
            self.cache.store(messages, mock_response, selected_model.id)
            
            # 6. 计算实际成本
            usage = mock_response.get('usage', {})
            actual_cost = self.router.calculate_actual_cost(selected_model.id, usage)
            
            # 7. 记录使用
            self.cost_analyzer.log_usage(
                user_id=user_id,
                model_id=selected_model.id,
                cost=actual_cost,
                tokens=usage,
                cached=False
            )
            
            elapsed = time.time() - start_time
            logger.info(f"请求处理完成: 耗时={elapsed:.3f}s, 成本=${actual_cost:.6f}")
            
            return ProxyResponse(
                success=True,
                data=mock_response,
                cached=False,
                savings=0,
                cost=actual_cost,
                slop_score=slop_result.score,
                routing_info={
                    'model': selected_model.id,
                    'provider': selected_model.provider,
                    'reason': routing.reason,
                    'estimated_cost': routing.estimated_cost,
                    'actual_cost': actual_cost,
                    'latency_ms': int(elapsed * 1000)
                }
            )
            
        except Exception as e:
            logger.error(f"代理请求失败: {str(e)}")
            return ProxyResponse(
                success=False,
                error=str(e),
                routing_info={'error': str(e)}
            )
    
    def _mock_ai_response(self, model_id: str, messages: List[Dict[str, str]], 
                          options: Dict[str, Any]) -> Dict[str, Any]:
        """模拟AI响应"""
        query = " ".join([m.get("content", "") for m in messages])
        
        if "code" in query.lower() or "代码" in query:
            content = "```python\nprint('Hello, World!')\n```\n\n示例代码。"
        elif "explain" in query.lower() or "解释" in query:
            content = "这是一个很好的问题。让我为您详细解释..."
        else:
            content = f"这是对'{query[:50]}...'的回复。"
        
        prompt_tokens = len(query) // 4
        completion_tokens = len(content) // 4
        
        return {
            'id': f'mock-{int(time.time())}',
            'model': model_id,
            'choices': [{'message': {'role': 'assistant', 'content': content}}],
            'usage': {
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': prompt_tokens + completion_tokens
            }
        }
    
    def _extract_response_text(self, response: Dict[str, Any]) -> str:
        """提取响应文本"""
        try:
            return response['choices'][0]['message']['content']
        except:
            return str(response)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取服务统计"""
        cache_stats = self.cache.get_stats()
        cost_stats = self.cost_analyzer.get_stats()
        
        return {
            'cache': cache_stats,
            'cost': cost_stats,
            'timestamp': datetime.now().isoformat()
        }
    
    def cleanup_cache(self, max_age_days: int = 7) -> int:
        """清理过期缓存"""
        return self.cache.cleanup(max_age_days)
