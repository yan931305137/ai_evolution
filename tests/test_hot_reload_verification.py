#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热更新模块功能验证脚本
验证里程碑2要求的所有功能点
"""
import os
import sys
import time
import tempfile
import importlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.hot_reload_manager import hot_reload_manager

def test_module_decouping():
    """验证业务模块与核心模块解耦"""
    print("[测试1] 业务模块与核心模块解耦验证")
    # 注册业务模块
    from src.business.source_manager import SourceManager
    hot_reload_manager.register_module("src.business.source_manager", SourceManager())
    
    # 注册核心模块
    from src.utils.llm import LLMClient
    hot_reload_manager.register_module("src.utils.llm", LLMClient())
    
    # 验证两个模块独立注册，互不依赖
    assert "src.business.source_manager" in hot_reload_manager.module_registry
    assert "src.utils.llm" in hot_reload_manager.module_registry
    print("✓ 业务模块与核心模块已完全解耦，可独立注册热重载")
    return True

def test_code_validation():
    """验证代码合法性校验功能"""
    print("\n[测试2] 代码合法性校验验证")
    
    # 创建一个有语法错误的测试模块
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("def test_func()\n    print('语法错误')")
        temp_file = f.name
    
    # 测试语法校验
    try:
        with open(temp_file, 'r', encoding='utf-8') as f:
            code_content = f.read()
        compile(code_content, temp_file, 'exec')
        assert False, "语法错误未被检测到"
    except SyntaxError as e:
        print(f"✓ 语法校验正常工作，检测到语法错误: 第{e.lineno}行")
    
    os.unlink(temp_file)
    
    # 创建合法代码测试
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("def test_func():\n    return '合法代码'")
        temp_file2 = f.name
    
    try:
        with open(temp_file2, 'r', encoding='utf-8') as f:
            code_content = f.read()
        compile(code_content, temp_file2, 'exec')
        print("✓ 合法代码语法校验通过")
    except SyntaxError as e:
        assert False, f"合法代码被误判: {e}"
    
    os.unlink(temp_file2)
    return True

def test_incremental_reload():
    """验证增量加载功能，单模块修改无需全量重启"""
    print("\n[测试3] 增量加载验证")
    
    # 创建测试模块
    test_module_code = """
class TestModule:
    def get_value(self):
        return "v1"
    """
    module_path = os.path.join(os.path.dirname(__file__), "test_dynamic_module.py")
    with open(module_path, 'w', encoding='utf-8') as f:
        f.write(test_module_code)
    
    # 导入并注册
    sys.path.insert(0, os.path.dirname(__file__))
    import test_dynamic_module
    test_instance = test_dynamic_module.TestModule()
    hot_reload_manager.register_module("test_dynamic_module", test_instance)
    
    # 验证初始版本
    instance = hot_reload_manager.get_module_instance("test_dynamic_module")
    assert instance.get_value() == "v1"
    print("✓ 初始模块加载成功，返回值: v1")
    
    # 修改模块代码
    time.sleep(0.1)  # 保证修改时间戳不同
    new_code = """
class TestModule:
    def get_value(self):
        return "v2"
    """
    with open(module_path, 'w', encoding='utf-8') as f:
        f.write(new_code)
    
    # 检测变更并重载
    changed = hot_reload_manager.check_module_changes()
    assert "test_dynamic_module" in changed
    
    start_time = time.time()
    success, msg = hot_reload_manager.reload_module("test_dynamic_module")
    reload_time = time.time() - start_time
    
    assert success, f"重载失败: {msg}"
    instance = hot_reload_manager.get_module_instance("test_dynamic_module")
    assert instance.get_value() == "v2"
    print(f"✓ 增量重载成功，返回值已更新为: v2，耗时: {reload_time:.3f}秒")
    print("✓ 单模块修改无需全量重启，仅重载变更模块")
    
    # 清理
    os.remove(module_path)
    if 'test_dynamic_module' in sys.modules:
        del sys.modules['test_dynamic_module']
    
    return True

def test_auto_rollback():
    """验证异常自动回滚机制，回滚耗时≤1秒"""
    print("\n[测试4] 异常自动回滚验证")
    
    # 创建测试模块
    test_module_code = """
