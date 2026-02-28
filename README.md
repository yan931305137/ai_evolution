# OpenClaw - 自主进化 AI 助手

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

OpenClaw 是一个开源的个人 AI 助手框架，具备自主进化能力。

## 特性

- **人类级认知架构**: 模拟人类大脑的认知过程
- **自主进化**: 创造→评估→应用→进化的闭环
- **多模态感知**: 支持文本、图像等多种输入
- **情感系统**: 具有情感感知和表达能力
- **记忆系统**: 长期和短期记忆结合

## 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/openclaw.git
cd openclaw

# 安装依赖
make install

# 或手动安装
pip install -r requirements.txt
```

### 配置

复制示例配置文件并编辑：

```bash
cp config/config.example.yaml config/config.yaml
# 编辑 config/config.yaml 配置 API Keys
```

### 运行

```bash
# 启动交互式 CLI
make run

# 或
python -m src.cli
```

## 项目结构

```
openclaw/
├── src/                    # 源代码
│   ├── agents/            # AI 代理
│   ├── brain/             # 人类级大脑
│   ├── core/              # 核心组件
│   ├── skills/            # 技能系统
│   ├── storage/           # 存储层
│   ├── tools/             # 工具集
│   └── utils/             # 工具函数
├── tests/                 # 测试代码
├── config/                # 配置文件
├── docs/                  # 文档
├── scripts/               # 脚本工具
└── data/                  # 数据文件
```

## 开发

```bash
# 运行测试
make test

# 代码格式化
make format

# 类型检查
make lint
```

## 许可证

MIT License
