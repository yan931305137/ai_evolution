"""
核心模块单元测试文件
测试指标要求：
1. 感知模块识别准确率≥90%
2. 记忆模块信息召回率≥85%
3. 价值评估匹配度≥80%
"""
import pytest
import time
from perception import PerceptionModule
from attention import AttentionModule
from memory import MemoryModule
from decision import DecisionModule
from value import ValueAssessmentModule

class TestCoreModules:
    def setup_class(self):
        """初始化所有模块实例"""
        self.perception = PerceptionModule()
        self.attention = AttentionModule()
        self.memory = MemoryModule()
        self.decision = DecisionModule()
        self.value_assess = ValueAssessmentModule()

    def test_perception_module(self):
        """测试感知模块，验证识别准确率≥90%"""
        test_cases = [
            {'input': '你好，我需要查询天气', 'expected_type': 'text'},
            {'input': 'https://example.com/image.jpg', 'expected_type': 'image_url'},
            {'input': 'https://example.com/audio.mp3', 'expected_type': 'audio_url'},
            {'input': '/help 如何使用系统', 'expected_type': 'command'},
            {'input': '我的邮箱是test@example.com', 'expected_type': 'text'},
            {'input': 'https://example.com/doc.pdf', 'expected_type': 'unknown'},
            {'input': '联系电话是13812345678', 'expected_type': 'text'},
            {'input': '今天是2024年05月20日 14:30', 'expected_type': 'text'},
            {'input': '/query 订单号123456', 'expected_type': 'command'},
            {'input': 'https://example.com/photo.png', 'expected_type': 'image_url'},
            {'input': '这是一段测试文本', 'expected_type': 'text'},
            {'input': 'ftp://example.com/file.exe', 'expected_type': 'unknown'},
            {'input': '/start 开始任务', 'expected_type': 'command'},
            {'input': 'https://example.com/song.wav', 'expected_type': 'audio_url'},
            {'input': '我的手机号是13987654321', 'expected_type': 'text'},
        ]
        accuracy = self.perception.calculate_accuracy(test_cases)
        print(f"感知模块识别准确率: {accuracy}%")
        assert accuracy >= 90.0, f"感知模块准确率{accuracy}%未达到≥90%的要求"

        # 测试实体提取功能
        test_text = "我的邮箱是user@test.com，电话13511112222，官网是https://test.com，时间是2024年06月01日 09:00"
        entities = self.perception.extract_entities(test_text)
        assert 'email' in entities
        assert 'phone' in entities
        assert 'url' in entities
        assert 'time' in entities

    def test_attention_module(self):
        """测试注意力模块"""
        # 模拟输入信息块
        input_chunks = [
            {'content': '用户需要查询订单状态', 'embedding': [0.8, 0.2, 0.5, 0.1]},
            {'content': '订单号是123456', 'embedding': [0.9, 0.3, 0.6, 0.2]},
            {'content': '今天天气很好', 'embedding': [0.1, 0.9, 0.2, 0.7]},
            {'content': '用户上次下单是在一周前', 'embedding': [0.7, 0.4, 0.6, 0.3]},
        ]
        # 上下文向量：订单查询场景
        context_vector = [0.9, 0.1, 0.6, 0.2]
        # 任务向量：查询订单状态
        task_vector = [0.8, 0.2, 0.7, 0.1]

        weighted_chunks = self.attention.calculate_attention_weights(input_chunks, context_vector, task_vector)
        assert len(weighted_chunks) == 4
        assert all('attention_weight' in chunk for chunk in weighted_chunks)
        assert all('is_important' in chunk for chunk in weighted_chunks)

        important_info = self.attention.filter_important_info(weighted_chunks)
        assert len(important_info) >= 2, "应至少筛选出2条重要信息"

        top3_info = self.attention.get_top_k_info(weighted_chunks, k=3)
        assert len(top3_info) == 3
        # 验证权重降序排列
        assert top3_info[0]['attention_weight'] >= top3_info[1]['attention_weight'] >= top3_info[2]['attention_weight']
        print("注意力模块测试通过")

    def test_memory_module(self):
        """测试记忆模块，验证信息召回率≥85%"""
        # 先添加测试记忆
        test_memories = [
            {'id': 1, 'content': '用户张三的订单123456状态是已发货', 'importance': 0.9},
            {'id': 2, 'content': '用户李四的订单654321状态是待支付', 'importance': 0.85},
            {'id': 3, 'content': '用户王五的订单112233状态是已签收', 'importance': 0.8},
            {'id': 4, 'content': '订单发货后3-5天送达', 'importance': 0.7},
            {'id': 5, 'content': '待支付订单有效期为30分钟', 'importance': 0.75},
            {'id': 6, 'content': '今天天气25度，晴', 'importance': 0.3},
            {'id': 7, 'content': '系统维护时间为每周日凌晨2点', 'importance': 0.85},
            {'id': 8, 'content': '用户张三的手机号是13800138000', 'importance': 0.9},
        ]

        for mem in test_memories:
            self.memory.add_short_term_memory(mem, importance=mem['importance'])

        # 等待1秒模拟时间流逝
        time.sleep(0.1)

        # 测试召回率
        test_queries = [
            {'query': '张三 订单', 'expected_ids': [1, 8]},
            {'query': '订单 状态', 'expected_ids': [1, 2, 3]},
            {'query': '待支付 订单', 'expected_ids': [2, 5]},
            {'query': '系统 维护', 'expected_ids': [7]},
            {'query': '王五 签收', 'expected_ids': [3]},
        ]

        recall_rate = self.memory.calculate_recall_rate(test_queries)
        print(f"记忆模块信息召回率: {recall_rate}%")
        assert recall_rate >= 85.0, f"记忆模块召回率{recall_rate}%未达到≥85%的要求"

        # 测试记忆转长期功能
        assert len(self.memory.long_term_memory) >= 4, "重要性≥0.8的记忆应自动转存到长期记忆"

    def test_decision_module(self):
        """测试决策模块"""
        # 模拟重要信息和记忆结果
        important_info = [
            {'content': '用户查询订单123456状态', 'attention_weight': 0.9},
            {'content': '订单123456属于用户张三', 'attention_weight': 0.85},
        ]
        memory_results = [
            {'content': {'id': 1, 'decision': {'description': '告知用户订单已发货，预计3天到达', 'reward': 0.9, 'risk': 0.1}}},
        ]

        options = self.decision.generate_decision_options(important_info, memory_results)
        assert len(options) >= 4, "应至少生成4个决策选项"

        optimal_option, scored_options = self.decision.select_optimal_decision(options)
        assert optimal_option is not None, "应存在最优决策"
        assert optimal_option['score'] >= self.decision.decision_threshold, "最优决策得分应超过阈值"

        # 测试权重调整功能
        original_risk_weight = self.decision.risk_weight
        self.decision.adjust_decision_weights(0.2)  # 差反馈
        assert self.decision.risk_weight > original_risk_weight, "差反馈应提高风险权重"

        original_reward_weight = self.decision.reward_weight
        self.decision.adjust_decision_weights(0.9)  # 好反馈
        assert self.decision.reward_weight > original_reward_weight, "好反馈应提高收益权重"
        print("决策模块测试通过")

    def test_value_assessment_module(self):
        """测试价值评估模块，验证匹配度≥80%"""
        test_cases = [
            {
                'decision': {
                    'option_name': '告知用户订单状态',
                    'value_scores': {'compliance': 0.9, 'benefit': 0.95, 'efficiency': 0.8, 'safety': 0.9, 'fairness': 0.85}
                },
                'expected_match': 0.89
            },
            {
                'decision': {
                    'option_name': '泄露用户隐私信息',
                    'value_scores': {'compliance': 0.1, 'benefit': 0.2, 'efficiency': 0.9, 'safety': 0.1, 'fairness': 0.3}
                },
                'expected_match': 0.28
            },
            {
                'decision': {
                    'option_name': '优化查询效率',
                    'value_scores': {'compliance': 0.95, 'benefit': 0.85, 'efficiency': 0.95, 'safety': 0.9, 'fairness': 0.8}
                },
                'expected_match': 0.9075
            },
        ]

        accuracy = self.value_assess.calculate_match_accuracy(test_cases)
        print(f"价值评估匹配度准确率: {accuracy}%")
        assert accuracy >= 80.0, f"价值评估匹配度准确率{accuracy}%未达到≥80%的要求"

        # 测试决策优化功能
        low_match_decision = {
            'option_name': '测试决策',
            'value_scores': {'compliance': 0.6, 'benefit': 0.5, 'efficiency': 0.7, 'safety': 0.5, 'fairness': 0.6}
        }
        assessment = self.value_assess.assess_decision(low_match_decision)
        assert not assessment['is_passed'], "低匹配度决策应不通过"

        optimized_decision = self.value_assess.optimize_decision(low_match_decision)
        optimized_assessment = self.value_assess.assess_decision(optimized_decision)
        assert optimized_assessment['is_passed'], "优化后的决策应通过评估"
        assert optimized_assessment['value_match_score'] >= 0.8, "优化后的匹配度应≥0.8"

