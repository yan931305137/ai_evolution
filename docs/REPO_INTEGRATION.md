# GitHub 和 Gitee 代码仓库管理功能

## 概述

本项目已成功集成 GitHub 和 Gitee 代码仓库管理功能，Agent 现在可以通过工具直接访问和管理这两个平台的代码仓库。

## 功能特性

### 1. GitHub 支持
- ✅ 获取用户仓库列表（支持认证和公共用户）
- ✅ 获取单个仓库详细信息
- ✅ 查看仓库元数据（Stars, Forks, 语言等）
- ✅ 克隆仓库到本地

### 2. Gitee 支持
- ✅ 获取用户仓库列表（支持认证和公共用户）
- ✅ 获取单个仓库详细信息
- ✅ 查看仓库元数据（Stars, Forks, 语言等）
- ✅ 克隆仓库到本地

### 3. 统一管理
- ✅ 同时管理多个平台的仓库
- ✅ 统一的仓库信息结构
- ✅ 灵活的认证方式

## 可用工具

### 1. `list_github_repos(username=None)`
获取 GitHub 仓库列表。

**参数:**
- `username` (可选): GitHub 用户名。如果不提供，则获取认证用户的仓库（需要设置 GITHUB_TOKEN）

**示例:**
```
# 获取公共用户的仓库
list_github_repos("octocat")

# 获取自己的仓库（需要设置 GITHUB_TOKEN）
list_github_repos()
```

### 2. `list_gitee_repos(username=None)`
获取 Gitee 仓库列表。

**参数:**
- `username` (可选): Gitee 用户名。如果不提供，则获取认证用户的仓库（需要设置 GITEE_TOKEN）

**示例:**
```
# 获取公共用户的仓库
list_gitee_repos("liugezhou")

# 获取自己的仓库（需要设置 GITEE_TOKEN）
list_gitee_repos()
```

### 3. `list_all_repos(username=None)`
同时获取 GitHub 和 Gitee 的仓库列表。

**参数:**
- `username` (可选): 用户名。如果不提供，则获取认证用户的仓库

**示例:**
```
# 获取所有平台的仓库
list_all_repos()
```

### 4. `clone_repo(repo_url, target_dir, branch=None)`
克隆代码仓库到本地。

**参数:**
- `repo_url`: 仓库的克隆 URL（HTTPS 或 SSH）
- `target_dir`: 本地目标目录
- `branch` (可选): 要克隆的分支名

**示例:**
```
# 克隆 GitHub 仓库
clone_repo("https://github.com/octocat/Hello-World.git", "/tmp/my_repo")

# 克隆特定分支
clone_repo("https://github.com/user/repo.git", "/tmp/my_repo", "develop")

# 克隆 Gitee 仓库
clone_repo("https://gitee.com/user/repo.git", "/tmp/my_repo")
```

### 5. `get_repo_info(platform, owner, repo_name)`
获取单个仓库的详细信息。

**参数:**
- `platform`: 平台名称（`github` 或 `gitee`）
- `owner`: 仓库所有者用户名
- `repo_name`: 仓库名称

**示例:**
```
# 获取 GitHub 仓库信息
get_repo_info("github", "octocat", "Hello-World")

# 获取 Gitee 仓库信息
get_repo_info("gitee", "liugezhou", "studyweb")
```

## 配置认证

### GitHub 认证

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token" -> "Generate new token (classic)"
3. 选择权限：
   - `repo` (完整控制私有仓库)
   - `public_repo` (只访问公共仓库)
4. 复制生成的 Token
5. 设置环境变量：

```bash
export GITHUB_TOKEN=your_github_token_here
```

### Gitee 认证

1. 访问 https://gitee.com/profile/personal_access_tokens
2. 点击 "生成新令牌"
3. 选择权限：
   - `projects` (访问项目)
   - `user_info` (访问用户信息)
4. 复制生成的 Token
5. 设置环境变量：

```bash
export GITEE_TOKEN=your_gitee_token_here
```

### 永久配置

将环境变量添加到 `.env` 文件：

```bash
# 复制示例配置
cp .env.example.repo .env

# 编辑 .env 文件，填入你的 Token
vim .env
```

## 使用示例

### 示例 1: 查看某个用户的 GitHub 仓库

```
你可以这样使用：
"帮我查看 octocat 用户在 GitHub 上有哪些仓库"
"获取 GitHub 用户 torvalds 的仓库列表"
```

Agent 会调用 `list_github_repos("octocat")` 工具。

### 示例 2: 克隆一个项目

