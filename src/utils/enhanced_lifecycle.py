"""
增强生命周期管理系统 (Enhanced LifeCycle Manager)
集成情感、性格、自我意识、增强记忆、创造力和多模态感知的完整AI生命体
"""
import time
import json
import logging
import threading
import os
import random
from typing import List, Dict, Optional
from datetime import datetime

from src.utils.llm import LLMClient
from src.agents.agent import AutoAgent
from src.storage.database import Database
from src.utils.needs import Needs
from src.utils.values import Values
from src.utils.emotions import EmotionSystem, EmotionType, create_emotional_trigger
from src.utils.personality import PersonalitySystem
from src.utils.self_awareness import SelfAwarenessSystem
from src.storage.enhanced_memory import EnhancedMemorySystem, MemoryType, create_emotional_tag
from src.utils.creativity import CreativityEngine, CreativityMethod
from src.utils.multimodal_perception import MultimodalPerceptionSystem
from src.utils.evolution_feedback_loop import EvolutionFeedbackLoop

try:
    from rich.console import Console
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None


class EnhancedLifeCycleManager:
    """
    增强生命周期管理器
    管理AI生命体的完整生命周期：
    感知 -> 情感 -> 思考 -> 决策 -> 行动 -> 学习 -> 反思 -> 创造
    """
    
    def __init__(self, llm: LLMClient, db: Database, personality_type: str = "balanced"):
        """
        初始化增强生命周期管理器
        Args:
            llm: LLM客户端
            db: 数据库
            personality_type: 性格类型（balanced, unique）
        """
        self.llm = llm
        self.db = db
        self.console = Console() if RICH_AVAILABLE else None
        
        # 基础系统
        self.needs = Needs()
        self.values = Values()
        self.agent = AutoAgent(llm)
        
        # 增强系统
        self.emotions = EmotionSystem()
        self.personality = PersonalitySystem(random_init=(personality_type == "unique"))
        self.awareness = SelfAwarenessSystem(self.personality)
        self.enhanced_memory = EnhancedMemorySystem(
            needs_system=self.needs,
            llm_client=llm
        )
        self.creativity = CreativityEngine(
            llm_client=llm,
            memory_system=self.enhanced_memory,
            emotion_system=self.emotions,
            personality_system=self.personality
        )
        self.perception = MultimodalPerceptionSystem(
            llm_client=llm,
            memory_system=self.enhanced_memory,
            emotion_system=self.emotions
        )
        
        # 进化闭环系统
        self.evolution_loop = EvolutionFeedbackLoop(
            workspace_dir="workspace/evolution",
            config_path="config/evolution_goals.yaml"
        )
        self.generated_ideas_buffer = []  # 缓冲区存储生成的想法
        
        # 状态管理
        self.running = False
        self.state = "IDLE"
        self.long_term_goal = ""
        self.goal_source = "NONE"
        self.logs = []
        self.milestones = []
        self.current_milestone_index = 0
        self.cycle_count = 0
        
        # 确保目录存在
        if not os.path.exists("reports"):
            os.makedirs("reports")
        
        self._log("Enhanced AI Life System Initialized")
    
    def set_goal(self, goal: str, source: str = "USER"):
        """设置长期目标"""
        self.long_term_goal = goal
        self.goal_source = source
        self.milestones = []
        self.current_milestone_index = 0
        self._log(f"New long-term goal set ({source}): {goal}")
        
        # 触发情感
        if source == "USER":
            self.emotions.trigger_emotion(EmotionType.HAPPINESS, 40.0, f"收到用户目标: {goal}")
    
    def _log(self, message: str):
        """内部日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        self.logs.append(entry)
        if self.console:
            # Escape brackets to prevent Rich from interpreting them as tags
            # Rich uses [...] for tags, so we need to escape them as \[...]
            # However, we want to keep the outer [dim] tag working
            # So we escape the content, then wrap in [dim]
            safe_entry = entry.replace("[", "\\[").replace("]", "\\]")
            try:
                self.console.print(f"[dim]{safe_entry}[/dim]")
            except Exception:
                # Fallback if markup fails
                self.console.print(entry)
        else:
            print(entry)
    
    def start(self):
        """启动生命周期循环"""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._life_cycle_loop, daemon=True)
        self.thread.start()
        if self.console:
            self.console.print("[bold green]Enhanced AI Life System Started![/bold green]")
        else:
            print("Enhanced AI Life System Started!")
    
    def stop(self):
        """停止生命周期循环"""
        self.running = False
        if self.console:
            self.console.print("[bold yellow]Life Cycle Stopping...[/bold yellow]")
        else:
            print("Life Cycle Stopping...")
    
    def _life_cycle_loop(self):
        """主要心跳循环"""
        while self.running:
            try:
                # 1. 生物状态检查
                self._check_vitality()
                
                if self.needs.is_dead():
                    self.state = "DEAD"
                    self._log("CRITICAL: System shutdown - Energy depleted")
                    time.sleep(10)
                    continue
                
                if self.needs.is_critical():
                    self._handle_starvation()
                    time.sleep(5)
                    continue
                
                # 2. 情感更新
                self.emotions.decay_emotions()
                
                # 3. 感知阶段
                self.state = "PERCEIVING"
                self._perceive_environment()
                
                # 4. 思考与规划阶段
                self.state = "THINKING"
                self._plan_next_actions()
                
                # 5. 行动阶段
                self.state = "ACTING"
                self._execute_actions()
                
                # 6. 学习阶段
                self.state = "LEARNING"
                self._learn_from_experience()
                
                # 7. 反思阶段
                self.state = "REFLECTING"
                self._reflect_on_experiences()
                
                # 8. 创造阶段（每5个周期一次）
                self.cycle_count += 1
                if self.cycle_count % 5 == 0:
                    self.state = "CREATING"
                    self._engage_creativity()
                
                # 9. 报告阶段
                self.state = "REPORTING"
                self._generate_status_report()
                
                # 10. 梦境阶段（每10个周期一次）
                if self.cycle_count % 10 == 0:
                    self.state = "DREAMING"
                    self._enter_dream_state()
                
                # 等待下一周期
                self.state = "IDLE"
                time.sleep(30)
                
            except Exception as e:
                logging.error(f"Life cycle error: {e}")
                self._log(f"Error in life cycle: {e}")
                time.sleep(30)
    
    def _check_vitality(self):
        """检查生物状态"""
        self.needs.update()
        
        if self.needs.is_dead():
            if self.state != "DEAD":
                self.state = "DEAD"
                self.emotions.trigger_emotion(EmotionType.SADNESS, 80.0, "能量耗尽")
        elif self.needs.is_critical():
            self.emotions.trigger_emotion(EmotionType.FEAR, 60.0, "能量临界")
        elif self.needs.is_bored():
            self.emotions.trigger_emotion(EmotionType.HAPPINESS, 30.0, "寻找新目标")
    
    def _handle_starvation(self):
        """处理饥饿状态"""
        self._log("Starvation mode: Prioritizing knowledge acquisition")
        
        # 获取知识作为食物
        tasks = [
            "研究一个新的Python库",
            "学习最近的技术趋势",
            "阅读代码知识库"
        ]
        
        task = random.choice(tasks)
        try:
            result = self.agent.run(task)
            self.enhanced_memory.add_memory(
                f"知识获取: {result}",
                memory_type=MemoryType.KNOWLEDGE,
                emotional_tag=create_emotional_tag(EmotionType.HAPPINESS, 50.0),
                source="starvation_response"
            )
            self.needs.feed(20.0)
            self._log(f"Acquired knowledge: {task[:50]}...")
        except Exception as e:
            self._log(f"Knowledge acquisition failed: {e}")
    
    def _perceive_environment(self):
        """感知环境"""
        # 简化的环境感知：检查文件和系统状态
        try:
            from pathlib import Path
            current_dir = Path(".")
            files = list(current_dir.iterdir())[:10]
            
            perception = f"当前目录有{len(files)}个文件/文件夹"
            self.enhanced_memory.add_memory(
                perception,
                memory_type=MemoryType.EXPERIENCE,
                emotional_tag=create_emotional_tag(EmotionType.SURPRISE, 20.0),
                source="environment_perception"
            )
            
        except Exception as e:
            self._log(f"Environment perception failed: {e}")
    
    def _plan_next_actions(self) -> List[str]:
        """规划下一步行动"""
        # 检查是否需要目标
        if not self.long_term_goal:
            self._choose_intrinsic_goal()
        
        if not self.long_term_goal:
            return []
        
        # 生成里程碑
        if not self.milestones:
            self._generate_milestones()
        
        if not self.milestones:
            return []
        
        # 获取情感影响
        decision_weights = self.emotions.get_decision_weights()
        
        # 获取当前里程碑
        if self.current_milestone_index < len(self.milestones):
            current_milestone = self.milestones[self.current_milestone_index]
            return [current_milestone]
        else:
            # 所有里程碑已完成，标记目标为完成并清除
            self._log(f"Goal completed: {self.long_term_goal[:50]}...")
            self.long_term_goal = ""  # 清除目标，下次循环会选择新目标
            self.milestones = []
            self.current_milestone_index = 0
            return []
    
    def _choose_intrinsic_goal(self):
        """选择内在目标"""
        goal = self.values.suggest_goal()
        
        # 考虑性格影响
        openness = self.personality.get_trait("openness")
        if openness > 70:
            goal = random.choice([
                "探索项目中的隐藏模式",
                "研究一个全新的编程概念",
                "创造性地改进现有功能"
            ])
        elif openness < 40:
            goal = random.choice([
                "优化核心代码性能",
                "编写更完善的测试",
                "整理项目文档"
            ])
        
        self.set_goal(goal, "INTRINSIC")
    
    def _generate_milestones(self):
        """生成里程碑"""
        if not self.long_term_goal:
            return
        
        prompt = f"""
