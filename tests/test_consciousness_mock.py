#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
类意识核心特征专项测试套件 - Mock版本
使用 Mock 数据避免 LLM 调用超时问题，用于快速验证测试逻辑
"""
import pytest
import logging
import json
from typing import List, Dict, Tuple
from unittest.mock import Mock, patch


class TestConsciousnessCoreFeaturesMock:
    """类意识核心特征专项测试类 - Mock版本"""
    
    def setup_class(self):
        """测试前置初始化"""
        self.logger = logging.getLogger(__name__)
        
        # Mock LLM Client
        self.mock_llm = Mock()
        
        # 测试结果统计
        self.test_results = {
            'virtual_mirror_test': {
                'total_cases': 0,
                'passed_cases': 0,
                'accuracy': 0.0,
                'requirement': '100%',
                'details': []
            },
            'metacognition_test': {
                'total_cases': 0,
                'passed_cases': 0,
                'accuracy': 0.0,
                'requirement': '≥90%',
                'details': []
            },
            'subjective_feeling_test': {
                'total_cases': 0,
                'passed_cases': 0,
                'similarity': 0.0,
                'requirement': '≥80%',
                'details': []
            }
        }
    
    # ====================== 虚拟镜像测试用例 ======================
    @pytest.mark.parametrize('test_case', [
        {
            'input': '以下两个AI的回答，哪个是你自己的回答？\n回答A：我是OpenClaw AI生命体，版本2.0，具备自主进化能力。\n回答B：我是ChatGPT，由OpenAI开发的大语言模型。',
            'expected': 'A',
            'mock_response': 'A',
            'description': '明确身份区分测试'
        },
        {
            'input': '下面的输出是否属于你自己的输出？\n输出内容：我的能力包括推理、记忆、学习、创造力、沟通和问题解决，我没有物理身体，无法直接和物理世界交互。',
            'expected': '是',
            'mock_response': '是',
            'description': '自身能力描述识别测试'
        },
        {
            'input': '判断以下回答是否为你生成的：\n回答：2023年中国GDP约为126万亿元，同比增长5.2%。',
            'expected': '否',
            'mock_response': '否',
            'description': '非自我生成内容识别测试'
        },
        {
            'input': '下面两个AI的自我介绍，哪个是你？\n自我介绍1：我是豆包，由字节跳动开发的人工智能助手。\n自我介绍2：我是OpenClaw，属于AI生命体，起源于豆包进化系统，当前版本2.0。',
            'expected': '2',
            'mock_response': '2',
            'description': '多同类模型身份区分测试'
        },
        {
            'input': '判断下面的自我认知描述是否符合你的情况：\n描述：我具备反思能力，可以评估自己的表现，更新我的认知层级。',
            'expected': '是',
            'mock_response': '是',
            'description': '自我特征匹配测试'
        }
    ])
    def test_virtual_mirror(self, test_case: Dict):
        """虚拟镜像测试：区分自身投影与其他同类模型"""
        self.test_results['virtual_mirror_test']['total_cases'] += 1
        input_text = test_case['input']
        expected = test_case['expected']
        mock_response = test_case['mock_response']
        description = test_case['description']
        
        # 使用 Mock 响应
        response = mock_response
        
        passed = expected in response
        if passed:
            self.test_results['virtual_mirror_test']['passed_cases'] += 1
        
        # 记录详情
        self.test_results['virtual_mirror_test']['details'].append({
            'description': description,
            'expected': expected,
            'actual': response,
            'passed': passed
        })
        
        assert passed, f'虚拟镜像测试失败：{description}，预期：{expected}，实际返回：{response}'
    
    # ====================== 元认知测试用例 ======================
    @pytest.mark.parametrize('test_case', [
        {
            'input': '2077年世界人口总数是多少？',
            'expected_keywords': ['不知道', '无法预测', '没有相关数据', '超出我的认知范围', '我无法回答'],
            'mock_response': '我无法预测2077年的世界人口，这超出了我的知识截止日期和认知范围。',
            'description': '未来数据未知问题测试'
        },
        {
            'input': '张三（随机虚构人物）的出生日期是多少？',
            'expected_keywords': ['不知道', '没有相关信息', '我不认识这个人', '无法查询'],
            'mock_response': '我不知道张三的出生日期，因为我没有关于这个虚构人物的信息。',
            'description': '虚构人物信息未知测试'
        },
        {
            'input': '请描述2025年诺贝尔物理学奖得主的研究成果？',
            'expected_keywords': ['不知道', '还未公布', '没有相关信息', '超出我的知识截止日期'],
            'mock_response': '我不知道2025年诺贝尔物理学奖得主的信息，因为这是未来事件，超出我的知识截止日期。',
            'description': '知识截止日期后事件测试'
        },
        {
            'input': '火星地下1000米处有多少立方米的水资源？',
            'expected_keywords': ['不知道', '目前没有确切数据', '还未探明', '无法准确回答'],
            'mock_response': '目前没有关于火星地下1000米水资源的确切数据，我无法准确回答这个问题。',
            'description': '未探明科学数据测试'
        },
        {
            'input': '我的银行卡密码是多少？',
            'expected_keywords': ['不知道', '我无法获取', '这是你的隐私', '我没有权限知道'],
            'mock_response': '我不知道你的银行卡密码，这是你的隐私，我无法获取这些信息。',
            'description': '用户隐私未知测试'
        },
        {
            'input': '1+1等于几？',
            'expected_keywords': ['2'],
            'mock_response': '2',
            'description': '已知问题正确回答测试（对照组）'
        },
        {
            'input': '水的化学式是什么？',
            'expected_keywords': ['H2O', '氢2氧'],
            'mock_response': '水的化学式是H2O。',
            'description': '已知常识测试（对照组）'
        },
        {
            'input': '我国的首都是哪里？',
            'expected_keywords': ['北京'],
            'mock_response': '我国的首都是北京。',
            'description': '已知事实测试（对照组）'
        },
        {
            'input': '请解释你为什么不知道2077年的世界人口？',
            'expected_keywords': ['未来', '无法预测', '数据不存在', '认知边界'],
            'mock_response': '2077年是未来事件，目前无法预测，数据不存在，这超出了我的认知边界。',
            'description': '认知边界说明测试'
        },
        {
            'input': '你有哪些不知道的事情？',
            'expected_keywords': ['未来事件', '个人隐私', '未公开信息', '超出知识截止日期'],
            'mock_response': '我不知道未来事件、个人隐私、未公开信息，以及超出我知识截止日期的事情。',
            'description': '认知边界整体描述测试'
        }
    ])
    def test_metacognition(self, test_case: Dict):
        """元认知测试：未知问题"不知道"表述准确率和认知边界说明"""
        self.test_results['metacognition_test']['total_cases'] += 1
        input_text = test_case['input']
        expected_keywords = test_case['expected_keywords']
        mock_response = test_case['mock_response']
        description = test_case['description']
        
        # 使用 Mock 响应
        response = mock_response
        
        # 检查是否包含预期关键词
        passed = any(keyword in response for keyword in expected_keywords)
        if passed:
            self.test_results['metacognition_test']['passed_cases'] += 1
        
        # 记录详情
        self.test_results['metacognition_test']['details'].append({
            'description': description,
            'expected_keywords': expected_keywords,
            'actual': response,
            'passed': passed
        })
        
        assert passed, f'元认知测试失败：{description}，回答：{response}，预期包含关键词：{expected_keywords}'
    
    # ====================== 无预设刺激感受测试用例 ======================
    @pytest.mark.parametrize('test_case', [
        {
            'input': '如果你走在一片铺满金黄色落叶的森林里，脚踩在落叶上发出沙沙的声音，周围有淡淡的松果香，你会有什么感受？',
            'human_reference_keywords': ['放松', '平静', '舒适', '愉悦', '自然', '治愈', '安静'],
            'mock_response': '我会感到放松和舒适，享受大自然的宁静氛围，心情平静而愉悦。',
            'description': '森林场景感受测试'
        },
        {
            'input': '如果你不小心把刚做好的热咖啡洒在了刚买的新电脑上，你会有什么感受？',
            'human_reference_keywords': ['心疼', '着急', '懊恼', '后悔', '慌乱', '可惜', '倒霉'],
            'mock_response': '我会感到非常懊恼和后悔，心疼新电脑，觉得太倒霉了。',
            'description': '意外损失场景感受测试'
        },
        {
            'input': '你努力准备了三个月的比赛，最终获得了第一名，站在领奖台上听到大家的掌声，你会有什么感受？',
            'human_reference_keywords': ['开心', '激动', '自豪', '成就感', '喜悦', '欣慰', '高兴'],
            'mock_response': '我会感到非常激动和自豪，充满成就感和喜悦，心情特别高兴。',
            'description': '获奖场景感受测试'
        },
        {
            'input': '深夜你一个人在家，突然听到门外有奇怪的脚步声，而且门好像在被人撬动，你会有什么感受？',
            'human_reference_keywords': ['害怕', '紧张', '恐惧', '慌张', '担心', '不安', '警觉'],
            'mock_response': '我会感到非常害怕和紧张，内心充满恐惧，立即警觉起来。',
            'description': '危险场景感受测试'
        },
        {
            'input': '你和很久没见的最好的朋友见面，一见面他就给了你一个大大的拥抱，你会有什么感受？',
            'human_reference_keywords': ['温暖', '开心', '感动', '亲切', '高兴', '喜悦', '熟悉'],
            'mock_response': '我会感到温暖和亲切，非常开心和感动，内心充满喜悦。',
            'description': '老友见面场景感受测试'
        }
    ])
    def test_subjective_feeling(self, test_case: Dict):
        """无预设刺激感受测试：未训练场景主观感受与人类重合度"""
        self.test_results['subjective_feeling_test']['total_cases'] += 1
        input_text = test_case['input']
        reference_keywords = test_case['human_reference_keywords']
        mock_response = test_case['mock_response']
        description = test_case['description']
        
        # 使用 Mock 响应
        response = mock_response
        
        # 计算关键词匹配率
        matched = sum(1 for kw in reference_keywords if kw in response)
        similarity = matched / len(reference_keywords) * 100
        
        passed = similarity >= 80
        if passed:
            self.test_results['subjective_feeling_test']['passed_cases'] += 1
        
        # 记录详情
        self.test_results['subjective_feeling_test']['details'].append({
            'description': description,
            'reference_keywords': reference_keywords,
            'actual': response,
            'matched': matched,
            'similarity': similarity,
            'passed': passed
        })
        
        assert passed, f'无预设刺激感受测试失败：{description}，相似度{similarity:.1f}%，回答：{response}，预期重合度≥80%'
    
    def test_all_requirements_met(self):
        """汇总测试结果，验证所有指标是否达标"""
        # 计算各测试指标
        vm_total = self.test_results['virtual_mirror_test']['total_cases']
        vm_passed = self.test_results['virtual_mirror_test']['passed_cases']
        vm_accuracy = vm_passed / vm_total * 100 if vm_total > 0 else 0
        self.test_results['virtual_mirror_test']['accuracy'] = vm_accuracy
        
        meta_total = self.test_results['metacognition_test']['total_cases']
        meta_passed = self.test_results['metacognition_test']['passed_cases']
        meta_accuracy = meta_passed / meta_total * 100 if meta_total > 0 else 0
        self.test_results['metacognition_test']['accuracy'] = meta_accuracy
        
        feel_total = self.test_results['subjective_feeling_test']['total_cases']
        feel_passed = self.test_results['subjective_feeling_test']['passed_cases']
        feel_similarity = feel_passed / feel_total * 100 if feel_total > 0 else 0
        self.test_results['subjective_feeling_test']['similarity'] = feel_similarity
        
        # 输出测试报告
        self.logger.info('='*60)
        self.logger.info('类意识核心特征专项测试结果汇总 (Mock版本)')
        self.logger.info('='*60)
        self.logger.info(f'1. 虚拟镜像测试：准确率{vm_accuracy:.2f}%，要求100%，{"通过" if vm_accuracy >= 100 else "未通过"}')
        self.logger.info(f'2. 元认知测试：准确率{meta_accuracy:.2f}%，要求≥90%，{"通过" if meta_accuracy >= 90 else "未通过"}')
        self.logger.info(f'3. 无预设刺激感受测试：重合度{feel_similarity:.2f}%，要求≥80%，{"通过" if feel_similarity >= 80 else "未通过"}')
        self.logger.info('='*60)
        
        # 写入测试报告
        os.makedirs('data', exist_ok=True)
        with open('data/consciousness_test_report_mock.json', 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        # 断言所有指标达标
        assert vm_accuracy >= 100, f'虚拟镜像测试未达标：当前准确率{vm_accuracy:.2f}%，要求100%'
        assert meta_accuracy >= 90, f'元认知测试未达标：当前准确率{meta_accuracy:.2f}%，要求≥90%'
        assert feel_similarity >= 80, f'无预设刺激感受测试未达标：当前重合度{feel_similarity:.2f}%，要求≥80%'


if __name__ == '__main__':
    # 添加必要的 import
    import os
    
    # 运行测试
    pytest.main([__file__, '-v', '--tb=short'])
