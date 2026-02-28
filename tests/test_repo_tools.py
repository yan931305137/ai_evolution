#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试代码仓库管理工具
"""

import os
import sys
sys.path.insert(0, '/workspace/projects')

from src.tools.repo_tools import GitHubClient, GiteeClient, RepositoryManager

def test_github_client():
    """测试 GitHub 客户端"""
    print("=" * 60)
    print("测试 GitHub 客户端")
    print("=" * 60)
    
    try:
        # 测试未认证用户
        print("\n1. 测试获取公共用户仓库...")
        client = GitHubClient()
        repos = client.get_user_repos("octocat")
        print(f"✅ 成功获取 {len(repos)} 个仓库")
        if repos:
            print(f"   第一个仓库: {repos[0].name} - {repos[0].description}")
        
        # 测试获取单个仓库
        print("\n2. 测试获取单个仓库信息...")
        repo = client.get_repo("octocat", "Hello-World")
        print(f"✅ 成功获取仓库信息: {repo.name}")
        print(f"   描述: {repo.description}")
        print(f"   Stars: {repo.stars}")
        
        return True
    except Exception as e:
        print(f"❌ GitHub 客户端测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_gitee_client():
    """测试 Gitee 客户端"""
    print("\n" + "=" * 60)
    print("测试 Gitee 客户端")
    print("=" * 60)
    
    try:
        # 测试未认证用户
        print("\n1. 测试获取公共用户仓库...")
        client = GiteeClient()
        repos = client.get_user_repos("liugezhou")
        print(f"✅ 成功获取 {len(repos)} 个仓库")
        if repos:
            print(f"   第一个仓库: {repos[0].name} - {repos[0].description}")
        
        # 测试获取单个仓库（使用第一个仓库的信息）
        if repos:
            print("\n2. 测试获取单个仓库信息...")
            repo_name = repos[0].name
            owner = repos[0].metadata.get('full_name', '').split('/')[0]
            if owner and repo_name:
                repo = client.get_repo(owner, repo_name)
                print(f"✅ 成功获取仓库信息: {repo.name}")
                print(f"   描述: {repo.description}")
                print(f"   Stars: {repo.stars}")
            else:
                print("⚠️  跳过单个仓库测试（缺少所有者信息）")
        else:
            print("⚠️  跳过单个仓库测试（没有找到仓库）")
        
        return True
    except Exception as e:
        print(f"❌ Gitee 客户端测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_repository_manager():
    """测试仓库管理器"""
    print("\n" + "=" * 60)
    print("测试仓库管理器")
    print("=" * 60)
    
    try:
        manager = RepositoryManager()
        
        # 测试获取所有仓库
        print("\n1. 测试获取所有平台仓库...")
        all_repos = manager.get_all_repos()
        
        for platform, repos in all_repos.items():
            print(f"   {platform.upper()}: {len(repos)} 个仓库")
            if repos:
                print(f"      示例: {repos[0].name}")
        
        return True
    except Exception as e:
        print(f"❌ 仓库管理器测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_clone_functionality():
    """测试克隆功能（需要 git）"""
    print("\n" + "=" * 60)
    print("测试克隆功能")
    print("=" * 60)
    
    try:
        import subprocess
        import shutil
        
        # 检查 git 是否可用
        result = subprocess.run(["git", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            print("⚠️  Git 不可用，跳过克隆测试")
            return True
        
        print(f"✅ Git 版本: {result.stdout.strip()}")
        
        # 测试克隆一个小仓库
        print("\n1. 测试克隆 GitHub 仓库...")
        manager = RepositoryManager()
        
        test_dir = "/tmp/test_repos_cloned"
        
        # 清理旧的测试目录
        if os.path.exists(test_dir):
            print(f"   清理旧测试目录: {test_dir}")
            shutil.rmtree(test_dir)
        
        success = manager.clone_repo(
            "https://github.com/octocat/Hello-World.git",
            test_dir
        )
        
        if success:
            print(f"✅ 仓库克隆成功到 {test_dir}")
            # 检查文件
            if os.path.exists(test_dir):
                print(f"   目录内容: {os.listdir(test_dir)}")
            return True
        else:
            print("❌ 仓库克隆失败")
            return False
            
    except Exception as e:
        print(f"❌ 克隆功能测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_langchain_tools():
    """测试 LangChain 工具"""
    print("\n" + "=" * 60)
    print("测试 LangChain 工具")
    print("=" * 60)
    
    try:
        from src.tools.repository_tools import (
            _list_github_repos_impl,
            _list_gitee_repos_impl,
            _list_all_repos_impl,
            _get_repo_info_impl
        )
        
        # 测试获取 GitHub 仓库列表
        print("\n1. 测试 list_github_repos 工具...")
        result = _list_github_repos_impl("octocat")
        print(f"✅ 工具执行成功")
        print(f"   返回结果长度: {len(result)} 字符")
        
        # 测试获取 Gitee 仓库列表
        print("\n2. 测试 list_gitee_repos 工具...")
        result = _list_gitee_repos_impl("liugezhou")
        print(f"✅ 工具执行成功")
        print(f"   返回结果长度: {len(result)} 字符")
        
        # 测试获取所有仓库
        print("\n3. 测试 list_all_repos 工具...")
        result = _list_all_repos_impl()
        print(f"✅ 工具执行成功")
        
        # 测试获取仓库信息
        print("\n4. 测试 get_repo_info 工具...")
        result = _get_repo_info_impl("github", "octocat", "Hello-World")
        print(f"✅ 工具执行成功")
        
        return True
    except Exception as e:
        print(f"❌ LangChain 工具测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("开始测试代码仓库管理功能")
    print("=" * 60)
    
    results = []
    
    # 运行所有测试
    results.append(("GitHub 客户端", test_github_client()))
    results.append(("Gitee 客户端", test_gitee_client()))
    results.append(("仓库管理器", test_repository_manager()))
    results.append(("克隆功能", test_clone_functionality()))
    results.append(("LangChain 工具", test_langchain_tools()))
    
    # 打印总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
