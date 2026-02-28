#!/bin/bash
#
# 本地 CI 测试脚本
# 模拟 GitHub Actions CI 流程在本地运行
#

set -e  # 遇到错误立即退出

echo "======================================"
echo "🚀 OpenClaw 本地 CI 测试"
echo "======================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 计数器
PASSED=0
FAILED=0

# 辅助函数
run_step() {
    local step_name=$1
    local command=$2
    
    echo ""
    echo "--------------------------------------"
    echo "📋 $step_name"
    echo "--------------------------------------"
    
    if eval "$command"; then
        echo -e "${GREEN}✅ $step_name 通过${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ $step_name 失败${NC}"
        ((FAILED++))
        return 1
    fi
}

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "📁 项目目录: $PROJECT_ROOT"
echo ""

# ========== Stage 1: 代码质量校验与单元测试 ==========

echo ""
echo "🔷 Stage 1: 代码质量校验与单元测试"
echo "======================================"

# 检查 Python 版本
run_step "检查 Python 版本" "python --version"

# 安装依赖
run_step "安装项目依赖" "pip install -q -r requirements.txt"

# 安装测试工具
run_step "安装测试工具" "pip install -q pytest pytest-cov safety pip-audit"

# 运行单元测试
run_step "运行单元测试 (阈值: 25%)" \
    "pytest tests/ --cov=src --cov-report=term --cov-fail-under=25 -v --tb=short"

# 生成覆盖率报告
run_step "生成 HTML 覆盖率报告" \
    "pytest tests/ --cov=src --cov-report=html -q"

echo ""
echo "📊 覆盖率报告已生成: htmlcov/index.html"
echo ""

# ========== Stage 2: 敏感信息扫描 ==========

echo ""
echo "🔷 Stage 2: 敏感信息扫描"
echo "======================================"

# 运行安全扫描器
run_step "执行敏感信息扫描" \
    "python -m src.utils.security_scanner . --format text --max-critical 10 --max-high 10 || true"

# ========== Stage 3: 依赖安全扫描 ==========

echo ""
echo "🔷 Stage 3: 依赖安全扫描"
echo "======================================"

# Safety 扫描（允许失败，继续执行）
run_step "Safety 依赖漏洞扫描" \
    "safety check --full-report || echo '⚠️ Safety 扫描发现问题（非阻塞）'"

# pip-audit 扫描
run_step "pip-audit 依赖扫描" \
    "pip-audit --desc || echo '⚠️ pip-audit 发现问题（非阻塞）'"

# ========== Stage 4: Docker 镜像构建测试 ==========

echo ""
echo "🔷 Stage 4: Docker 镜像构建测试"
echo "======================================"

# 检查 Docker 是否可用
if command -v docker &> /dev/null; then
    run_step "构建 Docker 镜像" \
        "docker build -t openclaw:test ."
    
    echo ""
    echo "🐳 Docker 镜像构建成功"
    echo "   镜像: openclaw:test"
    echo ""
else
    echo -e "${YELLOW}⚠️ Docker 未安装，跳过镜像构建测试${NC}"
fi

# ========== 汇总报告 ==========

echo ""
echo "======================================"
echo "📊 CI 测试结果汇总"
echo "======================================"
echo -e "${GREEN}通过: $PASSED${NC}"
echo -e "${RED}失败: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 所有检查通过！CI 应该可以正常运行。${NC}"
    echo ""
    echo "提示: 在实际 CI 中还需要配置 GitHub Secrets 才能推送镜像和部署"
    exit 0
else
    echo -e "${RED}⚠️ 有 $FAILED 个检查失败，请修复后重试。${NC}"
    exit 1
fi
