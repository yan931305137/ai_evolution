# SSH Key 项目配置指南

## 🎯 配置位置总览

```
┌────────────────────────────────────────────────────────────────────┐
│  1️⃣ GitHub Secrets（私钥）                                          │
│     位置: https://github.com/你的用户名/openclaw/settings/secrets   │
│                                                                       │
│  2️⃣ 服务器 authorized_keys（公钥）                                  │
│     位置: root@你的服务器IP:~/.ssh/authorized_keys                   │
│                                                                       │
│  3️⃣ CI/CD 配置文件（引用）                                           │
│     位置: .github/workflows/ci-cd-pipeline.yml                       │
└────────────────────────────────────────────────────────────────────┘
```

---

## 📍 第一步：在 GitHub 项目中配置私钥

### 操作地址
```
https://github.com/你的用户名/openclaw/settings/secrets/actions
```

### 操作步骤

1. **打开 GitHub 仓库页面**
   ```
   https://github.com/你的用户名/openclaw
   ```

2. **点击 Settings 标签**
   
   ![Settings 位置](https://i.imgur.com/example1.png)
   
   在页面顶部，Code / Issues / Pull requests / **Settings**

3. **进入 Secrets 页面**
   
   左侧菜单 → **Secrets and variables** → **Actions**

4. **点击 New repository secret**

5. **填写信息**
   ```
   Name: TEST_SERVER_SSH_KEY
   Value: (粘贴你的私钥内容)
   ```

6. **点击 Add secret**

### 验证是否配置成功
```
页面会显示:
✅ TEST_SERVER_SSH_KEY  Updated just now
```

---

## 📍 第二步：在服务器上配置公钥

### 连接到你的服务器

```bash
# 用你现有的方式连接服务器
ssh root@你的服务器IP

# 或者如果有现有密钥
ssh -i 现有密钥 root@服务器IP
```

### 在服务器上执行

```bash
# 1. 创建 .ssh 目录
mkdir -p ~/.ssh

# 2. 添加公钥到 authorized_keys
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI... github-actions" >> ~/.ssh/authorized_keys

# ⚠️ 注意：把上面的内容换成你的真实公钥

# 3. 设置正确的权限
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys

# 4. 验证
ls -la ~/.ssh/
# 应该显示:
# drwx------ 2 root root  .ssh/
# -rw------- 1 root root  authorized_keys
```

---

## 📍 第三步：验证 CI/CD 配置引用

### 检查配置文件

文件: `.github/workflows/ci-cd-pipeline.yml`

```yaml
# 第 5 阶段：测试环境自动部署
deploy-test:
  runs-on: ubuntu-latest
  needs: build-image
  if: github.ref == 'refs/heads/dev'
  steps:
    - name: 配置SSH连接测试服务器
      uses: appleboy/ssh-action@v1.0.3
      with:
        host: ${{ env.TEST_SERVER_HOST }}        # ← 需要配置 Secret
        username: ${{ env.TEST_SERVER_USER }}    # ← 需要配置 Secret
        key: ${{ secrets.TEST_SERVER_SSH_KEY }}  # ← 就是你刚才配置的私钥
        script: |
          docker pull ...
          docker run ...
```

### 其他需要配置的 Secrets

除了 `TEST_SERVER_SSH_KEY`，还需要配置：

| Secret Name | 说明 | 配置位置 |
|-------------|------|----------|
| `TEST_SERVER_HOST` | 服务器 IP 或域名 | GitHub Secrets |
| `TEST_SERVER_USER` | SSH 用户名（如 root） | GitHub Secrets |

---

## 🔧 一键配置脚本

### 本地生成密钥并显示配置信息

```bash
#!/bin/bash
# 保存为 setup-ssh.sh，在本地运行

echo "🔐 生成 SSH Key 用于 GitHub Actions..."

# 生成密钥
KEY_NAME="github_actions_$(date +%Y%m%d)"
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/$KEY_NAME -N ""

echo ""
echo "=========================================="
echo "📋 请按以下步骤配置:"
echo "=========================================="
echo ""
echo "【步骤 1】复制私钥到 GitHub Secrets:"
echo "------------------------------------------"
cat ~/.ssh/$KEY_NAME
echo ""
echo "Secret Name: TEST_SERVER_SSH_KEY"
echo ""
echo "【步骤 2】复制公钥到服务器:"
echo "------------------------------------------"
cat ~/.ssh/$KEY_NAME.pub
echo ""
echo "在服务器上执行:"
echo "echo '$(cat ~/.ssh/$KEY_NAME.pub)' >> ~/.ssh/authorized_keys"
echo ""
echo "【步骤 3】测试连接:"
echo "------------------------------------------"
echo "ssh -i ~/.ssh/$KEY_NAME root@你的服务器IP"
echo ""
echo "🔑 密钥文件保存位置:"
echo "   私钥: ~/.ssh/$KEY_NAME"
echo "   公钥: ~/.ssh/$KEY_NAME.pub"
```

---

## ✅ 配置检查清单

- [ ] 在 GitHub Secrets 中添加了 `TEST_SERVER_SSH_KEY`
- [ ] 在 GitHub Secrets 中添加了 `TEST_SERVER_HOST`
- [ ] 在 GitHub Secrets 中添加了 `TEST_SERVER_USER`
- [ ] 在服务器 `~/.ssh/authorized_keys` 中添加了公钥
- [ ] 服务器上 `.ssh` 目录权限为 700
- [ ] 服务器上 `authorized_keys` 文件权限为 600
- [ ] 本地测试连接成功

---

## 🆘 常见问题

### Q: 配置后 CI 还是报 "Permission denied"
A: 检查以下几点：
1. 服务器上 `~/.ssh/authorized_keys` 文件是否存在
2. 文件权限是否正确（700 和 600）
3. GitHub Secret 是否复制了完整的私钥（包含 BEGIN/END 行）

### Q: 应该配置在哪个文件里？
A: **不要**把密钥写到项目文件里！应该：
- 私钥 → GitHub Secrets（GitHub 网站）
- 公钥 → 服务器 ~/.ssh/authorized_keys
- CI 配置文件只引用 `${{ secrets.TEST_SERVER_SSH_KEY }}`

### Q: 如何查看已配置的 Secrets？
A: 在 GitHub 页面上：
```
Settings > Secrets > Actions
```
可以看到已配置的 Secrets 名称，但**看不到内容**（GitHub 会隐藏）。
