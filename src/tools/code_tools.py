import os
import shutil
import difflib
import subprocess
import sys
from pathlib import Path
from src.tools import skills
from src.utils.code_editor import CodeEditor

def run_core_tests() -> tuple[bool, str]:
    """
    Run the core test suite to ensure system stability.
    """
    try:
        # Run pytest on the tests directory
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/"],
            capture_output=True,
            text=True,
            timeout=60,  # 1 minute timeout for tests
            cwd=os.getcwd()
        )
        return result.returncode == 0, result.stdout + "\n" + result.stderr
    except Exception as e:
        return False, f"Failed to execute tests: {str(e)}"

def modify_skill(skill_name: str, new_code: str, test_code: str) -> str:
    """
    Safely modify or create a Python skill in 'core/skills.py'.
    Runs the provided 'test_code' against the new implementation before saving.
    """
    return CodeEditor.modify_skill(skill_name, new_code, test_code)

def patch_core_code(file_path: str, new_content: str, test_code: str) -> str:
    """
    Safely modify a CORE system file (e.g., core/agent.py) with rollback protection.
    DANGEROUS: This modifies the brain of the agent.
    """
    # 1. Run basic unit tests BEFORE attempting modification to ensure baseline is clean
    passed, output = run_core_tests()
    if not passed:
        return f"Evolution Guardrail Blocked: Existing tests failed. Cannot proceed with core modification.\nOutput:\n{output}"

    # 2. Proceed with modification using CodeEditor
    return CodeEditor.safe_patch_core(file_path, new_content, test_code)

def create_skill(name: str, code: str, description: str) -> str:
    """
    Create a new Python skill (function) and save it to the skills library.
    """
    try:
        # 1. Basic Validation
        if not name.isidentifier():
            return f"Error: '{name}' is not a valid Python identifier."
        
        if f"def {name}" not in code:
            return f"Error: The code must contain a function definition named '{name}'."
            
        # 2. Append to skills.py
        skills_path = Path("core/skills.py").resolve()
        
        with open(skills_path, "a", encoding="utf-8") as f:
            f.write(f"\n\n# Skill: {description}\n")
            f.write(code)
            f.write("\n")
            
        # 3. Reload module to make it available immediately
        importlib.reload(skills)
        
        return f"Successfully created skill '{name}'. It is now available for use."
        
    except Exception as e:
        return f"Error creating skill: {str(e)}"

def patch_code(file_path: str, old_str: str, new_str: str, force: bool = False) -> str:
    """
    Modify a file by replacing a specific string block.
    Features:
    - Fuzzy matching (ignores whitespace differences) if exact match fails.
    - Backup and rollback on failure.
    - Runs core tests after patching (Guardrail).
    
    Args:
        file_path: Path to the file.
        old_str: The code block to replace.
        new_str: The new code block.
        force: If True, skip post-patch testing (Use with caution!).
    """
    try:
        path = Path(file_path).resolve()
        if not path.exists():
            return f"Error: File '{file_path}' not found."
            
        # Create Backup
        backup_path = path.with_suffix(path.suffix + ".bak")
        shutil.copy2(path, backup_path)
        
        content = path.read_text(encoding='utf-8')
        
        # Normalize line endings
        content_norm = content.replace('\r\n', '\n')
        old_str_norm = old_str.replace('\r\n', '\n')
        new_str_norm = new_str.replace('\r\n', '\n')
        
        new_content = None
        
        # 1. Try Exact Match
        if old_str_norm in content_norm:
            new_content = content_norm.replace(old_str_norm, new_str_norm, 1)
        else:
            # 2. Try Fuzzy Match (Ignore leading/trailing whitespace on lines)
            # Split into lines
            content_lines = content_norm.splitlines()
            old_lines = old_str_norm.splitlines()
            
            # Find matching block
            start_idx = -1
            
            # Simple fuzzy search: match lines stripping whitespace
            # This is O(N*M) but files are usually small enough
            for i in range(len(content_lines) - len(old_lines) + 1):
                match = True
                for j in range(len(old_lines)):
                    if content_lines[i+j].strip() != old_lines[j].strip():
                        match = False
                        break
                if match:
                    start_idx = i
                    break
            
            if start_idx != -1:
                # Construct new content
                # Keep indentation of the first line if possible? 
                # Or just replace the block entirely. 
                # Issue: If we replace based on stripped match, we might lose indentation of the original file 
                # if we replace with new_str which has different indentation.
                # However, the user usually provides new_str with correct relative indentation.
                # Let's trust new_str but replace the lines found in content.
                
                prefix = "\n".join(content_lines[:start_idx])
                suffix = "\n".join(content_lines[start_idx + len(old_lines):])
                
                # Handle edge case where prefix/suffix might be empty
                new_content = (prefix + "\n" if prefix else "") + new_str_norm + ("\n" + suffix if suffix else "")
            else:
                 # Clean up backup
                if backup_path.exists(): os.remove(backup_path)
                return "Error: 'old_str' not found in file (tried exact and fuzzy match). Please check the content."

        # Write new content
        path.write_text(new_content, encoding='utf-8')
        
        # 3. Guardrail: Run Tests
        if not force:
            passed, output = run_core_tests()
            if not passed:
                # Rollback
                shutil.copy2(backup_path, path)
                if backup_path.exists(): os.remove(backup_path)
                return f"Evolution Guardrail Blocked: Tests failed after patching. Rolled back changes.\nOutput:\n{output}"
        
        # Success cleanup
        if backup_path.exists(): os.remove(backup_path)
        return f"Successfully patched '{file_path}'."
        
    except Exception as e:
        # Emergency Rollback
        if Path(file_path).with_suffix(Path(file_path).suffix + ".bak").exists():
             shutil.copy2(Path(file_path).with_suffix(Path(file_path).suffix + ".bak"), file_path)
        return f"Error patching file: {str(e)}"
