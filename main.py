#!/usr/bin/env python3
"""
PricePrompter Cloud - 主入口文件
"""
import sys
import os
import argparse
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from src.logger import get_logger, log_execution_start, log_execution_end
from src.api_server import run_server
from src.proxy_service import PricePrompterProxy
from src.config import load_config

logger = get_logger()


def cmd_server(args):
    """启动服务器"""
    logger.info("启动 PricePrompter Cloud 服务器")
    try:
        run_server()
    except KeyboardInterrupt:
        logger.info("服务器已停止")
    except Exception as e:
        logger.error(f"服务器启动失败: {str(e)}")
        sys.exit(1)


def cmd_test(args):
    """运行测试"""
    logger.info("运行测试代理请求")
    
    try:
        config = load_config()
        proxy = PricePrompterProxy(config)
        
        # 测试消息
        messages = [
            {"role": "user", "content": args.message or "Hello, explain AI cost optimization briefly."}
        ]
        
        provider = args.provider or "auto"
        
        logger.info(f"测试 provider={provider}, message='{messages[0]['content'][:50]}...'")
        
        response = proxy.proxy_request(
            provider=provider,
            messages=messages,
            user_id="test-user"
        )
        
        if response.success:
            print("[OK] Test passed")
            print(f"   Model: {response.routing_info.get('model', 'N/A')}")
            print(f"   Cost: ${response.cost:.6f}")
            print(f"   Cache: {'Hit' if response.cached else 'Miss'}")
            print(f"   Slop score: {(response.slop_score * 100):.1f}%")
            
            # 如果需要输出结果
            if args.output:
                print("\nResponse:")
                print(json.dumps(response.data, indent=2, ensure_ascii=False))
        else:
            print("[FAIL] Test failed")
            print(f"   Error: {response.error}")
        
        # 显示统计
        stats = proxy.get_stats()
        print("\nCurrent Statistics:")
        print(f"   Cache entries: {stats['cache']['total_entries']}")
        print(f"   Tokens saved: {stats['cache']['tokens_saved']}")
        print(f"   Total requests: {stats['cost']['total_requests']}")
        print(f"   Total cost: ${stats['cost']['total_cost']:.6f}")
        print(f"   Cache hit rate: {stats['cost']['cache_hit_rate'] * 100:.1f}%")
            
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        print(f"[ERROR] Test exception: {str(e)}")
        sys.exit(1)


def cmd_cleanup(args):
    """清理缓存"""
    logger.info("清理过期缓存")
    
    try:
        config = load_config()
        proxy = PricePrompterProxy(config)
        
        max_age = args.days or 7
        deleted = proxy.cleanup_cache(max_age)
        
        print(f"[OK] Cleanup complete: {deleted} expired entries removed")
        
    except Exception as e:
        logger.error(f"清理失败: {str(e)}")
        print(f"[ERROR] Cleanup failed: {str(e)}")
        sys.exit(1)


def cmd_stats(args):
    """显示统计"""
    try:
        config = load_config()
        proxy = PricePrompterProxy(config)
        
        stats = proxy.get_stats()
        
        print("PricePrompter Cloud Statistics")
        print("=" * 40)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nCache Statistics:")
        print(f"  Total entries: {stats['cache']['total_entries']}")
        print(f"  Tokens saved: {stats['cache']['tokens_saved']}")
        print(f"  Added today: {stats['cache']['today_added']}")
        print("\nCost Statistics (last 7 days):")
        print(f"  Total requests: {stats['cost']['total_requests']}")
        print(f"  Total cost: ${stats['cost']['total_cost']:.6f}")
        print(f"  Avg cost: ${stats['cost']['avg_cost']:.6f}")
        print(f"  Cache hit rate: {stats['cost']['cache_hit_rate'] * 100:.1f}%")
        
    except Exception as e:
        logger.error(f"获取统计失败: {str(e)}")
        print(f"Error: {str(e)}")
        sys.exit(1)


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description="PricePrompter Cloud - AI成本优化工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s server                 # 启动Web服务器
  %(prog)s test --message "你好"   # 测试代理请求
  %(prog)s cleanup --days 7       # 清理7天前的缓存
  %(prog)s stats                  # 显示统计信息
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # server 命令
    server_parser = subparsers.add_parser('server', help='启动Web服务器')
    
    # test 命令
    test_parser = subparsers.add_parser('test', help='测试代理请求')
    test_parser.add_argument('--message', '-m', type=str, help='测试消息内容')
    test_parser.add_argument('--provider', '-p', type=str, choices=['openai', 'anthropic', 'auto'], default='auto', help='AI提供商')
    test_parser.add_argument('--output', '-o', action='store_true', help='输出完整响应')
    
    # cleanup 命令
    cleanup_parser = subparsers.add_parser('cleanup', help='清理过期缓存')
    cleanup_parser.add_argument('--days', '-d', type=int, default=7, help='清理多少天前的缓存')
    
    # stats 命令
    stats_parser = subparsers.add_parser('stats', help='显示统计信息')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    log_execution_start(f"priceprompter-{args.command}")
    
    try:
        if args.command == 'server':
            cmd_server(args)
        elif args.command == 'test':
            cmd_test(args)
        elif args.command == 'cleanup':
            cmd_cleanup(args)
        elif args.command == 'stats':
            cmd_stats(args)
        
        log_execution_end(f"priceprompter-{args.command}", True)
    except Exception as e:
        log_execution_end(f"priceprompter-{args.command}", False, str(e))
        raise


if __name__ == '__main__':
    main()