```
"帮我把这个项目克隆到 /tmp/myproject 目录：https://github.com/user/project.git"
"克隆 Gitee 上的这个仓库到本地：https://gitee.com/user/repo.git"
```

Agent 会调用 `clone_repo()` 工具。

### 示例 3: 查看仓库详细信息

```
"告诉我 GitHub 上的 octocat/Hello-World 仓库的详细信息"
"查看 Gitee 上某个仓库的 star 数和 fork 数"
```

Agent 会调用 `get_repo_info()` 工具。

### 示例 4: 同时管理多个平台

```
"帮我查看我在 GitHub 和 Gitee 上所有的仓库"
"列出我在两个平台的代码项目"
```

Agent 会调用 `list_all_repos()` 工具。

## 架构说明

### 文件结构

```
src/tools/
├── repo_tools.py              # 核心仓库管理逻辑
│   ├── GitHubClient          # GitHub API 客户端
│   ├── GiteeClient          # Gitee API 客户端
│   ├── Repository           # 仓库数据类
│   └── RepositoryManager    # 统一管理器
│
└── repository_tools.py        # LangChain 工具包装器
    ├── list_github_repos
    ├── list_gitee_repos
    ├── list_all_repos
    ├── clone_repo
    └── get_repo_info
```

### 技术实现

1. **GitHub API**
   - 使用 REST API v3
   - 支持无认证公共访问
   - 支持 Token 认证

2. **Gitee API**
   - 使用 REST API v5
   - 支持无认证公共访问
   - 支持 Token 认证

3. **克隆功能**
   - 使用 git 命令行工具
   - 支持分支选择
   - 自动处理目录创建

## 测试

运行完整测试套件：

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行测试
python tests/test_repo_tools.py
```

测试包括：
- ✅ GitHub 客户端功能
- ✅ Gitee 客户端功能
- ✅ 仓库管理器
- ✅ 克隆功能
- ✅ LangChain 工具集成

## 最佳实践

### 1. 安全性
- ⚠️ 不要将 Token 提交到代码仓库
- ⚠️ 使用最小权限原则
- ⚠️ 定期轮换 Token
- ⚠️ 使用 `.env` 文件管理敏感信息

### 2. 使用建议
- 对于公共仓库，不需要认证即可访问
- 对于私有仓库，必须提供 Token
- 克隆大型仓库时，建议使用 SSH URL 和密钥认证
- 注意 API 速率限制（GitHub: 60次/小时，Gitee: 500次/小时）

### 3. 错误处理
- 网络错误会自动重试
- 无效的仓库 URL 会返回清晰的错误信息
- 权限不足时会提示需要认证

## 限制

1. **API 限制**
   - GitHub: 未认证 60 次/小时，认证 5000 次/小时
   - Gitee: 未认证 60 次/小时，认证 500 次/小时

2. **功能限制**
   - 目前不支持创建/删除仓库
   - 不支持 issue/PR 管理
   - 不支持 Wiki 管理

3. **网络要求**
   - 需要能够访问 github.com 和 gitee.com
   - 克隆功能需要 git 命令行工具

## 未来扩展

计划中的功能：
- [ ] 支持 GitLab 平台
- [ ] 支持创建仓库
- [ ] 支持 issue 和 PR 管理
- [ ] 支持仓库搜索
- [ ] 支持批量克隆
- [ ] 支持 SSH 密钥认证

## 常见问题

### Q: 为什么某些仓库无法访问？
A: 可能的原因：
1. 仓库是私有的，需要提供 Token
2. 仓库不存在或已被删除
3. 网络连接问题
4. API 速率限制

### Q: 如何提高 API 速率限制？
A: 创建 Personal Access Token 并设置环境变量，认证用户的速率限制会显著提高。

### Q: 克隆仓库失败怎么办？
A: 检查以下几点：
1. 仓库 URL 是否正确
2. 网络连接是否正常
3. 是否有访问权限
4. git 命令行工具是否可用
5. 目标目录是否有写权限

### Q: 可以同时管理 GitHub 和 Gitee 吗？
A: 可以！使用 `list_all_repos()` 工具可以同时获取两个平台的仓库列表。

## 贡献

如需添加新功能或修复问题，请：
1. 在 `src/tools/repo_tools.py` 中添加核心逻辑
2. 在 `src/tools/repository_tools.py` 中添加 LangChain 工具包装器
3. 在 `src/tools/__init__.py` 中注册工具
4. 在 `tests/test_repo_tools.py` 中添加测试用例

## 许可

本功能集成遵循项目的整体许可证。
