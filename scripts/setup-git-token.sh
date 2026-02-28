#!/bin/bash
# GitHub Token 配置脚本
# 将 GITHUB_TOKEN 配置到 Git remote URL 中

set -e

echo "🔐 配置 GitHub Token 到 Git remote..."
echo ""

# 读取 .env 文件中的 token
if [ -f .env ]; then
    # 从 .env 文件中提取 GITHUB_TOKEN
    TOKEN=$(grep "^GITHUB_TOKEN=" .env | cut -d '=' -f2 | tr -d '"' | tr -d "'")
    
    if [ -z "$TOKEN" ] || [ "$TOKEN" = "ghp_xxxxxxxxxxxxxxxxxxxx" ]; then
        echo "❌ 错误: .env 文件中的 GITHUB_TOKEN 未配置或仍是占位符"
        echo ""
        echo "请编辑 .env 文件，设置你的真实 GitHub Token:"
        echo "GITHUB_TOKEN=ghp_你的真实token"
        echo ""
        echo "获取 token: https://github.com/settings/tokens"
        exit 1
    fi
    
    echo "✅ 从 .env 读取到 GITHUB_TOKEN"
    echo ""
    
    # 配置 Git remote URL 包含 token
    git remote set-url origin "https://${TOKEN}@github.com/yan931305137/ai_evolution.git"
    
    echo "✅ Git remote URL 已更新"
    echo ""
    echo "当前 remote URL:"
    git remote get-url origin | sed "s/${TOKEN}/*****/g"
    echo ""
    echo "🎉 配置完成！现在可以免密推送到 GitHub"
    echo ""
    echo "测试推送:"
    echo "  git push origin main"
    
else
    echo "❌ 错误: 未找到 .env 文件"
    exit 1
fi
