# GitHub 推送配置指南

## ⚠️ 紧急：Token 已泄露！

你刚才发送的 token 是敏感信息，请**立即撤销**：

1. 打开 https://github.com/settings/tokens
2. 找到名为 `ghp_r8sTR...` 的 token
3. 点击 **Delete**
4. 点击 **Generate new token** 创建新的

---

## 配置步骤

### 第一步：生成新的 GitHub Token

1. 访问: https://github.com/settings/tokens
2. 点击 **Generate new token (classic)**
3. 填写信息:
   - **Note**: `OpenClaw Push`
   - **Expiration**: 根据需要选择（建议 30-90 天）
   - **Scopes**: 勾选
     - ✅ `repo` (完整仓库访问)
     - ✅ `workflow` (如果需要更新 CI/CD)

4. 点击 **Generate token**
5. **立即复制 token**（页面关闭后无法再次查看）

### 第二步：配置到 .env 文件

编辑 `.env` 文件：

```bash
# 将这一行替换为你的新 token
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
```

### 第三步：配置 GitHub Secrets（用于 CI/CD）

1. 打开: https://github.com/yan931305137/ai_evolution/settings/secrets/actions
2. 点击 **New repository secret**
3. Name: `GITHUB_TOKEN`
4. Value: 粘贴你的新 token
5. 点击 **Add secret**

### 第四步：测试推送

```bash
# 配置 Git 使用 token
git remote set-url origin https://ghp_你的TOKEN@github.com/yan931305137/ai_evolution.git

# 或者使用 SSH 方式（推荐）
git remote set-url origin git@github.com:yan931305137/ai_evolution.git

# 测试推送
git push origin main
```

---

## 两种推送方式

### 方式一：HTTPS + Token（简单，但不安全）

```bash
# 每次推送都需要输入 token
git remote set-url origin https://ghp_你的TOKEN@github.com/yan931305137/ai_evolution.git
```

### 方式二：SSH 密钥（推荐，更安全）

```bash
# 1. 生成 SSH 密钥
ssh-keygen -t ed25519 -C "你的邮箱@example.com"

# 2. 添加公钥到 GitHub
# 访问: https://github.com/settings/keys
# 点击 New SSH key
# 粘贴 ~/.ssh/id_ed25519.pub 的内容

# 3. 配置仓库使用 SSH
git remote set-url origin git@github.com:yan931305137/ai_evolution.git

# 4. 测试
git push
```

---

## 配置清单

- [ ] 撤销旧的泄露 token
- [ ] 生成新的 GitHub token
- [ ] 更新 `.env` 文件中的 `GITHUB_TOKEN`
- [ ] （可选）配置 GitHub Secrets
- [ ] 测试 `git push` 成功

---

## 🔐 安全提醒

1. **Token 权限最小化**
   - 只给必要的权限
   - 设置过期时间

2. **不要在代码中硬编码 token**
   - `.env` 已在 `.gitignore` 中，不会提交
   - CI/CD 使用 GitHub Secrets

3. **定期轮换 token**
   - 建议每 3 个月更换一次

4. **监控 token 使用**
   - GitHub 会显示 token 最近使用时间
