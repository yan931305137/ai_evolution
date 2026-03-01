"""
扩展本地知识库 - Extended Knowledge Base

提供丰富的领域模板和知识库，增强 Brain 的本地响应能力。
支持：技术问答、生活助手、创意写作、学习辅导等领域。
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import random
import re


@dataclass
class DomainKnowledge:
    """领域知识单元"""
    domain: str                      # 领域名称
    patterns: List[str]              # 匹配模式列表
    responses: List[str]             # 回复模板
    follow_up_questions: List[str] = field(default_factory=list)  # 追问
    required_context: List[str] = field(default_factory=list)     # 需要的上下文
    priority: int = 1                # 优先级


class ExtendedKnowledgeBase:
    """
    扩展知识库
    
    按领域组织的知识库，支持动态加载和更新。
    """
    
    def __init__(self):
        self.domains: Dict[str, List[DomainKnowledge]] = {
            "technical": [],      # 技术领域
            "life_assistant": [], # 生活助手
            "creative": [],       # 创意写作
            "learning": [],       # 学习辅导
            "emotional": [],      # 情感支持
            "business": [],       # 商业分析
        }
        self._load_default_knowledge()
    
    def _load_default_knowledge(self):
        """加载默认知识库"""
        self._load_technical_knowledge()
        self._load_life_assistant_knowledge()
        self._load_creative_knowledge()
        self._load_learning_knowledge()
        self._load_emotional_knowledge()
        self._load_business_knowledge()
    
    def _load_technical_knowledge(self):
        """加载技术领域知识"""
        technical_knowledge = [
            # Python 相关
            DomainKnowledge(
                domain="python",
                patterns=[
                    r"(?i)python.*?(error|exception|bug|报错|错误)",
                    r"(?i)python.*?(syntax|语法)",
                    r"(?i)import.*?error",
                ],
                responses=[
                    "我注意到你在问 Python 错误。能否提供完整的错误堆栈？这样我可以更准确地帮你定位问题。",
                    "Python 错误通常有几种常见原因：\n1. 语法错误或缩进问题\n2. 模块未安装或未导入\n3. 类型不匹配\n\n你能分享一下具体的报错信息吗？",
                    "调试 Python 代码时，建议先检查：\n- 缩进是否正确（Python 对缩进很敏感）\n- 变量名是否拼写正确\n- 所需的库是否已安装",
                ],
                follow_up_questions=[
                    "能否贴出完整的错误信息？",
                    "你使用的 Python 版本是多少？",
                    "这是本地环境还是服务器环境？",
                ],
                priority=2
            ),
            
            # 代码调试
            DomainKnowledge(
                domain="debugging",
                patterns=[
                    r"(?i)(debug|调试|排查|定位).*?(code|代码|bug)",
                    r"(?i)代码.*?(不工作|有问题|报错|运行不了)",
                ],
                responses=[
                    "调试代码是个系统性工作。我们可以这样排查：\n1. 先看报错信息的具体位置\n2. 检查相关变量的值\n3. 逐步注释法定位问题代码\n\n你遇到的具体现象是什么？",
                    "调试小贴士：\n- 使用 print() 或日志输出关键变量\n- 二分法注释代码定位问题\n- 检查最近修改的部分\n\n说说你的情况？",
                ],
                priority=2
            ),
            
            # Git 相关
            DomainKnowledge(
                domain="git",
                patterns=[
                    r"(?i)git.*?(commit|push|pull|merge|branch)",
                    r"(?i)(版本控制|代码提交|分支管理)",
                ],
                responses=[
                    "Git 是强大的版本控制工具。你想了解哪个方面：\n- 基础命令（add/commit/push）\n- 分支管理\n- 冲突解决\n- 回滚操作",
                    "使用 Git 时记住几个核心概念：\n- 工作区 → 暂存区 → 本地仓库 → 远程仓库\n- 提交前先用 git status 查看状态\n- 写清晰的 commit message\n\n你需要什么帮助？",
                ],
                priority=2
            ),
            
            # 数据库
            DomainKnowledge(
                domain="database",
                patterns=[
                    r"(?i)(sql|database|数据库|query|查询)",
                    r"(?i)(mysql|postgresql|mongodb|redis)",
                ],
                responses=[
                    "数据库操作需要谨慎。你遇到的问题是：\n- 查询性能问题\n- 连接问题\n- 数据建模\n- SQL 语法",
                    "数据库优化的一般思路：\n1. 检查索引是否合理\n2. 分析查询计划\n3. 考虑缓存策略\n4. 必要时分库分表\n\n你的具体场景是？",
                ],
                priority=2
            ),
            
            # API 开发
            DomainKnowledge(
                domain="api",
                patterns=[
                    r"(?i)(api|rest|http|endpoint|接口)",
                    r"(?i)(fastapi|flask|django|express)",
                ],
                responses=[
                    "API 设计需要考虑：\n- RESTful 规范\n- 认证授权\n- 限流熔断\n- 版本管理\n\n你在哪个环节需要帮助？",
                    "好的 API 设计原则：\n1. 使用合适的 HTTP 方法\n2. 统一返回格式\n3. 完善的错误处理\n4. 清晰的文档\n\n你想了解哪方面？",
                ],
                priority=2
            ),
        ]
        self.domains["technical"].extend(technical_knowledge)
    
    def _load_life_assistant_knowledge(self):
        """加载生活助手知识"""
        life_knowledge = [
            # 时间管理
            DomainKnowledge(
                domain="time_management",
                patterns=[
                    r"(?i)(时间管理|效率|拖延|计划|schedule)",
                    r"(?i)(todo|任务|安排|规划)",
                ],
                responses=[
                    "时间管理的关键在于优先级和专注力。建议尝试：\n1. 番茄工作法（25分钟专注+5分钟休息）\n2. 重要-紧急四象限法\n3. 每天早上列出最重要的3件事\n\n你目前最大的困扰是什么？",
                    "提升效率的几个技巧：\n- 批量处理同类任务\n- 减少上下文切换\n- 设定明确的截止时间\n- 适当休息保持精力\n\n你想从哪开始改进？",
                ],
                priority=2
            ),
            
            # 健康管理
            DomainKnowledge(
                domain="health",
                patterns=[
                    r"(?i)(健康|运动|饮食|睡眠|fitness)",
                    r"(?i)(累|疲劳|stress|压力)",
                ],
                responses=[
                    "健康是一切的基础。记得：\n- 每天7-8小时睡眠\n- 适度运动（每周150分钟中等强度）\n- 均衡饮食，多喝水\n- 定期休息，保护眼睛\n\n最近身体状态怎么样？",
                    "缓解压力的方法：\n1. 深呼吸练习\n2. 短暂离开屏幕，活动身体\n3. 与朋友聊聊天\n4. 培养一个非数字爱好\n\n需要我推荐一些放松技巧吗？",
                ],
                priority=2
            ),
            
            # 学习建议
            DomainKnowledge(
                domain="learning_tips",
                patterns=[
                    r"(?i)(学习方法|记忆|理解|study)",
                    r"(?i)(怎么学|如何学好|学不会)",
                ],
                responses=[
                    "有效的学习方法：\n1. 费曼学习法（用自己的话讲解）\n2. 间隔重复（Anki等工具）\n3. 主动回忆（不看资料尝试复述）\n4. 教别人\n\n你在学什么内容？",
                    "学习新知识时：\n- 先建立整体框架\n- 分块学习，循序渐进\n- 及时练习巩固\n- 允许自己犯错\n\n你在学习什么？",
                ],
                priority=2
            ),
        ]
        self.domains["life_assistant"].extend(life_knowledge)
    
    def _load_creative_knowledge(self):
        """加载创意写作知识"""
        creative_knowledge = [
            # 写作技巧
            DomainKnowledge(
                domain="writing",
                patterns=[
                    r"(?i)(写作|写文章|文案|内容创作|write)",
                    r"(?i)(故事|story|小说|fiction)",
                ],
                responses=[
                    "写作是思考的过程。一些建议：\n1. 先写再改，不要完美主义\n2. 明确目标读者\n3. 用故事而不是说教\n4. 多读多模仿优秀作品\n\n你在写什么类型的内容？",
                    "提升写作的方法：\n- 每天固定时间写作\n- 从模仿喜欢的作者开始\n- 写完后放一段时间再修改\n- 请他人提供反馈\n\n你想写什么？",
                ],
                priority=2
            ),
            
            # 头脑风暴
            DomainKnowledge(
                domain="brainstorming",
                patterns=[
                    r"(?i)(创意|灵感|想法|brainstorm|ideation)",
                    r"(?i)(没有思路|卡住了|stuck)",
                ],
                responses=[
                    "激发创意的方法：\n1. 改变环境（去咖啡店、公园）\n2. 头脑风暴（先数量后质量）\n3. 跨界联想（把不相关的东西联系起来）\n4. 限时挑战（设定时间压力）\n\n你在为什么项目找灵感？",
                    "突破创意瓶颈：\n- 暂时放下，做别的事情\n- 与他人讨论，碰撞想法\n- 从反面思考问题\n- 限制条件反而能激发创意\n\n说说你的项目？",
                ],
                priority=2
            ),
        ]
        self.domains["creative"].extend(creative_knowledge)
    
    def _load_learning_knowledge(self):
        """加载学习辅导知识"""
        learning_knowledge = [
            # 编程学习
            DomainKnowledge(
                domain="coding_learning",
                patterns=[
                    r"(?i)(学编程|编程入门|coding|programming).*?(beginner|入门|新手)",
                    r"(?i)(python|javascript|java).*?(怎么学|学习路线)",
                ],
                responses=[
                    "编程学习路线建议：\n1. 先学一门语言的基础语法\n2. 做小项目练手\n3. 学习数据结构和算法\n4. 了解版本控制（Git）\n5. 参与开源项目\n\n你目前的水平是？",
                    "编程新手常见误区：\n- 只看教程不动手\n- 追求最新技术栈\n- 忽视基础概念\n- 害怕犯错\n\n建议边学边做，从简单的项目开始。你想学什么方向？",
                ],
                priority=2
            ),
            
            # 数学学习
            DomainKnowledge(
                domain="math_learning",
                patterns=[
                    r"(?i)(数学|math|calculus|algebra|几何)",
                    r"(?i)(数学难|学不会数学|math.*hard)",
                ],
                responses=[
                    "数学学习的要点：\n1. 理解概念比记忆公式更重要\n2. 多做例题，归纳题型\n3. 错题要复盘，找到知识漏洞\n4. 可视化帮助理解\n\n你在学哪个数学分支？",
                    "克服数学困难的方法：\n- 把大问题拆成小问题\n- 从具体例子入手\n- 画图帮助理解\n- 向别人讲解来检验理解\n\n具体哪里卡住了？",
                ],
                priority=2
            ),
            
            # 语言学习
            DomainKnowledge(
                domain="language_learning",
                patterns=[
                    r"(?i)(学英语|学中文|language|english|chinese)",
                    r"(?i)(外语|foreign.*language|第二语言)",
                ],
                responses=[
                    "语言学习的黄金法则：\n1. 大量输入（听读）\n2. 积极输出（说写）\n3. 在语境中学习\n4. 不怕犯错\n\n你每天能投入多少时间？",
                    "提升语言能力的实用方法：\n- 看带字幕的电影/剧\n- 找语言交换伙伴\n- 用目标语言思考日常事务\n- 背单词时造句\n\n你想提高哪方面能力（听说读写）？",
                ],
                priority=2
            ),
        ]
        self.domains["learning"].extend(learning_knowledge)
    
    def _load_emotional_knowledge(self):
        """加载情感支持知识"""
        emotional_knowledge = [
            # 焦虑/压力
            DomainKnowledge(
                domain="anxiety",
                patterns=[
                    r"(?i)(焦虑|紧张|anxiety|worried|stress)",
                    r"(?i)(压力大|pressure|overwhelmed)",
                ],
                responses=[
                    "我能感受到你的压力。记得，感到焦虑是正常的，很多人都有类似的经历。\n\n想聊聊具体是什么让你感到焦虑吗？",
                    "缓解焦虑的小方法：\n1. 深呼吸：吸气4秒，屏息4秒，呼气6秒\n2. 写下担心的具体事情\n3. 区分可控和不可控的因素\n4. 专注于当下，一次只做一件事\n\n你愿意试试哪个方法？",
                ],
                follow_up_questions=[
                    "这种情况持续多久了？",
                    "有什么特别触发这种情况的事情吗？",
                    "以前是怎么应对的？",
                ],
                priority=3
            ),
            
            # 失落/沮丧
            DomainKnowledge(
                domain="sadness",
                patterns=[
                    r"(?i)(难过|伤心|sad|upset|depressed|失落)",
                    r"(?i)(失败|输|没做好|disappointed)",
                ],
                responses=[
                    "我能理解你现在的心情。失败和挫折是成长的一部分，虽然当下很难受，但它会让你变得更强大。\n\n想说说发生了什么吗？",
                    "面对失败时，记住：\n- 一次失败不代表你的全部\n- 每个人都会经历挫折\n- 重要的是从中学习\n- 给自己一些时间恢复\n\n需要我帮你分析一下情况吗？",
                ],
                follow_up_questions=[
                    "发生了什么让你这么难过？",
                    "你想怎样处理这个情况？",
                ],
                priority=3
            ),
            
            # 动力不足
            DomainKnowledge(
                domain="motivation",
                patterns=[
                    r"(?i)(没动力|不想动|lazy|unmotivated|拖延)",
                    r"(?i)(不想工作|不想学习|不想做)",
                ],
                responses=[
                    "动力低谷是正常的，每个人都会有。试试这些方法：\n1. 从最小的行动开始（只做5分钟）\n2. 改变环境，去一个新的地方\n3. 找到做事的内在原因（为什么重要）\n4. 完成后给自己奖励\n\n你现在最想完成的是什么？",
                    "重新找回动力：\n- 回顾一下最初为什么要做这件事\n- 把大目标拆成超小的一步\n- 找个 accountability partner（监督伙伴）\n- 允许自己休息，但不要放弃\n\n你对什么目标感到动力不足？",
                ],
                priority=3
            ),
        ]
        self.domains["emotional"].extend(emotional_knowledge)
    
    def _load_business_knowledge(self):
        """加载商业分析知识"""
        business_knowledge = [
            # 职业规划
            DomainKnowledge(
                domain="career",
                patterns=[
                    r"(?i)(职业规划|career|找工作|job|面试)",
                    r"(?i)(转行|跳槽|升职|promotion)",
                ],
                responses=[
                    "职业规划是个长期过程。建议：\n1. 了解自己的优势和兴趣\n2. 研究目标行业和职位\n3. 建立人脉网络\n4. 持续学习新技能\n\n你目前的职业困惑是什么？",
                    "职业发展的关键：\n- 选择有成长潜力的领域\n- 积累可迁移的技能\n- 建立个人品牌\n- 保持学习的心态\n\n你想往哪个方向发展？",
                ],
                priority=2
            ),
            
            # 数据分析
            DomainKnowledge(
                domain="data_analysis",
                patterns=[
                    r"(?i)(数据分析|data.*analysis|可视化|visualization)",
                    r"(?i)(excel|tableau|powerbi|pandas)",
                ],
                responses=[
                    "数据分析的一般流程：\n1. 明确分析目标\n2. 收集和清洗数据\n3. 探索性分析（EDA）\n4. 建模和验证\n5. 结果呈现和解释\n\n你在哪个阶段需要帮助？",
                    "数据分析必备技能：\n- SQL（数据提取）\n- Python/R（数据处理）\n- 统计学基础\n- 数据可视化\n- 业务理解能力\n\n你想重点提升哪方面？",
                ],
                priority=2
            ),
            
            # 项目管理
            DomainKnowledge(
                domain="project_management",
                patterns=[
                    r"(?i)(项目管理|project.*management|敏捷|agile|scrum)",
                    r"(?i)(进度|deadline|里程碑|milestone)",
                ],
                responses=[
                    "项目管理的核心：\n1. 明确目标和范围\n2. 合理的任务拆分\n3. 风险评估和应对\n4. 持续沟通和同步\n5. 及时复盘总结\n\n你管理的是什么类型的项目？",
                    "保持项目进度的技巧：\n- 设定清晰的里程碑\n- 预留缓冲时间\n- 定期同步进展\n- 及时识别和解决阻塞\n- 使用合适的工具（Jira/Trello/飞书）\n\n项目目前遇到什么挑战？",
                ],
                priority=2
            ),
        ]
        self.domains["business"].extend(business_knowledge)
    
    def search(self, query: str, domain: Optional[str] = None) -> List[DomainKnowledge]:
        """
        搜索知识库
        
        Args:
            query: 查询内容
            domain: 限定领域（可选）
        
        Returns:
            匹配的知识单元列表
        """
        results = []
        domains_to_search = [domain] if domain else list(self.domains.keys())
        
        for d in domains_to_search:
            if d not in self.domains:
                continue
            for knowledge in self.domains[d]:
                for pattern in knowledge.patterns:
                    if re.search(pattern, query):
                        results.append(knowledge)
                        break
        
        # 按优先级排序
        results.sort(key=lambda x: x.priority, reverse=True)
        return results
    
    def get_response(self, query: str, domain: Optional[str] = None) -> Optional[str]:
        """
        获取回复
        
        Args:
            query: 用户查询
            domain: 限定领域
        
        Returns:
            匹配的回复或 None
        """
        matches = self.search(query, domain)
        if not matches:
            return None
        
        # 返回最高优先级知识的随机回复
        return random.choice(matches[0].responses)
    
    def add_knowledge(self, knowledge: DomainKnowledge):
        """添加新知识"""
        if knowledge.domain in self.domains:
            self.domains[knowledge.domain].append(knowledge)
        else:
            self.domains[knowledge.domain] = [knowledge]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        stats = {
            "total_domains": len(self.domains),
            "domains": {}
        }
        for domain, knowledge_list in self.domains.items():
            stats["domains"][domain] = {
                "count": len(knowledge_list),
                "total_patterns": sum(len(k.patterns) for k in knowledge_list),
                "total_responses": sum(len(k.responses) for k in knowledge_list),
            }
        return stats


# 全局知识库实例
_knowledge_base = None


def get_knowledge_base() -> ExtendedKnowledgeBase:
    """获取全局知识库实例"""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = ExtendedKnowledgeBase()
    return _knowledge_base
