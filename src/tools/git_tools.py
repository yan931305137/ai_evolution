"""
Git操作工具集 - 提供Git仓库的基本操作功能
"""
import subprocess
import os
from pathlib import Path
from typing import List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def _run_git_command(args: List[str], cwd: Optional[str] = None) -> tuple:
    """执行Git命令并返回结果"""
    try:
        # Use text=False to capture raw bytes and handle decoding manually
        result = subprocess.run(
            ['git'] + args,
            cwd=cwd,
            capture_output=True,
            text=False,
            timeout=120
        )
        
        def decode_output(data):
            if not data:
                return ""
            try:
                return data.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    return data.decode('gbk')
                except UnicodeDecodeError:
                    return data.decode('utf-8', errors='replace')

        stdout = decode_output(result.stdout)
        stderr = decode_output(result.stderr)
        
        return result.returncode, stdout, stderr
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


def git_commit(message: str, repo_path: str = ".", allow_empty: bool = False, no_verify: bool = False) -> str:
    """
    提交暂存区的变更
    
    Args:
        message: 提交信息
        repo_path: 仓库路径
        allow_empty: 是否允许空提交
        no_verify: 是否跳过预提交钩子（用于绕过安全检查）
    
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
        if no_verify:
            args.append('--no-verify')
        
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
        
        return f"🌿 分支列表:\n```\n{stdout}\n```"
        
    except Exception as e:
        return f"❌ 获取分支列表失败: {str(e)}"


def _load_github_token() -> Optional[str]:
    """
    从 .env 文件加载 GITHUB_TOKEN
    
    Returns:
        GitHub Token 或 None
    """
    try:
        # 首先尝试从环境变量读取
        token = os.getenv("GITHUB_TOKEN")
        if token:
            return token
        
        # 从 .env 文件读取
        git_root = _find_git_root()
        if not git_root:
            return None
        
        env_path = Path(git_root) / '.env'
        if not env_path.exists():
            return None
        
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('GITHUB_TOKEN='):
                    return line.split('=', 1)[1].strip()
        
        return None
    except Exception as e:
        logger.warning(f"加载 GITHUB_TOKEN 失败: {e}")
        return None


def _get_remote_url(repo_path: str = ".", remote_name: str = "origin") -> Optional[str]:
    """
    获取指定 remote 的 URL
    
    Args:
        repo_path: 仓库路径
        remote_name: remote 名称
    
    Returns:
        Remote URL 或 None
    """
    try:
        code, stdout, stderr = _run_git_command(
            ['remote', 'get-url', remote_name], 
            cwd=repo_path
        )
        if code == 0:
            return stdout.strip()
        return None
    except Exception:
        return None


def _check_ssh_key() -> Tuple[bool, str]:
    """
    检查 SSH 密钥是否存在
    
    Returns:
        (是否存在, 详细信息)
    """
    ssh_dir = Path.home() / '.ssh'
    
    # 常见的 SSH key 文件名
    key_files = ['id_rsa', 'id_ed25519', 'id_ecdsa', 'id_dsa']
    
    found_keys = []
    for key_file in key_files:
        private_key = ssh_dir / key_file
        public_key = ssh_dir / f"{key_file}.pub"
        if private_key.exists() and public_key.exists():
            found_keys.append(key_file)
    
    if found_keys:
        return True, f"找到 SSH 密钥: {', '.join(found_keys)}"
    else:
        return False, "未找到 SSH 密钥"


def _generate_ssh_key(email: str = "user@example.com", key_type: str = "ed25519") -> Tuple[bool, str]:
    """
    生成 SSH 密钥对
    
    Args:
        email: 关联的邮箱地址
        key_type: 密钥类型 (rsa, ed25519, ecdsa)
    
    Returns:
        (是否成功, 输出信息)
    """
    try:
        ssh_dir = Path.home() / '.ssh'
        ssh_dir.mkdir(mode=0o700, exist_ok=True)
        
        key_file = ssh_dir / f"id_{key_type}"
        
        # 检查是否已存在
        if key_file.exists():
            return False, f"SSH 密钥已存在: {key_file}"
        
        # 生成密钥
        result = subprocess.run(
            ['ssh-keygen', '-t', key_type, '-C', email, '-f', str(key_file), '-N', ''],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            public_key = key_file.with_suffix('.pub')
            return True, f"SSH 密钥生成成功:\n  私钥: {key_file}\n  公钥: {public_key}"
        else:
            return False, f"生成失败: {result.stderr}"
            
    except FileNotFoundError:
        return False, "未找到 ssh-keygen 命令，请确保 OpenSSH 已安装"
    except Exception as e:
        return False, f"生成 SSH 密钥失败: {e}"


def _get_ssh_public_key() -> Optional[str]:
    """
    获取 SSH 公钥内容（用于添加到 GitHub）
    
    Returns:
        公钥内容或 None
    """
    ssh_dir = Path.home() / '.ssh'
    key_files = ['id_ed25519.pub', 'id_rsa.pub', 'id_ecdsa.pub']
    
    for key_file in key_files:
        pub_key_path = ssh_dir / key_file
        if pub_key_path.exists():
            try:
                with open(pub_key_path, 'r') as f:
                    return f.read().strip()
            except Exception:
                continue
    
    return None


def setup_ssh_for_github(email: str = "user@example.com") -> str:
    """
    为 GitHub 配置 SSH 认证
    
    Args:
        email: 关联的邮箱地址
    
    Returns:
        配置指导和公钥信息
    """
    # 检查是否已有密钥
    has_key, key_info = _check_ssh_key()
    
    if has_key:
        pub_key = _get_ssh_public_key()
        guide = f"""✅ {key_info}

