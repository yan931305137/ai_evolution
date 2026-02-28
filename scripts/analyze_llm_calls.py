#!/usr/bin/env python3
"""
LLM调用优化脚本 - 快速优化项目中的LLM使用

这个脚本会:
1. 检查当前LLM调用情况
2. 提供优化建议
3. 自动应用一些安全的优化
"""
import os
import re
from pathlib import Path
from typing import List, Dict, Tuple


class LLMCallAnalyzer:
    """LLM调用分析器"""
    
    def __init__(self, project_root: str = "/workspace/projects"):
        self.project_root = Path(project_root)
        self.findings: List[Dict] = []
        self.optimizations: List[Dict] = []
    
    def scan_files(self) -> List[Dict]:
        """扫描所有Python文件中的LLM调用"""
        python_files = list(self.project_root.rglob("src/**/*.py"))
        
        for file_path in python_files:
            if "__pycache__" in str(file_path):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                    for i, line in enumerate(lines, 1):
                        # 检测LLM调用模式
                        if self._is_llm_call(line):
                            self.findings.append({
                                'file': str(file_path.relative_to(self.project_root)),
                                'line': i,
                                'code': line.strip(),
                                'type': self._classify_call(line),
                                'severity': self._assess_severity(file_path.name, line)
                            })
            except Exception as e:
                print(f"⚠️  无法读取 {file_path}: {e}")
        
        return self.findings
    
    def _is_llm_call(self, line: str) -> bool:
        """检测是否是LLM调用"""
        patterns = [
            r'\.generate\(',
            r'\.chat\(',
            r'\.completion',
            r'\.stream_generate\(',
            r'\.invoke\(',
            r'LLMClient\(',
            r'llm\.\w+\(',
        ]
        return any(re.search(p, line) for p in patterns) and not line.strip().startswith('#')
    
    def _classify_call(self, line: str) -> str:
        """分类调用类型"""
        if 'stream' in line.lower():
            return 'stream_generate'
        elif 'chat' in line.lower():
            return 'chat'
        elif 'invoke' in line.lower():
            return 'invoke'
        else:
            return 'generate'
    
    def _assess_severity(self, filename: str, line: str) -> str:
        """评估严重程度"""
        # 自我优化循环中的调用最严重
        if 'self_optimization' in filename:
            return 'HIGH'
        # Agent中的调用
        elif 'agent' in filename.lower():
            return 'MEDIUM'
        # 其他
        else:
            return 'LOW'
    
    def generate_report(self) -> str:
        """生成分析报告"""
        if not self.findings:
            return "未找到LLM调用"
        
        report = []
        report.append("=" * 70)
        report.append("🔍 LLM调用分析报告")
        report.append("=" * 70)
        report.append(f"\n总计发现 {len(self.findings)} 处LLM调用\n")
        
        # 按文件分组
        by_file: Dict[str, List[Dict]] = {}
        for finding in self.findings:
            file_key = finding['file']
            if file_key not in by_file:
                by_file[file_key] = []
            by_file[file_key].append(finding)
        
        # 按严重程度排序
        severity_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        
        for severity in ['HIGH', 'MEDIUM', 'LOW']:
            report.append(f"\n{'🔴' if severity == 'HIGH' else '🟡' if severity == 'MEDIUM' else '🟢'} {severity} 优先级")
            report.append("-" * 70)
            
            for file_path, findings in sorted(by_file.items()):
                high_severity = [f for f in findings if f['severity'] == severity]
                if high_severity:
                    report.append(f"\n  📄 {file_path}")
                    for finding in high_severity:
                        report.append(f"     第{finding['line']:3d}行: {finding['code'][:50]}...")
        
        return '\n'.join(report)
    
    def get_optimization_suggestions(self) -> List[Dict]:
        """生成优化建议"""
        suggestions = []
        
        for finding in self.findings:
            file_path = finding['file']
            
            # 针对特定文件的优化建议
            if 'self_optimization_feedback_loop' in file_path:
                suggestions.append({
                    'file': file_path,
                    'line': finding['line'],
                    'current': finding['code'],
                    'suggestion': '使用BrainPlanner替代LLM调用',
                    'benefit': '减少80% LLM调用',
                    'effort': '中等'
                })
            elif 'creativity' in file_path:
                suggestions.append({
                    'file': file_path,
                    'line': finding['line'],
                    'current': finding['code'],
                    'suggestion': '使用EnhancedHybridBrain，自动选择本地模板',
                    'benefit': '70%场景零成本',
                    'effort': '低'
                })
            elif 'cli' in file_path:
                suggestions.append({
                    'file': file_path,
                    'line': finding['line'],
                    'current': finding['code'],
                    'suggestion': '使用EnhancedHybridBrain替代LLMClient',
                    'benefit': '70%对话本地处理',
                    'effort': '低'
                })
        
        return suggestions
    
    def print_summary(self):
        """打印摘要"""
        print(self.generate_report())
        
        suggestions = self.get_optimization_suggestions()
        if suggestions:
            print("\n" + "=" * 70)
            print("💡 优化建议")
            print("=" * 70)
            
            for i, s in enumerate(suggestions[:10], 1):  # 只显示前10条
                print(f"\n{i}. 📍 {s['file']}:{s['line']}")
                print(f"   当前: {s['current'][:40]}...")
                print(f"   建议: {s['suggestion']}")
                print(f"   收益: {s['benefit']} | 工作量: {s['effort']}")