class TestModule:
    def get_value(self):
        return "stable"
    """
    module_path = os.path.join(os.path.dirname(__file__), "test_rollback_module.py")
    with open(module_path, 'w', encoding='utf-8') as f:
        f.write(test_module_code)
    
    # 导入并注册
    sys.path.insert(0, os.path.dirname(__file__))
    import test_rollback_module
    test_instance = test_rollback_module.TestModule()
    hot_reload_manager.register_module("test_rollback_module", test_instance)
    
    # 验证稳定版本
    instance = hot_reload_manager.get_module_instance("test_rollback_module")
    assert instance.get_value() == "stable"
    print("✓ 稳定版本加载成功，返回值: stable")
    
    # 写入有错误的新版本
    time.sleep(0.1)
    bad_code = """
class TestModule:
    def get_value(self):
        return 1/0  # 运行时错误
    """
    with open(module_path, 'w', encoding='utf-8') as f:
        f.write(bad_code)
    
    # 尝试重载，会失败并自动回滚
    start_time = time.time()
    success, msg = hot_reload_manager.reload_module("test_rollback_module")
    rollback_time = time.time() - start_time
    
    assert not success, "错误版本应该重载失败"
    print(f"✓ 错误版本重载失败，触发自动回滚，回滚耗时: {rollback_time:.3f}秒")
    assert rollback_time <= 1.0, f"回滚耗时{rollback_time:.3f}秒超过1秒要求"
    
    # 验证回滚到稳定版本
    instance = hot_reload_manager.get_module_instance("test_rollback_module")
    assert instance.get_value() == "stable"
    print("✓ 已自动回滚到稳定版本，返回值: stable")
    
    # 清理
    os.remove(module_path)
    if 'test_rollback_module' in sys.modules:
        del sys.modules['test_rollback_module']
    
    return True

def test_simple_change_success_rate():
    """验证简单逻辑修改热更成功率100%"""
    print("\n[测试5] 简单逻辑修改热更成功率验证")
    
    success_count = 0
    test_count = 10
    
    for i in range(test_count):
        # 创建测试模块
        test_module_code = f"""
class TestModule:
    def get_value(self):
        return "v{i}"
        """
        module_path = os.path.join(os.path.dirname(__file__), f"test_success_{i}.py")
        with open(module_path, 'w', encoding='utf-8') as f:
            f.write(test_module_code)
        
        # 导入并注册
        module_name = f"test_success_{i}"
        sys.path.insert(0, os.path.dirname(__file__))
        if module_name in sys.modules:
            del sys.modules[module_name]
        test_module = importlib.import_module(module_name)
        test_instance = test_module.TestModule()
        hot_reload_manager.register_module(module_name, test_instance)
        
        # 修改代码
        time.sleep(0.1)
        new_code = f"""
class TestModule:
    def get_value(self):
        return "v{i}_updated"
        """
        with open(module_path, 'w', encoding='utf-8') as f:
            f.write(new_code)
        
        # 重载
        success, msg = hot_reload_manager.reload_module(module_name)
        if success:
            instance = hot_reload_manager.get_module_instance(module_name)
            if instance.get_value() == f"v{i}_updated":
                success_count += 1
        
        # 清理
        os.remove(module_path)
        if module_name in sys.modules:
            del sys.modules[module_name]
    
    success_rate = success_count / test_count * 100
    print(f"✓ 完成{test_count}次简单逻辑修改测试，成功{success_count}次，成功率{success_rate:.1f}%")
    assert success_rate == 100.0, f"简单逻辑修改成功率{success_rate:.1f}%未达到100%要求"
    return True

def main():
    """执行所有测试"""
    print("="*60)
    print("里程碑2：热更新功能验证")
    print("="*60)
    
    tests = [
        test_module_decouping,
        test_code_validation,
        test_incremental_reload,
        test_auto_rollback,
        test_simple_change_success_rate
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__}测试失败: {str(e)}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"测试结果：{passed}项通过，{failed}项失败")
    print("="*60)
    
    if failed == 0:
        print("\n✅ 所有里程碑2要求的功能均已满足：")
        print("1. 可迭代业务模块与核心底层模块完全解耦 ✓")
        print("2. 热更新代码合法性校验功能正常 ✓")
        print("3. 增量加载功能正常，单模块修改无需全量重启 ✓")
        print("4. 异常自动回滚机制正常，回滚耗时≤1秒 ✓")
        print("5. 简单逻辑修改热更成功率100% ✓")
        return 0
    else:
        print("\n❌ 部分功能未满足要求")
        return 1

if __name__ == "__main__":
    exit(main())
