# GitHub CI/CD 安全集成文档

## 概述

本文档说明 OpenClaw 项目中 GitHub CI/CD 与安全隐私检查的集成机制，确保在自动化流程中防止敏感信息泄露。

## 安全机制架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      Security Check Layers                       │
├─────────────────────────────────────────────────────────────────┤
│  Layer 1: Pre-commit Hook (Local)                               │
│  ├── 扫描暂存文件中的敏感信息                                    │
│  ├── 检查提交信息安全性                                          │
│  └── 阻止包含 secrets 的提交                                     │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: CI/CD Pipeline (GitHub Actions)                       │
│  ├── 敏感信息扫描 (secrets-scan job)                            │
│  ├── TruffleHog 深度扫描                                         │
│  └── 依赖安全扫描 (security-scan job)                           │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3: Evolution Feedback Loop                               │
│  ├── CI/CD 触发前安全预检查                                      │
│  ├── PR 内容安全检查                                             │
│  └── 日志敏感信息清理                                            │
├─────────────────────────────────────────────────────────────────┤
│  Layer 4: Runtime Protection                                     │
│  ├── API 调用参数检查                                            │
│  ├── 日志自动脱敏                                                │
│  └── 错误信息清理                                                │
└─────────────────────────────────────────────────────────────────┘
```

## 敏感信息检测规则

### 检测类别

1. **API Keys & Tokens (CRITICAL)**
   - GitHub Token (ghp_xxx, gho_xxx, etc.)
   - AWS Access Key (AKIA...)
   - OpenAI API Key (sk-...)
   - Google API Key (AIza...)
   - Slack Token (xoxb-...)
   - Private Keys (RSA, DSA, EC)
   - JWT Tokens
   - Bearer Tokens
   - Coze API Keys

2. **Passwords & Credentials (CRITICAL)**
   - Hardcoded passwords
   - Secret values
   - Admin passwords

3. **Personal Information (HIGH)**
   - Email addresses
   - Chinese phone numbers
   - Chinese ID cards
   - IP addresses

4. **Sensitive URLs (MEDIUM)**
   - Localhost URLs
   - Internal IP addresses

### 例外规则（允许的内容）

以下模式不会被标记为敏感：
- 环境变量引用 (`${VAR}`, `getenv()`)
- 占位符 (`YOUR_KEY_HERE`, `PLACEHOLDER`, `EXAMPLE`)
- 示例域名 (`example.com`)
- 配置文件读取 (`config.get()`, `os.environ.get()`)
- 空/Null 值

## 配置说明

### 1. 环境变量配置 (.env)

```bash
# GitHub CI/CD 安全设置
GITHUB_SECURITY_BLOCK_ON_FAILURE=true
EVOLUTION_CICD_SECURITY_ENABLE_SCAN=true
EVOLUTION_CICD_SECURITY_BLOCK_ON_FAILURE=true
EVOLUTION_CICD_MAX_CRITICAL_ISSUES=0
EVOLUTION_CICD_MAX_HIGH_ISSUES=0
```

### 2. 配置文件 (config/github_cicd.yaml)

```yaml
github:
  security:
    block_on_failure: true
    sanitize_logs: true
    require_security_check_before_pr: true
    require_security_check_for_commits: true

self_evolution:
  cicd:
    security:
      enable_security_scan: true
      block_on_failure: true
      max_critical_issues: 0
      max_high_issues: 0
      include_scan_report_in_pr: true
```

### 3. 规则配置 (config/security_rules.json)

可自定义检测规则和例外模式：

```json
{
  "patterns": {
    "api_keys": {
      "severity": "CRITICAL",
      "patterns": [...]
    }
  },
  "allowed_patterns": [...],
  "severity_levels": {...}
}
```

## 使用指南

### 命令行安全扫描

```bash
# 扫描整个项目
python -m src.utils.security_scanner . --format text

# 扫描指定文件
python -m src.utils.security_scanner --files src/main.py config.yaml

# JSON 格式输出
python -m src.utils.security_scanner . --format json

# Markdown 报告
python -m src.utils.security_scanner . --format markdown
```

### Agent 工具函数

```python
# 扫描代码
from src.tools.security_tools import scan_code_for_secrets

result = scan_code_for_secrets(
    file_paths=["src/main.py"],
    max_critical=0,
    max_high=0
)
print(result["summary"])

# 检查文本安全
from src.tools.security_tools import check_text_security

