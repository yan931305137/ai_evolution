# GitHub Actions 运行环境变量配置指引
## 需配置的三个必填参数

### 1. GITHUB_TOKEN
- **获取方式**：进入GitHub账号 -> Settings -> Developer settings -> Personal access tokens -> 新建经典令牌（Tokens(classic)）
- **权限要求**：必须勾选`repo`、`workflow`两个权限范围
- **配置位置**：项目仓库页面 -> Settings -> Secrets and variables -> Actions -> Secrets -> 点击「New repository secret」添加

### 2. GITHUB_OWNER
- **取值规则**：你的GitHub用户名或组织名，例如仓库地址为`https://github.com/zhangsan/my-app`则值为`zhangsan`
- **配置位置**：项目仓库页面 -> Settings -> Secrets and variables -> Actions -> Variables -> 点击「New repository variable」添加

### 3. GITHUB_REPO
- **取值规则**：当前项目的仓库名，例如仓库地址为`https://github.com/zhangsan/my-app`则值为`my-app`
- **配置位置**：同上Variables位置添加

## 配置完成后验证流程
配置完成后执行CI流水线触发命令即可验证优化效果：
1. 自动执行静态代码扫描、依赖漏洞双检测、镜像签名校验、最小权限管控4项核心安全能力
2. 自动统计构建时长，对比优化前数据确认是否达到≥15%的优化目标
3. 连续运行15次全量构建成功率达到100%即可通过安全团队核验