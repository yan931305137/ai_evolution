#!/usr/bin/env python3
"""
验证项目结构是否正确
"""
import sys
from pathlib import Path

def check_file(path, description):
    """检查文件是否存在"""
    if Path(path).exists():
        print(f"✅ {description}: {path}")
        return True
    else:
        print(f"❌ 缺失 {description}: {path}")
        return False

def check_dir(path, description):
    """检查目录是否存在"""
    if Path(path).is_dir():
        print(f"✅ {description}: {path}/")
        return True
    else:
        print(f"❌ 缺失 {description}: {path}/")
        return False

def main():
    print("🔍 验证项目结构")
    print("=" * 60)
    
    checks = []
    
    # 核心文件
    print("\n📄 核心文件:")
    checks.append(check_file("README.md", "项目说明"))
    checks.append(check_file("pyproject.toml", "项目配置"))
    checks.append(check_file("requirements.txt", "生产依赖"))
    checks.append(check_file("requirements-dev.txt", "开发依赖"))
    checks.append(check_file("Makefile", "构建脚本"))
    checks.append(check_file("Dockerfile", "Docker配置"))
    checks.append(check_file(".gitignore", "Git忽略"))
    
    # 配置文件
    print("\n⚙️  配置文件:")
    checks.append(check_dir("config", "配置目录"))
    checks.append(check_file("config/config.example.yaml", "配置示例"))
    checks.append(check_file("config/evolution_goals.yaml", "进化目标"))
    
    # 源代码
    print("\n💻 源代码:")
    checks.append(check_dir("src", "源代码目录"))
    checks.append(check_file("src/__init__.py", "包初始化"))
    checks.append(check_file("src/cli.py", "CLI入口"))
    checks.append(check_dir("src/agents", "代理模块"))
    checks.append(check_dir("src/brain", "大脑模块"))
    checks.append(check_dir("src/skills", "技能模块"))
    checks.append(check_dir("src/utils", "工具模块"))
    
    # 测试
    print("\n🧪 测试:")
    checks.append(check_dir("tests", "测试目录"))
    
    # 文档
    print("\n📚 文档:")
    checks.append(check_dir("docs", "文档目录"))
    checks.append(check_file("docs/PROJECT_STRUCTURE.md", "项目结构说明"))
    
    # 检查不应该存在的文件/目录
    print("\n🗑️  清理检查:")
    bad_paths = [
        "src/config",
        "src/tmp",
        "core",
        "src/__pycache__",
        ":memory:",
    ]
    for path in bad_paths:
        if Path(path).exists():
            print(f"⚠️  应删除: {path}")
            checks.append(False)
        else:
            print(f"✅ 已清理: {path}")
    
    # 统计
    print("\n" + "=" * 60)
    passed = sum(checks)
    total = len(checks)
    print(f"结果: {passed}/{total} 检查通过")
    
    if passed == total:
        print("✅ 项目结构符合标准！")
        return 0
    else:
        print("⚠️  项目结构存在问题")
        return 1

if __name__ == "__main__":
    sys.exit(main())
