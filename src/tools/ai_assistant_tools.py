"""
AI 助手专用工具集
为 AI Agent 提供代码分析、项目洞察、智能搜索等能力
"""
import os
import re
import ast
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class FunctionInfo:
    """函数信息"""
    name: str
    file_path: str
    line_start: int
    line_end: int
    args: List[str]
    docstring: Optional[str]
    calls: List[str]  # 调用的其他函数
    complexity: int  # 简单复杂度估算


@dataclass
class ClassInfo:
    """类信息"""
    name: str
    file_path: str
    line_start: int
    line_end: int
    methods: List[str]
    docstring: Optional[str]
    base_classes: List[str]


class CodeAnalyzer:
    """代码分析器"""
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path).resolve()
        self.functions: Dict[str, List[FunctionInfo]] = defaultdict(list)
        self.classes: Dict[str, List[ClassInfo]] = defaultdict(list)
        self.imports: Dict[str, Set[str]] = defaultdict(set)
        self._indexed = False
    
    def index_project(self) -> str:
        """索引整个项目代码"""
        logger.info(f"Indexing project: {self.project_path}")
        py_files = list(self.project_path.rglob("*.py"))
        
        for file_path in py_files:
            if any(part.startswith('.') or part in ['venv', '__pycache__'] 
                   for part in file_path.parts):
                continue
            try:
                self._analyze_file(file_path)
            except Exception as e:
                logger.debug(f"Failed to analyze {file_path}: {e}")
        
        self._indexed = True
        return f"Indexed {len(py_files)} files, found {sum(len(v) for v in self.functions.values())} functions, {sum(len(v) for v in self.classes.values())} classes"
    
    def _analyze_file(self, file_path: Path):
        """分析单个文件"""
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)
            
            lines = content.splitlines()
            relative_path = str(file_path.relative_to(self.project_path))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    self._extract_function(node, relative_path, lines)
                elif isinstance(node, ast.ClassDef):
                    self._extract_class(node, relative_path, lines)
                elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    self._extract_import(node, relative_path)
        except SyntaxError:
            pass  # 忽略语法错误的文件
    
    def _extract_function(self, node: ast.FunctionDef, file_path: str, lines: List[str]):
        """提取函数信息"""
        # 获取函数调用
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.append(child.func.attr)
        
        # 简单复杂度：语句数量
        complexity = len(list(ast.walk(node)))
        
        # 获取 docstring
        docstring = ast.get_docstring(node)
        
        func_info = FunctionInfo(
            name=node.name,
            file_path=file_path,
            line_start=node.lineno,
            line_end=node.end_lineno,
            args=[arg.arg for arg in node.args.args],
            docstring=docstring,
            calls=list(set(calls)),
            complexity=complexity
        )
        self.functions[node.name].append(func_info)
    
    def _extract_class(self, node: ast.ClassDef, file_path: str, lines: List[str]):
        """提取类信息"""
        methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
        docstring = ast.get_docstring(node)
        
        class_info = ClassInfo(
            name=node.name,
            file_path=file_path,
            line_start=node.lineno,
            line_end=node.end_lineno,
            methods=methods,
            docstring=docstring,
            base_classes=[ast.unparse(base) for base in node.bases]
        )
        self.classes[node.name].append(class_info)
    
    def _extract_import(self, node: ast.AST, file_path: str):
        """提取导入信息"""
        if isinstance(node, ast.Import):
            for alias in node.names:
                self.imports[file_path].add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            self.imports[file_path].add(node.module)
    
    def find_function(self, name: str) -> List[Dict]:
        """查找函数定义"""
        if not self._indexed:
            self.index_project()
        
        results = []
        for func_info in self.functions.get(name, []):
            results.append({
                "name": func_info.name,
                "file": func_info.file_path,
                "lines": f"{func_info.line_start}-{func_info.line_end}",
                "args": func_info.args,
                "docstring": func_info.docstring[:200] if func_info.docstring else None,
                "complexity": func_info.complexity
            })
        return results
    
    def find_class(self, name: str) -> List[Dict]:
        """查找类定义"""
        if not self._indexed:
            self.index_project()
        
        results = []
        for class_info in self.classes.get(name, []):
            results.append({
                "name": class_info.name,
                "file": class_info.file_path,
                "lines": f"{class_info.line_start}-{class_info.line_end}",
                "methods": class_info.methods,
                "docstring": class_info.docstring[:200] if class_info.docstring else None,
                "base_classes": class_info.base_classes
            })
        return results
    
    def get_call_graph(self, function_name: str, depth: int = 3) -> Dict:
        """获取函数调用图"""
        if not self._indexed:
            self.index_project()
        
        def build_graph(name: str, current_depth: int) -> Dict:
            if current_depth <= 0:
                return {"name": name, "calls": [], "truncated": True}
            
            funcs = self.functions.get(name, [])
            if not funcs:
                return {"name": name, "calls": [], "not_found": True}
            
            calls = []
            for called_func in funcs[0].calls:  # 使用第一个匹配
                calls.append(build_graph(called_func, current_depth - 1))
            
            return {
                "name": name,
                "file": funcs[0].file_path,
                "calls": calls
            }
        
        return build_graph(function_name, depth)
    
    def analyze_dependencies(self, file_path: str) -> Dict:
        """分析文件依赖关系"""
        if not self._indexed:
            self.index_project()
        
        # 找出哪些文件依赖这个文件
        dependents = []
        for fp, imports in self.imports.items():
            # 简化处理：检查导入路径
            if file_path.replace('/', '.').replace('.py', '') in str(imports):
                dependents.append(fp)
        
        return {
            "file": file_path,
            "imported_by": dependents,
            "dependent_count": len(dependents)
        }


