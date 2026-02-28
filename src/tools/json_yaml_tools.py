"""
JSON/YAML配置操作工具集 - 提供配置文件的读取、写入、更新功能
"""
import json
from pathlib import Path
from typing import Any, Dict, Union, Optional
import logging

logger = logging.getLogger(__name__)

# 尝试导入yaml
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


def read_json(file_path: str) -> str:
    """
    读取JSON文件内容
    
    Args:
        file_path: JSON文件路径
    
    Returns:
        格式化的JSON内容字符串
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return f"❌ 文件不存在: {file_path}"
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 格式化输出
        formatted = json.dumps(data, ensure_ascii=False, indent=2)
        
        # 截断过长的输出
        lines = formatted.split('\n')
        if len(lines) > 100:
            formatted = '\n'.join(lines[:100]) + f"\n\n... (共 {len(lines)} 行，已截断)"
        
        return f"📄 JSON内容: {file_path}\n```json\n{formatted}\n```"
        
    except json.JSONDecodeError as e:
        return f"❌ JSON解析错误: {file_path}\n错误: {str(e)}"
    except Exception as e:
        return f"❌ 读取JSON失败: {file_path}\n错误: {str(e)}"


def write_json(file_path: str, data: Union[str, Dict], overwrite: bool = False) -> str:
    """
    写入JSON文件
    
    Args:
        file_path: 目标文件路径
        data: JSON数据（字符串或字典）
        overwrite: 是否覆盖已存在的文件
    
    Returns:
        操作结果
    """
    try:
        path = Path(file_path)
        
        if path.exists() and not overwrite:
            return f"❌ 文件已存在，使用 overwrite=True 覆盖: {file_path}"
        
        # 解析输入数据
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError as e:
                return f"❌ 输入数据不是有效的JSON: {str(e)}"
        
        # 确保目录存在
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return f"✅ JSON文件写入成功: {file_path}"
        
    except Exception as e:
        return f"❌ 写入JSON失败: {file_path}\n错误: {str(e)}"


def update_json(file_path: str, key_path: str, value: Any, create_if_missing: bool = False) -> str:
    """
    更新JSON文件中的特定值
    
    Args:
        file_path: JSON文件路径
        key_path: 键路径，使用点号分隔，如 "database.host" 或 "users.0.name"
        value: 新值（字符串形式，会被解析为JSON）
        create_if_missing: 如果键不存在是否创建
    
    Returns:
        操作结果
    """
    try:
        path = Path(file_path)
        
        if not path.exists():
            if create_if_missing:
                data = {}
            else:
                return f"❌ 文件不存在: {file_path}"
        else:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        # 解析值
        try:
            parsed_value = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            # 如果解析失败，当作字符串处理
            parsed_value = value
        
        # 导航到目标位置
        keys = key_path.split('.')
        current = data
        
        for i, key in enumerate(keys[:-1]):
            if key.isdigit():
                key = int(key)
            
            if isinstance(current, dict):
                if key not in current:
                    if create_if_missing:
                        # 判断下一个key是否是数字，决定创建dict还是list
                        next_key = keys[i + 1]
                        current[key] = [] if next_key.isdigit() else {}
                    else:
                        return f"❌ 键不存在: {'.'.join(keys[:i+1])}"
                current = current[key]
            elif isinstance(current, list):
                if isinstance(key, int):
                    while len(current) <= key:
                        if not create_if_missing:
                            return f"❌ 数组索引越界: {key}"
                        current.append({})
                    current = current[key]
                else:
                    return f"❌ 无法访问列表的字符串键: {key}"
            else:
                return f"❌ 无法继续深入，当前不是容器类型: {'.'.join(keys[:i+1])}"
        
        # 设置最终值
        final_key = keys[-1]
        if final_key.isdigit():
            final_key = int(final_key)
        
        if isinstance(current, dict):
            old_value = current.get(final_key, "<不存在>")
            current[final_key] = parsed_value
        elif isinstance(current, list) and isinstance(final_key, int):
            while len(current) <= final_key:
                current.append(None)
            old_value = current[final_key] if final_key < len(current) else "<不存在>"
            current[final_key] = parsed_value
        else:
            return f"❌ 无法设置值，目标不是容器类型"
        
        # 写回文件
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return f"✅ JSON更新成功: {file_path}\n   路径: {key_path}\n   旧值: {old_value}\n   新值: {parsed_value}"
        
    except Exception as e:
        return f"❌ 更新JSON失败: {file_path}\n错误: {str(e)}"


def read_yaml(file_path: str) -> str:
    """
    读取YAML文件内容
    
    Args:
        file_path: YAML文件路径
    
    Returns:
        格式化的YAML内容字符串
    """
    if not YAML_AVAILABLE:
        return "❌ YAML模块未安装，请安装 PyYAML: pip install pyyaml"
    
    try:
        path = Path(file_path)
        if not path.exists():
            return f"❌ 文件不存在: {file_path}"
        
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # 转换为JSON格式显示（更易读）
        formatted = json.dumps(data, ensure_ascii=False, indent=2)
        
        # 截断过长的输出
        lines = formatted.split('\n')
        if len(lines) > 100:
            formatted = '\n'.join(lines[:100]) + f"\n\n... (共 {len(lines)} 行，已截断)"
        
        return f"📄 YAML内容: {file_path}\n```yaml\n{formatted}\n```"
        
    except Exception as e:
        return f"❌ 读取YAML失败: {file_path}\n错误: {str(e)}"


def write_yaml(file_path: str, data: Union[str, Dict], overwrite: bool = False) -> str:
    """
    写入YAML文件
    
    Args:
        file_path: 目标文件路径
        data: YAML数据（字符串或字典）
        overwrite: 是否覆盖已存在的文件
    
    Returns:
        操作结果
    """
    if not YAML_AVAILABLE:
        return "❌ YAML模块未安装，请安装 PyYAML: pip install pyyaml"
    
    try:
        path = Path(file_path)
        
        if path.exists() and not overwrite:
            return f"❌ 文件已存在，使用 overwrite=True 覆盖: {file_path}"
        
        # 解析输入数据
        if isinstance(data, str):
            try:
                # 尝试解析为JSON
                data = json.loads(data)
            except json.JSONDecodeError:
                # 尝试解析为YAML
                try:
                    data = yaml.safe_load(data)
                except:
                    pass  # 保持为字符串
        
        # 确保目录存在
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        return f"✅ YAML文件写入成功: {file_path}"
        
    except Exception as e:
        return f"❌ 写入YAML失败: {file_path}\n错误: {str(e)}"


def validate_json(file_path: str) -> str:
    """
    验证JSON文件格式是否正确
    
    Args:
        file_path: JSON文件路径
    
    Returns:
        验证结果
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return f"❌ 文件不存在: {file_path}"
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            data = json.loads(content)
            # 统计信息
            if isinstance(data, dict):
                count = len(data)
                return f"✅ JSON格式正确: {file_path}\n   根类型: 对象 (包含 {count} 个键)"
            elif isinstance(data, list):
                count = len(data)
                return f"✅ JSON格式正确: {file_path}\n   根类型: 数组 (包含 {count} 个元素)"
            else:
                return f"✅ JSON格式正确: {file_path}\n   根类型: {type(data).__name__}"
        except json.JSONDecodeError as e:
            return f"❌ JSON格式错误: {file_path}\n   错误: {str(e)}"
        
    except Exception as e:
        return f"❌ 验证失败: {file_path}\n错误: {str(e)}"
