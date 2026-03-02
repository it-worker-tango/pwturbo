#!/bin/bash
# Setup script for the web automation framework

echo "=== Web自动化框架安装脚本 ==="

# Install dependencies
echo "1. 安装依赖..."
uv sync

# Install Playwright browsers
echo "2. 安装 Playwright 浏览器..."
uv run playwright install chromium

# Setup Django test site
echo "3. 设置 Django 测试网站..."
cd test_site

# Run migrations
echo "4. 初始化数据库..."
uv run python manage.py migrate

# Create superuser (non-interactive)
echo "5. 创建测试用户..."
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@test.com', 'admin123')" | uv run python manage.py shell

cd ..

# Create necessary directories
echo "6. 创建必要的目录..."
mkdir -p logs
mkdir -p screenshots

echo ""
echo "=== 安装完成! ==="
echo ""
echo "启动测试网站："
echo "  cd test_site && uv run python manage.py runserver"
echo ""
echo "运行示例："
echo "  uv run python examples/basic_usage.py"
echo ""
echo "测试账号："
echo "  用户名: admin"
echo "  密码: admin123"