# 全局分析器实例
_code_analyzer = None

def get_analyzer() -> CodeAnalyzer:
    """获取全局代码分析器"""
    global _code_analyzer
    if _code_analyzer is None:
        _code_analyzer = CodeAnalyzer()
    return _code_analyzer


# ============ 工具函数 ============

def analyze_code(file_path: str = None, function_name: str = None, class_name: str = None) -> str:
    """
    分析代码结构
    
    Args:
        file_path: 文件路径（可选）
        function_name: 函数名（可选）
        class_name: 类名（可选）
    
    Returns:
        分析报告
    """
    analyzer = get_analyzer()
    
    if function_name:
        results = analyzer.find_function(function_name)
        if not results:
            return f"未找到函数: {function_name}"
        
        report = f"📍 函数 '{function_name}' 分析:\n"
        report += "=" * 50 + "\n"
        for r in results:
            report += f"📄 文件: {r['file']} (第 {r['lines']} 行)\n"
            report += f"   参数: {', '.join(r['args'])}\n"
            report += f"   复杂度: {r['complexity']}\n"
            if r['docstring']:
                report += f"   文档: {r['docstring']}\n"
            report += "\n"
        return report
    
    if class_name:
        results = analyzer.find_class(class_name)
        if not results:
            return f"未找到类: {class_name}"
        
        report = f"📍 类 '{class_name}' 分析:\n"
        report += "=" * 50 + "\n"
        for r in results:
            report += f"📄 文件: {r['file']} (第 {r['lines']} 行)\n"
            report += f"   方法数: {len(r['methods'])}\n"
            report += f"   方法: {', '.join(r['methods'][:10])}{'...' if len(r['methods']) > 10 else ''}\n"
            if r['base_classes']:
                report += f"   继承: {', '.join(r['base_classes'])}\n"
            if r['docstring']:
                report += f"   文档: {r['docstring']}\n"
            report += "\n"
        return report
    
    if file_path:
        full_path = Path(file_path)
        if not full_path.exists():
            return f"文件不存在: {file_path}"
        
        # 简单的文件分析
        content = full_path.read_text(encoding='utf-8', errors='ignore')
        lines = content.splitlines()
        
        # 统计
        func_count = len(re.findall(r'^\s*def\s+', content, re.MULTILINE))
        class_count = len(re.findall(r'^\s*class\s+', content, re.MULTILINE))
        import_count = len(re.findall(r'^\s*(import|from)\s+', content, re.MULTILINE))
        
        report = f"📄 文件 '{file_path}' 分析:\n"
        report += "=" * 50 + "\n"
        report += f"   总行数: {len(lines)}\n"
        report += f"   函数数: {func_count}\n"
        report += f"   类数: {class_count}\n"
        report += f"   导入数: {import_count}\n"
        
        # 依赖分析
        deps = analyzer.analyze_dependencies(file_path)
        if deps['dependent_count'] > 0:
            report += f"   被 {deps['dependent_count']} 个文件引用\n"
        
        return report
    
    return "请提供 file_path、function_name 或 class_name 之一"


