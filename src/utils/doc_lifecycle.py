"""
文档生命周期管理系统
解决 AI 生成文档后不更新、不删除的问题
"""
import os
import json
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

REGISTRY_FILE = Path("docs/.doc_registry.json")

@dataclass
class DocumentMeta:
    """文档元数据"""
    doc_id: str
    path: str
    title: str
    task_id: str
    created_at: str
    ttl_days: int  # -1 表示永久
    status: str  # active, stale, archived, deleted
    doc_type: str  # analysis, design, learning, decision, config, standard
    related_files: List[Dict[str, str]]  # [{"path": "...", "hash": "..."}]
    auto_delete: bool
    last_verified_at: Optional[str] = None
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl_days < 0:
            return False
        created = datetime.fromisoformat(self.created_at)
        return datetime.now() - created > timedelta(days=self.ttl_days)
    
    def is_stale(self, current_file_hashes: Dict[str, str]) -> bool:
        """检查关联文件是否已变更"""
        for file_info in self.related_files:
            path = file_info["path"]
            old_hash = file_info["hash"]
            current_hash = current_file_hashes.get(path)
            if current_hash and current_hash != old_hash:
                return True
        return False


class DocumentLifecycleManager:
    """文档生命周期管理器"""
    
    # 文档类型默认配置
    DEFAULT_CONFIG = {
        "analysis": {"ttl_days": 7, "auto_delete": True},      # 分析报告
        "design": {"ttl_days": 14, "auto_delete": True},      # 设计方案
        "learning": {"ttl_days": 3, "auto_delete": True},     # 学习笔记
        "decision": {"ttl_days": -1, "auto_delete": False},   # 技术决策（永久）
        "config": {"ttl_days": -1, "auto_delete": False},     # 配置文档（永久）
        "standard": {"ttl_days": 30, "auto_delete": False},   # 规范标准
    }
    
    def __init__(self):
        self.registry: Dict[str, Any] = {"version": "1.0", "documents": {}}
        self._load_registry()
    
    def _load_registry(self):
        """加载注册表"""
        if REGISTRY_FILE.exists():
            try:
                with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
                    self.registry = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load doc registry: {e}")
    
    def _save_registry(self):
        """保存注册表"""
        try:
            REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(REGISTRY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.registry, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save doc registry: {e}")
    
    def _calc_file_hash(self, file_path: str) -> str:
        """计算文件哈希"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()[:8]
        except Exception:
            return ""
    
    def register_document(self, 
                         doc_path: str, 
                         title: str,
                         task_id: str,
                         doc_type: str,
                         related_files: List[str]) -> str:
        """
        注册新文档
        
        Args:
            doc_path: 文档路径
            title: 文档标题
            task_id: 关联任务ID
            doc_type: 文档类型 (analysis/design/learning/decision/config/standard)
            related_files: 关联的代码文件路径列表
        """
        doc_id = f"doc_{hashlib.md5(f'{doc_path}_{datetime.now()}'.encode()).hexdigest()[:8]}"
        
        # 获取类型配置
        config = self.DEFAULT_CONFIG.get(doc_type, {"ttl_days": 7, "auto_delete": True})
        
        # 计算关联文件哈希
        file_hashes = []
        for fpath in related_files:
            if os.path.exists(fpath):
                file_hashes.append({
                    "path": fpath,
                    "hash": self._calc_file_hash(fpath)
                })
        
        doc_meta = DocumentMeta(
            doc_id=doc_id,
            path=doc_path,
            title=title,
            task_id=task_id,
            created_at=datetime.now().isoformat(),
            ttl_days=config["ttl_days"],
            status="active",
            doc_type=doc_type,
            related_files=file_hashes,
            auto_delete=config["auto_delete"],
            last_verified_at=datetime.now().isoformat()
        )
        
        self.registry["documents"][doc_id] = asdict(doc_meta)
        self._save_registry()
        
        logger.info(f"Document registered: {doc_id} ({doc_path}), TTL={config['ttl_days']} days")
        return doc_id
    
    def check_file_changes(self, file_path: str) -> List[str]:
        """
        检查文件变更影响的文档
        
        Returns:
            需要更新的文档ID列表
        """
        affected_docs = []
        current_hash = self._calc_file_hash(file_path)
        
        for doc_id, doc_data in self.registry["documents"].items():
            if doc_data["status"] != "active":
                continue
                
            for file_info in doc_data.get("related_files", []):
                if file_info["path"] == file_path:
                    if file_info["hash"] != current_hash:
                        # 文件已变更，标记为 stale
                        doc_data["status"] = "stale"
                        affected_docs.append(doc_id)
                        logger.warning(f"Document {doc_id} marked as stale due to file change: {file_path}")
        
        if affected_docs:
            self._save_registry()
        
        return affected_docs
    
    def get_stale_documents(self) -> List[Dict]:
        """获取所有需要更新的文档"""
        stale_docs = []
        for doc_id, doc_data in self.registry["documents"].items():
            if doc_data["status"] == "stale":
                stale_docs.append(doc_data)
        return stale_docs
    
    def update_document(self, doc_id: str, related_files: List[str]):
        """更新文档（重新计算文件哈希）"""
        if doc_id not in self.registry["documents"]:
            return False
        
        doc_data = self.registry["documents"][doc_id]
        
        # 更新文件哈希
        file_hashes = []
        for fpath in related_files:
            if os.path.exists(fpath):
                file_hashes.append({
                    "path": fpath,
                    "hash": self._calc_file_hash(fpath)
                })
        
        doc_data["related_files"] = file_hashes
        doc_data["status"] = "active"
        doc_data["last_verified_at"] = datetime.now().isoformat()
        
        self._save_registry()
        logger.info(f"Document updated: {doc_id}")
        return True
    
    def cleanup_task_documents(self, task_id: str) -> Dict[str, List[str]]:
        """
        清理任务相关的文档
        
        Returns:
            {"deleted": [...], "archived": [...], "kept": [...]}
        """
        result = {"deleted": [], "archived": [], "kept": []}
        
        for doc_id, doc_data in list(self.registry["documents"].items()):
            if doc_data["task_id"] != task_id:
                continue
            
            if doc_data["auto_delete"]:
                # 自动删除
                doc_path = doc_data["path"]
                if os.path.exists(doc_path):
                    os.remove(doc_path)
                    logger.info(f"Auto-deleted document: {doc_path}")
                
                doc_data["status"] = "deleted"
                result["deleted"].append(doc_id)
            else:
                # 保留，更新验证时间
                doc_data["last_verified_at"] = datetime.now().isoformat()
                result["kept"].append(doc_id)
        
        self._save_registry()
        return result
    
    def periodic_cleanup(self) -> Dict[str, List[str]]:
        """定期清理过期文档"""
        result = {"expired": [], "orphaned": [], "kept": []}
        
        for doc_id, doc_data in list(self.registry["documents"].items()):
            doc = DocumentMeta(**doc_data)
            doc_path = doc_data["path"]
            
            # 检查过期
            if doc.is_expired():
                if doc_data["auto_delete"]:
                    if os.path.exists(doc_path):
                        os.remove(doc_path)
                    doc_data["status"] = "deleted"
                    result["expired"].append(doc_id)
                    logger.info(f"Deleted expired document: {doc_path}")
                else:
                    # 移动到 archive
                    archive_path = f"docs/archive/{os.path.basename(doc_path)}"
                    if os.path.exists(doc_path):
                        os.rename(doc_path, archive_path)
                    doc_data["status"] = "archived"
                    result["expired"].append(doc_id)
            
            # 检查孤立（关联文件已删除）
            elif doc_data["related_files"]:
                all_files_exist = all(
                    os.path.exists(f["path"]) 
                    for f in doc_data["related_files"]
                )
                if not all_files_exist:
                    if doc_data["auto_delete"]:
                        if os.path.exists(doc_path):
                            os.remove(doc_path)
                        doc_data["status"] = "deleted"
                        result["orphaned"].append(doc_id)
                        logger.info(f"Deleted orphaned document: {doc_path}")
        
        self._save_registry()
        return result
    
    def generate_report(self) -> str:
        """生成文档状态报告"""
        total = len(self.registry["documents"])
        active = sum(1 for d in self.registry["documents"].values() if d["status"] == "active")
        stale = sum(1 for d in self.registry["documents"].values() if d["status"] == "stale")
        expired = sum(1 for d in self.registry["documents"].values() if d["status"] == "deleted")
        
        report = f"""
📊 文档生命周期报告
═══════════════════════════════════
总文档数: {total}
✅ 正常: {active}
⚠️  待更新: {stale}
🗑️  已删除: {expired}
═══════════════════════════════════
"""
        
        if stale > 0:
            report += "\n⚠️  需要更新的文档:\n"
            for doc_id, doc_data in self.registry["documents"].items():
                if doc_data["status"] == "stale":
                    report += f"  - {doc_data['path']} ({doc_data['title']})\n"
        
        return report


# 全局实例
doc_lifecycle = DocumentLifecycleManager()
