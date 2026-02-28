"""
代码数据工厂

生成各种测试用的代码片段
"""

import random
from typing import List, Dict, Any, Optional


class CodeFactory:
    """代码数据工厂"""
    
    # 代码模板库
    TEMPLATES = {
        "python": {
            "function": """
def {name}({params}):
    \"\"\"
    {docstring}
    \"\"\"
    {body}
    return {return_value}
""",
            "class": """
class {name}:
    \"\"\"
    {docstring}
    \"\"\"
    
    def __init__(self{init_params}):
        {init_body}
    
    {methods}
""",
            "method": """
    def {name}(self{params}):
        {body}
        return {return_value}
"""
        },
        "javascript": {
            "function": """
function {name}({params}) {{
    {body}
    return {return_value};
}}
""",
            "class": """
class {name} {{
    constructor({init_params}) {{
        {init_body}
    }}
    
    {methods}
}}
"""
        }
    }
    
    @classmethod
    def create_python_function(
        cls,
        name: Optional[str] = None,
        params: Optional[List[str]] = None,
        return_value: str = "None",
        docstring: Optional[str] = None,
        complexity: str = "simple"
    ) -> str:
        """
        创建 Python 函数
        
        Args:
            name: 函数名
            params: 参数列表
            return_value: 返回值
            docstring: 文档字符串
            complexity: 复杂度 (simple/medium/complex)
        
        Returns:
            函数代码字符串
        """
        name = name or f"func_{random.randint(100, 999)}"
        params = params or ["arg1", "arg2"]
        docstring = docstring or f"{name} 函数"
        
        if complexity == "simple":
            body = f"    result = {params[0]} + {params[1]} if len(params) > 1 else {params[0]}"
        elif complexity == "medium":
            body = f"""    if not {params[0]}:
        raise ValueError("参数不能为空")
    result = process({params[0]})
    return result"""
        else:  # complex
            body = f"""    try:
        validated = validate_input({params[0]})
        processed = process_data(validated)
        result = format_output(processed)
    except ValidationError as e:
        logger.error(f"验证失败: {{e}}")
        raise
    except Exception as e:
        logger.exception("处理异常")
        result = default_value"""
        
        return cls.TEMPLATES["python"]["function"].format(
            name=name,
            params=", ".join(params),
            docstring=docstring,
            body=body,
            return_value=return_value
        )
    
    @classmethod
    def create_python_class(
        cls,
        name: Optional[str] = None,
        methods_count: int = 3,
        attributes: Optional[List[str]] = None
    ) -> str:
        """
        创建 Python 类
        
        Args:
            name: 类名
            methods_count: 方法数量
            attributes: 属性列表
        
        Returns:
            类代码字符串
        """
        name = name or f"Class{random.randint(100, 999)}"
        attributes = attributes or ["name", "value", "status"]
        
        init_params = "" if not attributes else ", " + ", ".join(attributes)
        init_body = "\n        ".join([f"self.{attr} = {attr}" for attr in attributes])
        
        methods = []
        for i in range(methods_count):
            method = cls.TEMPLATES["python"]["method"].format(
                name=f"method_{i+1}",
                params="",
                body=f"# 方法 {i+1} 实现",
                return_value="None"
            )
            methods.append(method)
        
        return cls.TEMPLATES["python"]["class"].format(
            name=name,
            docstring=f"{name} 类",
            init_params=init_params,
            init_body=init_body,
            methods="\n".join(methods)
        )
    
    @classmethod
    def create_test_function(
        cls,
        target_func: str = "target_function",
        test_cases: Optional[List[Dict]] = None
    ) -> str:
        """
        创建测试函数
        
        Args:
            target_func: 被测试的函数名
            test_cases: 测试用例列表
        
        Returns:
            pytest 测试代码
        """
        if test_cases is None:
            test_cases = [
                {"input": "(1, 2)", "expected": "3", "name": "正常情况"},
                {"input": "(0, 0)", "expected": "0", "name": "边界情况"},
                {"input": "(-1, 1)", "expected": "0", "name": "负数情况"},
            ]
        
        test_code = f"""import pytest
from src.module import {target_func}


class Test{target_func.title().replace('_', '')}:
    \"\"\"
    {target_func} 的测试类
    \"\"\"
"""
        
        for i, case in enumerate(test_cases):
            test_code += f"""
    def test_{case.get('name', f'case_{i}').replace(' ', '_')}(self):
        \"\"\"
        测试: {case.get('name', f'用例 {i}')}
        \"\"\"
        result = {target_func}{case['input']}
        assert result == {case['expected']}
"""
        
        return test_code
    
    @classmethod
    def create_buggy_code(
        cls,
        bug_type: str = "runtime_error"
    ) -> str:
        """
        创建带有 Bug 的代码（用于测试修复功能）
        
        Args:
            bug_type: 错误类型
        
        Returns:
            有 Bug 的代码
        """
        buggy_codes = {
            "runtime_error": """
def divide(a, b):
    return a / b  # Bug: 未处理 b=0 的情况
""",
            "logic_error": """
def calculate_average(numbers):
    total = sum(numbers)
    return total  # Bug: 忘记除以 len(numbers)
""",
            "name_error": """
def process():
    result = undefined_variable  # Bug: 未定义变量
    return result
""",
            "type_error": """
def concat(a, b):
    return a + b  # Bug: 如果 a 和 b 类型不匹配会出错
""",
            "resource_leak": """
def read_file(path):
    f = open(path, 'r')  # Bug: 未关闭文件
    return f.read()
"""
        }
        
        return buggy_codes.get(bug_type, buggy_codes["runtime_error"])
    
    @classmethod
    def create_optimized_code(
        cls,
        optimization: str = "list_comprehension"
    ) -> str:
        """
        创建优化后的代码示例
        
        Args:
            optimization: 优化类型
        
        Returns:
            优化后的代码
        """
        optimizations = {
            "list_comprehension": """
# 优化前:
result = []
for i in range(1000):
    if i % 2 == 0:
        result.append(i * 2)

# 优化后:
result = [i * 2 for i in range(1000) if i % 2 == 0]
""",
            "generator": """
# 优化前:
def get_large_list():
    return [x**2 for x in range(1000000)]

# 优化后:
def get_large_generator():
    for x in range(1000000):
        yield x**2
""",
            "set_lookup": """
# 优化前:
if item in large_list:  # O(n)

# 优化后:
large_set = set(large_list)
if item in large_set:  # O(1)
"""
        }
        
        return optimizations.get(optimization, optimizations["list_comprehension"])
    
    @classmethod
    def create_html_page(
        cls,
        title: str = "Test Page",
        elements: Optional[List[str]] = None
    ) -> str:
        """
        创建 HTML 页面
        
        Args:
            title: 页面标题
            elements: HTML 元素列表
        
        Returns:
            HTML 代码
        """
        elements = elements or ["<h1>标题</h1>", "<p>段落内容</p>", "<button>按钮</button>"]
        
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
    </style>
</head>
<body>
    {"\n    ".join(elements)}
    <script>
        console.log('Page loaded');
    </script>
</body>
</html>"""
    
    @classmethod
    def create_shell_script(
        cls,
        name: str = "script",
        operations: Optional[List[str]] = None
    ) -> str:
        """
        创建 Shell 脚本
        
        Args:
            name: 脚本名称
            operations: 操作列表
        
        Returns:
            Shell 脚本代码
        """
        operations = operations or [
            'echo "Starting script..."',
            'mkdir -p output',
            'echo "Done"'
        ]
        
        return f"""#!/bin/bash
# {name}.sh
# Generated test script

set -e  # 遇到错误立即退出

echo "================================"
echo "Running {name}"
echo "================================"

{"\n\n".join(operations)}

echo "================================"
echo "Script completed successfully!"
echo "================================"
"""
