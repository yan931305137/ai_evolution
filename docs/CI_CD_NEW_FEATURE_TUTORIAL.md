# CI/CD 新功能操作教程

## 一、新增功能总览
本次CI/CD迭代新增5大核心功能：
1. ✨ 自动进化CI/CD全流程集成
2. 🧪 灰度测试执行能力
3. ⏪ 一键回滚功能
4. 📊 CI运行监控看板
5. 🔔 异常告警推送

---

## 二、功能1：自动进化CI/CD全流程集成
**功能说明**：AI自主迭代优化代码后，自动触发CI测试、PR创建，无需人工干预
**操作步骤**：
1. 开启自动进化配置
yaml
# config/config.yaml
self_evolution:
 enabled: true
 cicd:
 enabled: true
 auto_trigger: true
 create_pr: true
 auto_merge: false # 生产环境建议关闭

2. 启动进化系统即可自动触发完整流程
**效果示例**：

🔧 应用阶段完成 → 🚀 自动触发CI → ✅ 测试通过 → 📝 自动创建PR #42


---

## 三、功能2：灰度测试执行
**功能说明**：代码上线前先在小流量环境执行测试，验证无问题再全量上线
**操作步骤**：
1. 编写对应功能的测试用例，存放在tests/目录下
2. 调用灰度测试工具：
python
from src.skills.evolution_skills import grayscale_test_executor

# 执行灰度测试
success, result = grayscale_test_executor(
 module_path="src/utils/your_module.py",
 test_case_paths=["tests/test_your_module.py"],
 coverage_threshold=80.0
)

if success:
 print("✅ 灰度测试通过，可以上线")
else:
 print("❌ 灰度测试不通过，问题：", result["error"])

**指标要求**：测试覆盖率≥80%，用例通过率100%才可进入全量上线流程

---

## 四、功能3：一键回滚功能
**功能说明**：CI上线后发现问题可一键回滚到指定版本，快速恢复业务
**操作步骤**：
python
from src.skills.evolution_skills import deployment_rollback_manager

# 执行回滚
success, result = deployment_rollback_manager(
 target_file_path="src/utils/your_module.py",
 new_version_content=open("backup/old_version.py").read(), # 回滚的版本内容
 smoke_test_case="def test_normal(): assert your_function() == expected",
 auto_rollback=True
)

print("回滚结果：", result["message"])

**注意事项**：回滚后会自动执行冒烟测试，验证功能正常后才会完成回滚操作

---

## 五、功能4：CI运行监控看板
**功能说明**：实时查看所有CI运行状态、成功率、耗时等核心指标
**操作步骤**：
1. 运行监控启动命令：
bash
python scripts/ci_monitor.py

2. 打开浏览器访问 http://localhost:8080 即可查看监控看板
**核心指标**：
- 近7天CI成功率
- 平均CI运行耗时
- 失败率Top3的测试用例
- 待合并PR列表

---

## 六、功能5：异常告警推送
**功能说明**：CI运行失败、PR创建失败等异常场景自动推送告警到企业微信/飞书群
**配置步骤**：
1. 在config.yaml中配置告警webhook：
yaml
alert:
 webhook_url: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"
 at_users: ["user1", "user2"] # 告警时@的人员

2. 告警触发后会自动推送包含错误原因、CI链接的告警消息

---

## 七、新功能常见问题
1. Q：灰度测试覆盖率不达标怎么办？
A：补充对应功能的单元测试用例，覆盖更多场景后重新执行测试
2. Q：一键回滚后冒烟测试失败怎么办？
A：系统会自动恢复到回滚前版本，需要人工排查回滚版本的问题后再重试
3. Q：告警收不到怎么办？
A：检查webhook地址是否正确，网络是否可以访问企业微信/飞书接口