result = check_text_security("API key: sk-abc123")
print(f"Safe: {result['is_safe']}")
print(f"Issues: {result['issues']}")

# 验证 PR 内容
from src.tools.security_tools import validate_pr_content

result = validate_pr_content(
    title="Fix: update config",
    body="Changed setting to value",
    branch="feature/update"
)
if not result["is_valid"]:
    print(result["recommendation"])

# 清理敏感数据
from src.tools.security_tools import sanitize_sensitive_data

safe_text = sanitize_sensitive_data("Key: sk-secret123")
# 输出: "Key: [REDACTED:OpenAI API Key]"
```

### 预提交钩子

```bash
# 安装 Git hooks
./scripts/install-hooks.sh

# 手动运行安全检查
./scripts/pre-commit-security.sh

# 绕过安全检查（不推荐）
git commit --no-verify
```

## CI/CD 集成流程

### 进化反馈循环中的安全检查

```
┌─────────────┐
│  Evolution  │
│   Apply     │
└──────┬──────┘
       │
       ▼
┌─────────────┐     No      ┌─────────────┐
│ Security    │────────────▶│   Block     │
│ Pre-check   │             │   CI/CD     │
└──────┬──────┘             └─────────────┘
       │ Yes
       ▼
┌─────────────┐     No      ┌─────────────┐
│  PR Content │────────────▶│ Add Warning │
│    Check    │             │   to PR     │
└──────┬──────┘             └─────────────┘
       │ Yes
       ▼
┌─────────────┐
│  Trigger    │
│  CI/CD      │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   GitHub    │
│  Actions    │
│   Pipeline  │
└─────────────┘
```

### GitHub Actions 工作流

1. **secrets-scan job**: 使用内置扫描器和 TruffleHog 扫描代码
2. **security-scan job**: 使用 safety 和 pip-audit 扫描依赖
3. **build-image job**: 仅在安全扫描通过后构建镜像
4. **deploy-test job**: 自动部署到测试环境

## 安全事件响应

### 发现敏感信息时的处理流程

1. **Pre-commit 阶段**
   - 阻止提交
   - 显示具体问题
   - 提供修复建议

2. **CI/CD 阶段**
   - 立即失败并告警
   - 阻止后续流程
   - 记录安全事件

3. **PR 创建阶段**
   - 阻止 PR 创建（可配置）
   - 或在 PR 中添加安全警告
   - 通知管理员

### 修复建议

如果发现敏感信息泄露：

1. **立即撤销凭证**
   ```bash
   # GitHub Token
   https://github.com/settings/tokens
   
   # AWS Keys
   aws iam update-access-key --access-key-id AKIA... --status Inactive
   ```

2. **从历史中移除**
   ```bash
   # 使用 git-filter-repo
   git filter-repo --replace-text <(echo 'sk-secret123==>REDACTED')
   
   # 强制推送
   git push --force
   ```

3. **轮换所有相关凭证**
   - 生成新的 API Keys
   - 更新环境变量
   - 验证应用正常运行

4. **审查访问日志**
   - 检查是否有未授权访问
   - 评估影响范围

## 最佳实践

1. **使用环境变量**
   ```python
   # ❌ 不要硬编码
   API_KEY = "sk-abc123"
   
   # ✅ 使用环境变量
   import os
   API_KEY = os.getenv("API_KEY")
   ```

2. **.gitignore 配置**
   ```gitignore
   # 敏感文件
   .env
   .env.local
   .env.production
   *.key
   *.pem
   secrets.yaml
   config.local.yaml
   ```

3. **占位符使用**
   ```python
   # ✅ 使用占位符
   API_KEY = "YOUR_API_KEY_HERE"
   ```

4. **定期扫描**
   ```bash
   # 定期运行安全扫描
   python -m src.utils.security_scanner . --format markdown > reports/security_report.md
   ```

## 故障排除

### 常见问题

**Q: 安全扫描误报了正常代码**
- 检查 `config/security_rules.json` 中的例外规则
- 添加自定义允许模式

**Q: CI/CD 被安全扫描阻止**
- 检查日志中的具体问题
- 修复敏感信息泄露
- 或临时设置 `EVOLUTION_CICD_SECURITY_BLOCK_ON_FAILURE=false`（不推荐）

**Q: 预提交钩子太慢**
- 仅扫描暂存文件（已默认）
- 排除大文件和依赖目录
- 使用缓存

## 参考资料

- [TruffleHog 文档](https://github.com/trufflesecurity/trufflehog)
- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning)
- [OWASP Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
