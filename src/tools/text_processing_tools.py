"""
文本处理工具集 - 提供文件内容搜索、替换、统计功能
"""
import re
from pathlib import Path
from typing import List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def find_in_files(
    pattern: str,
    directory: str = ".",
    file_pattern: str = "*.py",
    use_regex: bool = False,
    case_sensitive: bool = False
) -> str:
    """
    在多个文件中搜索文本内容
    
    Args:
        pattern: 搜索模式（字符串或正则表达式）
        directory: 搜索目录
        file_pattern: 文件匹配模式，如 "*.py", "*.txt", "*"
        use_regex: 是否使用正则表达式
        case_sensitive: 是否区分大小写
    
    Returns:
        搜索结果
    """
    try:
        dir_path = Path(directory)
        if not dir_path.exists():
            return f"❌ 目录不存在: {directory}"
        
        # 编译正则表达式
        flags = 0 if case_sensitive else re.IGNORECASE
        if use_regex:
            try:
                regex = re.compile(pattern, flags)
            except re.error as e:
                return f"❌ 正则表达式错误: {str(e)}"
        else:
            regex = re.compile(re.escape(pattern), flags)
        
        results = []
        files_searched = 0
        files_matched = 0
        total_matches = 0
        
        for file_path in dir_path.rglob(file_pattern):
            if not file_path.is_file():
                continue
            
            # 跳过二进制文件
            if _is_binary(file_path):
                continue
            
            files_searched += 1
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                file_matches = []
                for line_num, line in enumerate(lines, 1):
                    if regex.search(line):
                        file_matches.append((line_num, line.strip()))
                
                if file_matches:
                    files_matched += 1
                    total_matches += len(file_matches)
                    
                    # 只显示前3个匹配
                    display_matches = file_matches[:3]
                    match_str = "\n".join([
                        f"      行 {num}: {content[:80]}{'...' if len(content) > 80 else ''}"
                        for num, content in display_matches
                    ])
                    
                    if len(file_matches) > 3:
                        match_str += f"\n      ... 还有 {len(file_matches) - 3} 处匹配"
                    
                    results.append(f"📄 {file_path.relative_to(dir_path)} ({len(file_matches)} 处):\n{match_str}")
                    
            except Exception as e:
                logger.debug(f"无法读取文件 {file_path}: {e}")
                continue
        
        if not results:
            return f"📭 未找到匹配 (搜索了 {files_searched} 个文件)"
        
        # 截断结果
        summary = f"🔍 搜索结果: '{pattern}'\n"
        summary += f"   搜索范围: {directory}/{file_pattern}\n"
        summary += f"   文件: {files_matched}/{files_searched}, 匹配数: {total_matches}\n"
        summary += "=" * 50 + "\n"
        
        # 最多显示10个文件的结果
        if len(results) > 10:
            summary += "\n\n".join(results[:10])
            summary += f"\n\n... 还有 {len(results) - 10} 个文件"
        else:
            summary += "\n\n".join(results)
        
        return summary
        
    except Exception as e:
        return f"❌ 搜索失败: {str(e)}"


def replace_in_files(
    old_text: str,
    new_text: str,
    directory: str = ".",
    file_pattern: str = "*.py",
    preview: bool = True,
    case_sensitive: bool = True
) -> str:
    """
    在多个文件中替换文本内容
    
    Args:
        old_text: 要替换的文本
        new_text: 新文本
        directory: 目标目录
        file_pattern: 文件匹配模式
        preview: 是否预览模式（不实际执行替换）
        case_sensitive: 是否区分大小写
    
    Returns:
        操作结果
    """
    try:
        dir_path = Path(directory)
        if not dir_path.exists():
            return f"❌ 目录不存在: {directory}"
        
        flags = 0 if case_sensitive else re.IGNORECASE
        old_pattern = re.compile(re.escape(old_text), flags)
        
        results = []
        files_to_modify = []
        total_replacements = 0
        
        for file_path in dir_path.rglob(file_pattern):
            if not file_path.is_file():
                continue
            
            if _is_binary(file_path):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                matches = list(old_pattern.finditer(content))
                
                if matches:
                    count = len(matches)
                    total_replacements += count
                    files_to_modify.append((file_path, count))
                    
                    # 显示前2个匹配位置
                    preview_lines = []
                    for i, match in enumerate(matches[:2]):
                        start = max(0, match.start() - 30)
                        end = min(len(content), match.end() + 30)
                        context = content[start:end]
                        context = context.replace('\n', ' ')
                        preview_lines.append(f"      匹配 {i+1}: ...{context}...")
                    
                    results.append(
                        f"📄 {file_path.relative_to(dir_path)} ({count} 处)\n" +
                        "\n".join(preview_lines)
                    )
                    
            except Exception as e:
                continue
        
        if not files_to_modify:
            return f"📭 未找到匹配文本: '{old_text}'"
        
        # 构建报告
        mode = "🔍 预览模式" if preview else "✅ 执行替换"
        report = f"{mode}\n"
        report += f"   替换: '{old_text}' → '{new_text}'\n"
        report += f"   范围: {directory}/{file_pattern}\n"
        report += f"   影响: {len(files_to_modify)} 个文件, {total_replacements} 处\n"
        report += "=" * 50 + "\n"
        report += "\n\n".join(results[:10])
        
        if len(results) > 10:
            report += f"\n\n... 还有 {len(results) - 10} 个文件"
        
        if preview:
            report += "\n\n💡 使用 preview=False 执行实际替换"
            return report
        
        # 执行替换
        success_count = 0
        for file_path, _ in files_to_modify:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                new_content = old_pattern.sub(new_text, content)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                success_count += 1
            except Exception as e:
                report += f"\n❌ 替换失败 {file_path}: {e}"
        
        report += f"\n\n✅ 成功替换 {success_count}/{len(files_to_modify)} 个文件"
        return report
        
    except Exception as e:
        return f"❌ 替换失败: {str(e)}"


