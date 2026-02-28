# CI/CD 故障排查指南

## 一、快速排查流程

1. 查看CI运行状态 → 2. 检查错误日志 → 3. 定位问题类型 → 4. 执行对应解决方案 → 5. 重跑CI验证


## 二、常见问题与解决方案

### 🚩 问题1：CI/CD 未触发
**现象**：代码提交/手动触发后无CI运行记录
**排查步骤**：
1. 检查CI功能是否开启
python
from src.utils.config import cfg
print(cfg.get("self_evolution.cicd.enabled")) # 需返回True

2. 检查GitHub Token是否配置正确且未过期
3. 检查分支是否匹配工作流触发规则（查看.github/workflows/ci.yml的on配置）
4. 检查工作流文件名是否和配置一致

### 🚩 问题2：认证失败
**现象**：CI触发时报401/403错误
**排查步骤**：
1. 确认GitHub Token包含`repo`、`workflow`、`pull_requests:write`权限
2. 确认Token未过期、未被撤销
3. 确认配置的owner和repo名称完全匹配GitHub上的仓库信息

### 🚩 问题3：工作流运行失败
**现象**：CI触发后执行到某一步报错
**排查步骤**：
1. 下载CI运行日志，定位具体报错步骤
2. 依赖安装失败：检查requirements.txt是否完整、镜像源是否可用
3. 测试用例失败：查看测试报告，修复对应的代码/测试用例
4. 代码检查失败：根据flake8/mypy的报错信息修复代码规范问题

### 🚩 问题4：PR创建失败
**现象**：CI测试通过后无自动创建PR
**排查步骤**：
1. 检查配置中`create_pr`是否设为True
2. 检查目标分支是否存在，是否有合并冲突
3. 检查是否已有相同分支的未合并PR

### 🚩 问题5：自动合并失败
**现象**：PR创建后无法自动合并
**排查步骤**：
1. 检查是否开启了分支保护规则，是否满足合并条件
2. 检查PR是否存在合并冲突，需先手动解决冲突
3. 检查Token是否有PR合并权限

## 三、日志查看方法
### 3.1 在线查看日志
1. 打开GitHub仓库 → Actions → 对应CI运行记录 → 查看各步骤日志
2. 通过代码查询日志：
python
from src.tools.cicd_tools import get_ci_logs
logs = get_ci_logs(run_id=123456789, max_lines=200)
print(logs)


## 四、紧急回滚方案
当CI上线后发现生产问题时：
1. 立即暂停自动进化功能：将`self_evolution.enabled`设为False
2. 找到最近一次正常的commit，手动回滚main分支
3. 触发回滚后的CI流水线，验证恢复正常
4. 排查问题根因，修复后重新上线

## 五、联系支持
如遇无法解决的问题，可联系DevOps团队，提供以下信息：
- CI运行ID/链接
- 错误日志截图
- 触发CI的分支/ commit信息