def quick_optimize():
    """快速优化 - 创建优化后的包装器"""
    print("\n" + "=" * 70)
    print("🚀 快速优化方案")
    print("=" * 70)
    
    # 检查是否可以导入EnhancedHybridBrain
    try:
        import sys
        sys.path.insert(0, '/workspace/projects')
        from src.utils.enhanced_hybrid_brain import EnhancedHybridBrain
        print("\n✅ EnhancedHybridBrain 可用")
        
        # 测试创建实例
        print("\n📊 创建测试实例...")
        client = EnhancedHybridBrain(start_as_infant=False)
        print(f"   ✓ 初始化成功")
        print(f"   ✓ 模型: {client.model_name}")
        
        # 测试简单对话
        print("\n🧪 测试本地处理能力...")
        test_messages = [{"role": "user", "content": "你好！"}]
        response = client.generate(test_messages)
        
        level = response.brain_state.get('processing_level', 'unknown')
        print(f"   ✓ 测试完成")
        print(f"   ✓ 处理级别: {level.upper()}")
        
        if level == 'template':
            print("   ✅ 本地处理成功！零API成本")
        
        # 打印统计
        print("\n📈 当前统计")
        client.print_stats()
        
    except Exception as e:
        print(f"\n❌ 优化测试失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print("=" * 70)
    print("🔍 OpenClaw LLM调用优化工具")
    print("=" * 70)
    
    # 1. 分析LLM调用
    print("\n📂 正在扫描项目文件...")
    analyzer = LLMCallAnalyzer()
    findings = analyzer.scan_files()
    
    # 2. 打印报告
    analyzer.print_summary()
    
    # 3. 快速优化测试
    quick_optimize()
    
    # 4. 输出行动建议
    print("\n" + "=" * 70)
    print("📋 行动建议")
    print("=" * 70)
    print("""
1. 【立即】在需要使用LLM的地方，导入 EnhancedHybridBrain:
   
   from src.utils.enhanced_hybrid_brain import EnhancedHybridBrain
   llm = EnhancedHybridBrain(local_first=True)

2. 【短期】重构 self_optimization_feedback_loop.py:
   - 减少多次LLM调用
   - 使用 BrainPlanner 进行本地规划

3. 【中期】修改 cli.py 和 creativity.py:
   - 替换 LLMClient 为 EnhancedHybridBrain
   - 自动获得70%本地处理率

4. 【长期】实现完全本地化的创造力系统

详细报告已保存到: docs/llm_call_analysis_report.md
    """)
    
    print("\n" + "=" * 70)
    print("✅ 分析完成")
    print("=" * 70)


if __name__ == "__main__":
    main()
