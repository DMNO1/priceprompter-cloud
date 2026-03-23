# PricePrompter Cloud - AI成本优化工具

## 项目简介

PricePrompter Cloud 是一个AI成本优化SaaS工具，通过智能路由、语义缓存和AI Slop检测，帮助开发者节省 AI API 调用成本。

## 核心功能

### 1. API代理服务
- 兼容 OpenAI 和 Anthropic API 格式
- 自动选择最具性价比的模型
- 支持请求重试、超时控制

### 2. 语义缓存
- 基于词频的轻量级向量化
- 余弦相似度匹配
- 自动清理过期缓存

### 3. 智能路由
- 自动评估查询复杂度
- 根据成本选择最优模型
- 支持多提供商比较

### 4. AI Slop检测
- 识别低质量AI生成内容
- 提供改进建议
- 可配置阈值

## 快速开始

### 环境要求
- Python 3.10+
- Windows/Linux/macOS

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动服务

```bash
# 启动Web服务器
py main.py server

# 或直接运行API
py main.py test --message "你好"
```

访问仪表板: http://localhost:3000

### API 使用示例

```bash
# 测试代理请求
curl -X POST http://localhost:3000/v1/proxy/auto \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "解释一下量子计算"}
    ],
    "user_id": "user-123"
  }'
```

### 查看统计

```bash
# 获取缓存统计
curl http://localhost:3000/v1/cache/stats

# 获取成本分析
curl http://localhost:3000/v1/analytics/cost

# 清理缓存
curl -X POST http://localhost:3000/admin/cleanup-cache?max_age_days=7
```

## 项目结构

```
priceprompter-cloud/
├── src/
│   ├── config.py           # 配置管理
│   ├── logger.py           # 日志管理
│   ├── cache_manager.py    # 语义缓存
│   ├── smart_router.py     # 智能路由
│   ├── slop_detector.py    # AI Slop检测
│   ├── proxy_service.py    # 代理服务核心
│   └── __init__.py
├── tests/
│   ├── test_dry_run.py     # 完整测试
│   └── simple_test.py      # 简单测试
├── logs/                   # 日志目录
├── requirements.txt        # Python依赖
└── main.py                 # 命令行入口
```

## 配置

环境变量（可选）：
- `HOST`: 服务器主机 (默认: 0.0.0.0)
- `PORT`: 端口 (默认: 3000)
- `DATABASE_URL`: 数据库连接 (默认: SQLite)
- `SIMILARITY_THRESHOLD`: 相似度阈值 (默认: 0.95)
- `CACHE_TTL`: 缓存TTL秒数 (默认: 604800)

## 性能指标

- 缓存命中率: >30%
- 平均响应延迟: <200ms
- 成本节省: >20%

## 技术栈

- **后端**: Flask (Python)
- **缓存**: SQLite + 余弦相似度
- **分析**: Pandas/Numpy
- **部署**: Docker/Vercel

## 开发

运行完整测试（干运行）：
```bash
py tests/test_dry_run.py
```

查看统计：
```bash
py main.py stats
```

清理缓存：
```bash
py main.py cleanup --days 7
```

## License

MIT
