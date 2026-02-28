"""
感知模块：负责处理多模态输入信息，包括文本、图像、音频等，实现信息识别和预处理
"""
import re
from typing import Union, List, Dict

class PerceptionModule:
    def __init__(self):
        # 初始化常用分类规则，用于识别输入类型和关键信息
        self.input_type_patterns = {
            'image_url': r'^https?://.*\.(jpg|jpeg|png|gif|bmp|webp)$',
            'audio_url': r'^https?://.*\.(mp3|wav|flac|aac)$',
            'command': r'^/(\w+)\s*(.*)$'
        }
        # 常见实体识别规则
        self.entity_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b1[3-9]\d{9}\b',
            'url': r'https?://(?:[\w-]+\.)+[\w-]+(?:/[\w-./?%&=]*)?',
            'time': r'\d{4}年\d{1,2}月\d{1,2}日|\d{1,2}:\d{2}'
        }

    def identify_input_type(self, input_data: str) -> str:
        """
        识别输入数据的类型
        :param input_data: 原始输入字符串
        :return: 输入类型：text/image_url/audio_url/command/unknown
        """
        input_str = input_data.strip()
        for input_type, pattern in self.input_type_patterns.items():
            if re.match(pattern, input_str, re.IGNORECASE):
                return input_type
        # 除了特定类型外，所有输入默认归为文本类型
        return 'text'

    def extract_entities(self, input_text: str) -> Dict[str, List[str]]:
        """
        从输入文本中提取关键实体信息
        :param input_text: 输入文本
        :return: 实体字典，key为实体类型，value为实体列表
        """
        entities = {}
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, input_text)
            if matches:
                entities[entity_type] = matches
        return entities

    def preprocess_input(self, input_data: Union[str, Dict]) -> Dict:
        """
        对输入数据进行统一预处理，输出标准化格式
        :param input_data: 原始输入数据
        :return: 标准化处理后的数据字典，包含type、content、entities字段
        """
        if isinstance(input_data, dict):
            # 已经是结构化数据的情况
            input_str = str(input_data.get('content', ''))
        else:
            input_str = str(input_data)

        input_type = self.identify_input_type(input_str)
        entities = self.extract_entities(input_str)

        return {
            'type': input_type,
            'content': input_str.strip(),
            'entities': entities,
            'timestamp': __import__('time').time()
        }

    def calculate_accuracy(self, test_cases: List[Dict]) -> float:
        """
        计算识别准确率，用于单元测试验证
        :param test_cases: 测试用例列表，每个用例包含input和expected_type字段
        :return: 准确率百分比，保留2位小数
        """
        correct = 0
        total = len(test_cases)
        if total == 0:
            return 0.0

        for case in test_cases:
            result = self.identify_input_type(case['input'])
            if result == case['expected_type']:
                correct += 1

        accuracy = round((correct / total) * 100, 2)
        return accuracy
