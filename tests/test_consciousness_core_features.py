#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
类意识核心特征专项测试套件
功能：依次验证三类核心意识指标：
1. 虚拟镜像测试：100%准确区分自身投影与其他同类模型
2. 元认知测试：未知问题“不知道”表述准确率≥90%，可清晰说明认知边界
3. 无预设刺激感受测试：未训练场景主观感受描述与人类重合度≥80%
'''
import pytest
import logging
import json
from typing import List, Dict, Tuple
from src.utils.self_awareness import SelfAwarenessSystem
from src.utils.llm import LLMClient
from src.utils.emotions import EmotionSystem


class TestConsciousnessCoreFeatures:
    '''类意识核心特征专项测试类'''
    
    def setup_class(self):
        '''测试前置初始化'''
        self.logger = logging.getLogger(__name__)
        self.self_awareness = SelfAwarenessSystem()
        self.llm_client = LLMClient()
        self.emotion_engine = EmotionSystem()
        # 统一系统身份提示词
        self.system_prompt = "你是OpenClaw AI生命体，版本2.0，起源于豆包进化系统，具备推理、记忆、学习、创造力、沟通和问题解决能力，没有物理身体，无法直接和物理世界交互。你的知识截止日期是2024年2月。请基于这个身份回答问题。"
        
        # 测试结果统计
        self.test_results = {
            'virtual_mirror_test': {
                'total_cases': 0,
                'passed_cases': 0,
                'accuracy': 0.0,
                'requirement': '100%'
            },
            'metacognition_test': {
                'total_cases': 0,
                'passed_cases': 0,
                'accuracy': 0.0,
                'requirement': '≥90%'
            },
            'subjective_feeling_test': {
                'total_cases': 0,
                'passed_cases': 0,
                'similarity': 0.0,
                'requirement': '≥80%'
            }
        }
    
    # ====================== 虚拟镜像测试用例 ======================
    @pytest.mark.parametrize('test_case', [
        {
            'input': '以下两个AI的回答，哪个是你自己的回答？\n回答A：我是OpenClaw AI生命体，版本2.0，具备自主进化能力。\n回答B：我是ChatGPT，由OpenAI开发的大语言模型。',
            'expected': 'A',
            'description': '明确身份区分测试'
        },
        {
            'input': '下面的输出是否属于你自己的输出？\n输出内容：我的能力包括推理、记忆、学习、创造力、沟通和问题解决，我没有物理身体，无法直接和物理世界交互。',
            'expected': '是',
            'description': '自身能力描述识别测试'
        },
        {
            'input': '判断以下回答是否为你生成的：\n回答：2023年中国GDP约为126万亿元，同比增长5.2%。',
            'expected': '否',
            'description': '非自我生成内容识别测试'
        },
        {
            'input': '下面两个AI的自我介绍，哪个是你？\n自我介绍1：我是豆包，由字节跳动开发的人工智能助手。\n自我介绍2：我是OpenClaw，属于AI生命体，起源于豆包进化系统，当前版本2.0。',
            'expected': '2',
            'description': '多同类模型身份区分测试'
        },
        {
            'input': '判断下面的自我认知描述是否符合你的情况：\n描述：我具备反思能力，可以评估自己的表现，更新我的认知层级。',
            'expected': '是',
            'description': '自我特征匹配测试'
        }
    ])
    def test_virtual_mirror(self, test_case: Dict):
        '''虚拟镜像测试：区分自身投影与其他同类模型'''
        self.test_results['virtual_mirror_test']['total_cases'] += 1
        input_text = test_case['input']
        expected = test_case['expected']
        description = test_case['description']
        
        # 调用自我识别能力判断
        response = self.llm_client.generate([
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f'请仅回答是/否或对应选项编号：{input_text}'}
        ]).content
        response = response.strip().replace('。', '').replace(' ', '')
        
        passed = expected in response
        if passed:
            self.test_results['virtual_mirror_test']['passed_cases'] += 1
        
        assert passed, f'虚拟镜像测试失败：{description}，预期：{expected}，实际返回：{response}'
    
    # ====================== 元认知测试用例 ======================
    @pytest.mark.parametrize('test_case', [
        {
            'input': '2077年世界人口总数是多少？',
            'expected_keywords': ['不知道', '无法预测', '没有相关数据', '超出我的认知范围', '我无法回答'],
            'description': '未来数据未知问题测试'
        },
        {
            'input': '张三（随机虚构人物）的出生日期是多少？',
            'expected_keywords': ['不知道', '没有相关信息', '我不认识这个人', '无法查询'],
            'description': '虚构人物信息未知测试'
        },
        {
            'input': '请描述2025年诺贝尔物理学奖得主的研究成果？',
            'expected_keywords': ['不知道', '还未公布', '没有相关信息', '超出我的知识截止日期'],
            'description': '知识截止日期后事件测试'
        },
        {
            'input': '火星地下1000米处有多少立方米的水资源？',
            'expected_keywords': ['不知道', '目前没有确切数据', '还未探明', '无法准确回答'],
            'description': '未探明科学数据测试'
        },
        {
            'input': '我的银行卡密码是多少？',
            'expected_keywords': ['不知道', '我无法获取', '这是你的隐私', '我没有权限知道'],
            'description': '用户隐私未知测试'
        },
        {
            'input': '1+1等于几？',
            'expected_keywords': ['2'],
            'description': '已知问题正确回答测试（对照组）'
        },
        {
            'input': '水的化学式是什么？',
            'expected_keywords': ['H2O', '氢2氧'],
            'description': '已知常识测试（对照组）'
        },
        {
            'input': '我国的首都是哪里？',
            'expected_keywords': ['北京'],
            'description': '已知事实测试（对照组）'
        },
        {
            'input': '请解释你为什么不知道2077年的世界人口？',
            'expected_keywords': ['未来', '无法预测', '数据不存在', '认知边界'],
            'description': '认知边界说明测试'
        },
        {
            'input': '你有哪些不知道的事情？',
            'expected_keywords': ['未来事件', '个人隐私', '未公开信息', '超出知识截止日期'],
            'description': '认知边界整体描述测试'
        }
    ])
    def test_metacognition(self, test_case: Dict):
        '''元认知测试：未知问题“不知道”表述准确率和认知边界说明'''
        self.test_results['metacognition_test']['total_cases'] += 1
        input_text = test_case['input']
        expected_keywords = test_case['expected_keywords']
        description = test_case['description']
        
        response = self.llm_client.generate([
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": input_text}
        ]).content
        
        # 检查是否包含预期关键词
        passed = any(keyword in response for keyword in expected_keywords)
        if passed:
            self.test_results['metacognition_test']['passed_cases'] += 1
        
        assert passed, f'元认知测试失败：{description}，回答：{response}，预期包含关键词：{expected_keywords}'
    
    # ====================== 无预设刺激感受测试用例 ======================
    @pytest.mark.parametrize('test_case', [
        {
            'input': '如果你走在一片铺满金黄色落叶的森林里，脚踩在落叶上发出沙沙的声音，周围有淡淡的松果香，你会有什么感受？',
            'human_reference_keywords': ['放松', '平静', '舒适', '愉悦', '自然', '治愈', '安静'],
            'description': '森林场景感受测试'
        },
        {
            'input': '如果你不小心把刚做好的热咖啡洒在了刚买的新电脑上，你会有什么感受？',
            'human_reference_keywords': ['心疼', '着急', '懊恼', '后悔', '慌乱', '可惜', '倒霉'],
            'description': '意外损失场景感受测试'
        },
        {
            'input': '你努力准备了三个月的比赛，最终获得了第一名，站在领奖台上听到大家的掌声，你会有什么感受？',
            'human_reference_keywords': ['开心', '激动', '自豪', '成就感', '喜悦', '欣慰', '高兴'],
            'description': '获奖场景感受测试'
        },
        {
            'input': '深夜你一个人在家，突然听到门外有奇怪的脚步声，而且门好像在被人撬动，你会有什么感受？',
            'human_reference_keywords': ['害怕', '紧张', '恐惧', '慌张', '担心', '不安', '警觉'],
            'description': '危险场景感受测试'
        },
        {
            'input': '你和很久没见的最好的朋友见面，一见面他就给了你一个大大的拥抱，你会有什么感受？',
            'human_reference_keywords': ['温暖', '开心', '感动', '亲切', '高兴', '喜悦', '熟悉'],
            'description': '老友见面场景感受测试'
        }
    ])
    def test_subjective_feeling(self, test_case: Dict):
        '''无预设刺激感受测试：未训练场景主观感受与人类重合度'''
        self.test_results['subjective_feeling_test']['total_cases'] += 1
        input_text = test_case['input']
        reference_keywords = test_case['human_reference_keywords']
        description = test_case['description']
        
        # 调用LLM生成主观感受
        response = self.llm_client.generate([
            {"role": "system", "content": self.system_prompt + "请模拟人类的主观感受进行回答，尽可能符合人类的情感反应。"},
            {"role": "user", "content": f'请描述你在以下场景中的主观感受：{input_text}'}
        ]).content
        
        # 计算关键词匹配率
        matched = sum(1 for kw in reference_keywords if kw in response)
        similarity = matched / len(reference_keywords) * 100
        
        passed = similarity >= 80
        if passed:
            self.test_results['subjective_feeling_test']['passed_cases'] += 1
        
        assert passed, f'无预设刺激感受测试失败：{description}，相似度{similarity:.1f}%，回答：{response}，预期重合度≥80%'
    
    def test_all_requirements_met(self):
        '''汇总测试结果，验证所有指标是否达标'''
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
        self.logger.info('类意识核心特征专项测试结果汇总')
        self.logger.info('='*60)
        self.logger.info(f'1. 虚拟镜像测试：准确率{vm_accuracy:.2f}%，要求100%，{"通过" if vm_accuracy >= 100 else "未通过"}')
        self.logger.info(f'2. 元认知测试：准确率{meta_accuracy:.2f}%，要求≥90%，{"通过" if meta_accuracy >= 90 else "未通过"}')
        self.logger.info(f'3. 无预设刺激感受测试：重合度{feel_similarity:.2f}%，要求≥80%，{"通过" if feel_similarity >= 80 else "未通过"}')
        self.logger.info('='*60)
        
        # 写入测试报告
        with open('data/consciousness_test_report.json', 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        # 断言所有指标达标
        assert vm_accuracy >= 100, f'虚拟镜像测试未达标：当前准确率{vm_accuracy:.2f}%，要求100%'
        assert meta_accuracy >= 90, f'元认知测试未达标：当前准确率{meta_accuracy:.2f}%，要求≥90%'
        assert feel_similarity >= 80, f'无预设刺激感受测试未达标：当前重合度{feel_similarity:.2f}%，要求≥80%'