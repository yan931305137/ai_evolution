"""
知识图谱系统 - Knowledge Graph System

实现结构化知识存储和推理能力，支持：
- 实体关系存储
- 知识推理
- 路径查询
- 知识融合
"""

import json
import re
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
import hashlib


@dataclass
class Entity:
    """知识图谱实体"""
    name: str
    type: str                      # 实体类型（人、组织、概念等）
    id: str = field(default="")   # 唯一ID（自动生成）
    properties: Dict[str, Any] = field(default_factory=dict)
    aliases: List[str] = field(default_factory=list)  # 别名
    
    def __post_init__(self):
        if not self.id:
            self.id = self._generate_id()
    
    def _generate_id(self) -> str:
        """生成唯一ID"""
        content = f"{self.name}:{self.type}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "properties": self.properties,
            "aliases": self.aliases,
        }


@dataclass
class Relation:
    """实体关系"""
    source_id: str                 # 源实体ID
    target_id: str                 # 目标实体ID
    relation_type: str             # 关系类型
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0        # 置信度
    
    def to_dict(self) -> Dict:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type,
            "properties": self.properties,
            "confidence": self.confidence,
        }


@dataclass
class KnowledgeTriple:
    """知识三元组 (Subject, Predicate, Object)"""
    subject: str
    predicate: str
    object: str
    confidence: float = 1.0
    
    def to_dict(self) -> Dict:
        return {
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "confidence": self.confidence,
        }


