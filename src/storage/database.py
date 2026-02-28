import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from src.utils.config import cfg
from src.utils.constants import DB_FILE

class Database:
    """Manages the local database for storing conversation history and training data."""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = cfg.get("database.path", str(DB_FILE))
            
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(str(self.db_path))
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        """Create necessary tables if they don't exist."""
        # Conversation history table (for RAG and evolution)
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instruction TEXT,
            input TEXT,
            output TEXT,
            feedback TEXT,
            rating INTEGER DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            model_used TEXT
        )
        ''')
        
        # Metadata table (for tracking evolution progress)
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        ''')
        self.conn.commit()

    def save_conversation(self, input_text: str, output_text: str, instruction: str = "", model_used: str = "unknown"):
        """Save a conversation turn to the database."""
        try:
            self.cursor.execute('''
            INSERT INTO conversations (instruction, input, output, model_used)
            VALUES (?, ?, ?, ?)
            ''', (instruction, input_text, output_text, model_used))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            logging.error(f"Failed to save conversation: {e}")
            return None

    def update_feedback(self, conversation_id: int, feedback: str, rating: int = 0):
        """Update feedback for a conversation turn (Crucial for RLHF/DPO)."""
        try:
            self.cursor.execute('''
            UPDATE conversations 
            SET feedback = ?, rating = ?
            WHERE id = ?
            ''', (feedback, rating, conversation_id))
            self.conn.commit()
        except Exception as e:
            logging.error(f"Failed to update feedback: {e}")

    def get_training_data(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Retrieve high-quality conversations for training (rating > 0 or manual selection)."""
        self.cursor.execute('''
        SELECT instruction, input, output FROM conversations
        WHERE rating > 0 OR feedback IS NOT NULL
        LIMIT ?
        ''', (limit,))
        
        rows = self.cursor.fetchall()
        return [{"instruction": r[0], "input": r[1], "output": r[2]} for r in rows]

    def get_recent_interactions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取最近的交互记录
        Args:
            limit: 最多返回的记录条数
        Returns:
            交互记录列表，每条记录为包含id、指令、输入、输出、时间戳、评分、反馈的字典
        """
        self.cursor.execute('''
        SELECT id, instruction, input, output, timestamp, rating, feedback, model_used
        FROM conversations
        ORDER BY timestamp DESC
        LIMIT ?
        ''', (limit,))
        
        rows = self.cursor.fetchall()
        return [
            {
                "id": r[0],
                "instruction": r[1],
                "input": r[2],
                "output": r[3],
                "timestamp": r[4],
                "rating": r[5],
                "feedback": r[6],
                "model_used": r[7]
            } for r in rows
        ]

    def close(self):
        self.conn.close()

# Global instance will be initialized in main
