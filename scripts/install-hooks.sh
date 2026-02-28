#!/bin/bash
#
# 安装 Git hooks 脚本
# 安装安全预提交钩子
#

set -e

PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo "$(cd "$(dirname "$0")/.." && pwd)")
HOOKS_DIR="$PROJECT_ROOT/.git/hooks"
SCRIPTS_DIR="$PROJECT_ROOT/scripts"

echo "🔧 Installing Git hooks for security checks..."

# 检查 .git 目录是否存在
if [ ! -d "$PROJECT_ROOT/.git" ]; then
    echo "❌ Error: Not a git repository"
    exit 1
fi

# 创建 hooks 目录（如果不存在）
mkdir -p "$HOOKS_DIR"

# 备份现有的 pre-commit 钩子
if [ -f "$HOOKS_DIR/pre-commit" ]; then
    BACKUP_NAME="pre-commit.backup.$(date +%Y%m%d_%H%M%S)"
    echo "📦 Backing up existing pre-commit hook to $BACKUP_NAME"
    cp "$HOOKS_DIR/pre-commit" "$HOOKS_DIR/$BACKUP_NAME"
fi

# 安装新的 pre-commit 钩子
cp "$SCRIPTS_DIR/pre-commit-security.sh" "$HOOKS_DIR/pre-commit"
chmod +x "$HOOKS_DIR/pre-commit"

echo "✅ Pre-commit hook installed successfully!"
echo ""
echo "The hook will:"
echo "  - Scan staged files for secrets and sensitive data"
echo "  - Check commit messages for sensitive information"
echo "  - Block commits that contain potential security risks"
echo ""
echo "To bypass (not recommended): git commit --no-verify"
echo "To uninstall: rm $HOOKS_DIR/pre-commit"