def search_code(query: str, file_pattern: str = "*.py") -> str:
    """
    智能代码搜索
    
    Args:
        query: 搜索关键词（函数名、类名、变量名等）
        file_pattern: 文件匹配模式
    
    Returns:
        搜索结果
    """
    results = []
    
    for file_path in Path('.').rglob(file_pattern):
        if any(part.startswith('.') or part in ['venv', '__pycache__'] 
               for part in file_path.parts):
            continue
        
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.splitlines()
            
            # 逐行搜索
            for i, line in enumerate(lines, 1):
                if query in line:
                    # 获取上下文
                    context_start = max(0, i - 2)
                    context_end = min(len(lines), i + 2)
                    context = lines[context_start:context_end]
                    
                    results.append({
                        "file": str(file_path),
                        "line": i,
                        "content": line.strip(),
                        "context": context
                    })
        except Exception:
            continue
    
    if not results:
        return f"未找到包含 '{query}' 的代码"
    
    # 格式化输出
    report = f"🔍 代码搜索结果: '{query}'\n"
    report += "=" * 60 + "\n"
    report += f"找到 {len(results)} 处匹配:\n\n"
    
    # 按文件分组
    by_file = defaultdict(list)
    for r in results:
        by_file[r['file']].append(r)
    
    for file, matches in sorted(by_file.items())[:10]:  # 最多显示10个文件
        report += f"📄 {file}\n"
        for m in matches[:3]:  # 每个文件最多3处
            report += f"   第 {m['line']} 行: {m['content'][:60]}\n"
        if len(matches) > 3:
            report += f"   ... 还有 {len(matches) - 3} 处\n"
        report += "\n"
    
    return report


def get_project_overview() -> str:
    """获取项目概览"""
    analyzer = get_analyzer()
    analyzer.index_project()
    
    py_files = list(Path('.').rglob("*.py"))
    py_files = [f for f in py_files if not any(part.startswith('.') or part in ['venv', '__pycache__'] 
                                               for part in f.parts)]
    
    total_lines = 0
    for f in py_files:
        try:
            total_lines += len(f.read_text(encoding='utf-8', errors='ignore').splitlines())
        except:
            pass
    
    func_count = sum(len(v) for v in analyzer.functions.values())
    class_count = sum(len(v) for v in analyzer.classes.values())
    
    report = f"""
📊 项目概览
{'=' * 60}
📁 Python 文件数: {len(py_files)}
📄 总代码行数: {total_lines}
🔧 函数数量: {func_count}
📦 类数量: {class_count}

📂 主要目录结构:
"""
    
    # 显示目录结构
    dirs = set()
    for f in py_files:
        dirs.add(f.parent)
    
    for d in sorted(dirs)[:15]:  # 最多15个目录
        depth = len(d.relative_to(Path('.')).parts) - 1
        indent = "  " * depth
        report += f"{indent}📂 {d.name}/\n"
    
    return report


