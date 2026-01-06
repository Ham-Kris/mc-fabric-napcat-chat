#!/bin/bash

# MC-QQ Chat Bridge 后端安装脚本

echo "🚀 MC-QQ Chat Bridge 后端安装"
echo "================================"

# 检查 Python 版本
python3 --version || { echo "❌ 请先安装 Python 3.11+"; exit 1; }

# 创建虚拟环境
echo "📦 创建虚拟环境..."
python3 -m venv venv

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "📥 安装依赖..."
pip install -r requirements.txt

# 创建配置文件
if [ ! -f .env ]; then
    echo "📝 创建配置文件..."
    cp config.example.env .env
    echo "⚠️  请编辑 .env 文件配置你的参数"
else
    echo "✅ 配置文件已存在"
fi

echo ""
echo "================================"
echo "✅ 安装完成!"
echo ""
echo "下一步:"
echo "1. 编辑 .env 文件配置参数"
echo "2. 运行: source venv/bin/activate"
echo "3. 启动: python run.py"
echo "================================"

