# 快速开始：使用 GitHub 和 Gitee 集成

## 5 分钟快速上手

### 1. 无需认证（公共仓库）

你可以立即使用功能访问公共仓库，无需任何配置：

```python
# 查看某个用户的 GitHub 仓库
list_github_repos("octocat")

# 查看某个用户的 Gitee 仓库
list_gitee_repos("liugezhou")

# 克隆公共仓库
clone_repo("https://github.com/octocat/Hello-World.git", "/tmp/hello-world")
```

### 2. 使用自己的仓库（需要认证）

如果需要访问私有仓库，需要配置 Token：

**步骤 1: 获取 GitHub Token**
1. 访问: https://github.com/settings/tokens
2. 点击 "Generate new token" -> "Generate new token (classic)"
3. 勾选 `repo` 权限
4. 点击生成并复制 Token

**步骤 2: 获取 Gitee Token（可选）**
1. 访问: https://gitee.com/profile/personal_access_tokens
2. 点击 "生成新令牌"
3. 勾选 `projects` 和 `user_info` 权限
4. 点击生成并复制 Token

**步骤 3: 配置环境变量**

```bash
# 方式 1: 临时设置（当前终端有效）
export GITHUB_TOKEN=your_github_token_here
export GITEE_TOKEN=your_gitee_token_here

# 方式 2: 永久设置（添加到 .env 文件）
echo "GITHUB_TOKEN=your_github_token_here" >> .env
echo "GITEE_TOKEN=your_gitee_token_here" >> .env
```

**步骤 4: 使用功能**

```python
# 查看自己的仓库
list_github_repos()
list_gitee_repos()

# 查看所有平台的仓库
list_all_repos()

# 克隆私有仓库
clone_repo("https://github.com/your-username/private-repo.git", "/tmp/private-repo")
```

## 常用命令速查

### 查看仓库

```python
# GitHub 公共用户仓库
list_github_repos("octocat")

# Gitee 公共用户仓库
list_gitee_repos("liugezhou")

# 所有平台仓库
list_all_repos()
```

### 获取仓库详情

```python
# GitHub 仓库详情
get_repo_info("github", "octocat", "Hello-World")

# Gitee 仓库详情
get_repo_info("gitee", "liugezhou", "studyweb")
```

### 克隆仓库

```python
# 克隆到指定目录
clone_repo("https://github.com/user/repo.git", "/path/to/dir")

# 克隆特定分支
clone_repo("https://github.com/user/repo.git", "/path/to/dir", "develop")

# 克隆 Gitee 仓库
clone_repo("https://gitee.com/user/repo.git", "/path/to/dir")
```

## 实际使用场景

### 场景 1: 发现并克隆有趣的项目

**对话示例:**
```
你: "帮我看看 GitHub 上 torvalds 有哪些项目，然后把 Linux 内核仓库克隆下来"

Agent 执行:
1. 调用 list_github_repos("torvalds") 列出所有仓库
2. 识别 Linux 仓库
3. 调用 clone_repo("https://github.com/torvalds/linux.git", "/tmp/linux") 克隆项目
```

### 场景 2: 多平台代码管理

**对话示例:**
```
你: "查看我在 GitHub 和 Gitee 上所有的仓库，告诉我哪个项目 star 数最多"

Agent 执行:
1. 调用 list_all_repos() 获取所有平台仓库
2. 分析 star 数量
3. 返回排名结果
```

### 场景 3: 快速了解一个仓库

**对话示例:**
```
你: "告诉我 GitHub 上的 openai/openai-cookbook 这个仓库的信息"

Agent 执行:
1. 调用 get_repo_info("github", "openai", "openai-cookbook")
2. 返回仓库的详细信息（描述、语言、stars、forks等）
```

## 测试功能

运行测试确保一切正常：

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行测试
python tests/test_repo_tools.py
```

预期输出：
```
============================================================
开始测试代码仓库管理功能
============================================================
...
测试总结
============================================================
GitHub 客户端: ✅ 通过
Gitee 客户端: ✅ 通过
仓库管理器: ✅ 通过
克隆功能: ✅ 通过
LangChain 工具: ✅ 通过

总计: 5/5 测试通过

🎉 所有测试通过！
```

## 故障排除

### 问题 1: 提示 "客户端未初始化"

**原因**: 未配置 Token

**解决**:
```bash
export GITHUB_TOKEN=your_token
export GITEE_TOKEN=your_token
```

### 问题 2: 克隆失败

**原因**: 可能是网络问题或权限问题

**解决**:
1. 检查网络连接
2. 确认仓库 URL 正确
3. 确保有访问权限（私有仓库需要 Token）
4. 检查 git 命令是否可用: `git --version`

### 问题 3: API 速率限制

**原因**: 未认证用户访问频率过高

**解决**:
```bash
# 配置 Token 后速率限制会大幅提高
export GITHUB_TOKEN=your_token
export GITEE_TOKEN=your_token
```

## 下一步

- 📖 阅读完整文档: [docs/REPO_INTEGRATION.md](./REPO_INTEGRATION.md)
- 🧪 运行更多测试: 探索不同的仓库
- 🚀 在实际项目中使用: 开始管理你的代码仓库
- 🤝 贡献功能: 帮助改进这个集成

## 支持

遇到问题？检查：
1. [完整文档](./REPO_INTEGRATION.md) 的常见问题部分
2. 测试是否通过: `python tests/test_repo_tools.py`
3. 环境变量是否正确设置: `echo $GITHUB_TOKEN`

---

**提示**: 对于公共仓库，你可以直接使用而无需任何配置！
