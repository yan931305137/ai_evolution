#!/bin/bash
#
# Pre-commit hook for OpenClaw
# 检查敏感信息泄露，阻止包含密钥的提交
#

set -e

echo "🔒 Running security checks..."

# 获取项目根目录
PROJECT_ROOT=$(git rev-parse --show-toplevel)
cd "$PROJECT_ROOT"

# 检查 Python 是否可用
if ! command -v python3 &> /dev/null; then
    echo "⚠️  Warning: python3 not found, skipping security check"
    exit 0
fi

# 获取即将提交的文件
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)

if [ -z "$STAGED_FILES" ]; then
    echo "✅ No staged files to check"
    exit 0
fi

echo "📁 Checking ${#STAGED_FILES[@]} staged files..."

# 创建临时文件列表
TEMP_FILE=$(mktemp)
echo "$STAGED_FILES" > "$TEMP_FILE"

# 运行安全扫描
python3 -c "
import sys
sys.path.insert(0, 'src')
from utils.security_scanner import run_security_scan

with open('$TEMP_FILE', 'r') as f:
    files = [line.strip() for line in f if line.strip()]

if not files:
    print('✅ No files to scan')
    sys.exit(0)

# 只检查已暂存的文件
passed, output = run_security_scan(
    target_path='.',
    output_format='text',
    max_critical=0,
    max_high=0,
    specific_files=files
)

print(output)

if not passed:
    print()
    print('❌ SECURITY CHECK FAILED')
    print('Commit blocked due to potential secrets in staged files.')
    print()
    print('To bypass this check (NOT RECOMMENDED):')
    print('  git commit --no-verify')
    print()
    sys.exit(1)
else:
    print('✅ Security check passed')
    sys.exit(0)
"

EXIT_CODE=$?
rm -f "$TEMP_FILE"

# 额外检查：提交信息
COMMIT_MSG_FILE="$1"
if [ -n "$COMMIT_MSG_FILE" ] && [ -f "$COMMIT_MSG_FILE" ]; then
    echo "📝 Checking commit message..."
    
    python3 -c "
import sys
sys.path.insert(0, 'src')
from utils.security_scanner import check_text_for_secrets

with open('$COMMIT_MSG_FILE', 'r') as f:
    message = f.read()

is_safe, issues = check_text_for_secrets(message)

if not is_safe:
    print('❌ Commit message contains sensitive information:')
    for issue in issues:
        print(f'  - {issue}')
    sys.exit(1)
else:
    print('✅ Commit message check passed')
    sys.exit(0)
"
    
    if [ $? -ne 0 ]; then
        echo "❌ Commit message security check failed"
        exit 1
    fi
fi

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ All security checks passed!"
else
    exit $EXIT_CODE
fi
