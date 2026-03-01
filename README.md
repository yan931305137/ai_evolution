<div align="center">

# 🦞 OpenClaw

**自主进化型个人 AI 助手框架**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg?style=flat-square&logo=python)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![Evolution: Autonomous](https://img.shields.io/badge/evolution-autonomous-brightgreen.svg?style=flat-square)](docs/BRAIN_ENHANCEMENTS_REPORT.md)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-blue.svg?style=flat-square&logo=github-actions)](.github/workflows/ci.yml)

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
- **感知层 (Perception)**: 多模态输入预处理。
- **注意力系统 (Attention)**: 动态资源调度，聚焦关键任务上下文。
- **记忆层 (Memory)**: 包含瞬时、短期与长期记忆，支持向量检索与遗忘机制。
- **价值系统 (Value)**: 基于收益/损失评估决策优先级。
- **决策系统 (Decision)**: 基于记忆与价值进行逻辑推理与路径规划。

### 🔄 自主进化闭环 (Self-Evolution System)
- **数据采集**: 自动收集运行时运营数据。
- **缺口识别**: 识别能力短板与性能瓶颈。
- **自动迭代**: 生成迭代计划、编写代码、运行测试并自动应用。
- **热重载**: 无需重启，实时更新核心模块。

### 🛡️ 企业级安全与合规
- **存储合规**: 自动校验文件写入路径，确保代码、文档、数据分类存放。
- **代码扫描**: 迭代过程中自动进行安全性验证。
- **透明度监控**: 追踪每一个回答的信息来源与事实核查步骤。

---

## 🏗️ 项目结构

```text
openclaw/
├── src/
│   ├── agents/              # AI 代理实现 (动态代理, 专家代理)
│   ├── brain/               # 人类级大脑 (感知, 记忆, 决策, 价值系统)
│   ├── core/                # 核心组件
│   ├── skills/              # 技能系统
│   ├── storage/             # 存储层 (数据库, 增强记忆)
│   ├── tools/               # 工具集 (计算机操作, 文件, Git, Web等)
│   └── utils/               # 基础设施 (热重载, 安全扫描, LLM适配)
├── tests/                   # 测试代码
├── config/                  # 配置文件
├── docs/                    # 深度文档
└── scripts/                 # 脚本工具
```

---

## 🚀 快速开始

### 1. 环境准备
确保已安装 Python 3.12+。

```bash
# 克隆项目
git clone <repository-url>
cd ai

# 安装依赖
make install
```

### 2. 配置
复制 `.env.example` 为 `.env` 并配置你的 API Key（推荐使用豆包/Volengine）。

```bash
cp .env.example .env
# 编辑 .env 文件填入 API 密钥
```

### 3. 启动

```bash
# 启动交互式 CLI
make run
# 或者
python -m src.cli
```

---

## 📦 安装指南

### 系统要求

| 组件 | 最低要求 | 推荐配置 |
|------|----------|----------|
| Python | 3.12+ | 3.12+ |
| RAM | 4GB | 8GB+ |
| Disk | 10GB | 50GB+ |

### Docker 安装

```bash
# 构建镜像
make docker-build

# 运行容器
make docker-run
```

---

## ⚙️ 配置说明

### 核心配置项

| 配置项 | 说明 | 必需 |
|--------|------|------|
| `OPENAI_API_KEY` | OpenAI API 密钥 | ✅ |
| `ANTHROPIC_API_KEY` | Anthropic API 密钥 | 可选 |
| `COZE_API_KEY` | Coze API 密钥 | 可选 |
| `GITHUB_TOKEN` | GitHub Token（CI/CD） | 可选 |

### 配置文件结构

```text
config/
├── config.yaml              # 主配置
├── config.example.yaml      # 示例配置
├── evolution_goals.yaml     # 进化目标
├── github_cicd.yaml         # CI/CD 配置
├── compliance_rules.json    # 合规规则
└── security_rules.json      # 安全规则
```

---

## 📖 使用指南

### 命令行交互

在 CLI 界面中，你可以使用以下指令：
- `/agent <任务描述>`: 启动自主代理模式执行复杂任务（如：分析代码并编写单元测试）。
- `/evolve`: 开启 **自主进化闭环**，观察系统如何自我优化。
- `/auto`: 切换自主运行模式。
- `/reload`: 查看当前模块的热重载状态与性能统计。
- `/status`: 查看大脑状态、需求水平及进化进度。

---

## 🛠️ 开发指南

### 常用命令

```bash
# 运行测试
make test

# 运行带覆盖率的测试
make test-cov

# 代码格式化
make format

# 代码检查
make lint

# 清理临时文件
make clean
```

---

## 🔄 CI/CD 集成

### GitHub Actions 工作流

项目配置了完整的 CI/CD 流程，位于 `.github/workflows/ci.yml`，包含：
- 自动化测试
- 安全扫描
- 代码质量检查

### 进化系统集成

```bash
# 启用 CI/CD 自动触发
openclaw config set evolution.cicd.enabled true
openclaw config set evolution.cicd.auto_trigger true
```

---

## 🔒 安全策略

- ✅ **预提交钩子**: 自动扫描暂存文件 (`scripts/pre-commit-security.sh`)
- ✅ **CI/CD 扫描**: GitHub Actions 安全检测
- ✅ **日志脱敏**: 敏感信息自动清理
- ✅ **依赖扫描**: 确保依赖包安全

详细安全文档: [docs/GITHUB_CICD_SECURITY.md](docs/GITHUB_CICD_SECURITY.md)

---

## 🤝 贡献指南

我们欢迎各种形式的贡献！

1. **Fork** 仓库
2. **创建分支**: `git checkout -b feature/amazing-feature`
3. **提交更改**: `git commit -m 'Add amazing feature'`
4. **推送分支**: `git push origin feature/amazing-feature`
5. **创建 Pull Request**

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 许可证。

---

<div align="center">
  <b>探索 AI 的终极形态 —— 从对话到进化。</b>
</div>
