@echo off
echo ========================================
echo PricePrompter Cloud 部署脚本
echo ========================================

REM 检查Python
py --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请安装Python 3.10+
    pause
    exit /b 1
)

REM 安装依赖
echo [1/3] 安装依赖...
py -m pip install -r requirements.txt --quiet

if errorlevel 1 (
    echo [警告] 部分依赖安装失败，尝试继续...
)

REM 创建日志目录
if not exist logs mkdir logs

REM 运行测试
echo [2/3] 运行健康检查...
py tests/simple_test.py

if errorlevel 1 (
    echo [错误] 测试失败，请检查上述错误信息
    pause
    exit /b 1
)

echo [3/3] 部署完成！
echo.
echo 启动服务器:
echo   py main.py server
echo.
echo 查看统计:
echo   py main.py stats
echo.
echo 访问仪表板: http://localhost:3000
echo.
pause
