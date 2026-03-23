"""
PricePrompter Cloud - Flask Web 服务器
提供 REST API 和 Web 界面
"""
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import time
from datetime import datetime

from .config import load_config, MODELS
from .proxy_service import PricePrompterProxy
from .logger import get_logger

logger = get_logger()

# 创建Flask应用
app = Flask(__name__)
CORS(app)

# 初始化代理服务
proxy = None

def init_app():
    """初始化应用"""
    global proxy
    try:
        config = load_config()
        proxy = PricePrompterProxy(config)
        logger.info("Flask应用初始化完成")
        return True
    except Exception as e:
        logger.error(f"应用初始化失败: {str(e)}")
        return False


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'priceprompter-proxy'
    })


@app.route('/v1/proxy/<provider>', methods=['POST'])
def proxy_endpoint(provider):
    """代理API端点"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Invalid JSON payload'
            }), 400
        
        messages = data.get('messages', [])
        user_id = data.get('user_id', 'anonymous')
        options = data.get('options', {})
        
        if not messages:
            return jsonify({
                'success': False,
                'error': 'Messages are required'
            }), 400
        
        # 验证provider
        if provider not in ['openai', 'anthropic', 'auto']:
            return jsonify({
                'success': False,
                'error': f'Unsupported provider: {provider}'
            }), 400
        
        # 调用代理服务
        response = proxy.proxy_request(provider, messages, user_id, options)
        
        return jsonify(response.to_dict())
        
    except Exception as e:
        logger.error(f"代理端点错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Internal server error'
        }), 500


@app.route('/v1/cache/stats', methods=['GET'])
def cache_stats():
    """缓存统计"""
    try:
        stats = proxy.cache.get_stats()
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/v1/analytics/cost', methods=['GET'])
def cost_analytics():
    """成本分析"""
    try:
        days = request.args.get('days', 7, type=int)
        stats = proxy.cost_analyzer.get_stats(days)
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/v1/analytics/aggregated', methods=['GET'])
def aggregated_analytics():
    """聚合分析"""
    try:
        cache_stats = proxy.cache.get_stats()
        cost_stats = proxy.cost_analyzer.get_stats()
        
        return jsonify({
            'success': True,
            'data': {
                'cache': cache_stats,
                'cost': cost_stats,
                'timestamp': datetime.now().isoformat()
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/admin/cleanup-cache', methods=['POST'])
def admin_cleanup_cache():
    """管理端点：清理缓存"""
    try:
        max_age_days = request.args.get('max_age_days', 7, type=int)
        deleted = proxy.cleanup_cache(max_age_days)
        return jsonify({
            'success': True,
            'deleted': deleted,
            'message': f'Cleaned {deleted} cache entries'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# 简单的前端界面
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>PricePrompter Dashboard</title>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; border-radius: 10px; margin-bottom: 2rem; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
        .stat-card { background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-value { font-size: 2rem; font-weight: bold; color: #667eea; }
        .stat-label { color: #666; margin-top: 0.5rem; }
        .section { background: white; padding: 1.5rem; border-radius: 8px; margin-bottom: 1.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .test-form { display: flex; gap: 1rem; margin-top: 1rem; }
        .test-form textarea { flex: 1; height: 100px; padding: 1rem; border: 1px solid #ddd; border-radius: 4px; }
        .test-form button { background: #667eea; color: white; border: none; padding: 1rem 2rem; border-radius: 4px; cursor: pointer; }
        .test-form button:hover { background: #5a6fd8; }
        #result { margin-top: 1rem; padding: 1rem; background: #f8f9fa; border-radius: 4px; }
        .badge { display: inline-block; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.8rem; }
        .badge-cached { background: #d4edda; color: #155724; }
        .badge-miss { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💰 PricePrompter Cloud</h1>
            <p>AI成本优化仪表板</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value" id="today-savings">--</div>
                <div class="stat-label">今日节省 (tokens)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="cache-rate">--</div>
                <div class="stat-label">缓存命中率</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="total-cost">--</div>
                <div class="stat-label">总成本 ($)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="slop-alerts">--</div>
                <div class="stat-label">AI Slop 拦截</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📊 缓存统计</h2>
            <pre id="cache-stats">加载中...</pre>
        </div>
        
        <div class="section">
            <h2>🧪 测试代理服务</h2>
            <form class="test-form" id="test-form">
                <select id="provider" style="padding: 1rem;">
                    <option value="openai">OpenAI</option>
                    <option value="anthropic">Anthropic</option>
                    <option value="auto">自动选择</option>
                </select>
                <textarea id="messages" placeholder='[{"role": "user", "content": "Hello, world!"}]'></textarea>
                <button type="submit">发送请求</button>
            </form>
            <div id="result"></div>
        </div>
    </div>
    
    <script>
        async function loadStats() {
            try {
                const res = await fetch('/v1/analytics/aggregated');
                const data = await res.json();
                
                if (data.success) {
                    const stats = data.data;
                    document.getElementById('today-savings').textContent = 
                        (stats.cache.tokens_saved || 0).toLocaleString();
                    document.getElementById('cache-rate').textContent = 
                        (stats.cost.cache_hit_rate * 100).toFixed(1) + '%';
                    document.getElementById('total-cost').textContent = 
                        '$' + stats.cost.total_cost.toFixed(6);
                    document.getElementById('cache-stats').textContent = 
                        JSON.stringify(stats, null, 2);
                }
            } catch (e) {
                console.error('加载统计失败:', e);
            }
        }
        
        document.getElementById('test-form').onsubmit = async (e) => {
            e.preventDefault();
            const provider = document.getElementById('provider').value;
            const messages = JSON.parse(document.getElementById('messages').value || '[]');
            const resultDiv = document.getElementById('result');
            
            resultDiv.innerHTML = '发送中...';
            
            try {
                const res = await fetch(`/v1/proxy/${provider}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ messages })
                });
                const data = await res.json();
                
                if (data.success) {
                    resultDiv.innerHTML = `
                        <h3>✅ 请求成功</h3>
                        <p><strong>模型:</strong> ${data.routing_info?.model || 'N/A'}</p>
                        <p><strong>成本:</strong> $${data.cost.toFixed(6)}</p>
                        <p><strong>缓存:</strong> 
                            <span class="badge ${data.cached ? 'badge-cached' : 'badge-miss'}">
                                ${data.cached ? '命中' : '未命中'}
                            </span>
                        </p>
                        <p><strong>Slop分数:</strong> ${(data.slop_score * 100).toFixed(1)}%</p>
                        <hr>
                        <pre>${JSON.stringify(data.data, null, 2)}</pre>
                    `;
                } else {
                    resultDiv.innerHTML = `
                        <h3>❌ 请求失败</h3>
                        <p><strong>错误:</strong> ${data.error}</p>
                    `;
                }
            } catch (e) {
                resultDiv.innerHTML = `<h3>❌ 请求异常</h3><p>${e.message}</p>`;
            }
            
            loadStats();
        };
        
        loadStats();
        setInterval(loadStats, 5000);
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def dashboard():
    """仪表板"""
    return render_template_string(DASHBOARD_HTML)


def run_server():
    """运行服务器"""
    if not init_app():
        logger.error("应用初始化失败，无法启动服务器")
        return
    
    logger.info("PricePrompter Cloud 服务器启动中...")
    logger.info(f"访问仪表板: http://localhost:3000")
    logger.info(f"健康检查: http://localhost:3000/health")
    logger.info(f"代理API: http://localhost:3000/v1/proxy/<provider>")
    
    app.run(host='0.0.0.0', port=3000, debug=False)


if __name__ == '__main__':
    run_server()
