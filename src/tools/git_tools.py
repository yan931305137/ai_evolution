"""
Git操作工具集 - 提供Git仓库的基本操作功能
"""
import subprocess
import os
from pathlib import Path
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


def _run_git_command(args: List[str], cwd: Optional[str] = None) -> tuple:
    """执行Git命令并返回结果"""
    try:
        result = subprocess.run(
            ['git'] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "命令执行超时"
    except FileNotFoundError:
        return -1, "", "Git命令未找到，请确保Git已安装"
    except Exception as e:
        return -1, "", str(e)


def _find_git_root(path: str = ".") -> Optional[str]:
    """查找Git仓库根目录"""
    current = Path(path).resolve()
    while current != current.parent:
        if (current / '.git').exists():
            return str(current)
        current = current.parent
    return None


def git_status(repo_path: str = ".") -> str:
    """
    获取Git仓库状态
    
    Args:
        repo_path: 仓库路径，默认为当前目录
    
    Returns:
        Git状态描述
    """
    try:
        git_root = _find_git_root(repo_path)
        if not git_root:
            return f"❌ 未找到Git仓库: {repo_path}"
        
        # 获取状态
        code, stdout, stderr = _run_git_command(['status', '--short'], cwd=git_root)
        if code != 0:
            return f"❌ 获取Git状态失败: {stderr}"
        
        # 获取分支信息
        code2, branch_out, _ = _run_git_command(['branch', '-v'], cwd=git_root)
        current_branch = "unknown"
        if code2 == 0:
            for line in branch_out.split('\n'):
                if line.startswith('*'):
                    current_branch = line[2:].strip()
                    break
        
        # 获取最近的提交
        code3, log_out, _ = _run_git_command(['log', '-1', '--oneline'], cwd=git_root)
        last_commit = log_out.strip() if code3 == 0 else "N/A"
        
        # 构建报告
        report = f"""
🌿 Git 仓库状态: {git_root}
═══════════════════════════════════════
📍 当前分支: {current_branch}
💾 最近提交: {last_commit}

📋 工作区状态:
"""
        if stdout.strip():
            report += stdout
        else:
            report += "   工作区干净，没有变更\n"
        
        # 获取未跟踪文件
        code4, untracked, _ = _run_git_command(['ls-files', '--others', '--exclude-standard'], cwd=git_root)
        if code4 == 0 and untracked.strip():
            untracked_files = untracked.strip().split('\n')[:10]  # 只显示前10个
            report += f"\n📄 未跟踪文件 ({len(untracked.strip().split(chr(10)))} 个):\n"
            for f in untracked_files:
                report += f"   ?? {f}\n"
            if len(untracked.strip().split('\n')) > 10:
                report += "   ... 和其他文件\n"
        
        return report
        
    except Exception as e:
        return f"❌ 获取Git状态失败: {str(e)}"


def git_diff(file_path: Optional[str] = None, repo_path: str = ".", cached: bool = False) -> str:
    """
    查看Git差异
    
    Args:
        file_path: 指定文件路径，None则显示所有变更
        repo_path: 仓库路径
        cached: 是否查看暂存区的差异
    
    Returns:
        差异内容
    """
    try:
        git_root = _find_git_root(repo_path)
        if not git_root:
            return f"❌ 未找到Git仓库: {repo_path}"
        
        args = ['diff']
        if cached:
            args.append('--cached')
        if file_path:
            args.append(file_path)
        
        code, stdout, stderr = _run_git_command(args, cwd=git_root)
        
        if code != 0:
            return f"❌ 获取Git差异失败: {stderr}"
        
        if not stdout.strip():
            if cached:
                return "✅ 暂存区没有差异"
            else:
                return "✅ 工作区没有差异"
        
        # 截断过长的输出
        lines = stdout.split('\n')
        if len(lines) > 100:
            stdout = '\n'.join(lines[:100]) + f"\n\n... (共 {len(lines)} 行，已截断)"
        
        return f"📊 Git Diff ({'暂存区' if cached else '工作区'}):\n```diff\n{stdout}\n```"
        
    except Exception as e:
        return f"❌ 获取Git差异失败: {str(e)}"


def git_add(files: str, repo_path: str = ".") -> str:
    """
    添加文件到暂存区
    
    Args:
        files: 文件路径，可以是单个文件或用逗号分隔的多个文件，也可以用 '.' 表示所有
        repo_path: 仓库路径
    
    Returns:
        操作结果
    """
    try:
        git_root = _find_git_root(repo_path)
        if not git_root:
            return f"❌ 未找到Git仓库: {repo_path}"
        
        # 支持多个文件
        file_list = [f.strip() for f in files.split(',')]
        
        args = ['add'] + file_list
        code, stdout, stderr = _run_git_command(args, cwd=git_root)
        
        if code != 0:
            return f"❌ Git add 失败: {stderr}"
        
        return f"✅ 已添加到暂存区: {files}"
        
    except Exception as e:
        return f"❌ Git add 失败: {str(e)}"


def git_commit(message: str, repo_path: str = ".", allow_empty: bool = False) -> str:
    """
    提交暂存区的变更
    
    Args:
        message: 提交信息
        repo_path: 仓库路径
        allow_empty: 是否允许空提交
    
    Returns:
        操作结果
    """
    try:
        git_root = _find_git_root(repo_path)
        if not git_root:
            return f"❌ 未找到Git仓库: {repo_path}"
        
        args = ['commit', '-m', message]
        if allow_empty:
            args.append('--allow-empty')
        
        code, stdout, stderr = _run_git_command(args, cwd=git_root)
        
        if code != 0:
            if "nothing to commit" in stderr.lower():
                return "⚠️ 没有要提交的变更"
            return f"❌ Git commit 失败: {stderr}"
        
        # 提取提交哈希
        commit_hash = ""
        for line in stdout.split('\n'):
            if line.startswith('['):
                parts = line.split()
                if len(parts) >= 2:
                    commit_hash = parts[1].rstrip(']')
        
        return f"✅ Git提交成功: {commit_hash}\n💬 {message}"
        
    except Exception as e:
        return f"❌ Git commit 失败: {str(e)}"


def git_log(max_count: int = 10, repo_path: str = ".", oneline: bool = True) -> str:
    """
    查看提交历史
    
    Args:
        max_count: 显示的最大提交数
        repo_path: 仓库路径
        oneline: 是否单行显示
    
    Returns:
        提交历史
    """
    try:
        git_root = _find_git_root(repo_path)
        if not git_root:
            return f"❌ 未找到Git仓库: {repo_path}"
        
        args = ['log', f'-{max_count}']
        if oneline:
            args.append('--oneline')
        else:
            args.append('--pretty=format:%h - %an, %ar : %s')
        
        code, stdout, stderr = _run_git_command(args, cwd=git_root)
        
        if code != 0:
            return f"❌ 获取Git日志失败: {stderr}"
        
        if not stdout.strip():
            return "📭 暂无提交历史"
        
        return f"📜 最近 {max_count} 次提交:\n```\n{stdout}\n```"
        
    except Exception as e:
        return f"❌ 获取Git日志失败: {str(e)}"


def git_branch(repo_path: str = ".") -> str:
    """
    查看分支列表
    
    Args:
        repo_path: 仓库路径
    
    Returns:
        分支列表
    """
    try:
        git_root = _find_git_root(repo_path)
        if not git_root:
            return f"❌ 未找到Git仓库: {repo_path}"
        
        code, stdout, stderr = _run_git_command(['branch', '-a'], cwd=git_root)
        
        if code != 0:
            return f"❌ 获取分支列表失败: {stderr}"
        
        return f"🌿 分支列表:\n```\n{stdout}\n```"
        
    except Exception as e:
        return f"❌ 获取分支列表失败: {str(e)}"
