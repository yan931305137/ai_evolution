# GitHub CI/CD 集成文档

## 概述

GitHub CI/CD 集成允许 AutoAgent 在代码进化完成后自动触发 GitHub Actions，运行测试、创建 PR、并可选自动合并。

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                  Evolution Feedback Loop                     │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │  Create  │→ │ Evaluate │→ │  Apply   │→│   CI/CD    │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────────┘  │
│                                                   ↓         │
│                                            ┌────────────┐   │
│                                            │  Evolve    │   │
│                                            └────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              GitHub CI/CD Integration                        │
│                                                              │
│  1. Trigger Workflow  →  Run Tests  →  Create PR  →  Merge │
└─────────────────────────────────────────────────────────────┘
```

## 配置

### 1. 环境变量方式（推荐）

```bash
export GITHUB_TOKEN="your_github_personal_access_token"
export GITHUB_OWNER="your_username"
export GITHUB_REPO="your_repo"
```

### 2. 配置文件方式

编辑 `config/config.yaml`:

```yaml
# GitHub Configuration
github:
  token: "your_github_personal_access_token"
  owner: "your_username"
  repo: "your_repo"

# Self-Evolution Configuration
self_evolution:
  enabled: true
  
  # CI/CD Integration
  cicd:
    enabled: true              # 启用 CI/CD 自动化
    auto_trigger: true         # 应用阶段后自动触发
    branch: "evolution"        # 进化分支名称
    create_pr: true            # 成功后自动创建 PR
    auto_merge: false          # 是否自动合并（谨慎开启）
    workflow: "ci.yml"         # CI 工作流文件名
```

### 3. GitHub Token 权限

需要以下权限：
- `repo` - 访问仓库
- `workflow` - 触发工作流
- `pull_requests:write` - 创建和合并 PR

## 工作流程

### 完整进化 + CI/CD 流程

```
1. 创造 (Create)     → 产生新想法
2. 评估 (Evaluate)   → 评估想法质量
3. 应用 (Apply)      → 应用通过评估的想法
4. CI/CD             → 触发 GitHub Actions
   a. 运行测试
   b. 创建 PR
   c. 可选：自动合并
5. 进化 (Evolve)     → 根据结果调整策略
```

## 工具函数

### 1. trigger_ci_pipeline

触发 CI/CD Pipeline 并等待结果。

```python
from src.tools.cicd_tools import trigger_ci_pipeline

# 基本用法
result = trigger_ci_pipeline(branch="main", workflow="ci.yml")

# 不等待完成
result = trigger_ci_pipeline(
    branch="feature/new-auth",
    workflow="ci.yml",
    wait_for_completion=False
)
```

### 2. run_evolution_ci_pipeline

进化专用的完整 CI/CD Pipeline。

```python
from src.tools.cicd_tools import run_evolution_ci_pipeline

# 标准进化流程
result = run_evolution_ci_pipeline(
    evolution_branch="evolution",
    create_pr=True,
    auto_merge=False
)
```

### 3. check_ci_status

检查 CI/CD Pipeline 状态。

```python
from src.tools.cicd_tools import check_ci_status

status = check_ci_status(run_id=1234567890)
print(status)
```

### 4. create_pr_from_branch

从分支创建 PR。

```python
from src.tools.cicd_tools import create_pr_from_branch

result = create_pr_from_branch(
    branch="feature/auth",
    title="Add authentication module",
    body="This PR adds user authentication...",
    base_branch="main"
)
```

### 5. merge_pull_request

合并 PR。

```python
from src.tools.cicd_tools import merge_pull_request

result = merge_pull_request(
    pr_number=42,
    commit_message="Merge authentication feature"
)
```

## 使用示例

### 示例 1: Agent 使用 CI/CD

```python
# Agent 在执行任务后触发 CI
result = agent.run("优化数据库查询性能")

# Agent 自动触发测试
trigger_ci_pipeline(branch="main")
```

### 示例 2: 进化完成后自动 CI/CD

当进化系统启用 CI/CD 后，会在应用阶段自动触发：

```
🔄 启动进化周期 cycle_1699123456
============================================================

🎨 [Stage 1/5] 创造阶段
  💡 优化缓存机制
  💡 重构错误处理

📊 [Stage 2/5] 评估阶段
  已评估: 2 个想法
  推荐应用: 2 个

🔧 [Stage 3/5] 应用阶段
  ✅ 已应用: 优化缓存机制
  ✅ 已应用: 重构错误处理

