<div align="center">

# 🦞 OpenClaw

**自主进化型个人 AI 助手框架**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg?style=flat-square&logo=python)](https://www.python.org/downloads/)
[![Node.js 20+](https://img.shields.io/badge/node.js-20+-green.svg?style=flat-square&logo=node.js)](https://nodejs.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-blue.svg?style=flat-square&logo=github-actions)](.github/workflows/ci-cd-pipeline.yml)
[![Security](https://img.shields.io/badge/security-scan%20passed-brightgreen.svg?style=flat-square&logo=shield)](docs/GITHUB_CICD_SECURITY.md)

[English](README_EN.md) | [中文文档](README.md) | [Documentation](docs/)

</div>

---

## 📋 目录

- [项目简介](#-项目简介)
- [核心特性](#-核心特性)
- [系统架构](#-系统架构)
- [快速开始](#-快速开始)
- [安装指南](#-安装指南)
- [配置说明](#-配置说明)
- [使用指南](#-使用指南)
- [API 文档](#-api-文档)
- [开发指南](#-开发指南)
- [CI/CD 集成](#-cicd-集成)
- [安全策略](#-安全策略)
- [贡献指南](#-贡献指南)
- [许可证](#-许可证)

---

## 🎯 项目简介

**OpenClaw** 是一个开源的个人 AI 助手框架，具备**自主进化能力**。它采用人类级认知架构，能够不断学习、优化和进化，成为真正理解用户的智能伙伴。

### 为什么选择 OpenClaw？

| 特性 | 传统 AI 助手 | OpenClaw |
|------|-------------|----------|
| 学习能力 | 静态模型 | ✅ 自主进化 |
| 认知深度 | 简单问答 | ✅ 人类级大脑 |
| 个性化 | 通用回复 | ✅ 深度定制 |
| 多模态 | 文本为主 | ✅ 全模态支持 |
| 隐私保护 | 云端依赖 | ✅ 本地优先 |

---

## ✨ 核心特性

### 🧠 人类级认知架构
- **感知层**: 多模态输入处理（文本、图像、语音）
- **认知层**: 意图识别、上下文理解、推理规划
- **记忆层**: 向量记忆、知识图谱、经验存储
- **表达层**: 自然语言生成、情感表达

### 🔄 自主进化系统
- **创造**: 基于需求产生新想法
- **评估**: 多维度评估想法价值
- **应用**: 自动实现优质想法
- **进化**: 根据反馈调整策略

### 🛡️ 企业级安全
- 敏感信息自动扫描
- CI/CD 安全检查集成
- 预提交钩子保护
- 日志自动脱敏

### 🔌 丰富集成
- **IM 渠道**: 飞书、钉钉、微信、Telegram
- **开发工具**: GitHub、GitLab、Jira
- **云服务**: AWS、阿里云、腾讯云
- **数据库**: ChromaDB、PostgreSQL、MongoDB

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        OpenClaw 系统架构                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   Channels   │    │   Gateway    │    │    Agent     │       │
│  │  (飞书/钉钉)  │◄──►│    (5000)    │◄──►│   (Pi/π)     │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│                               │                                  │
│                    ┌──────────┴──────────┐                      │
│                    ▼                     ▼                      │
│           ┌──────────────┐      ┌──────────────┐               │
│           │   Skills     │      │    Brain     │               │
│           │  (工具扩展)   │      │  (人类级大脑) │               │
│           └──────────────┘      └──────────────┘               │
│                                          │                      │
│                    ┌─────────────────────┼─────────────────┐   │
│                    ▼                     ▼                 ▼   │
│           ┌──────────────┐    ┌──────────────┐  ┌──────────┐  │
│           │   Memory     │    │  Evolution   │  │  Emotion │  │
│           │  (记忆系统)   │    │  (进化系统)   │  │ (情感系统)│  │
│           └──────────────┘    └──────────────┘  └──────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 使用 Docker（推荐）

```bash
# 克隆仓库
git clone https://github.com/yourusername/openclaw.git
cd openclaw

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f gateway
```

### 本地安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/openclaw.git
cd openclaw

# 安装依赖
make install

# 或手动安装
pip install -r requirements.txt
```

### 一键启动

```bash
# 启动所有服务
make up

# 启动 Gateway
make gateway

# 启动 Agent
make agent
```

---

## 📦 安装指南

### 系统要求

| 组件 | 最低要求 | 推荐配置 |
|------|----------|----------|
| Python | 3.12+ | 3.12+ |
| Node.js | 20.x | 22.x |
| RAM | 4GB | 8GB+ |
| Disk | 10GB | 50GB+ |
| GPU | 可选 | 推荐用于大模型 |

### 环境准备

```bash
# 安装 Python 3.12
# macOS
brew install python@3.12

# Ubuntu
sudo apt install python3.12 python3.12-venv

# 安装 Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

### 完整安装

```bash
# 1. 克隆仓库
git clone https://github.com/yourusername/openclaw.git
cd openclaw

# 2. 创建虚拟环境
python3.12 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或: venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 4. 安装 Git hooks（推荐）
./scripts/install-hooks.sh

# 5. 验证安装
make doctor
```

---

## ⚙️ 配置说明

### 快速配置

```bash
# 复制示例配置
cp .env.example .env

# 编辑配置文件
vim .env
```

### 核心配置项

| 配置项 | 说明 | 必需 |
|--------|------|------|
| `OPENAI_API_KEY` | OpenAI API 密钥 | ✅ |
| `ANTHROPIC_API_KEY` | Anthropic API 密钥 | 可选 |
| `COZE_API_KEY` | Coze API 密钥 | 可选 |
| `GITHUB_TOKEN` | GitHub Token（CI/CD） | 可选 |

### 配置文件结构

```
config/
├── config.yaml              # 主配置
├── config.example.yaml      # 示例配置
├── evolution.yaml           # 进化系统配置
├── github_cicd.yaml         # CI/CD 配置
├── compliance_rules.json    # 合规规则
└── security_rules.json      # 安全规则
```

### 渠道配置示例

```yaml
# config/config.yaml
channels:
  feishu:
    enabled: true
    appId: "cli_xxxxxxxx"
    appSecret: "xxxxxxxx"
    encryptKey: "xxxxxxxx"
  
  dingtalk:
    enabled: true
    clientId: "dingxxxxxxxx"
    clientSecret: "xxxxxxxx"
```

---

## 📖 使用指南

### 命令行交互

```bash
# 启动交互式 CLI
python -m src.cli

# 发送消息
openclaw message send --to "user123" --message "Hello!"

# 查看状态
openclaw status --all
```

### API 调用

```python
import requests

# Gateway 默认端口 5000
response = requests.post("http://localhost:5000/api/v1/chat", json={
    "message": "你好，OpenClaw！",
    "session_id": "test_session"
})

print(response.json())
```

### WebSocket 实时通信

```javascript
const ws = new WebSocket('ws://localhost:5000/ws/chat');

ws.onopen = () => {
    ws.send(JSON.stringify({
        type: 'message',
        content: 'Hello!'
    }));
};

ws.onmessage = (event) => {
    console.log('Received:', event.data);
};
```

---

## 🔌 API 文档

### REST API

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/chat` | POST | 发送消息 |
| `/api/v1/sessions` | GET | 获取会话列表 |
| `/api/v1/agents` | GET | 获取 Agent 列表 |
| `/api/v1/skills` | GET | 获取技能列表 |

完整 API 文档: [docs/API.md](docs/API.md)

### WebSocket 事件

| 事件 | 方向 | 描述 |
|------|------|------|
| `message` | C→S | 发送消息 |
| `response` | S→C | 接收回复 |
| `typing` | S→C | 输入中状态 |
| `error` | S→C | 错误通知 |

---

## 🛠️ 开发指南

### 项目结构

```
openclaw/
├── src/                      # 源代码
│   ├── agents/              # AI 代理实现
│   │   ├── base.py         # 基础 Agent
│   │   └── pi_agent.py     # Pi Agent
│   ├── brain/               # 人类级大脑
│   │   ├── perception.py   # 感知层
│   │   ├── cognition.py    # 认知层
│   │   ├── memory.py       # 记忆层
│   │   └── expression.py   # 表达层
│   ├── channels/            # 渠道适配器
│   │   ├── feishu.py       # 飞书
│   │   └── dingtalk.py     # 钉钉
│   ├── core/                # 核心组件
│   ├── skills/              # 技能系统
│   ├── storage/             # 存储层
│   ├── tools/               # 工具集
│   └── utils/               # 工具函数
├── tests/                   # 测试代码
├── config/                  # 配置文件
├── docs/                    # 文档
├── scripts/                 # 脚本工具
└── data/                    # 数据文件
```

### 开发命令

```bash
# 运行测试
make test

# 运行特定测试
pytest tests/test_brain.py -v

# 代码格式化
make format

# 类型检查
make lint

# 安全检查
make security-scan

# 构建文档
make docs
```

### 创建自定义 Skill

```python
# skills/my_skill.py
from src.skills.base import Skill

class MySkill(Skill):
    name = "my_skill"
    description = "My custom skill"
    
    def run(self, **kwargs):
        # 实现逻辑
        return {"result": "success"}
```

---

## 🔄 CI/CD 集成

### GitHub Actions 工作流

```yaml
# .github/workflows/ci-cd-pipeline.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, dev ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: make test
      
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Security scan
        run: make security-scan
```

### 进化系统集成

```bash
# 启用 CI/CD 自动触发
openclaw config set evolution.cicd.enabled true
openclaw config set evolution.cicd.auto_trigger true

# 运行完整进化周期
openclaw evolution run --full-cycle
```

---

## 🔒 安全策略

### 安全特性

- ✅ **预提交钩子**: 自动扫描暂存文件
- ✅ **CI/CD 扫描**: GitHub Actions 安全检测
- ✅ **日志脱敏**: 敏感信息自动清理
- ✅ **依赖扫描**: Safety 和 pip-audit 集成

### 报告安全问题

如果你发现了安全漏洞，请通过以下方式报告：

1. **不要**在公共 Issue 中披露
2. 发送邮件至: security@openclaw.ai
3. 或创建私人安全公告

详细安全文档: [docs/GITHUB_CICD_SECURITY.md](docs/GITHUB_CICD_SECURITY.md)

---

## 🤝 贡献指南

我们欢迎各种形式的贡献！

### 贡献流程

1. **Fork** 仓库
2. **创建分支**: `git checkout -b feature/amazing-feature`
3. **提交更改**: `git commit -m 'Add amazing feature'`
4. **推送分支**: `git push origin feature/amazing-feature`
5. **创建 Pull Request**

### 开发规范

- 遵循 [PEP 8](https://pep8.org/) 代码规范
- 使用 [Black](https://black.readthedocs.io/) 格式化代码
- 添加单元测试覆盖新功能
- 更新相关文档

### 行为准则

请阅读 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) 了解我们的行为准则。

---

## 📊 项目状态

### 健康度指标

![Tests](https://img.shields.io/badge/tests-passing-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen)
![Security](https://img.shields.io/badge/security-audit%20passed-brightgreen)

### 路线图

- [x] 人类级大脑架构 v1.0
- [x] 自主进化系统 v1.0
- [x] CI/CD 集成 v1.0
- [x] 安全扫描系统 v1.0
- [ ] 多模态感知 v2.0 (进行中)
- [ ] 分布式 Agent 系统 v2.0 (计划中)
- [ ] 可视化控制台 v2.0 (计划中)

---

## 🙏 致谢

感谢以下项目和社区的支持：

- [LangGraph](https://langchain-ai.github.io/langgraph/) - Agent 工作流框架
- [ChromaDB](https://www.trychroma.com/) - 向量数据库
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架
- [React](https://react.dev/) - UI 框架

---

## 📄 许可证

本项目采用 [MIT](LICENSE) 许可证。

```
MIT License

Copyright (c) 2024 OpenClaw Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

<div align="center">

**⭐ Star 我们，如果你认为这个项目有帮助！**

[Report Bug](https://github.com/yourusername/openclaw/issues) · 
[Request Feature](https://github.com/yourusername/openclaw/issues) · 
[Discussions](https://github.com/yourusername/openclaw/discussions)

</div>
