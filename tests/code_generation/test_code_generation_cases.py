import pytest
import tempfile
import os
from src.tools.code_tools import generate_code

# 测试用例集合：覆盖代码生成的不同场景
class TestCodeGenerationCases:
 def test_simple_function_generation(self):
 """测试用例1：简单函数生成，验证基础代码生成能力"""
 prompt = "写一个Python函数，输入两个整数，返回它们的最大公约数"
 code = generate_code(prompt, language="python")
 # 验证生成的代码包含关键要素
 assert "def " in code
 assert "gcd" in code.lower() or "最大公约数" in code
 assert "return " in code

 def test_complex_class_generation(self):
 """测试用例2：复杂类生成，验证面向对象代码生成能力"""
 prompt = "写一个Python的用户管理类，支持用户添加、删除、查询、修改密码功能，包含完整的异常处理"
 code = generate_code(prompt, language="python")
 # 验证类结构和方法完整性
 assert "class " in code
 assert "def add_user" in code or "添加用户" in code
 assert "def delete_user" in code or "删除用户" in code
 assert "try:" in code or "except" in code

 def test_bug_fix_generation(self):
 """测试用例3：Bug修复代码生成，验证问题修复能力"""
 prompt = "修复下面这段Python代码的bug：
def divide(a, b):
 return a / b
# 问题：除数为0时会崩溃"
 code = generate_code(prompt, language="python")
 # 验证修复逻辑存在
 assert "if b == 0" in code or "ZeroDivisionError" in code

 def test_comment_generation(self):
 """测试用例4：代码注释生成，验证代码理解和注释编写能力"""
 prompt = "给下面这段Python代码添加详细的中文注释：
def quicksort(arr):
 if len(arr) <= 1:
 return arr
 pivot = arr[len(arr) // 2]
 left = [x for x in arr if x < pivot]
 middle = [x for x in arr if x == pivot]
 right = [x for x in arr if x > pivot]
 return quicksort(left) + middle + quicksort(right)"
 code = generate_code(prompt, language="python")
 # 验证注释存在
 assert '# ' in code
 assert "快速排序" in code or "quicksort" in code.lower()

 def test_shell_script_generation(self):
 """测试用例5：Shell脚本生成，验证多语言生成能力"""
 prompt = "写一个Shell脚本，批量压缩当前目录下所有的.log文件，压缩后删除原文件，压缩包命名为日志_日期.tar.gz"
 code = generate_code(prompt, language="shell")
 # 验证Shell脚本特征
 assert "#!/bin/bash" in code
 assert "tar" in code
 assert ".log" in code

 def test_frontend_code_generation(self):
 """测试用例6：前端代码生成，验证跨领域代码生成能力"""
 prompt = "写一个简单的HTML登录页面，包含用户名、密码输入框和登录按钮，带基础的CSS样式"
 code = generate_code(prompt, language="html")
 # 验证前端代码特征
 assert "<html>" in code or "<!DOCTYPE html>" in code
 assert "<input" in code
 assert "<button" in code
 assert "style=" in code or ".css" in code

 def test_empty_requirement_generation(self):
 """测试用例7：空需求场景处理，验证边界情况处理能力"""
 prompt = ""
 code = generate_code(prompt, language="python")
 # 空需求应该返回提示或者空，不报错
 assert isinstance(code, str)

 def test_performance_optimization_generation(self):
 """测试用例8：性能优化代码生成，验证代码优化能力"""
 prompt = "优化下面这段Python代码的性能，它要处理100万条数据：
result = []
for i in range(1000000):
 result.append(i * 2)"
 code = generate_code(prompt, language="python")
 # 验证优化逻辑，比如列表推导式、numpy等优化方案
 assert "[x * 2 for x in range" in code or "numpy" in code or "map" in code

 def test_test_case_generation(self):
 """测试用例9：测试用例生成，验证配套代码生成能力"""
 prompt = "给下面这个Python函数写pytest单元测试用例，覆盖正常和边界情况：
def add(a, b):
 return a + b"
 code = generate_code(prompt, language="python")
 # 验证测试用例特征
 assert "import pytest" in code
 assert "def test_add" in code
 assert "assert " in code

 def test_algorithm_implementation_generation(self):
 """测试用例10：算法实现生成，验证复杂逻辑代码生成能力"""
 prompt = "用Python实现二叉树的层序遍历算法，返回每一层的节点值列表"
 code = generate_code(prompt, language="python")
 # 验证算法关键特征
 assert "二叉树" in code or "TreeNode" in code
 assert "层序遍历" in code or "BFS" in code or "广度优先" in code
 assert "queue" in code or "deque" in code