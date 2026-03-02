@echo off
REM Setup script for Windows

echo === Web自动化框架安装脚本 ===

echo 1. 安装依赖...
uv sync

echo 2. 安装 Playwright 浏览器...
uv run playwright install chromium

echo 3. 设置 Django 测试网站...
cd test_site

echo 4. 初始化数据库...
uv run python manage.py migrate

echo 5. 创建测试用户...
echo from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@test.com', 'admin123') | uv run python manage.py shell

cd ..

echo 6. 创建必要的目录...
if not exist logs mkdir logs
if not exist screenshots mkdir screenshots

echo.
echo === 安装完成! ===
echo.
echo 启动测试网站：
echo   cd test_site ^&^& uv run python manage.py runserver
echo.
echo 运行示例：
echo   uv run python examples/basic_usage.py
echo.
echo 测试账号：
echo   用户名: admin
echo   密码: admin123

pause