def analyze_change_impact(file_path: str, change_description: str) -> str:
    """
    分析代码变更的影响范围
    
    Args:
        file_path: 要修改的文件路径
        change_description: 变更描述
    
    Returns:
        影响分析报告
    """
    analyzer = get_analyzer()
    
    if not Path(file_path).exists():
        return f"文件不存在: {file_path}"
    
    # 分析依赖关系
    deps = analyzer.analyze_dependencies(file_path)
    
    report = f"""
🔍 变更影响分析: {file_path}
{'=' * 60}
变更描述: {change_description}

📊 影响范围:
"""
    
    if deps['dependent_count'] == 0:
        report += "   ✅ 该文件未被其他文件引用，变更影响范围小\n"
    else:
        report += f"   ⚠️  该文件被 {deps['dependent_count']} 个文件引用:\n"
        for f in deps['imported_by'][:10]:
            report += f"      - {f}\n"
        if len(deps['imported_by']) > 10:
            report += f"      ... 还有 {len(deps['imported_by']) - 10} 个文件\n"
    
    # 尝试分析文件内容
    try:
        content = Path(file_path).read_text(encoding='utf-8')
        tree = ast.parse(content)
        
        funcs = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        
        if funcs:
            report += f"\n🔧 文件包含 {len(funcs)} 个函数:\n"
            for f in funcs[:5]:
                report += f"   - {f}()\n"
            if len(funcs) > 5:
                report += f"   ... 还有 {len(funcs) - 5} 个\n"
        
        if classes:
            report += f"\n📦 文件包含 {len(classes)} 个类:\n"
            for c in classes[:5]:
                report += f"   - {c}\n"
            if len(classes) > 5:
                report += f"   ... 还有 {len(classes) - 5} 个\n"
    
    except Exception as e:
        report += f"\n⚠️  文件解析失败: {e}\n"
    
    report += "\n💡 建议:\n"
    report += "   - 修改前请检查相关测试\n"
    if deps['dependent_count'] > 0:
        report += "   - 修改后需验证依赖该文件的模块是否正常工作\n"
    report += "   - 考虑是否需要更新相关文档\n"
    
    return report


def get_code_summary(file_path: str, max_lines: int = 50) -> str:
    """
    获取代码摘要
    
    Args:
        file_path: 文件路径
        max_lines: 最大行数
    
    Returns:
        代码摘要
    """
    path = Path(file_path)
    if not path.exists():
        return f"文件不存在: {file_path}"
    
    try:
        content = path.read_text(encoding='utf-8', errors='ignore')
        lines = content.splitlines()
        
        # 提取关键信息
        summary = []
        summary.append(f"📄 {file_path}")
        summary.append("=" * 60)
        summary.append("")
        
        # 导入语句
        imports = [l for l in lines if l.strip().startswith(('import ', 'from '))]
        if imports:
            summary.append("📥 导入:")
            for imp in imports[:10]:
                summary.append(f"   {imp.strip()}")
            summary.append("")
        
        # 类和函数定义
        definitions = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('class ') or stripped.startswith('def '):
                definitions.append((i, stripped))
        
        if definitions:
            summary.append("🔧 定义:")
            for line_no, definition in definitions[:15]:
                summary.append(f"   第 {line_no} 行: {definition}")
            summary.append("")
        
        # 代码开头
        summary.append("📝 代码开头:")
        code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
        for line in code_lines[:max_lines]:
            summary.append(line)
        
        return "\n".join(summary)
    
    except Exception as e:
        return f"读取文件失败: {e}"


# 工具注册表（用于动态加载）
TOOLS = {
    'analyze_code': analyze_code,
    'search_code': search_code,
    'get_project_overview': get_project_overview,
    'analyze_change_impact': analyze_change_impact,
    'get_code_summary': get_code_summary,
}