def count_lines(directory: str = ".", file_pattern: str = "*.py") -> str:
    """
    统计代码行数
    
    Args:
        directory: 目标目录
        file_pattern: 文件匹配模式
    
    Returns:
        统计结果
    """
    try:
        dir_path = Path(directory)
        if not dir_path.exists():
            return f"❌ 目录不存在: {directory}"
        
        total_lines = 0
        code_lines = 0
        comment_lines = 0
        blank_lines = 0
        file_stats = []
        
        for file_path in dir_path.rglob(file_pattern):
            if not file_path.is_file():
                continue
            
            if _is_binary(file_path):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                file_total = len(lines)
                file_code = 0
                file_comment = 0
                file_blank = 0
                
                for line in lines:
                    stripped = line.strip()
                    if not stripped:
                        file_blank += 1
                    elif stripped.startswith('#') or stripped.startswith('//') or stripped.startswith('/*'):
                        file_comment += 1
                    else:
                        file_code += 1
                
                total_lines += file_total
                code_lines += file_code
                comment_lines += file_comment
                blank_lines += file_blank
                
                file_stats.append((file_path.relative_to(dir_path), file_total, file_code))
                
            except Exception as e:
                continue
        
        # 按行数排序
        file_stats.sort(key=lambda x: x[1], reverse=True)
        
        report = f"""
📊 代码统计: {directory}/{file_pattern}
═══════════════════════════════════════
📁 总文件数: {len(file_stats)}
📄 总行数: {total_lines:,}
   💻 代码行: {code_lines:,} ({code_lines/total_lines*100:.1f}%)
   💬 注释行: {comment_lines:,} ({comment_lines/total_lines*100:.1f}%)
   ⬜ 空行: {blank_lines:,} ({blank_lines/total_lines*100:.1f}%)

📈 文件排行榜 (Top 10):
"""
        for i, (path, total, code) in enumerate(file_stats[:10], 1):
            report += f"   {i:2}. {str(path):50} {total:6} 行\n"
        
        return report
        
    except Exception as e:
        return f"❌ 统计失败: {str(e)}"


def extract_strings(file_path: str, min_length: int = 5) -> str:
    """
    从代码文件中提取字符串字面量
    
    Args:
        file_path: 文件路径
        min_length: 最小字符串长度
    
    Returns:
        提取的字符串列表
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return f"❌ 文件不存在: {file_path}"
        
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 匹配单引号和双引号字符串
        strings = []
        
        # 双引号字符串
        for match in re.finditer(r'"([^"\n]{%d,})"' % min_length, content):
            strings.append((match.start(), match.group(1), '"'))
        
        # 单引号字符串
        for match in re.finditer(r"'([^'\n]{%d,})'" % min_length, content):
            strings.append((match.start(), match.group(1), "'"))
        
        # 去重并排序
        seen = set()
        unique_strings = []
        for pos, s, quote in sorted(strings, key=lambda x: x[0]):
            if s not in seen:
                seen.add(s)
                unique_strings.append((pos, s, quote))
        
        if not unique_strings:
            return f"📭 未找到长度 ≥{min_length} 的字符串"
        
        result = f"📝 提取的字符串 ({len(unique_strings)} 个):\n"
        result += "=" * 50 + "\n"
        
        for pos, s, quote in unique_strings[:50]:  # 最多显示50个
            display = s[:60] + "..." if len(s) > 60 else s
            result += f"  行 {content[:pos].count(chr(10)) + 1}: {quote}{display}{quote}\n"
        
        if len(unique_strings) > 50:
            result += f"\n... 还有 {len(unique_strings) - 50} 个字符串"
        
        return result
        
    except Exception as e:
        return f"❌ 提取失败: {str(e)}"


def _is_binary(file_path: Path) -> bool:
    """检测文件是否为二进制文件"""
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            return b'\x00' in chunk
    except:
        return True
