# CI/CD 平台切换指南

本文档介绍如何在 GitHub 和 Gitee 之间切换 CI/CD 平台。

## 快速切换

### 方法 1: 通过 `.env` 文件切换（推荐）

编辑项目根目录的 `.env` 文件：

```bash
# 切换到 GitHub
CICD_PLATFORM=github

# 切换到 Gitee
CICD_PLATFORM=gitee
```

修改后重新加载环境变量：

```bash
export $(cat .env | grep -v '#' | xargs)
```

### 方法 2: 通过环境变量临时切换

```bash
# 临时切换到 Gitee（仅当前终端会话有效）
export CICD_PLATFORM=gitee

# 临时切换到 GitHub
export CICD_PLATFORM=github
```

### 方法 3: 通过代码动态切换

```python
from src.utils.cicd_manager import switch_cicd_platform

# 切换到 Gitee
manager = switch_cicd_platform("gitee")

# 切换到 GitHub
manager = switch_cicd_platform("github")
```

## 平台配置

### GitHub 配置

1. 获取 GitHub Token:
   - 访问 https://github.com/settings/tokens
   - 创建 Personal Access Token
   - 权限: `repo`, `workflow`, `pull_requests:write`

2. 配置 `.env`:
   ```bash
   CICD_PLATFORM=github
   GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
   GITHUB_OWNER=你的用户名
   GITHUB_REPO=你的仓库名
   ```

3. GitHub Actions 工作流文件: `.github/workflows/ci-cd-pipeline.yml`

### Gitee 配置

1. 获取 Gitee Token:
   - 访问 https://gitee.com/profile/personal_access_tokens
   - 创建私人令牌
   - 权限: `projects`, `hook`, `pull_requests`

2. 配置 `.env`:
   ```bash
   CICD_PLATFORM=gitee
   GITEE_TOKEN=your_gitee_token_here
   GITEE_OWNER=你的用户名
   GITEE_REPO=你的仓库名
   ```

3. Gitee CI/CD 流水线文件: `.gitee-ci.yml`

## 验证配置

### 检查当前配置

```bash
python -m src.utils.cicd_manager status
```

输出示例：
```
当前平台: gitee
启用状态: ✅ 已启用
仓库: username/openclaw
进化分支: evolution
自动触发: 是
自动合并 PR: 否
```

### 测试触发 CI/CD

```bash
# 触发当前配置的 CI/CD
python -m src.utils.cicd_manager trigger dev
```

## 平台特性对比

| 特性 | GitHub | Gitee |
|------|--------|-------|
| 国内访问速度 | 较慢 | 快速 |
| 免费私有仓库 | 是 | 是 |
| Actions/流水线 | GitHub Actions | Gitee Go |
| 配置文件 | `.github/workflows/*.yml` | `.gitee-ci.yml` |
| 镜像仓库 | Docker Hub/阿里云 | 阿里云（推荐） |
| PyPI 镜像 | 官方 | 阿里云镜像 |

## 推荐配置

### 国内用户（推荐 Gitee）

```bash
# .env
CICD_PLATFORM=gitee

# 使用阿里云镜像加速
DOCKER_REGISTRY=registry.cn-hangzhou.aliyuncs.com
DOCKER_IMAGE_NAME=your-namespace/openclaw
```

### 国际用户（推荐 GitHub）

```bash
# .env
CICD_PLATFORM=github

# 使用 Docker Hub
DOCKER_REGISTRY=docker.io
DOCKER_IMAGE_NAME=your-username/openclaw
```

## 自动检测逻辑

如果没有设置 `CICD_PLATFORM`，系统会按以下顺序自动检测：

1. 检查 `CICD_PLATFORM` 环境变量
2. 检查是否存在 Gitee 配置文件 (`.gitee-ci.yml`) 和 Token
3. 默认使用 GitHub

## 在进化系统中使用

进化系统会自动读取当前 CI/CD 配置：

```python
from src.utils.cicd_manager import get_cicd_manager

manager = get_cicd_manager()

if manager.is_enabled():
    # 触发 CI/CD
    manager.trigger_cicd(branch="evolution")
    
    # 获取状态
    status = manager.get_cicd_status()
    print(f"CI/CD 状态: {status}")
```

## 故障排查

### 问题 1: "CI/CD 未启用"

检查 Token 是否配置：
```bash
echo $GITHUB_TOKEN  # 或 $GITEE_TOKEN
```

### 问题 2: 触发失败

检查仓库信息：
```bash
python -m src.utils.cicd_manager status
```

### 问题 3: 平台切换不生效

重新加载环境变量：
```bash
unset CICD_PLATFORM
export $(cat .env | grep -v '#' | xargs)
```

## 参考文档

- [GitHub Actions 文档](https://docs.github.com/cn/actions)
- [Gitee CI/CD 文档](https://gitee.com/help/categories/53)