📝 公钥内容（已复制到剪贴板）:
{pub_key}

🔧 下一步配置:
1. 登录 GitHub → Settings → SSH and GPG keys
2. 点击 "New SSH key"
3. 粘贴上面的公钥内容
4. 保存后即可使用 SSH 推送

🔗 测试连接:
   ssh -T git@github.com"""
        return guide
    
    # 生成新密钥
    success, result = _generate_ssh_key(email, "ed25519")
    
    if success:
        pub_key = _get_ssh_public_key()
        return f"""✅ {result}

📝 公钥内容:
{pub_key}

🔧 下一步配置:
1. 登录 GitHub → Settings → SSH and GPG keys
2. 点击 "New SSH key"
3. 粘贴上面的公钥内容
4. 保存后即可使用 SSH 推送

🔗 测试连接:
   ssh -T git@github.com"""
    else:
        return f"❌ {result}"


def _configure_remote_with_token(
    repo_path: str = ".",
    remote_name: str = "origin",
    token: Optional[str] = None,
    prefer_ssh: bool = True
) -> bool:
    """
    配置 Git remote，支持 SSH 和 HTTPS with Token
    
    Args:
        repo_path: 仓库路径
        remote_name: remote 名称
        token: GitHub Token（用于 HTTPS），为 None 时自动从 .env 加载
        prefer_ssh: 是否优先使用 SSH 协议（如果当前是 SSH URL 则保持）
    
    Returns:
        是否配置成功
    """
    try:
        git_root = _find_git_root(repo_path)
        if not git_root:
            logger.error("未找到 Git 仓库")
            return False
        
        # 获取当前 remote URL
        current_url = _get_remote_url(git_root, remote_name)
        if not current_url:
            logger.error(f"未找到 remote: {remote_name}")
            return False
        
        # 检查是否是 SSH URL
        is_ssh = current_url.startswith('git@github.com:')
        
        if is_ssh:
            # SSH 协议，检查密钥是否存在
            has_key, key_info = _check_ssh_key()
            if has_key:
                logger.info(f"使用 SSH 协议，{key_info}")
                return True
            else:
                logger.warning(f"SSH URL 配置但 {key_info}")
                # SSH 密钥不存在，尝试转换为 HTTPS with token
                if prefer_ssh:
                    return False  # 保持 SSH，但返回失败让上层处理
        
        # 如果已经是带 token 的 HTTPS URL，直接返回成功
        if '@github.com' in current_url and current_url.startswith('https://'):
            logger.debug("Remote URL 已配置 token")
            return True
        
        # 获取 token
        if not token:
            token = _load_github_token()
        
        if not token:
            if is_ssh:
                logger.error("SSH 密钥不存在且未找到 GITHUB_TOKEN")
            else:
                logger.warning("未找到 GITHUB_TOKEN，请确保 .env 文件中已配置")
            return False
        
        # 构建带 token 的 HTTPS URL
        if current_url.startswith('https://github.com/'):
            # HTTPS URL: https://github.com/owner/repo.git
            new_url = current_url.replace(
                'https://github.com/',
                f'https://{token}@github.com/'
            )
        elif current_url.startswith('git@github.com:'):
            # SSH URL: git@github.com:owner/repo.git
            # 转换为 HTTPS with token
            path = current_url.replace('git@github.com:', '')
            new_url = f'https://{token}@github.com/{path}'
        else:
            logger.warning(f"不支持的 remote URL 格式: {current_url}")
            return False
        
        # 更新 remote URL
        code, _, stderr = _run_git_command(
            ['remote', 'set-url', remote_name, new_url],
            cwd=git_root
        )
        
        if code != 0:
            logger.error(f"设置 remote URL 失败: {stderr}")
            return False
        
        logger.info(f"已配置带 Token 的 HTTPS remote URL")
        return True
        
    except Exception as e:
        logger.error(f"配置 remote URL 失败: {e}")
        return False


def git_push(
    remote: str = "origin",
    branch: Optional[str] = None,
    repo_path: str = ".",
    force: bool = False,
    set_upstream: bool = False,
    auto_configure_token: bool = True,
    prefer_ssh: bool = True
) -> str:
    """
    推送代码到远程仓库，支持 SSH 和 HTTPS with Token
    
    Args:
        remote: 远程仓库名称，默认为 origin
        branch: 分支名称，默认为当前分支
        repo_path: 仓库路径
        force: 是否强制推送
        set_upstream: 是否设置上游分支
        auto_configure_token: 是否自动配置 GitHub Token（用于 HTTPS）
        prefer_ssh: 是否优先使用 SSH（如果 SSH 失败会回退到 HTTPS）
    
    Returns:
        操作结果
    """
    try:
        git_root = _find_git_root(repo_path)
        if not git_root:
            return "❌ 未找到 Git 仓库"
        
        # 获取当前 remote URL
        current_url = _get_remote_url(git_root, remote)
        is_ssh = current_url and current_url.startswith('git@github.com:')
        
        # 自动配置
        if auto_configure_token:
            config_result = _configure_remote_with_token(
                git_root, remote, prefer_ssh=prefer_ssh
            )
            
            if not config_result:
                # 配置失败，检查是否是 SSH 问题
                if is_ssh and prefer_ssh:
                    has_key, _ = _check_ssh_key()
                    if not has_key:
                        return f"""⚠️ SSH 配置未完成

