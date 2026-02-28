# GitHub Secrets 配置指南

本文档说明如何配置 CI/CD 所需的 GitHub Secrets。

## 🔐 必需的 Secrets

### 1. 容器镜像仓库配置

用于构建和推送 Docker 镜像到阿里云容器镜像服务 (ACR)。

| Secret Name | 说明 | 获取方式 |
|------------|------|---------|
| `DOCKER_IMAGE_NAME` | 镜像名称 | 例如: `mynamespace/openclaw` |
| `DOCKER_REGISTRY_USER` | 阿里云账号 | 阿里云控制台 > 右上角头像 |
| `DOCKER_REGISTRY_PASSWORD` | 阿里云登录密码或访问令牌 | 阿里云控制台 > 访问控制 > 创建 AccessKey |

#### 配置步骤：

1. **登录阿里云控制台**: https://www.aliyun.com
2. **开通容器镜像服务**: https://cr.console.aliyun.com
3. **创建命名空间**: 在【实例列表】中创建个人版实例
4. **创建镜像仓库**: 记录仓库路径，格式为 `命名空间/仓库名`
5. **获取访问凭证**:
   - 方式一：使用阿里云账号密码
   - 方式二（推荐）：创建 AccessKey
     - 进入【访问控制 RAM】>【AccessKey 管理】
     - 创建 AccessKey，记录 `AccessKey ID` 和 `AccessKey Secret`

6. **在 GitHub 配置 Secrets**:
   ```
   GitHub 仓库页面 > Settings > Secrets and variables > Actions > New repository secret
   ```

### 2. 测试服务器配置

用于自动部署到测试服务器。

| Secret Name | 说明 | 获取方式 |
|------------|------|---------|
| `TEST_SERVER_HOST` | 测试服务器 IP 或域名 | 你的服务器地址 |
| `TEST_SERVER_USER` | SSH 用户名 | 通常是 `root` 或其他有权限的用户 |
| `TEST_SERVER_SSH_KEY` | SSH 私钥 | 生成密钥对，公钥添加到服务器 |

#### 配置步骤：

1. **生成 SSH 密钥对**（在本地执行）：
   ```bash
   ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/github_actions
   # 或传统 RSA 格式
   ssh-keygen -t rsa -b 4096 -C "github-actions" -f ~/.ssh/github_actions
   ```

2. **添加公钥到服务器**：
   ```bash
   # 复制公钥内容
   cat ~/.ssh/github_actions.pub
   
   # 在服务器上添加到 authorized_keys
   echo "<粘贴公钥内容>" >> ~/.ssh/authorized_keys
   ```

3. **配置 Secrets**：
   - `TEST_SERVER_HOST`: 例如 `192.168.1.100` 或 `test.example.com`
   - `TEST_SERVER_USER`: 例如 `root` 或 `ubuntu`
   - `TEST_SERVER_SSH_KEY`: 复制私钥文件内容
     ```bash
     cat ~/.ssh/github_actions
     ```

## 📝 配置清单

在 GitHub 仓库中配置以下 6 个 Secrets：

```
✅ DOCKER_IMAGE_NAME        = your-namespace/openclaw
✅ DOCKER_REGISTRY_USER     = your-aliyun-username
✅ DOCKER_REGISTRY_PASSWORD = your-aliyun-password-or-accesskey-secret
✅ TEST_SERVER_HOST         = your-server-ip-or-domain
✅ TEST_SERVER_USER         = root
✅ TEST_SERVER_SSH_KEY      = -----BEGIN OPENSSH PRIVATE KEY-----
                              ...
                              -----END OPENSSH PRIVATE KEY-----
```

## 🔧 验证配置

### 1. 验证 Docker 配置

```bash
# 本地测试登录
docker login --username=your-username registry.cn-hangzhou.aliyuncs.com

# 测试构建和推送
docker build -t registry.cn-hangzhou.aliyuncs.com/your-namespace/openclaw:test .
docker push registry.cn-hangzhou.aliyuncs.com/your-namespace/openclaw:test
```

### 2. 验证 SSH 配置

```bash
# 使用生成的密钥测试连接
ssh -i ~/.ssh/github_actions root@your-server-ip

# 测试后在服务器上检查
whoami  # 应该显示 root
```

## 🚨 安全注意事项

1. **不要泄露 Secrets**:
   - 不要在代码中硬编码 secrets
   - 不要在日志中打印 secrets
   - 定期轮换 AccessKey 和 SSH 密钥

2. **最小权限原则**:
   - 为 GitHub Actions 创建专门的阿里云子账号，只授予容器镜像服务权限
   - 服务器用户只授予必要的部署权限

3. **网络访问控制**:
   - 限制测试服务器的 SSH 访问来源（仅允许 GitHub Actions IP 段）
   - 使用安全组规则限制端口访问

## 🔄 其他可选配置

### 修改镜像仓库

如果不想使用阿里云，可以修改 `.github/workflows/ci-cd-pipeline.yml`：

```yaml
# 使用 Docker Hub
env:
  DOCKER_REGISTRY: 'docker.io'
  DOCKER_IMAGE_NAME: ${{ secrets.DOCKERHUB_USERNAME }}/openclaw

# 使用 GitHub Container Registry
env:
  DOCKER_REGISTRY: 'ghcr.io'
  DOCKER_IMAGE_NAME: ${{ github.repository }}
```

### 禁用自动部署

如果暂时不需要自动部署，可以删除或注释掉 `deploy-test` job：

```yaml
# 在 ci-cd-pipeline.yml 中注释掉以下内容
#
#  deploy-test:
#    runs-on: ubuntu-latest
#    needs: build-image
#    if: github.ref == 'refs/heads/dev'
#    steps:
#      ...
```

## 🆘 故障排查

### 问题：Docker 登录失败
```
Error response from daemon: login attempt failed
```
**解决**: 检查 `DOCKER_REGISTRY_USER` 和 `DOCKER_REGISTRY_PASSWORD` 是否正确

### 问题：SSH 连接失败
```
ssh: connect to host xxx port 22: Connection timed out
```
**解决**: 检查服务器安全组是否开放 22 端口，防火墙设置

### 问题：权限 denied
```
Permission denied (publickey)
```
**解决**: 检查 SSH 公钥是否正确添加到服务器的 `~/.ssh/authorized_keys`

## 📚 参考文档

- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [阿里云容器镜像服务](https://help.aliyun.com/product/60716.html)
- [Docker 官方文档](https://docs.docker.com/)
