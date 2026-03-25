"""
PricePrompter Cloud - 语义缓存管理器
支持基于向量相似度的智能缓存
"""
import json
import hashlib
import sqlite3
import os
import math
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from .logger import get_logger

logger = get_logger()


class CacheEntry:
    """缓存条目"""
    def __init__(self, id: str, query: str, response: Dict, tokens_saved: int, 
                 similarity: float, created_at: str, model: str):
        self.id = id
        self.query = query
        self.response = response
        self.tokens_saved = tokens_saved
        self.similarity = similarity
        self.created_at = created_at
        self.model = model


class SemanticCacheManager:
    """语义缓存管理器 - 使用SQLite存储和余弦相似度计算"""
    
    def __init__(self, db_path: str = "./cache.db"):
        # Force in-memory for serverless
        if os.getenv("PRICEPROMPTER_SERVERLESS") == "1":
            db_path = ":memory:"
        self.db_path = db_path
        # 对于内存模式，保持连接打开以维持数据
        self._is_memory = db_path == ":memory:"
        if self._is_memory:
            self._conn = sqlite3.connect(db_path, check_same_thread=False)
            self._init_memory_db()
        else:
            self._conn = None
            # Ensure directory exists for file DB
            if db_path != ":memory:":
                db_file = Path(db_path)
                db_file.parent.mkdir(parents=True, exist_ok=True)
            self._init_db()
        logger.info(f"语义缓存管理器初始化完成: {db_path}")
    
    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        self._create_tables(conn)
        conn.close()
    
    def _init_memory_db(self):
        """初始化内存数据库 (保持连接)"""
        self._create_tables(self._conn)
    
    def _create_tables(self, conn):
        """创建表结构"""
        cursor = conn.cursor()
        
        # 创建缓存表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache_entries (
                id TEXT PRIMARY KEY,
                query TEXT NOT NULL,
                query_embedding BLOB,
                response TEXT NOT NULL,
                tokens_saved INTEGER DEFAULT 0,
                model TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP
            )
        ''')
        
        # 创建索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_created_at ON cache_entries(created_at)
        ''')
        
        conn.commit()
    
    def _generate_fingerprint(self, messages: List[Dict[str, str]]) -> str:
        """生成请求指纹"""
        content = json.dumps(messages, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()
    
    def _simple_embed(self, text: str) -> List[float]:
        """简化的文本向量化 (基于词频)"""
        # 简单的词袋模型实现
        words = text.lower().split()
        vocab = list(set(words))
        vector = [words.count(word) for word in vocab]
        
        # 归一化
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [v / norm for v in vector]
        
        return vector
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        # 将向量补齐到相同长度
        max_len = max(len(vec1), len(vec2))
        vec1 = vec1 + [0] * (max_len - len(vec1))
        vec2 = vec2 + [0] * (max_len - len(vec2))
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(x * x for x in vec1))
        norm2 = math.sqrt(sum(x * x for x in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _get_connection(self):
        """获取数据库连接 (支持内存和文件模式)"""
        if self._is_memory and self._conn:
            return self._conn
        return sqlite3.connect(self.db_path)
    
    def semantic_search(self, messages: List[Dict[str, str]], threshold: float = 0.95) -> Optional[CacheEntry]:
        """语义相似度搜索"""
        try:
            query_text = " ".join([m.get("content", "") for m in messages])
            query_embedding = self._simple_embed(query_text)
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 获取所有缓存条目
            cursor.execute('''
                SELECT id, query, query_embedding, response, tokens_saved, model, created_at
                FROM cache_entries
                ORDER BY created_at DESC
                LIMIT 100
            ''')
            
            rows = cursor.fetchall()
            if not self._is_memory:
                conn.close()
            
            best_match = None
            best_similarity = 0.0
            
            for row in rows:
                id, query, stored_embedding_blob, response, tokens_saved, model, created_at = row
                
                if stored_embedding_blob:
                    stored_embedding = json.loads(stored_embedding_blob)
                    similarity = self._cosine_similarity(query_embedding, stored_embedding)
                    
                    if similarity > best_similarity and similarity >= threshold:
                        best_similarity = similarity
                        best_match = {
                            'id': id,
                            'query': query,
                            'response': json.loads(response),
                            'tokens_saved': tokens_saved,
                            'similarity': similarity,
                            'created_at': created_at,
                            'model': model
                        }
            
            if best_match:
                # 更新访问计数
                self._update_access_count(best_match['id'])
                logger.info(f"缓存命中: similarity={best_similarity:.4f}")
                return CacheEntry(**best_match)
            
            return None
            
        except Exception as e:
            logger.error(f"语义搜索失败: {str(e)}")
            return None
    
    def _update_access_count(self, entry_id: str):
        """更新访问计数"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE cache_entries
                SET access_count = access_count + 1, last_accessed = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (entry_id,))
            conn.commit()
            if not self._is_memory:
                conn.close()
        except Exception as e:
            logger.error(f"更新访问计数失败: {str(e)}")
    
    def store(self, messages: List[Dict[str, str]], response: Dict[str, Any], 
              model: str = "unknown") -> bool:
        """存储响应到缓存"""
        try:
            fingerprint = self._generate_fingerprint(messages)
            query_text = " ".join([m.get("content", "") for m in messages])
            query_embedding = self._simple_embed(query_text)
            
            tokens_saved = response.get('usage', {}).get('total_tokens', 0)
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO cache_entries
                (id, query, query_embedding, response, tokens_saved, model, created_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                fingerprint,
                query_text[:1000],  # 限制长度
                json.dumps(query_embedding),
                json.dumps(response),
                tokens_saved,
                model
            ))
            
            conn.commit()
            if not self._is_memory:
                conn.close()
            
            logger.info(f"缓存存储成功: {fingerprint[:8]}...")
            return True
            
        except Exception as e:
            logger.error(f"缓存存储失败: {str(e)}")
            return False
    
    def cleanup(self, max_age_days: int = 7) -> int:
        """清理过期缓存"""
        try:
            cutoff = datetime.now() - timedelta(days=max_age_days)
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM cache_entries
                WHERE created_at < ?
            ''', (cutoff.strftime('%Y-%m-%d %H:%M:%S'),))
            
            deleted = cursor.rowcount
            conn.commit()
            if not self._is_memory:
                conn.close()
            
            logger.info(f"清理过期缓存: {deleted} 条")
            return deleted
            
        except Exception as e:
            logger.error(f"缓存清理失败: {str(e)}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 总条目数
            cursor.execute('SELECT COUNT(*) FROM cache_entries')
            total = cursor.fetchone()[0]
            
            # 总节省tokens
            cursor.execute('SELECT SUM(tokens_saved) FROM cache_entries')
            tokens_saved = cursor.fetchone()[0] or 0
            
            # 今日新增
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT COUNT(*) FROM cache_entries
                WHERE DATE(created_at) = ?
            ''', (today,))
            today_added = cursor.fetchone()[0]
            
            if not self._is_memory:
                conn.close()
            
            return {
                'total_entries': total,
                'tokens_saved': tokens_saved,
                'today_added': today_added
            }
            
        except Exception as e:
            logger.error(f"获取缓存统计失败: {str(e)}")
            return {'total_entries': 0, 'tokens_saved': 0, 'today_added': 0}