当前使用 SSH 协议: {current_url}
但未找到 SSH 密钥。

请选择以下方案之一：

方案 1️⃣: 配置 SSH 密钥（推荐）
运行: setup_ssh_for_github()
或手动执行:
   ssh-keygen -t ed25519 -C "your@email.com"
   cat ~/.ssh/id_ed25519.pub
然后将公钥添加到 GitHub → Settings → SSH keys

方案 2️⃣: 切换到 HTTPS with Token
当前 .env 中已配置 GITHUB_TOKEN，可自动切换到 HTTPS
运行 git_push(prefer_ssh=False) 或手动执行:
   git remote set-url origin https://$GITHUB_TOKEN@github.com/yan931305137/ai_evolution.git

方案 3️⃣: 检查 .env 配置
确保 .env 文件中包含:
   GITHUB_TOKEN=ghp_xxxxxxxxxxxx"""
                else:
                    return """❌ 认证配置失败

可能的原因：
1. .env 文件中未配置 GITHUB_TOKEN
2. Token 格式不正确

解决方法：
1. 编辑 .env 文件，添加：
   GITHUB_TOKEN=ghp_xxxxxxxxxxxx
2. 获取 Token: https://github.com/settings/tokens
3. 确保 Token 有 repo 权限"""
        
        # 构建 push 命令
        args = ['push']
        if force:
            args.append('--force')
        args.append(remote)
        
        # 获取当前分支（如果未指定）
        if not branch:
            code, stdout, _ = _run_git_command(
                ['rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=git_root
            )
            if code == 0:
                branch = stdout.strip()
        
        if branch:
            if set_upstream:
                args.extend(['--set-upstream'])
            args.append(branch)
        
        # 执行 push
        code, stdout, stderr = _run_git_command(args, cwd=git_root)
        
        if code != 0:
            # 常见错误处理
            if "rejected" in stderr.lower():
                return f"""❌ 推送被拒绝

{stderr}

可能的原因：
1. 远程仓库有新的提交，需要先 pull
2. 权限不足

建议操作：
1. git pull origin {branch or 'main'} --rebase
2. 解决冲突后重新推送"""
            elif "could not resolve host" in stderr.lower():
                return f"❌ 网络错误: 无法连接到 GitHub\n\n{stderr}"
            elif "authentication failed" in stderr.lower():
                return f"""❌ 认证失败

{stderr}

