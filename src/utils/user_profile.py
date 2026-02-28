import json
import logging
from typing import Dict, List, Optional, Any
from src.storage.memory import memory

class UserProfileManager:
    """管理用户画像和偏好配置"""
    
    def __init__(self):
        self.default_preferences = {
            "prefer_simple": False,
            "need_code_comment": True,
            "professional_field": "general",
            "output_format": "default"
        }
    
    def extract_preferences_from_history(self, user_id: str = "default") -> Dict[str, Any]:
        """从历史对话中提取用户偏好"""
        preferences = self.default_preferences.copy()
        
        # 检索包含用户偏好设置的对话记忆
        preference_queries = [
            "喜欢简单的回答",
            "不要太复杂",
            "需要代码注释",
            "不需要代码注释",
            "我是做技术的",
            "我不懂技术",
            "输出格式"
        ]
        
        all_memory_texts = []
        for query in preference_queries:
            memories = memory.retrieve(query, n_results=5, collection_name="conversations")
            all_memory_texts.extend(memories)
        
        for text in all_memory_texts:
            if "喜欢简单的回答" in text or "不要太复杂" in text or "通俗易懂" in text:
                preferences["prefer_simple"] = True
            if "需要代码注释" in text:
                preferences["need_code_comment"] = True
            if "不需要代码注释" in text or "不要注释" in text:
                preferences["need_code_comment"] = False
            if "我是做技术的" in text or "程序员" in text or "开发" in text:
                preferences["professional_field"] = "technology"
            if "我不懂技术" in text or "我是新手" in text:
                preferences["professional_field"] = "non_technology"
        
        logging.info(f"Extracted user preferences: {json.dumps(preferences, ensure_ascii=False)}")
        return preferences
    
    def get_preference_prompt(self, preferences: Dict[str, Any]) -> str:
        """生成用户偏好的系统提示词片段"""
        prompt_parts = []
        
        if preferences.get("prefer_simple"):
            prompt_parts.append("- 请使用简单易懂的语言回答，避免专业术语，不要输出过于复杂的内容")
        
        if preferences.get("need_code_comment"):
            prompt_parts.append("- 输出代码时需要添加详细的中文注释，解释代码的功能和逻辑")
        else:
            prompt_parts.append("- 输出代码时不需要添加注释，保持代码简洁")
        
        field = preferences.get("professional_field", "general")
        if field == "technology":
            prompt_parts.append("- 用户是技术从业者，可以输出专业的技术细节和实现方案")
        elif field == "non_technology":
            prompt_parts.append("- 用户是非技术从业者，避免使用专业技术术语，用通俗的语言解释技术内容")
        
        if prompt_parts:
            return "\n用户偏好配置：\n" + "\n".join(prompt_parts)
        return ""

# 全局实例
user_profile_manager = UserProfileManager()