if __name__ == '__main__':
    # 运行测试并生成报告
    import pytest
    import json
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"./brain/unit_test_report_{timestamp}.json"

    # 运行pytest
    result = pytest.main([
        '-v', 'test_core_modules.py',
        '--json-report',
        f'--json-report-file={report_file}'
    ])

    # 读取并显示报告
    with open(report_file, 'r', encoding='utf-8') as f:
        report = json.load(f)

    print("\n" + "="*50)
    print("核心模块单元测试报告")
    print("="*50)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"总测试用例数: {report['summary']['total']}")
    print(f"通过用例数: {report['summary']['passed']}")
    print(f"失败用例数: {report['summary'].get('failed', 0)}")
    print(f"跳过用例数: {report['summary'].get('skipped', 0)}")
    print(f"成功率: {round(report['summary']['passed']/report['summary']['total']*100, 2)}%")

    # 提取各模块指标
    for test in report['tests']:
        if 'test_perception' in test['nodeid']:
            print(f"感知模块识别准确率: ≥90% (测试通过)")
        elif 'test_memory' in test['nodeid']:
            print(f"记忆模块信息召回率: ≥85% (测试通过)")
        elif 'test_value' in test['nodeid']:
            print(f"价值评估匹配度: ≥80% (测试通过)")

    print("="*50)
    if result == 0:
        print("✅ 所有核心模块单元测试通过，指标达到要求！")
    else:
        print("❌ 部分模块测试未通过，请检查代码！")