🚀 [Stage 3.5/5] CI/CD 自动化阶段
  分支: evolution
  自动创建 PR: True
  自动合并: False
  ✅ CI/CD 成功!
     耗时: 125.3s
     提交: abc1234
     PR: #42

🌱 [Stage 5/5] 进化阶段
  应用成功率: 100.0%
  进化速度: 1.00

✅ 进化周期完成，总耗时: 145.2s
```

### 示例 3: 手动触发进化 CI/CD

```python
from src.tools.cicd_tools import run_evolution_ci_pipeline

# 手动触发完整进化流程
result = run_evolution_ci_pipeline(
    evolution_branch="evolution",
    create_pr=True,
    auto_merge=False
)

print(result)
```

输出：
```
✅ Evolution CI Pipeline Complete

Branch: evolution
Status: success
Duration: 125.3s

CI Pipeline completed successfully

📊 Build Details:
- Commit: abc1234
- Message: Apply optimization ideas
- URL: https://github.com/user/repo/actions/runs/123456

📋 Pull Request:
- PR #42
- URL: https://github.com/user/repo/pull/42
```

## GitHub Actions 工作流示例

创建 `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [ main, evolution ]
  pull_request:
    branches: [ main ]
  workflow_dispatch:  # 允许手动触发

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: pytest --cov=src tests/
    
    - name: Lint
      run: |
        pip install flake8
        flake8 src/ --max-line-length=100
    
    - name: Type check
      run: |
        pip install mypy
        mypy src/ --ignore-missing-imports
```

## 自动 PR 模板

进化系统自动创建的 PR 包含：

```markdown
## 🤖 Automated Evolution Changes

This PR contains changes generated by the AI evolution system.

### Changes Summary
- Code improvements based on evaluation
- Automated refactoring and optimizations
- Test coverage enhancements

### Verification
- [x] All tests passing
- [x] Code quality checks passed
- [x] No breaking changes introduced

---
*This PR was automatically created by the Evolution Feedback Loop*
```

## 最佳实践

### 1. 分支策略

```
main              ← 生产分支
  ↑
evolution         ← 进化分支（自动创建 PR）
  ↑
feature/xxx       ← 功能分支（可选）
```

### 2. 安全建议

- **不要启用 auto_merge** 除非你完全信任进化系统
- 始终在合并前人工审查 PR
- 使用保护分支规则防止直接推送到 main

### 3. 配置保护分支

在 GitHub 仓库设置中：
1. Settings → Branches → Add rule
2. Branch name pattern: `main`
3. 勾选：
   - Require pull request reviews before merging
   - Require status checks to pass before merging
   - Include administrators

### 4. 监控 CI/CD

```python
# 在进化循环中设置回调
cicd = GitHubCICDIntegration()

def on_status_change(run: WorkflowRun):
    print(f"Workflow status changed to: {run.status.value}")

def on_complete(result: CICDResult):
    if result.success:
        print("✅ CI/CD passed!")
    else:
        print("❌ CI/CD failed, checking logs...")
        logs = cicd.get_run_logs(result.workflow_run.run_id)
        print(logs)

cicd.on_status_change = on_status_change
cicd.on_complete = on_complete
```

## 故障排除

### 问题 1: CI/CD 未触发

检查：
```python
from src.utils.config import cfg

print(cfg.get("self_evolution.cicd.enabled"))  # 应为 True
print(cfg.get("github.token"))  # 应已设置
```

### 问题 2: 认证失败

确保 GitHub Token 有 `workflow` 权限。

### 问题 3: 工作流未找到

检查 `config.yaml` 中的 workflow 名称是否正确：
```yaml
self_evolution:
  cicd:
    workflow: "ci.yml"  # 确保与 .github/workflows/ 下的文件名匹配
```

## 集成流程图

```
用户/Agent
    ↓
触发进化
    ↓
┌─────────────────┐
│ Evolution Loop  │
│ - Create        │
│ - Evaluate      │
│ - Apply         │
└─────────────────┘
    ↓ (应用成功)
┌─────────────────┐
│ CI/CD Trigger   │
│ - Run tests     │
│ - Build         │
└─────────────────┘
    ↓ (测试通过)
┌─────────────────┐
│ Create PR       │
│ - Auto title    │
│ - Description   │
└─────────────────┘
    ↓ (可选)
┌─────────────────┐
│ Auto Merge      │
│ - Merge to main │
└─────────────────┘
    ↓
Evolution Complete
```
