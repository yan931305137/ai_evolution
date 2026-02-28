# CI/CD 使用手册 V2.0

## 一、功能概述
本CI/CD系统支持代码提交后自动触发测试、代码质量检查、PR创建、可选自动合并等全流程自动化，大幅提升研发迭代效率，同时保障代码质量。

## 二、配置指南
### 2.1 环境变量配置（推荐）
bash
export GITHUB_TOKEN="你的GitHub个人访问令牌"
export GITHUB_OWNER="你的GitHub用户名/组织名"
export GITHUB_REPO="目标仓库名"

### 2.2 配置文件方式
编辑 `config/config.yaml`：
yaml
github:
 token: "你的GitHub个人访问令牌"
 owner: "你的GitHub用户名/组织名"
 repo: "目标仓库名"

self_evolution:
 enabled: true
 cicd:
 enabled: true # 启用CI/CD自动化
 auto_trigger: true # 代码应用后自动触发
 branch: "evolution" # 进化分支名称
 create_pr: true # 测试通过后自动创建PR
 auto_merge: false # 自动合并（非生产环境可开启）
 workflow: "ci.yml" # CI工作流文件名

### 2.3 Token权限要求
- `repo`：仓库读写权限
- `workflow`：工作流触发权限
- `pull_requests:write`：PR创建和合并权限

## 三、核心使用流程
### 3.1 标准完整流程

1. 代码提交/想法应用 → 2. 自动触发CI → 3. 执行测试/代码检查 → 4. 自动创建PR → 5. 人工审核后合并

### 3.2 自动进化集成流程

1. 创造阶段：生成优化想法
2. 评估阶段：验证想法可行性
3. 应用阶段：代码修改落地
4. CI/CD阶段：自动执行测试、创建PR
5. 进化阶段：根据CI结果迭代优化策略


## 四、核心工具函数使用
### 4.1 手动触发CI流水线
python
from src.tools.cicd_tools import trigger_ci_pipeline

# 触发指定分支的CI
result = trigger_ci_pipeline(branch="feature/your-feature", wait_for_completion=True)
print(result)

### 4.2 触发进化专用CI流程
python
from src.tools.cicd_tools import run_evolution_ci_pipeline

result = run_evolution_ci_pipeline(
 evolution_branch="evolution",
 create_pr=True,
 auto_merge=False
)

### 4.3 查看CI状态
python
from src.tools.cicd_tools import check_ci_status
status = check_ci_status(run_id=123456789)
print(f"CI状态：{status}")

### 4.4 手动创建PR
python
from src.tools.cicd_tools import create_pr_from_branch
result = create_pr_from_branch(
 branch="feature/your-feature",
 title="新增XX功能",
 body="功能说明：xxxx",
 base_branch="main"
)


## 五、最佳实践
1. **分支策略**：main为生产分支，evolution为自动进化分支，功能开发使用feature/xxx命名的分支
2. **安全规范**：生产环境不开启auto_merge，所有PR必须人工审核后合并
3. **保护分支配置**：在GitHub仓库设置中为main分支开启PR审核、状态检查通过才能合并的规则
4. **监控配置**：可自定义CI状态变更回调，及时接收异常告警

## 六、版本历史
- V2.0 2026-03-01：新增自动进化集成、灰度测试支持、故障排查指引
- V1.0 2026-02-28：初始版本，基础CI/CD功能