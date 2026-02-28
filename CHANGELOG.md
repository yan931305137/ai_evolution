# Changelog

所有项目的显著变更都将记录在此文件。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Added
- 新增进化闭环系统（创造→评估→应用→进化）
- 新增进化目标配置系统（config/evolution_goals.yaml）
- 新增项目工程化配置（Makefile, pyproject.toml, Dockerfile）
- 新增项目结构文档（docs/PROJECT_STRUCTURE.md）

### Changed
- 统一配置文件位置到 config/ 目录
- 规范化项目结构，符合大厂标准
- 删除冗余测试文件和空目录
- 清理 __pycache__ 和临时文件

### Removed
- 删除 src/config 目录（已合并到 config/）
- 删除 core/ 目录（已合并到 src/）
- 删除 src/tmp 目录
- 删除不必要的测试文件

## [0.1.0] - 2025-03-01

### Added
- 初始版本发布
- 人类级认知架构（Brain）
- 增强版混合大脑（EnhancedHybridBrain）
- 多模态感知系统
- 创造力和梦境系统
- 自我意识系统
- 生命周期管理系统
- 技能系统
- 工具系统
- CLI 交互界面
