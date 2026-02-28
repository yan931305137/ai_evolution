# 项目结构说明

## 目录结构

```
openclaw/
├── .github/                    # GitHub Actions 工作流
│   └── workflows/
│       └── ci-cd-pipeline.yml  # CI/CD 配置
│
├── config/                     # 配置文件
│   ├── config.yaml            # 主配置文件
│   ├── config.example.yaml    # 配置示例
│   ├── evolution_goals.yaml   # 进化目标配置
│   └── compliance_rules.json  # 合规规则
│
├── data/                       # 数据文件（不提交到 git）
│   └── chroma_db/             # 向量数据库
│
├── docs/                       # 文档
│
├── scripts/                    # 脚本工具
│   ├── analyze_llm_calls.py   # LLM 调用分析
│   ├── setup_chroma_cache.py  # 初始化 ChromaDB
│   └── agent_learning/        # 智能体学习脚本
│
├── src/                        # 源代码
│   ├── __init__.py
│   ├── __main__.py            # 模块入口
│   ├── cli.py                 # 命令行界面
│   │
│   ├── agents/                # AI 代理
│   │   ├── agent.py           # 主代理
│   │   ├── agent_matrix_manager.py
│   │   ├── multi_agent_system.py
│   │   └── ...
│   │
│   ├── brain/                 # 人类级大脑架构
│   │   ├── human_level_brain.py
│   │   ├── human_cognition.py
│   │   ├── local_response_system.py
│   │   ├── orchestrator.py
│   │   ├── learning_system.py
│   │   ├── planning_system.py
│   │   ├── monitoring_system.py
│   │   ├── self_evolution_system.py
│   │   ├── user_profiling_system.py
│   │   ├── attention_system/   # 注意力系统
│   │   ├── decision_system/    # 决策系统
│   │   ├── memory_system/      # 记忆系统
│   │   ├── perception_system/  # 感知系统
│   │   └── value_system/       # 价值系统
│   │
│   ├── core/                  # 核心组件
│   │   ├── skills.py
│   │   └── agents/
│   │
│   ├── skills/                # 技能系统
│   │   ├── __init__.py
│   │   ├── custom_skills_registry.py  # 自定义技能
│   │   ├── business_skills.py
│   │   ├── file_skills.py
│   │   ├── security_skills.py
│   │   └── test_skills.py
│   │
│   ├── storage/               # 存储层
│   │   ├── database.py
│   │   ├── memory.py
│   │   └── enhanced_memory.py
│   │
│   ├── tools/                 # 工具集
│   │   ├── __init__.py
│   │   ├── file_tools.py
│   │   ├── git_tools.py
│   │   └── ...
│   │
│   └── utils/                 # 工具函数
│       ├── llm.py             # LLM 客户端
│       ├── config.py          # 配置管理
│       ├── creativity.py      # 创造力引擎
│       ├── emotions.py        # 情感系统
│       ├── personality.py     # 性格系统
│       ├── self_awareness.py  # 自我意识
│       ├── enhanced_lifecycle.py  # 生命周期
│       ├── evolution_feedback_loop.py  # 进化闭环
│       └── ...
│
├── tests/                      # 测试代码
│   ├── __init__.py
│   ├── test_evolution_loop.py
│   └── test_enhanced_hybrid.py
│
├── .dockerignore              # Docker 忽略文件
├── .gitignore                 # Git 忽略文件
├── Dockerfile                 # Docker 构建文件
├── Makefile                   # 构建脚本
├── README.md                  # 项目说明
├── openclaw_kernel.py         # 监控进程
├── pyproject.toml             # Python 项目配置
├── requirements.txt           # 生产依赖
└── requirements-dev.txt       # 开发依赖
```

## 关键文件说明

### 入口文件

- `python -m src` - 直接运行 CLI
- `python openclaw_kernel.py` - 带监控的 CLI（自动重启）

### 配置文件

- `config/config.yaml` - 主配置文件（API Keys、模型设置等）
- `config/evolution_goals.yaml` - AI 进化目标配置

### 核心模块

- `src/cli.py` - 命令行交互界面
- `src/brain/` - 人类级认知架构
- `src/utils/enhanced_lifecycle.py` - 完整生命周期管理
- `src/utils/evolution_feedback_loop.py` - 进化闭环系统

## 开发规范

1. **代码风格**: 使用 Black 格式化，行长度 120
2. **类型注解**: 鼓励使用类型注解
3. **文档**: 函数和类必须有 docstring
4. **测试**: 新功能必须包含测试

## 运行测试

```bash
make test
```

## 代码格式化

```bash
make format
```
