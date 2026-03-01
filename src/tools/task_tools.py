
import os
import logging
from typing import List, Dict, Optional
import json
import time

TODO_FILE = "TODO.md"

def manage_todo(action: str, task_id: Optional[str] = None, description: Optional[str] = None, status: Optional[str] = None) -> str:
    """
    Manage a persistent TODO list for the project.
    
    Args:
        action: 'add', 'list', 'update', 'remove', 'clear'
        task_id: ID of the task (required for update/remove)
        description: Task description (required for add)
        status: 'pending', 'in_progress', 'done' (for update)
        
    Returns:
        Result of the operation.
    """
    tasks = _load_tasks()
    
    if action == "add":
        if not description:
            return "Error: Description required for 'add'."
        new_id = str(int(time.time()))[-6:] # Simple ID
        tasks.append({
            "id": new_id,
            "description": description,
            "status": "pending",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        _save_tasks(tasks)
        return f"Task added: [{new_id}] {description}"
        
    elif action == "list":
        if not tasks:
            return "No tasks in TODO list."
        
        output = ["# Project TODO List\n"]
        for t in tasks:
            icon = " " if t['status'] == 'pending' else ("x" if t['status'] == 'done' else ">")
            output.append(f"- [{icon}] {t['id']}: {t['description']} ({t['status']})")
        return "\n".join(output)
        
    elif action == "update":
        if not task_id:
            return "Error: Task ID required for 'update'."
        
        found = False
        for t in tasks:
            if t['id'] == task_id:
                if status: t['status'] = status
                if description: t['description'] = description
                found = True
                break
        
        if found:
            _save_tasks(tasks)
            return f"Task {task_id} updated."
        return f"Task {task_id} not found."
        
    elif action == "remove":
        if not task_id:
            return "Error: Task ID required for 'remove'."
        
        initial_len = len(tasks)
        tasks = [t for t in tasks if t['id'] != task_id]
        
        if len(tasks) < initial_len:
            _save_tasks(tasks)
            return f"Task {task_id} removed."
        return f"Task {task_id} not found."
        
    elif action == "clear":
        _save_tasks([])
        return "TODO list cleared."
        
    return f"Unknown action: {action}"

def _load_tasks() -> List[Dict]:
    """Load tasks from TODO.md (parsing a simple markdown format)."""
    if not os.path.exists(TODO_FILE):
        return []
        
    tasks = []
    try:
        with open(TODO_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Parse format: - [x] 123456: Task description (status)
                if line.startswith("- [") and "]: " in line:
                    try:
                        # Extract status from bracket
                        check = line[3]
                        
                        # Extract ID
                        rest = line[6:]
                        if ": " not in rest: continue
                        task_id, rest = rest.split(": ", 1)
                        
                        # Extract description and status text
                        # Expected: Description (status)
                        if "(" in rest and rest.endswith(")"):
                            desc = rest.rsplit(" (", 1)[0]
                            status_text = rest.rsplit(" (", 1)[1][:-1]
                        else:
                            desc = rest
                            status_text = "done" if check == 'x' else ("in_progress" if check == '>' else "pending")
                            
                        tasks.append({
                            "id": task_id,
                            "description": desc,
                            "status": status_text,
                            "created_at": "" # Lost in MD format, acceptable
                        })
                    except:
                        continue
    except Exception as e:
        logging.error(f"Failed to load tasks: {e}")
        
    return tasks

def _save_tasks(tasks: List[Dict]):
    """Save tasks to TODO.md."""
    try:
        with open(TODO_FILE, 'w', encoding='utf-8') as f:
            f.write("# Project TODO List\n\n")
            for t in tasks:
                icon = " "
                if t['status'] == 'done': icon = "x"
                elif t['status'] == 'in_progress': icon = ">"
                
                f.write(f"- [{icon}] {t['id']}: {t['description']} ({t['status']})\n")
    except Exception as e:
        logging.error(f"Failed to save tasks: {e}")
