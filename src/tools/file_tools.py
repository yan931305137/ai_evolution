import os
import shutil
from pathlib import Path
from datetime import datetime

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
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to '{file_path}'."
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