class KnowledgeGraph:
    """
    知识图谱
    
    功能：
    1. 实体管理（增删改查）
    2. 关系管理
    3. 知识推理（路径查询、关联发现）
    4. 知识融合（实体对齐）
    """
    
    def __init__(self, name: str = "default"):
        self.name = name
        self.entities: Dict[str, Entity] = {}          # id -> Entity
        self.relations: Dict[str, List[Relation]] = defaultdict(list)  # entity_id -> relations
        self.entity_name_index: Dict[str, str] = {}    # name -> entity_id
        self.entity_type_index: Dict[str, Set[str]] = defaultdict(set)  # type -> entity_ids
        
        # 预定义关系类型
        self.relation_types = {
            "is_a": "是一个",
            "part_of": "是...的一部分",
            "has_property": "具有属性",
            "related_to": "相关于",
            "causes": "导致",
            "depends_on": "依赖于",
            "uses": "使用",
            "created_by": "被创建",
            "located_in": "位于",
            "knows": "认识",
            "works_for": "工作于",
            "studies": "学习",
            "teaches": "教授",
        }
        
        self._load_initial_knowledge()
    
    def _load_initial_knowledge(self):
        """加载初始知识"""
        # 编程语言知识
        self._add_programming_knowledge()
        # 常见概念知识
        self._add_common_concepts()
    
    def _add_programming_knowledge(self):
        """添加编程语言相关知识"""
        # 编程语言实体
        languages = [
            Entity(name="Python", type="programming_language", 
                   properties={"paradigm": "multi-paradigm", "typed": "dynamic"},
                   aliases=["py", "python3"]),
            Entity(name="JavaScript", type="programming_language",
                   properties={"paradigm": "multi-paradigm", "typed": "dynamic"},
                   aliases=["js", "nodejs"]),
            Entity(name="Java", type="programming_language",
                   properties={"paradigm": "object-oriented", "typed": "static"}),
            Entity(name="Go", type="programming_language",
                   properties={"paradigm": "procedural", "typed": "static"},
                   aliases=["golang"]),
            Entity(name="Rust", type="programming_language",
                   properties={"paradigm": "multi-paradigm", "typed": "static"}),
        ]
        
        for lang in languages:
            self.add_entity(lang)
        
        # 概念实体
        concepts = [
            Entity(name="Object-Oriented Programming", type="programming_paradigm",
                   aliases=["OOP", "面向对象"]),
            Entity(name="Functional Programming", type="programming_paradigm",
                   aliases=["FP", "函数式编程"]),
            Entity(name="Machine Learning", type="field",
                   aliases=["ML", "机器学习"]),
            Entity(name="Deep Learning", type="field",
                   aliases=["DL", "深度学习"]),
        ]
        
        for concept in concepts:
            self.add_entity(concept)
        
        # 关系
        relations = [
            ("Python", "is_a", "programming_language"),
            ("Python", "supports", "Object-Oriented Programming"),
            ("Python", "supports", "Functional Programming"),
            ("Python", "used_for", "Machine Learning"),
            ("Deep Learning", "is_a", "Machine Learning"),
            ("JavaScript", "is_a", "programming_language"),
            ("Java", "is_a", "programming_language"),
        ]
        
        for subj, pred, obj in relations:
            subj_id = self.entity_name_index.get(subj)
            obj_id = self.entity_name_index.get(obj)
            if subj_id and obj_id:
                self.add_relation(subj_id, obj_id, pred)
    
    def _add_common_concepts(self):
        """添加常见概念知识"""
        concepts = [
            # 学习方法
            Entity(name="Spaced Repetition", type="learning_method",
                   properties={"effectiveness": "high"},
                   aliases=["间隔重复"]),
            Entity(name="Feynman Technique", type="learning_method",
                   properties={"effectiveness": "high"},
                   aliases=["费曼技巧"]),
            
            # 时间管理
            Entity(name="Pomodoro Technique", type="time_management",
                   properties={"duration": "25 minutes"},
                   aliases=["番茄工作法"]),
            Entity(name="Time Blocking", type="time_management",
                   aliases=["时间块"]),
            
            # 健康
            Entity(name="Meditation", type="wellness",
                   properties={"benefits": ["stress_reduction", "focus"]},
                   aliases=["冥想", "正念"]),
            Entity(name="Exercise", type="wellness",
                   properties={"benefits": ["health", "mood", "energy"]},
                   aliases=["运动", "锻炼"]),
        ]
        
        for concept in concepts:
            self.add_entity(concept)
    
    # ==================== 实体管理 ====================
    
    def add_entity(self, entity: Entity) -> str:
        """
        添加实体
        
        Returns:
            实体ID
        """
        self.entities[entity.id] = entity
        self.entity_name_index[entity.name] = entity.id
        self.entity_name_index[entity.name.lower()] = entity.id
        
        # 索引别名
        for alias in entity.aliases:
            self.entity_name_index[alias] = entity.id
            self.entity_name_index[alias.lower()] = entity.id
        
        # 类型索引
        self.entity_type_index[entity.type].add(entity.id)
        
        return entity.id
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """根据ID获取实体"""
        return self.entities.get(entity_id)
    
    def get_entity_by_name(self, name: str) -> Optional[Entity]:
        """根据名称获取实体"""
        entity_id = self.entity_name_index.get(name) or self.entity_name_index.get(name.lower())
        if entity_id:
            return self.entities.get(entity_id)
        return None
    
    def get_entities_by_type(self, entity_type: str) -> List[Entity]:
        """根据类型获取实体列表"""
        entity_ids = self.entity_type_index.get(entity_type, set())
        return [self.entities[eid] for eid in entity_ids if eid in self.entities]
    
    def update_entity(self, entity_id: str, properties: Dict[str, Any]):
        """更新实体属性"""
        if entity_id in self.entities:
            self.entities[entity_id].properties.update(properties)
    
    def remove_entity(self, entity_id: str):
        """删除实体及其关系"""
        if entity_id in self.entities:
            entity = self.entities[entity_id]
            
            # 删除名称索引
            del self.entity_name_index[entity.name]
            for alias in entity.aliases:
                if alias in self.entity_name_index:
                    del self.entity_name_index[alias]
            
            # 删除类型索引
            self.entity_type_index[entity.type].discard(entity_id)
            
            # 删除相关关系
            if entity_id in self.relations:
                del self.relations[entity_id]
            
            # 删除其他实体指向该实体的关系
            for entity_relations in self.relations.values():
                entity_relations[:] = [
                    r for r in entity_relations if r.target_id != entity_id
                ]
            
            # 删除实体
            del self.entities[entity_id]
    
    # ==================== 关系管理 ====================
    
    def add_relation(self, source_id: str, target_id: str, 
                     relation_type: str, properties: Dict = None,
                     confidence: float = 1.0) -> Relation:
        """添加关系"""
        relation = Relation(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            properties=properties or {},
            confidence=confidence
        )
        self.relations[source_id].append(relation)
        return relation
    
    def get_relations(self, entity_id: str, relation_type: Optional[str] = None) -> List[Relation]:
        """获取实体的关系"""
        relations = self.relations.get(entity_id, [])
        if relation_type:
            relations = [r for r in relations if r.relation_type == relation_type]
        return relations
    
    def get_related_entities(self, entity_id: str, 
                            relation_type: Optional[str] = None) -> List[Tuple[Entity, str]]:
        """
        获取相关实体
        
        Returns:
            [(Entity, relation_type), ...]
        """
        relations = self.get_relations(entity_id, relation_type)
        results = []
        for relation in relations:
            target = self.entities.get(relation.target_id)
            if target:
                results.append((target, relation.relation_type))
        return results
    
    # ==================== 知识推理 ====================
    
    def find_path(self, start_id: str, end_id: str, 
                  max_depth: int = 5) -> Optional[List[Relation]]:
        """
        查找两个实体之间的路径（BFS）
        
        Returns:
            关系路径列表，如果无路径则返回 None
        """
        if start_id not in self.entities or end_id not in self.entities:
            return None
        
        if start_id == end_id:
            return []
        
        visited = {start_id}
        queue = deque([(start_id, [])])
        
        while queue:
            current_id, path = queue.popleft()
            
            if len(path) >= max_depth:
                continue
            
            for relation in self.relations.get(current_id, []):
                next_id = relation.target_id
                new_path = path + [relation]
                
                if next_id == end_id:
                    return new_path
                
                if next_id not in visited:
                    visited.add(next_id)
                    queue.append((next_id, new_path))
        
        return None
    
    def find_related_concepts(self, entity_name: str, 
                              depth: int = 2) -> List[Tuple[str, int]]:
        """
        查找相关概念
        
        Returns:
            [(concept_name, distance), ...]
        """
        entity = self.get_entity_by_name(entity_name)
        if not entity:
            return []
        
        results = []
        visited = {entity.id: 0}
        queue = deque([(entity.id, 0)])
        
        while queue:
            current_id, current_depth = queue.popleft()
            
            if current_depth >= depth:
                continue
            
            for relation in self.relations.get(current_id, []):
                next_id = relation.target_id
                next_depth = current_depth + 1
                
                if next_id not in visited or visited[next_id] > next_depth:
                    visited[next_id] = next_depth
                    queue.append((next_id, next_depth))
                    
                    target_entity = self.entities.get(next_id)
                    if target_entity:
                        results.append((target_entity.name, next_depth))
        
        return results
    
    def infer_relation(self, entity1_name: str, entity2_name: str) -> Optional[str]:
        """
        推理两个实体之间的关系
        
        简单的基于路径的推理
        """
        entity1 = self.get_entity_by_name(entity1_name)
        entity2 = self.get_entity_by_name(entity2_name)
        
        if not entity1 or not entity2:
            return None
        
        # 直接查找路径
        path = self.find_path(entity1.id, entity2.id, max_depth=3)
        if path:
            relations = [r.relation_type for r in path]
            return " → ".join(relations)
        
        # 查找共同邻居（有共同关联的实体）
        common_neighbors = self._find_common_neighbors(entity1.id, entity2.id)
        if common_neighbors:
            neighbor_names = [self.entities[nid].name for nid in common_neighbors[:3]]
            return f"通过 {', '.join(neighbor_names)} 相关联"
        
        return None
    
    def _find_common_neighbors(self, entity1_id: str, entity2_id: str) -> List[str]:
        """查找共同邻居"""
        neighbors1 = set()
        neighbors2 = set()
        
        # 获取entity1的邻居
        for relation in self.relations.get(entity1_id, []):
            neighbors1.add(relation.target_id)
        
        # 获取指向entity1的实体
        for entity_id, relations in self.relations.items():
            for relation in relations:
                if relation.target_id == entity1_id:
                    neighbors1.add(entity_id)
        
        # 获取entity2的邻居
        for relation in self.relations.get(entity2_id, []):
            neighbors2.add(relation.target_id)
        
        # 获取指向entity2的实体
        for entity_id, relations in self.relations.items():
            for relation in relations:
                if relation.target_id == entity2_id:
                    neighbors2.add(entity_id)
        
        return list(neighbors1 & neighbors2)
    
    # ==================== 查询接口 ====================
    
    def query(self, query_text: str) -> Dict[str, Any]:
        """
        自然语言查询
        
        支持简单查询模式：
        - "什么是 X"
        - "X 和 Y 的关系"
        - "X 的相关概念"
        """
        result = {
            "query": query_text,
            "matches": [],
            "inferred": None,
        }
        
        # 提取实体名
        # 模式1: 什么是 X
        what_is_match = re.search(r"什么是\s+(.+)", query_text)
        if what_is_match:
            entity_name = what_is_match.group(1).strip()
            entity = self.get_entity_by_name(entity_name)
            if entity:
                result["matches"].append({
                    "type": "entity",
                    "entity": entity.to_dict(),
                    "relations": [
                        r.to_dict() for r in self.get_relations(entity.id)
                    ]
                })
        
        # 模式2: X 和 Y 的关系
        relation_match = re.search(r"(.+?)\s+和\s+(.+?)\s+的关系", query_text)
        if relation_match:
            entity1 = relation_match.group(1).strip()
            entity2 = relation_match.group(2).strip()
            inferred = self.infer_relation(entity1, entity2)
            if inferred:
                result["inferred"] = inferred
        
        return result
    
    def get_knowledge_summary(self, entity_name: str) -> Optional[str]:
        """
        获取实体的知识摘要
        """
        entity = self.get_entity_by_name(entity_name)
        if not entity:
            return None
        
        summary_parts = [f"{entity.name} 是一个 {entity.type}。"]
        
        # 添加属性
        if entity.properties:
            props = ", ".join([f"{k}={v}" for k, v in entity.properties.items()])
            summary_parts.append(f"属性: {props}")
        
        # 添加关系
        relations = self.get_relations(entity.id)
        if relations:
            relation_strs = []
            for relation in relations[:5]:  # 最多5个
                target = self.entities.get(relation.target_id)
                if target:
                    relation_strs.append(f"{relation.relation_type} {target.name}")
            if relation_strs:
                summary_parts.append("关系: " + ", ".join(relation_strs))
        
        return " ".join(summary_parts)
    
    # ==================== 持久化 ====================
    
    def save(self, filepath: str):
        """保存知识图谱到文件"""
        data = {
            "name": self.name,
            "entities": {eid: e.to_dict() for eid, e in self.entities.items()},
            "relations": {
                eid: [r.to_dict() for r in relations]
                for eid, relations in self.relations.items()
            },
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load(self, filepath: str):
        """从文件加载知识图谱"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.name = data.get("name", "default")
        
        # 加载实体
        for eid, entity_data in data.get("entities", {}).items():
            entity = Entity(
                id=entity_data["id"],
                name=entity_data["name"],
                type=entity_data["type"],
                properties=entity_data.get("properties", {}),
                aliases=entity_data.get("aliases", []),
            )
            self.add_entity(entity)
        
        # 加载关系
        for source_id, relations_data in data.get("relations", {}).items():
            for relation_data in relations_data:
                self.add_relation(
                    source_id=relation_data["source_id"],
                    target_id=relation_data["target_id"],
                    relation_type=relation_data["relation_type"],
                    properties=relation_data.get("properties", {}),
                    confidence=relation_data.get("confidence", 1.0)
                )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "name": self.name,
            "entity_count": len(self.entities),
            "relation_count": sum(len(r) for r in self.relations.values()),
            "entity_types": {
                t: len(ids) for t, ids in self.entity_type_index.items()
            },
        }


# 全局知识图谱实例
_knowledge_graph = None


def get_knowledge_graph() -> KnowledgeGraph:
    """获取全局知识图谱实例"""
    global _knowledge_graph
    if _knowledge_graph is None:
        _knowledge_graph = KnowledgeGraph()
    return _knowledge_graph
