"""
PricePrompter Cloud - AI Slop检测器
识别并优化低质量AI输出
"""
import re
from typing import List, Dict, Any
from dataclasses import dataclass

from .logger import get_logger

logger = get_logger()


@dataclass
class SlopAnalysisResult:
    """Slop分析结果"""
    score: float  # 0-1, 越高表示越像AI Slop
    issues: List[str]
    suggestions: List[str]
    category_scores: Dict[str, float]


class SlopDetector:
    """AI Slop检测器"""
    
    def __init__(self):
        # AI陈词滥调模式
        self.cliches = [
            'in the ever-changing landscape',
            'leverage the power of',
            'unlock the potential',
            'game-changer',
            'synergy',
            'paradigm shift',
            'think outside the box',
            'low-hanging fruit',
            'move the needle',
            'circle back',
            'touch base',
            'deep dive',
            'boil the ocean',
            'run it up the flagpole',
            'in today\'s world',
            'in the digital age',
            'at the end of the day',
            'the fact of the matter is',
            'it is what it is',
            'going forward',
            'moving forward',
            'in order to',
            'due to the fact that',
            '综上所述',
            '值得注意的是',
            '需要指出的是',
            '不可否认的是',
            '显而易见',
            '众所周知',
            '在数字化时代',
            '在当今世界',
        ]
        
        # 空洞修饰语
        self.fluff_words = [
            'very', 'extremely', 'incredibly', 'absolutely',
            'undoubtedly', 'certainly', 'definitely', 'really',
            'quite', 'rather', 'pretty', 'fairly', 'somewhat',
            'basically', 'essentially', 'fundamentally',
            'significantly', 'substantially', 'considerably',
            '很', '非常', '极其', '绝对', '确实', '相当', '比较'
        ]
        
        # 冗余表达
        self.redundancies = [
            'advance forward',
            'collaborate together',
            'end result',
            'future plans',
            'past history',
            'free gift',
            'new innovation',
            'close proximity',
            'revert back',
            'return back',
            'continue on',
            'enter in',
            'exit out',
            '合并一起',
            '返回回来',
            '继续向前',
        ]
        
        logger.info("AI Slop检测器初始化完成")
    
    def analyze(self, response: str) -> SlopAnalysisResult:
        """分析文本的AI Slop程度"""
        if not response or len(response) < 10:
            return SlopAnalysisResult(
                score=0.0,
                issues=["文本过短，无法分析"],
                suggestions=["提供更长文本以获得准确分析"],
                category_scores={}
            )
        
        issues = []
        category_scores = {}
        
        # 1. 检测陈词滥调
        cliche_score, cliche_issues = self._detect_cliches(response)
        category_scores['cliches'] = cliche_score
        if cliche_issues:
            issues.extend(cliche_issues[:3])
        
        # 2. 检测空洞修饰语
        fluff_score, fluff_issues = self._detect_fluff(response)
        category_scores['fluff'] = fluff_score
        if fluff_issues:
            issues.extend(fluff_issues[:2])
        
        # 3. 检测冗余表达
        redundancy_score, redundancy_issues = self._detect_redundancy(response)
        category_scores['redundancy'] = redundancy_score
        if redundancy_issues:
            issues.extend(redundancy_issues[:2])
        
        # 4. 检测重复内容
        repetition_score, repetition_issues = self._detect_repetition(response)
        category_scores['repetition'] = repetition_score
        if repetition_issues:
            issues.extend(repetition_issues[:2])
        
        # 计算总分
        weights = {
            'cliches': 0.30,
            'fluff': 0.25,
            'redundancy': 0.20,
            'repetition': 0.25
        }
        
        total_score = sum(category_scores.get(k, 0) * weights[k] for k in weights)
        total_score = min(total_score, 1.0)
        
        # 生成建议
        suggestions = self._generate_suggestions(category_scores)
        
        logger.info(f"Slop分析完成: score={total_score:.2f}")
        
        return SlopAnalysisResult(
            score=total_score,
            issues=issues,
            suggestions=suggestions,
            category_scores=category_scores
        )
    
    def _detect_cliches(self, text: str) -> tuple:
        """检测陈词滥调"""
        text_lower = text.lower()
        found = []
        
        for cliche in self.cliches:
            if cliche.lower() in text_lower:
                found.append(cliche)
        
        score = min(len(found) * 0.15, 0.8)
        issues = [f"检测到AI陈词滥调: '{c}'" for c in found[:5]]
        
        return score, issues
    
    def _detect_fluff(self, text: str) -> tuple:
        """检测空洞修饰语"""
        words = re.findall(r'\b\w+\b', text.lower())
        found = [w for w in words if w in self.fluff_words]
        
        density = len(found) / len(words) if words else 0
        score = min(density * 3, 0.7)
        
        issues = []
        if found:
            unique_fluff = list(set(found))[:5]
            issues = [f"过度使用空洞修饰语: '{w}'" for w in unique_fluff]
        
        return score, issues
    
    def _detect_redundancy(self, text: str) -> tuple:
        """检测冗余表达"""
        text_lower = text.lower()
        found = []
        
        for phrase in self.redundancies:
            if phrase.lower() in text_lower:
                found.append(phrase)
        
        score = min(len(found) * 0.2, 0.6)
        issues = [f"冗余表达: '{r}'" for r in found[:3]]
        
        return score, issues
    
    def _detect_repetition(self, text: str) -> tuple:
        """检测重复内容"""
        sentences = [s.strip() for s in re.split(r'[.!?。！？]+', text) if s.strip()]
        if len(sentences) < 3:
            return 0.0, []
        
        # 检测重复句子
        unique_sentences = set(s.lower() for s in sentences)
        repetition_ratio = 1 - (len(unique_sentences) / len(sentences))
        
        score = min(repetition_ratio * 2, 0.5)
        
        issues = []
        if repetition_ratio > 0.2:
            issues.append(f"检测到重复内容，重复率: {repetition_ratio:.1%}")
        
        return score, issues
    
    def _generate_suggestions(self, category_scores: Dict[str, float]) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        if category_scores.get('cliches', 0) > 0.3:
            suggestions.append("避免使用AI陈词滥调，使用更具体的描述")
        
        if category_scores.get('fluff', 0) > 0.3:
            suggestions.append("减少空洞修饰语，直接表达核心观点")
        
        if category_scores.get('redundancy', 0) > 0.2:
            suggestions.append("删除冗余表达，使语言更简洁")
        
        if category_scores.get('repetition', 0) > 0.2:
            suggestions.append("避免重复内容，增加信息密度")
        
        if not suggestions:
            suggestions.append("内容质量良好，无明显AI Slop特征")
        
        return suggestions
    
    def is_slop(self, text: str, threshold: float = 0.6) -> bool:
        """快速判断是否为AI Slop"""
        result = self.analyze(text)
        return result.score >= threshold
