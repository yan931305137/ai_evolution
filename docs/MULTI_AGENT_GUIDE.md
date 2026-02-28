# 多 Agent 系统使用指南

## 概述

多 Agent 系统通过协调多个 Specialist Agent 来处理复杂任务，相比单 Agent 模式具有更高的效率和专业化程度。

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                   MultiAgentRunner                       │
│  (智能路由: 根据任务复杂度选择 Single-Agent 或 Multi-Agent) │
└─────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
┌─────────────────────┐         ┌─────────────────────────┐
│    AutoAgent        │         │   AgentOrchestrator     │
│   (单 Agent 模式)    │         │    (多 Agent 协调器)     │
└─────────────────────┘         └─────────────────────────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    ▼                       ▼                       ▼
            ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
            │  CodeAgent   │    │  TestAgent   │    │   DocAgent   │
            │   代码开发    │    │   测试编写    │    │   文档生成    │
            └──────────────┘    └──────────────┘    └──────────────┘
            ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
            │ ReviewAgent  │    │ AnalyzeAgent │    │ RefactorAgent│
            │   代码审查    │    │   代码分析    │    │   代码重构    │
            └──────────────┘    └──────────────┘    └──────────────┘
                                    ┌──────────────┐
                                    │  DebugAgent  │
                                    │   调试排错    │
                                    └──────────────┘
```

## 快速开始

### 1. 自动模式（推荐）

系统自动检测任务复杂度并选择合适的模式：

```python
from src.agents.multi_agent import run_sync

# 简单任务 -> 使用单 Agent
result = run_sync("修复 utils.py 中的拼写错误")

# 复杂任务 -> 自动使用多 Agent
result = run_sync("重构认证模块，添加单元测试和文档")
```

### 2. 强制使用多 Agent 模式

```python
from src.agents.multi_agent import run_sync

result = run_sync("分析项目结构", mode="multi")
```

### 3. 强制使用单 Agent 模式

```python
result = run_sync("简单修改", mode="single")
```

### 4. 直接使用 Specialist Agent

```python
from src.agents.multi_agent import run_specialist
import asyncio

# 运行代码审查 Agent
result = asyncio.run(run_specialist("review", "审查 auth.py 的代码质量"))

# 运行测试编写 Agent
result = asyncio.run(run_specialist("test", "为 user_service.py 添加单元测试"))
```

## 使用示例

### 示例 1: 完整功能开发流程

```python
from src.agents.multi_agent import run_sync

# 一个复杂任务会被自动分解为多个子任务
result = run_sync("""
分析 src/payment 模块的代码结构，
然后重构其中的重复代码，
添加单元测试确保重构后的正确性，
最后更新相关文档说明变更。
""")

print(result)
```

输出示例：
```
============================================================
🎯 Goal: 分析 src/payment 模块的代码结构，然后重构...
Analyzing task complexity...
✓ Task complexity: 15 estimated steps
✓ Execution mode: hybrid
✓ Subtasks: 4
  - [analyze] 分析 src/payment 模块的代码结构和依赖关系...
  - [refactor] 重构 src/payment 模块中的重复代码...
  - [test] 为重构后的 payment 模块添加单元测试...
  - [doc] 更新 payment 模块的文档说明变更...

▶ Starting: [analyze] 分析 src/payment 模块的代码结构...
✓ Completed: [analyze] in 3.2s
▶ Starting: [refactor] 重构 src/payment 模块中的重复代码...
✓ Completed: [refactor] in 8.5s
...
============================================================
✅ All Tasks Completed
Total time: 18.3s
Agents used: analyze, refactor, test, doc
============================================================
```

### 示例 2: 并行执行独立任务

```python
from src.agents.multi_agent import run_sync

# 多个独立的代码审查任务可以并行执行
result = run_sync("""
同时审查以下文件:
1. src/models/user.py
2. src/services/auth.py
3. src/utils/helpers.py
""")
```

### 示例 3: 特定 Specialist Agent

```python
import asyncio
from src.agents.multi_agent import run_specialist

