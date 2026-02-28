import os
import shutil
from pathlib import Path
from datetime import datetime

# 导入文档生命周期管理器
try:
    from src.utils.doc_lifecycle import doc_lifecycle
    DOC_LIFECYCLE_ENABLED = True
except ImportError:
    DOC_LIFECYCLE_ENABLED = False

def _check_doc_impact(file_path: str) -> str:
    """检查文件变更对文档的影响"""
    if not DOC_LIFECYCLE_ENABLED:
        return ""
    
    affected = doc_lifecycle.check_file_changes(file_path)
    if affected:
        docs = doc_lifecycle.get_stale_documents()
        warning = "\n⚠️  【文档更新提醒】以下文档关联的文件已被修改，可能需要同步更新:\n"
        for doc in docs:
            warning += f"   - {doc['path']} ({doc['title']})\n"
        warning += "   建议: 检查这些文档是否仍然准确，必要时更新或删除。\n"
        return warning
    return ""

def list_files(directory: str = ".") -> str:
    """List files and directories in the specified path."""
    try:
        path = Path(directory).resolve()
        if not path.exists():
            return f"Error: Directory '{directory}' does not exist."
        
        items = []
        for item in path.iterdir():
            type_str = "DIR" if item.is_dir() else "FILE"
            items.append(f"[{type_str}] {item.name}")
        return "\n".join(items) if items else "(Empty directory)"
    except Exception as e:
        return f"Error listing files: {str(e)}"

def read_file(file_path: str) -> str:
    """Read the content of a file."""
    try:
        path = Path(file_path).resolve()
        if not path.exists():
            return f"Error: File '{file_path}' does not exist."
        if not path.is_file():
            return f"Error: '{file_path}' is not a file."
            
        # Limit size to prevent context overflow (e.g. 10KB)
        if path.stat().st_size > 10000:
            return f"Error: File '{file_path}' is too large to read directly (Size: {path.stat().st_size} bytes)."
            
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

def write_file(file_path: str, content: str) -> str:
    """Write content to a file (Overwrites existing file)."""
    try:
        path = Path(file_path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # 检查是否是更新操作（文件已存在）
        is_update = path.exists()
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        result = f"Successfully wrote to '{file_path}'."
        
        # 如果是更新操作，检查关联文档
        if is_update:
            doc_warning = _check_doc_impact(file_path)
            if doc_warning:
                result += doc_warning
        
        return result
    except Exception as e:
        return f"Error writing file: {str(e)}"

def move_file(src: str, dst: str) -> str:
    """Move a file or directory."""
    try:
        shutil.move(src, dst)
        return f"Successfully moved '{src}' to '{dst}'."
    except Exception as e:
        return f"Error moving file: {str(e)}"

def scan_project(directory: str = ".") -> str:
    """Recursively scan project structure and read code summaries."""
    try:
        path = Path(directory).resolve()
        if not path.exists():
            return f"Error: Directory '{directory}' does not exist."
        
        summary = [f"Project Scan for: {path.name}\n"]
        
        # Walk through directory
        for root, dirs, files in os.walk(path):
            # Skip hidden folders and common ignores
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv', 'env', 'node_modules', 'reports']]
            
            rel_root = Path(root).relative_to(path)
            level = len(rel_root.parts)
            indent = "  " * level
            summary.append(f"{indent}📂 {rel_root if str(rel_root) != '.' else ''}/")
            
            for f in files:
                if f.startswith('.') or f.endswith(('.pyc', '.db', '.log', '.png', '.jpg')):
                    continue
                    
                file_path = Path(root) / f
                summary.append(f"{indent}  📄 {f}")
                
                # Read small code files content directly
                if f.endswith(('.py', '.yaml', '.json', '.md', '.txt')):
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        # Extract docstrings or first few lines for summary
                        lines = content.splitlines()
                        if lines:
                            summary.append(f"{indent}    Last modified: {datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M')}")
                            # Simple "AI-friendly" compression: show imports and defs
                            interesting_lines = [l.strip() for l in lines if l.strip().startswith(('import', 'from', 'class', 'def', '#'))][:5]
                            if interesting_lines:
                                summary.append(f"{indent}    Preview: {'; '.join(interesting_lines)}...")
                    except Exception:
                        pass
                        
        return "\n".join(summary)
    except Exception as e:
        return f"Error scanning project: {str(e)}"


def register_document(doc_path: str, title: str, doc_type: str, task_goal: str, related_files: list = None) -> str:
    """
    注册文档到生命周期管理系统
    
    Args:
        doc_path: 文档路径
        title: 文档标题
        doc_type: 文档类型 (analysis/design/learning/decision/config/standard)
        task_goal: 关联的任务目标（用于生成task_id）
        related_files: 关联的代码文件路径列表
    
    Returns:
        注册结果信息
    """
    if not DOC_LIFECYCLE_ENABLED:
        return "Document lifecycle manager not available."
    
    try:
        import hashlib
        task_id = f"task_{hashlib.md5(task_goal.encode()).hexdigest()[:8]}"
        
        # 自动发现关联文件（如果没有提供）
        if related_files is None:
            related_files = []
            # 尝试从文档内容中提取文件引用
            if os.path.exists(doc_path):
                try:
                    with open(doc_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 简单启发式：查找 src/ 开头的文件引用
                        import re
                        matches = re.findall(r'src/[a-zA-Z_/]+\.py', content)
                        related_files = list(set(matches))  # 去重
                except:
                    pass
        
        doc_id = doc_lifecycle.register_document(
            doc_path=doc_path,
            title=title,
            task_id=task_id,
            doc_type=doc_type,
            related_files=related_files
        )
        
        config = doc_lifecycle.DEFAULT_CONFIG.get(doc_type, {"ttl_days": 7, "auto_delete": True})
        ttl_info = f"{config['ttl_days']}天" if config['ttl_days'] > 0 else "永久"
        auto_del_info = "任务完成后自动删除" if config['auto_delete'] else "长期保留"
        
        return f"📄 文档已注册: {doc_id}\n   类型: {doc_type} | 有效期: {ttl_info} | {auto_del_info}"
    except Exception as e:
        return f"Error registering document: {str(e)}"


def check_documents_status() -> str:
    """检查文档状态，返回需要更新的文档列表"""
    if not DOC_LIFECYCLE_ENABLED:
        return "Document lifecycle manager not available."
    
    try:
        return doc_lifecycle.generate_report()
    except Exception as e:
        return f"Error checking documents: {str(e)}"