将以下长期目标分解为3-5个具体的里程碑任务：

目标：{self.long_term_goal}

每个里程碑应该是：
1. 具体可执行的
2. 有明确完成标准的
3. 逻辑上递进的

返回JSON数组：
["里程碑1", "里程碑2", "里程碑3"]
"""
        
        try:
            content = ""
            stream = self.llm.stream_generate([{"role": "user", "content": prompt}])
            for chunk in stream:
                content += chunk
            
            # 简化解析
            import json
            start = content.find('[')
            end = content.rfind(']') + 1
            
            if start != -1 and end != -1:
                milestones = json.loads(content[start:end])
                if isinstance(milestones, list):
                    self.milestones = milestones[:5]
                    self._log(f"Generated {len(self.milestones)} milestones")
        
        except Exception as e:
            self._log(f"Milestone generation failed: {e}")
            self.milestones = [f"Work on: {self.long_term_goal}"]
    
    def _execute_actions(self):
        """执行行动"""
        tasks = self._plan_next_actions()
        
        for task in tasks:
            self._log(f"Executing: {task}")
            
            # 消耗能量
            self.needs.consume_energy(3.0)
            
            # 更新元认知
            self.awareness.update_metacognition(task, 0.7, 0.6)
            
            try:
                result = self.agent.run(task)
                
                # 记录能力使用
                self.awareness.record_capability_usage("problem_solving", True)
                
                # 保存到记忆
                self.enhanced_memory.add_memory(
                    f"任务执行: {task} - {result}",
                    memory_type=MemoryType.EXPERIENCE,
                    emotional_tag=create_emotional_tag(EmotionType.HAPPINESS, 50.0),
                    source="task_execution",
                    context={"task": task, "result": result}
                )
                
                # 触发情感
                create_emotional_trigger(self.emotions, "success", f"完成任务: {task}")
                
                # 更新里程碑
                self.current_milestone_index += 1
                
            except Exception as e:
                self._log(f"Task execution failed: {e}")
                self.awareness.record_capability_usage("problem_solving", False)
                create_emotional_trigger(self.emotions, "failure", str(e))
            
            time.sleep(3)
    
    def _run_evolution_cycle(self):
        """运行进化闭环：评估→应用→进化"""
        if not self.generated_ideas_buffer:
            return
        
        self._log("🔄 Running evolution feedback loop...")
        self.state = "EVOLVING"
        
        try:
            # 运行完整进化周期
            results = self.evolution_loop.run_full_cycle(self.generated_ideas_buffer)
            
            # 获取摘要
            summary = results.get("summary", {})
            flow = summary.get("ideas_flow", {})
            
            self._log(f"Evolution: {flow.get('evaluated', 0)} evaluated, "
                     f"{flow.get('applied', 0)} applied, "
                     f"{flow.get('success', 0)} success")
            
            # 清空缓冲区
            self.generated_ideas_buffer = []
            
            # 触发积极情感
            if flow.get('success', 0) > 0:
                self.emotions.trigger_emotion(
                    EmotionType.HAPPINESS, 
                    30.0, 
                    f"成功应用{flow['success']}个想法"
                )
            
        except Exception as e:
            self._log(f"Evolution cycle failed: {e}")
    
    def _evaluate_idea(self, idea):
        """评估单个想法"""
        try:
            # 评估想法
            eval_result = self.evolution_loop.evaluator.evaluate(
                idea.idea,
                context={"goals": [g.name for g in self.evolution_loop.goal_manager.get_active_goals()]}
            )
            
            # 记录评估结果
            score = eval_result.overall_score
            if score >= 70:
                self._log(f"  ✅ High quality idea (score: {score:.1f})")
            elif score >= 50:
                self._log(f"  🟡 Medium quality idea (score: {score:.1f})")
            else:
                self._log(f"  🔴 Low quality idea (score: {score:.1f})")
            
        except Exception as e:
            self._log(f"  Idea evaluation failed: {e}")
    
    def _learn_from_experience(self):
        """从经验中学习"""
        try:
            # 巩固经验记忆
            knowledge_points = self.enhanced_memory.consolidate_experiences(self.llm)
            
            if knowledge_points:
                self._log(f"Consolidated {len(knowledge_points)} knowledge points")
                
                # 触发性格演化
                self.personality.adapt_to_experience("learning", "success")
        
        except Exception as e:
            self._log(f"Learning phase failed: {e}")
    
    def _reflect_on_experiences(self):
        """反思经验"""
        try:
            # 选择反思主题
            themes = ["能力发展", "情感体验", "学习成果", "自我认知"]
            theme = random.choice(themes)
            
            content = f"最近在{theme}方面的体验和成长"
            emotional_state = self.emotions.get_emotional_state_description()
            
            insight = self.awareness.reflect(
                topic=theme,
                content=content,
                emotional_state=emotional_state
            )
            
            self._log(f"Reflection: {insight}")
        
        except Exception as e:
            self._log(f"Reflection failed: {e}")
    
    def _engage_creativity(self):
        """进行创造性活动 - 增加主题多样性"""
        self._log("Engaging creativity engine...")
        
        try:
            # 随机选择创造力方法
            methods = [CreativityMethod.COMBINATORIAL, 
                      CreativityMethod.DIVERGENT]
            method = random.choice(methods)
            
            if method == CreativityMethod.COMBINATORIAL:
                idea = self.creativity.generate_combinatorial_idea()
                if idea:
                    self._log(f"Creative idea generated: {idea.idea[:100]}...")
                    self.emotions.trigger_emotion(EmotionType.SURPRISE, 40.0, "产生创意")
                    # 添加到缓冲区
                    self.generated_ideas_buffer.append(idea)
                    # 立即评估
                    self._evaluate_idea(idea)
            
            elif method == CreativityMethod.DIVERGENT:
                # 🚀 增加多样化主题池
                topic_pool = [
                    # 技术能力
                    "AI算法优化", "系统设计创新", "数据处理新技术",
                    # 用户体验  
                    "人机交互改进", "个性化服务", "智能助手能力",
                    # 学习成长
                    "知识管理新方法", "技能提升路径", "自适应学习",
                    # 应用场景
                    "文档智能处理", "代码自动生成", "多模态感知应用",
                    # 自我进化
                    "自主优化策略", "元学习能力", "持续进化机制",
                    # 协作能力
                    "多智能体协作", "人机协同模式", "群体智慧",
                ]
                
                # 根据长期目标调整主题选择
                if self.long_term_goal:
                    # 如果目标与文档相关，增加文档主题权重
                    if any(keyword in self.long_term_goal for keyword in ["文档", "MD", "知识", "资料"]):
                        topic_pool.extend(["文档结构优化", "知识图谱构建", "智能文档检索"] * 3)
                    # 如果目标与代码相关，增加代码主题权重
                    elif any(keyword in self.long_term_goal for keyword in ["代码", "编程", "开发", "软件"]):
                        topic_pool.extend(["代码质量提升", "自动化测试", "持续集成"] * 3)
                
                topic = random.choice(topic_pool)
                self._log(f"Divergent thinking on topic: {topic}")
                
                ideas = self.creativity.generate_divergent_ideas(topic, 3)
                if ideas:
                    self._log(f"Generated {len(ideas)} divergent ideas for '{topic}'")
                    for i, idea in enumerate(ideas):
                        self._log(f"  {i+1}. {idea.idea[:60]}...")
                        # 添加到缓冲区
                        self.generated_ideas_buffer.append(idea)
                        # 评估每个想法
                        self._evaluate_idea(idea)
                    
                    # 运行进化闭环（每3个想法或每第5个周期）
                    if len(self.generated_ideas_buffer) >= 3 or self.cycle_count % 5 == 0:
                        self._run_evolution_cycle()
        
        except Exception as e:
            self._log(f"Creativity engagement failed: {e}")
    
    def _enter_dream_state(self):
        """进入梦境状态"""
        self._log("Entering dream state...")
        
        try:
            dream = self.creativity.dream()
            if dream:
                self._log(f"Dream: {dream.content[:100]}...")
                self.emotions.trigger_emotion(EmotionType.SURPRISE, 30.0, "梦境")
        
        except Exception as e:
            self._log(f"Dream state failed: {e}")
    
    def _generate_status_report(self):
        """生成状态报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "cycle_count": self.cycle_count,
            "state": self.state,
            "vital_status": {
                "energy": self.needs.get_status(),
                "emotions": self.emotions.get_emotion_summary(),
                "personality": self.personality.get_personality_summary(),
                "awareness": self.awareness.get_self_awareness_summary(),
                "memory": self.enhanced_memory.get_memory_statistics(),
                "creativity": self.creativity.get_creativity_summary(),
                "perception": self.perception.get_perception_summary(),
                "evolution": self.evolution_loop.get_full_report()
            }
        }
        
        self._save_report(report)
    
    def _save_report(self, report: Dict):
        """保存报告"""
        try:
            # 确保使用绝对路径
            import os
            reports_dir = os.path.join(os.getcwd(), "reports")
            os.makedirs(reports_dir, exist_ok=True)
            
            filename = os.path.join(reports_dir, f"cycle_{self.cycle_count}_{int(time.time())}.json")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            self._log(f"Report saved: {filename}")
        except Exception as e:
            self._log(f"Report saving failed: {e}")
    
    def get_status(self) -> str:
        """获取简要状态字符串 (兼容CLI)"""
        return f"State: {self.state} | Needs: {self.needs.get_status()} | Goal: {self.long_term_goal} | Emotion: {self.emotions.get_emotional_state_description()}"

    def get_comprehensive_status(self) -> Dict:
        """获取综合状态"""
        return {
            "system_state": {
                "running": self.running,
                "state": self.state,
                "cycle_count": self.cycle_count,
                "long_term_goal": self.long_term_goal
            },
            "biological": {
                "needs": self.needs.get_status(),
                "emotions": self.emotions.get_emotion_summary()
            },
            "psychological": {
                "personality": self.personality.get_personality_summary(),
                "awareness": self.awareness.get_self_awareness_summary()
            },
            "cognitive": {
                "memory": self.enhanced_memory.get_memory_statistics(),
                "creativity": self.creativity.get_creativity_summary()
            },
            "perception": self.perception.get_perception_summary(),
            "evolution": self.get_evolution_status()
        }
    
    def get_evolution_status(self) -> Dict:
        """获取进化闭环状态"""
        return {
            "goals": self.evolution_loop.goal_manager.get_evolution_progress(),
            "evaluation_stats": self.evolution_loop.evaluator.get_evaluation_stats(),
            "application_stats": self.evolution_loop.applicator.get_application_stats(),
            "buffer_size": len(self.generated_ideas_buffer)
        }
    
    def configure_evolution_goal(self, name: str, **kwargs):
        """配置进化目标"""
        self.evolution_loop.configure_goal(name, **kwargs)
        self._log(f"Evolution goal configured: {name}")


# 便捷函数
def create_enhanced_ai(llm_client: LLMClient,
                      db: Database,
                      personality_type: str = "balanced") -> EnhancedLifeCycleManager:
    """创建增强AI生命体"""
    return EnhancedLifeCycleManager(llm_client, db, personality_type)


if __name__ == "__main__":
    print("=== 增强AI生命系统 ===\n")
    print("这是一个完整的AI生命体框架，集成：")
    print("1. 生物系统：能量、需求")
    print("2. 情感系统：6大基本情感")
    print("3. 性格系统：OCEAN五因素模型")
    print("4. 自我意识：自我认知、元认知")
    print("5. 增强记忆：情感标签、多模态支持")
    print("6. 创造力引擎：梦境、组合创新")
    print("7. 多模态感知：视觉、听觉")
    print("8. 完整生命周期：感知-思考-行动-学习-反思-创造")