# 仅使用 Debug Agent 排查问题
result = asyncio.run(run_specialist(
    "debug",
    "排查 src/api/routes.py 中的 500 错误"
))

# 仅使用 Doc Agent 生成文档
result = asyncio.run(run_specialist(
    "doc",
    "为 src/core/engine.py 生成 API 文档"
))
```

## 任务复杂度评估

系统使用以下规则自动评估任务复杂度（1-10）：

| 复杂度 | 关键词 | 处理方式 |
|--------|--------|----------|
| 1-3 | 修复、简单修改 | 单 Agent |
| 4-6 | 实现功能、添加 | 单 Agent / 简单多 Agent |
| 7-8 | 重构、优化架构 | 多 Agent |
| 9-10 | 多模块、架构重构 | 多 Agent + 详细分解 |

## 配置选项

在 `config/config.yaml` 中配置：

```yaml
agent:
  multi_agent:
    enabled: true              # 启用多 Agent 模式
    auto_detect: true          # 自动检测任务复杂度
    complexity_threshold: 4    # 多 Agent 触发阈值
    max_parallel_tasks: 3      # 最大并行任务数
    
    # Specialist Agent 配置
    specialists:
      code:
        max_steps: 50
        max_messages: 15
        max_tokens: 6000
      test:
        max_steps: 40
        max_messages: 15
        max_tokens: 6000
      # ... 其他配置
```

## 执行模式

### 1. Sequential（顺序执行）
子任务按依赖关系顺序执行，适合有明确前后依赖的任务。

### 2. Parallel（并行执行）
所有子任务同时执行，适合完全独立的任务。

### 3. Hybrid（混合模式，默认）
根据依赖图自动调度，无依赖的任务并行执行，有依赖的按顺序执行。

## Agent 类型说明

| Agent 类型 | 职责 | 适用场景 |
|------------|------|----------|
| `code` | 代码开发 | 编写新功能、修改代码 |
| `test` | 测试 | 编写单元测试、集成测试 |
| `doc` | 文档 | 生成文档、更新 README |
| `review` | 代码审查 | 代码质量检查、安全审查 |
| `analyze` | 分析 | 代码结构分析、依赖分析 |
| `refactor` | 重构 | 代码重构、优化 |
| `debug` | 调试 | Bug 排查、问题定位 |

## 最佳实践

1. **简单任务使用单 Agent**
   - 修改单个文件
   - 简单 Bug 修复
   - 文档小修改

2. **复杂任务使用多 Agent**
   - 跨模块重构
   - 功能开发 + 测试 + 文档
   - 代码审查 + 修改

3. **明确指定模式**
   - 当你确定需要多 Agent 协作时，使用 `mode="multi"`
   - 当任务虽然复杂但需要连贯上下文时，使用 `mode="single"`

4. **合理分解任务**
   - 如果自动分解不够理想，可以手动拆分后多次调用

## 故障排除

### 问题：多 Agent 模式没有触发

检查配置：
```python
from src.utils.config import cfg
print(cfg.get("agent.multi_agent.enabled"))
print(cfg.get("agent.multi_agent.complexity_threshold"))
```

### 问题：子任务执行失败

查看详细日志：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 问题：任务分解不合理

可以强制指定执行模式：
```python
result = run_sync(task, mode="single")  # 或 "multi"
```

## 扩展开发

添加新的 Specialist Agent：

```python
from src.agents.specialist_agents import BaseSpecialistAgent, AgentType

class SecurityAgent(BaseSpecialistAgent):
    """安全审计 Agent"""
    
    def __init__(self, llm):
        super().__init__(AgentType.SECURITY, llm)
    
    def get_system_prompt(self, task: str) -> str:
        return f"""You are a Security Specialist...
        TASK: {task}
        ..."""

# 注册到工厂
AGENT_REGISTRY[AgentType.SECURITY] = SecurityAgent
```
