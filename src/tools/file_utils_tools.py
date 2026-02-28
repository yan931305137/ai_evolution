"""
文件操作增强工具集 - 提供文件删除、复制、信息获取等功能
"""
import os
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Union, Optional
import logging

logger = logging.getLogger(__name__)


def delete_file(file_path: str, safe_mode: bool = True) -> str:
    """
    删除文件
    
    Args:
        file_path: 要删除的文件路径
        safe_mode: 安全模式（True时禁止删除核心目录文件）
    
    Returns:
        操作结果描述
    """
    try:
        path = Path(file_path)
        
        if not path.exists():
            return f"⚠️ 文件不存在: {file_path}"
        
        if path.is_dir():
            return f"❌ 路径是目录而非文件，请使用 rmdir 工具: {file_path}"
        
        # 安全模式检查
        if safe_mode:
            # 检查是否在禁止删除的核心目录
            forbidden_prefixes = ['./core/', './config/', './src/core/', './src/agents/', './skills/']
            abs_path = str(path.absolute())
            for prefix in forbidden_prefixes:
                if abs_path.startswith(str(Path(prefix).absolute())):
                    return f"🚫 安全模式: 禁止删除核心目录文件: {file_path}"
        
        path.unlink()
        return f"✅ 文件删除成功: {file_path}"
        
    except Exception as e:
        return f"❌ 删除文件失败: {file_path}, 错误: {str(e)}"


def copy_file(src: str, dst: str, overwrite: bool = False) -> str:
    """
    复制文件
    
    Args:
        src: 源文件路径
        dst: 目标文件路径
        overwrite: 如果目标存在是否覆盖
    
    Returns:
        操作结果描述
    """
    try:
        src_path = Path(src)
        dst_path = Path(dst)
        
        if not src_path.exists():
            return f"❌ 源文件不存在: {src}"
        
        if not src_path.is_file():
            return f"❌ 源路径不是文件: {src}"
        
        if dst_path.exists() and not overwrite:
            return f"❌ 目标文件已存在: {dst}"
        
        # 确保目标目录存在
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(src_path, dst_path)  # copy2 保留元数据
        return f"✅ 文件复制成功: {src} → {dst}"
        
    except Exception as e:
        return f"❌ 复制文件失败: {str(e)}"


def get_file_info(file_path: str) -> str:
    """
    获取文件详细信息
    
    Args:
        file_path: 文件路径
    
    Returns:
        文件信息描述
    """
    try:
        path = Path(file_path)
        
        if not path.exists():
            return f"❌ 文件不存在: {file_path}"
        
        stat = path.stat()
        
        # 格式化大小
        size_bytes = stat.st_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                size_str = f"{size_bytes:.2f} {unit}"
                break
            size_bytes /= 1024
        else:
            size_str = f"{size_bytes:.2f} TB"
        
        # 格式化时间
        mtime = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        ctime = datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
        atime = datetime.fromtimestamp(stat.st_atime).strftime('%Y-%m-%d %H:%M:%S')
        
        # 计算MD5（小文件才计算）
        md5_hash = "N/A (文件太大)"
        if stat.st_size < 10 * 1024 * 1024:  # 小于10MB
            try:
                with open(path, 'rb') as f:
                    md5_hash = hashlib.md5(f.read()).hexdigest()
            except:
                md5_hash = "计算失败"
        
        info = f"""
📄 文件信息: {path.name}
═══════════════════════════════════════
📍 路径: {path.absolute()}
📦 大小: {size_str} ({stat.st_size:,} bytes)

📝 类型信息:
   扩展名: {path.suffix or '(无)'}
   MIME类型: {get_mime_type(path)}

⏰ 时间戳:
   修改时间: {mtime}
   创建时间: {ctime}
   访问时间: {atime}

🔐 校验:
   MD5: {md5_hash}
   权限: {oct(stat.st_mode)[-3:]}
   inode: {stat.st_ino}
═══════════════════════════════════════
"""
        return info
        
    except Exception as e:
        return f"❌ 获取文件信息失败: {file_path}, 错误: {str(e)}"


def get_mime_type(path: Path) -> str:
    """获取文件的 MIME 类型"""
    ext = path.suffix.lower()
    mime_types = {
        '.txt': 'text/plain',
        '.py': 'text/x-python',
        '.js': 'application/javascript',
        '.ts': 'application/typescript',
        '.json': 'application/json',
        '.yaml': 'application/yaml',
        '.yml': 'application/yaml',
        '.xml': 'application/xml',
        '.html': 'text/html',
        '.css': 'text/css',
        '.md': 'text/markdown',
        '.csv': 'text/csv',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.pdf': 'application/pdf',
        '.zip': 'application/zip',
        '.tar': 'application/x-tar',
        '.gz': 'application/gzip',
    }
    return mime_types.get(ext, 'application/octet-stream')


def rename_file(src: str, dst: str, overwrite: bool = False) -> str:
    """
    重命名文件
    
    Args:
        src: 原文件名
        dst: 新文件名
        overwrite: 如果目标存在是否覆盖
    
    Returns:
        操作结果描述
    """
    try:
        src_path = Path(src)
        dst_path = Path(dst)
        
        if not src_path.exists():
            return f"❌ 源文件不存在: {src}"
        
        if dst_path.exists() and not overwrite:
            return f"❌ 目标文件已存在: {dst}"
        
        src_path.rename(dst_path)
        return f"✅ 文件重命名成功: {src} → {dst}"
        
    except Exception as e:
        return f"❌ 重命名文件失败: {str(e)}"


def compare_files(file1: str, file2: str) -> str:
    """
    比较两个文件的内容差异
    
    Args:
        file1: 第一个文件路径
        file2: 第二个文件路径
    
    Returns:
        比较结果
    """
    try:
        path1 = Path(file1)
        path2 = Path(file2)
        
        if not path1.exists():
            return f"❌ 文件不存在: {file1}"
        if not path2.exists():
            return f"❌ 文件不存在: {file2}"
        
        # 比较大小
        size1 = path1.stat().st_size
        size2 = path2.stat().st_size
        
        if size1 != size2:
            return f"📊 文件大小不同:\n  {file1}: {size1:,} bytes\n  {file2}: {size2:,} bytes"
        
        # 比较内容（文本文件）
        if path1.suffix in ['.txt', '.py', '.js', '.json', '.md', '.yaml', '.yml']:
            with open(path1, 'r', encoding='utf-8', errors='ignore') as f:
                content1 = f.read()
            with open(path2, 'r', encoding='utf-8', errors='ignore') as f:
                content2 = f.read()
            
            if content1 == content2:
                return f"✅ 文件内容完全相同\n  {file1}\n  {file2}"
            else:
                # 简单的行级别比较
                lines1 = content1.split('\n')
                lines2 = content2.split('\n')
                diff_count = sum(1 for a, b in zip(lines1, lines2) if a != b)
                diff_count += abs(len(lines1) - len(lines2))
                return f"⚠️ 文件内容不同\n  行数: {len(lines1)} vs {len(lines2)}\n  差异行数: {diff_count}"
        else:
            # 二进制文件，比较MD5
            with open(path1, 'rb') as f:
                md5_1 = hashlib.md5(f.read()).hexdigest()
            with open(path2, 'rb') as f:
                md5_2 = hashlib.md5(f.read()).hexdigest()
            
            if md5_1 == md5_2:
                return f"✅ 文件内容相同 (MD5: {md5_1})"
            else:
                return f"⚠️ 文件内容不同\n  MD1: {md5_1}\n  MD2: {md5_2}"
                
    except Exception as e:
        return f"❌ 比较文件失败: {str(e)}"
