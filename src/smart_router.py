"""
PricePrompter Cloud - 智能路由模块
根据查询复杂度自动选择最优模型
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .config import MODELS, ModelConfig
from .logger import get_logger

logger = get_logger()


@dataclass
class RoutingDecision:
    """路由决策结果"""
    selected_model: ModelConfig
    reason: str
    estimated_cost: float
    confidence: float


class SmartRouter:
    """智能路由器 - 自动选择性价比最优模型"""
    
    def __init__(self):
        self.models = MODELS
        logger.info(f"智能路由器初始化完成，加载 {len(self.models)} 个模型配置")
    
    def assess_complexity(self, query: str) -> str:
        """评估查询复杂度"""
        query_lower = query.lower()
        
        # 复杂查询指标
        complex_indicators = [
            'analyze', 'compare', 'implement', 'debug', 'refactor',
            'optimize', 'architecture', 'design pattern', 'algorithm',
            '分析', '比较', '实现', '调试', '重构', '优化'
        ]
        
        # 简单查询指标
        simple_indicators = [
            'hi', 'hello', 'what is', 'explain', 'define',
            '你好', '什么是', '解释', '定义'
        ]
        
        # 检查复杂度指标
        complex_score = sum(1 for ind in complex_indicators if ind in query_lower)
        simple_score = sum(1 for ind in simple_indicators if ind in query_lower)
        
        # 根据查询长度调整
        word_count = len(query.split())
        if word_count > 100:
            complex_score += 1
        elif word_count < 20:
            simple_score += 1
        
        # 判断复杂度
        if complex_score > 0:
            return 'complex'
        elif simple_score > 0:
            return 'simple'
        return 'medium'
    
    def estimate_tokens(self, text: str) -> int:
        """估算token数量"""
        # 粗略估计: 1 token ≈ 4 字符 (中文) 或 1 token ≈ 0.75 单词 (英文)
        import re
        
        # 中文字符
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        # 英文单词
        english_words = len(re.findall(r'[a-zA-Z]+', text))
        
        # 估算
        tokens = (chinese_chars / 4) + (english_words / 0.75)
        return int(tokens)
    
    def select_model(
        self,
        preferred_provider: str,
        messages: List[Dict[str, str]],
        options: Optional[Dict[str, Any]] = None
    ) -> RoutingDecision:
        """选择最优模型"""
        options = options or {}
        
        # 合并所有消息内容
        query = " ".join([m.get("content", "") for m in messages])
        
        # 评估复杂度
        complexity = self.assess_complexity(query)
        
        # 估算所需上下文
        required_tokens = self.estimate_tokens(query)
        max_tokens = options.get('max_tokens', 1000)
        total_required = required_tokens + max_tokens
        
        logger.info(f"查询复杂度: {complexity}, 预估tokens: {total_required}")
        
        # 过滤可用模型
        candidates = self.models.copy()
        
        if preferred_provider != 'auto':
            candidates = [m for m in candidates if m.provider == preferred_provider]
        
        if not candidates:
            candidates = self.models  # 回退到所有模型
        
        # 根据复杂度筛选
        if complexity == 'simple':
            # 简单查询：优先选择便宜快速的模型
            candidates = [m for m in candidates if 
                         'cheap' in m.strengths or 'fast' in m.strengths or 'simple' in m.strengths]
        elif complexity == 'complex':
            # 复杂查询：优先选择强大的模型
            candidates = [m for m in candidates if 
                         'complex' in m.strengths or 'analysis' in m.strengths or 'coding' in m.strengths]
        
        # 根据上下文长度筛选
        candidates = [m for m in candidates if m.context_window >= total_required]
        
        if not candidates:
            # 如果没有符合条件的，选择上下文最大的
            candidates = sorted(self.models, key=lambda m: m.context_window, reverse=True)[:1]
        
        # 按成本排序 (输入成本 + 预估输出成本)
        def estimate_cost(model: ModelConfig) -> float:
            input_cost = (required_tokens / 1000) * model.cost_per_1k_input
            output_cost = (max_tokens / 1000) * model.cost_per_1k_output
            return input_cost + output_cost
        
        candidates.sort(key=estimate_cost)
        selected = candidates[0]
        
        estimated_cost = estimate_cost(selected)
        
        # 生成选择原因
        if complexity == 'simple':
            reason = f"简单查询，选择成本最优模型 {selected.id}"
        elif complexity == 'complex':
            reason = f"复杂查询，选择能力强大的模型 {selected.id}"
        else:
            reason = f"中等复杂度查询，选择平衡型模型 {selected.id}"
        
        logger.info(f"路由决策: {selected.id}, 预估成本: ${estimated_cost:.6f}")
        
        return RoutingDecision(
            selected_model=selected,
            reason=reason,
            estimated_cost=estimated_cost,
            confidence=0.85 if complexity != 'medium' else 0.70
        )
    
    def calculate_actual_cost(self, model_id: str, usage: Dict[str, int]) -> float:
        """计算实际成本"""
        model = next((m for m in self.models if m.id == model_id), None)
        if not model:
            return 0.0
        
        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)
        
        input_cost = (prompt_tokens / 1000) * model.cost_per_1k_input
        output_cost = (completion_tokens / 1000) * model.cost_per_1k_output
        
        return input_cost + output_cost
    
    def get_model_recommendation(self, query: str) -> Dict[str, Any]:
        """获取模型推荐信息"""
        complexity = self.assess_complexity(query)
        tokens = self.estimate_tokens(query)
        
        recommendations = []
        for model in self.models:
            cost = (tokens / 1000) * model.cost_per_1k_input + (500 / 1000) * model.cost_per_1k_output
            recommendations.append({
                'model_id': model.id,
                'provider': model.provider,
                'estimated_cost': round(cost, 6),
                'context_window': model.context_window,
                'strengths': model.strengths
            })
        
        # 按成本排序
        recommendations.sort(key=lambda x: x['estimated_cost'])
        
        return {
            'query_complexity': complexity,
            'estimated_tokens': tokens,
            'recommendations': recommendations[:3]  # 前3个推荐
        }