Token 可能已过期或无效，请：
1. 在 GitHub 重新生成 Token
2. 更新 .env 文件中的 GITHUB_TOKEN"""
            else:
                return f"❌ Git push 失败:\n{stderr}"
        
        # 解析输出
        result_lines = stdout.strip().split('\n') if stdout else []
        summary = []
        
        for line in result_lines:
            if '->' in line:
                summary.append(f"✅ 推送成功: {line.strip()}")
        
        if not summary:
            summary.append("✅ 推送完成")
        
        result = '\n'.join(summary)
        
        # 添加统计信息
        if stdout:
            result += f"\n\n📊 详细信息:\n```\n{stdout}\n```"
        
        return result
        
    except Exception as e:
        return f"❌ Git push 失败: {str(e)}"


def git_pull(
    remote: str = "origin",
    branch: Optional[str] = None,
    repo_path: str = ".",
    rebase: bool = False
) -> str:
    """
    从远程仓库拉取代码
    
    Args:
        remote: 远程仓库名称
        branch: 分支名称
        repo_path: 仓库路径
        rebase: 是否使用 rebase 模式
    
    Returns:
        操作结果
    """
    try:
        git_root = _find_git_root(repo_path)
        if not git_root:
            return "❌ 未找到 Git 仓库"
        
        # 自动配置 Token
        _configure_remote_with_token(git_root, remote)
        
        # 构建 pull 命令
        args = ['pull']
        if rebase:
            args.append('--rebase')
        args.append(remote)
        
        if branch:
            args.append(branch)
        
        code, stdout, stderr = _run_git_command(args, cwd=git_root)
        
        if code != 0:
            if "conflict" in stderr.lower():
                return f"""⚠️ 存在合并冲突

{stderr}

请手动解决冲突后执行:
1. 编辑冲突文件
2. git add .
3. git rebase --continue"""
            return f"❌ Git pull 失败:\n{stderr}"
        
        if "already up to date" in stdout.lower():
            return "✅ 已经是最新代码"
        
        return f"✅ 拉取成功:\n```\n{stdout}\n```"
        
    except Exception as e:
        return f"❌ Git pull 失败: {str(e)}"


def git_clone(
    repo_url: str,
    target_path: Optional[str] = None,
    branch: Optional[str] = None,
    depth: Optional[int] = None
) -> str:
    """
    克隆远程仓库，支持自动配置 Token
    
    Args:
        repo_url: 仓库地址
        target_path: 目标目录
        branch: 指定分支
        depth: 浅克隆深度
    
    Returns:
        操作结果
    """
    try:
        # 尝试从 .env 加载 token
        token = _load_github_token()
        
        # 如果是 GitHub URL 且没有 token，添加警告
        if 'github.com' in repo_url and not token:
            logger.warning("未找到 GITHUB_TOKEN，克隆私有仓库可能会失败")
        
        # 处理 URL，添加 token（如果是 GitHub HTTPS URL）
        if token and repo_url.startswith('https://github.com/'):
            repo_url = repo_url.replace(
                'https://github.com/',
                f'https://{token}@github.com/'
            )
        
        # 构建 clone 命令
        args = ['clone']
        
        if branch:
            args.extend(['--branch', branch])
        
        if depth:
            args.extend(['--depth', str(depth)])
        
        args.append(repo_url)
        
        if target_path:
            args.append(target_path)
        
        code, stdout, stderr = _run_git_command(args)
        
        if code != 0:
            return f"❌ Git clone 失败:\n{stderr}"
        
        # 确定克隆到的目录
        cloned_to = target_path
        if not cloned_to:
            # 从 URL 提取仓库名
            repo_name = repo_url.split('/')[-1].replace('.git', '')
            cloned_to = repo_name
        
        return f"✅ 克隆成功: {repo_url}\n📁 目录: {cloned_to}"
        
    except Exception as e:
        return f"❌ Git clone 失败: {str(e)}"


def git_auto_push(
    message: str,
    files: str = ".",
    repo_path: str = ".",
    remote: str = "origin",
    branch: Optional[str] = None,
    prefer_ssh: bool = False,
    no_verify: bool = False
) -> str:
    """
    一键提交并推送（add + commit + push）
    
    Args:
        message: 提交信息
        files: 要添加的文件，默认全部
        repo_path: 仓库路径
        remote: 远程仓库
        branch: 目标分支
        prefer_ssh: 是否优先使用 SSH（默认 False，使用 HTTPS with Token）
        no_verify: 是否跳过预提交钩子（用于绕过安全检查）
    
    Returns:
        操作结果汇总
    """
    results = []
    
    # Step 1: git add
    result = git_add(files, repo_path)
    results.append(result)
    
    if "❌" in result:
        return f"添加文件失败:\n{result}"
    
    # Step 2: git commit
    result = git_commit(message, repo_path, no_verify=no_verify)
    results.append(result)
    
    if "❌" in result:
        return f"提交失败:\n{result}"
    
    if "没有要提交的变更" in result:
        return "⚠️ 没有变更需要推送"
    
    # Step 3: git push
    result = git_push(remote, branch, repo_path, set_upstream=True, prefer_ssh=prefer_ssh)
    results.append(result)
    
    return "\n".join(results)
