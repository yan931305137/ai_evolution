"""
目录操作工具集 - 提供目录创建、删除、信息获取等功能
"""
import os
import shutil
from pathlib import Path
from typing import Dict, Union, List
import logging

logger = logging.getLogger(__name__)


def mkdir(directory_path: str, exist_ok: bool = True, parents: bool = True) -> str:
    """
    创建目录
    
    重要说明：这是 Python 函数，不是 shell 命令。
    不支持 shell 的 brace expansion（如 {a,b,c}），如需创建多个目录请分别调用。
    
    Args:
        directory_path: 要创建的目录路径，例如："src/brain/memory"
        exist_ok: 如果目录已存在是否忽略错误
        parents: 是否自动创建父目录
    
    Returns:
        操作结果描述
    
    Examples:
        >>> mkdir("src/brain/memory")
        >>> mkdir("src/brain/perception")
        # 错误用法（不支持）：mkdir("src/brain/{memory,perception}")
    """
    try:
        path = Path(directory_path)
        path.mkdir(exist_ok=exist_ok, parents=parents)
        return f"✅ 目录创建成功: {directory_path}"
    except FileExistsError:
        return f"⚠️ 目录已存在: {directory_path}"
    except Exception as e:
        return f"❌ 创建目录失败: {directory_path}, 错误: {str(e)}"


def rmdir(directory_path: str, recursive: bool = False) -> str:
    """
    删除目录
    
    Args:
        directory_path: 要删除的目录路径
        recursive: 是否递归删除目录及其内容
    
    Returns:
        操作结果描述
    """
    try:
        path = Path(directory_path)
        if not path.exists():
            return f"⚠️ 目录不存在: {directory_path}"
        
        if not path.is_dir():
            return f"❌ 路径不是目录: {directory_path}"
        
        if recursive:
            shutil.rmtree(path)
            return f"✅ 目录递归删除成功: {directory_path}"
        else:
            path.rmdir()  # 只能删除空目录
            return f"✅ 空目录删除成功: {directory_path}"
    except OSError as e:
        if "Directory not empty" in str(e):
            return f"❌ 目录非空，无法删除。请使用 recursive=True 参数: {directory_path}"
        return f"❌ 删除目录失败: {directory_path}, 错误: {str(e)}"
    except Exception as e:
        return f"❌ 删除目录失败: {directory_path}, 错误: {str(e)}"


def get_dir_info(directory_path: str = ".") -> str:
    """
    获取目录详细信息
    
    Args:
        directory_path: 目录路径，默认为当前目录
    
    Returns:
        目录信息描述
    """
    try:
        path = Path(directory_path)
        if not path.exists():
            return f"❌ 目录不存在: {directory_path}"
        
        if not path.is_dir():
            return f"❌ 路径不是目录: {directory_path}"
        
        # 统计信息
        total_size = 0
        file_count = 0
        dir_count = 0
        file_types = {}
        
        for item in path.rglob("*"):
            if item.is_file():
                file_count += 1
                size = item.stat().st_size
                total_size += size
                
                # 统计文件类型
                ext = item.suffix.lower() or "(无扩展名)"
                file_types[ext] = file_types.get(ext, 0) + 1
            elif item.is_dir():
                dir_count += 1
        
        # 格式化大小
        def format_size(size_bytes):
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_bytes < 1024:
                    return f"{size_bytes:.2f} {unit}"
                size_bytes /= 1024
            return f"{size_bytes:.2f} TB"
        
        # 构建报告
        report = f"""
📁 目录信息: {path.absolute()}
═══════════════════════════════════════
📊 统计:
   文件数: {file_count}
   子目录: {dir_count}
   总大小: {format_size(total_size)}

📈 文件类型分布:
"""
        # 按数量排序显示文件类型
        sorted_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:10]
        for ext, count in sorted_types:
            report += f"   {ext:12} : {count} 个\n"
        
        if len(file_types) > 10:
            report += f"   ... 和其他 {len(file_types) - 10} 种类型\n"
        
        return report
        
    except Exception as e:
        return f"❌ 获取目录信息失败: {directory_path}, 错误: {str(e)}"


def list_dir_tree(directory_path: str = ".", max_depth: int = 3) -> str:
    """
    以树形结构列出目录内容
    
    Args:
        directory_path: 目录路径
        max_depth: 最大递归深度
    
    Returns:
        树形结构字符串
    """
    try:
        path = Path(directory_path)
        if not path.exists():
            return f"❌ 目录不存在: {directory_path}"
        
        if not path.is_dir():
            return f"❌ 路径不是目录: {directory_path}"
        
        def build_tree(current_path: Path, prefix: str = "", depth: int = 0) -> str:
            if depth > max_depth:
                return f"{prefix}... (达到最大深度 {max_depth})\n"
            
            result = ""
            try:
                items = sorted(current_path.iterdir(), key=lambda x: (x.is_file(), x.name))
            except PermissionError:
                return f"{prefix}[权限 denied]\n"
            
            for i, item in enumerate(items):
                is_last = (i == len(items) - 1)
                connector = "└── " if is_last else "├── "
                
                if item.is_dir():
                    result += f"{prefix}{connector}📂 {item.name}/\n"
                    new_prefix = prefix + ("    " if is_last else "│   ")
                    result += build_tree(item, new_prefix, depth + 1)
                else:
                    icon = "📄"
                    if item.suffix in ['.py', '.js', '.ts', '.java', '.go']:
                        icon = "🐍" if item.suffix == '.py' else "📜"
                    elif item.suffix in ['.md', '.txt', '.rst']:
                        icon = "📝"
                    elif item.suffix in ['.json', '.yaml', '.yml', '.xml']:
                        icon = "⚙️"
                    result += f"{prefix}{connector}{icon} {item.name}\n"
            
            return result
        
        tree = f"📁 {path.absolute()}\n"
        tree += build_tree(path)
        return tree
        
    except Exception as e:
        return f"❌ 生成目录树失败: {directory_path}, 错误: {str(e)}"


def copy_dir(src: str, dst: str, overwrite: bool = False) -> str:
    """
    复制整个目录
    
    Args:
        src: 源目录路径
        dst: 目标目录路径
        overwrite: 如果目标存在是否覆盖
    
    Returns:
        操作结果描述
    """
    try:
        src_path = Path(src)
        dst_path = Path(dst)
        
        if not src_path.exists():
            return f"❌ 源目录不存在: {src}"
        
        if not src_path.is_dir():
            return f"❌ 源路径不是目录: {src}"
        
        if dst_path.exists():
            if overwrite:
                shutil.rmtree(dst_path)
            else:
                return f"❌ 目标目录已存在: {dst}"
        
        shutil.copytree(src_path, dst_path)
        return f"✅ 目录复制成功: {src} → {dst}"
        
    except Exception as e:
        return f"❌ 复制目录失败: {str(e)}"
