#!/bin/bash
# SynHub 一键安装脚本
set -e

echo "=== SynHub 知识库安装 ==="

# 1. 克隆仓库
if [ ! -d "SynHub" ]; then
    echo "克隆仓库..."
    git clone https://github.com/rhMa0706/SynHub.git
fi

cd SynHub

# 2. 安装依赖
echo "安装依赖..."
pip install mcp python-dotenv

# 3. 配置环境变量
if [ ! -f ".env" ]; then
    echo "创建 .env 文件..."
    cp .env.example .env
    echo ""
    echo "请编辑 .env 文件，填入你的 MIFY_API_KEY 和 MIFY_DATASET_IDS"
    echo ""
fi

# 4. 验证
echo "验证安装..."
python -c "from config.settings import MIFY_API_KEY; print('API Key:', '已配置' if MIFY_API_KEY else '未配置')"

echo ""
echo "=== 安装完成 ==="
echo ""
echo "下一步："
echo "  1. 编辑 .env 填入 API Key"
echo "  2. 在你的项目 .mcp.json 中添加 synhub 配置"
echo "  3. 重启 Claude Code"
