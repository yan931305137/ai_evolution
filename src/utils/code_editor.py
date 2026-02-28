import os
import sys
import inspect
import importlib
import subprocess
import shutil
from pathlib import Path
from src.tools import skills

class CodeEditor:
    """
    A special tool for self-programming.
    Allows the Agent to modify 'core/skills.py' safely by running tests first.
    """
    
    SKILLS_FILE = Path("core/skills.py").resolve()
    TEMP_SKILLS_FILE = Path("core/skills_temp.py").resolve()
    TEMP_TEST_FILE = Path("tests/temp_skill_test.py").resolve()

    @staticmethod
    def _run_script_sandboxed(script_path: Path, timeout: int = 15) -> subprocess.CompletedProcess:
        """
        Runs a Python script. If 'USE_DOCKER_SANDBOX' is 'true', attempts to run inside a Docker container.
        """
        use_docker = os.getenv("USE_DOCKER_SANDBOX", "false").lower() == "true"
        cwd = os.getcwd()
        
        if use_docker:
            try:
                # Check if docker is available
                subprocess.run(["docker", "--version"], check=True, capture_output=True)
                
                # Assume python:3.10 image is available or pullable
                # Mount current directory to /app
                # script_path must be relative to cwd for docker mapping
                rel_path = script_path.relative_to(cwd)
                
                cmd = [
                    "docker", "run", "--rm",
                    "-v", f"{cwd}:/app",
                    "-w", "/app",
                    "python:3.10",
                    "python", str(rel_path)
                ]
                
                return subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=cwd
                )
            except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
                # ValueError might happen if script_path is not in cwd
                print("Warning: Docker enabled but not found or failed. Falling back to local execution.")
                
        # Local execution
        return subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd
        )

    @staticmethod
    def _extract_function_code(file_path: Path, func_name: str) -> tuple[str, int, int]:
        """
        Extracts the code, start line, and end line of a function from a file.
        Returns (code, start_line_idx, end_line_idx) or None.
        """
        if not file_path.exists():
            return None
            
        lines = file_path.read_text(encoding='utf-8').splitlines()
        
        # Simple parser to find function definition
        start_idx = -1
        end_idx = -1
        
        # 1. Find start
        for i, line in enumerate(lines):
            if line.strip().startswith(f"def {func_name}("):
                start_idx = i
                break
        
        if start_idx == -1:
            return None
            
        # 2. Find end (next def or end of file)
        # This is a naive heuristic: assumes top-level functions and standard indentation
        # For a robust solution, we would use AST, but this is sufficient for 'skills.py'
        # which usually contains flat functions.
        for i in range(start_idx + 1, len(lines)):
            if lines[i].startswith("def ") or lines[i].startswith("class ") or lines[i].startswith("# Skill:"):
                end_idx = i
                break
        
        if end_idx == -1:
            end_idx = len(lines)
            
        return "\n".join(lines[start_idx:end_idx]), start_idx, end_idx

    @classmethod
    def modify_skill(cls, skill_name: str, new_code: str, test_code: str) -> str:
        """
        Modify an existing skill in 'core/skills.py'.
        """
        # ... (validation skipped for brevity)
        if f"def {skill_name}" not in new_code:
            return f"Error: 'new_code' must contain 'def {skill_name}'."
            
        if not cls.SKILLS_FILE.exists():
            return "Error: core/skills.py not found."

        try:
            # 2. Read original content
            original_content = cls.SKILLS_FILE.read_text(encoding='utf-8')
            lines = original_content.splitlines()
            
            # 3. Locate function
            func_info = cls._extract_function_code(cls.SKILLS_FILE, skill_name)
            
            if func_info:
                _, start, end = func_info
                # Replace existing function
                new_lines = lines[:start] + new_code.splitlines() + lines[end:]
            else:
                # Function doesn't exist, append it
                new_lines = lines + ["\n"] + new_code.splitlines()
            
            new_content = "\n".join(new_lines)
            
            # 4. Write to TEMP file
            cls.TEMP_SKILLS_FILE.write_text(new_content, encoding='utf-8')
            
            # 5. Create Test File
            indented_test_code = "\n".join(["        " + line for line in test_code.splitlines()])
            
            test_file_content = f"""
import sys
import os
import inspect

# Add project root to path
sys.path.insert(0, os.getcwd())
# Also add the parent of 'tests' (which is project root)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Try to import the temporary module
    import src.tools.skills_temp as skills_temp
except ImportError as e:
    print(f"IMPORT_ERROR: {{e}}")
    print(f"sys.path: {{sys.path}}")
    sys.exit(1)

import traceback

# ... (imports)

def run_tests():
    print(f"Testing function '{skill_name}' from {{skills_temp.__file__}}")
    
    # Inject the function into global namespace for the test code to use directly
    if hasattr(skills_temp, '{skill_name}'):
        globals()['{skill_name}'] = getattr(skills_temp, '{skill_name}')
    else:
        print(f"FUNCTION_NOT_FOUND: {skill_name}")
        sys.exit(1)

    try:
{indented_test_code}
        print("TEST_PASSED")
    except AssertionError:
        print(f"TEST_FAILED: Assertion Error")
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"TEST_FAILED: {{e}}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
"""
            cls.TEMP_TEST_FILE.write_text(test_file_content, encoding='utf-8')
            
            # 6. Run Test
            result = cls._run_script_sandboxed(cls.TEMP_TEST_FILE, timeout=10)
            
            # 7. Check Result
            if result.returncode == 0 and "TEST_PASSED" in result.stdout:
                # Success! Overwrite original file
                cls.SKILLS_FILE.write_text(new_content, encoding='utf-8')
                
                # Cleanup
                if cls.TEMP_SKILLS_FILE.exists(): os.remove(cls.TEMP_SKILLS_FILE)
                if cls.TEMP_TEST_FILE.exists(): os.remove(cls.TEMP_TEST_FILE)
                
                # Reload skills
                importlib.reload(skills)
                
                return f"Successfully modified skill '{skill_name}'. Tests passed."
            else:
                # Failure
                error_msg = result.stderr + "\n" + result.stdout
                
                # Cleanup
                if cls.TEMP_SKILLS_FILE.exists(): os.remove(cls.TEMP_SKILLS_FILE)
                if cls.TEMP_TEST_FILE.exists(): os.remove(cls.TEMP_TEST_FILE)
                
                return f"Failed to modify skill. Tests failed:\n{error_msg}"

        except Exception as e:
            # Cleanup on error
            if cls.TEMP_SKILLS_FILE.exists(): os.remove(cls.TEMP_SKILLS_FILE)
            if cls.TEMP_TEST_FILE.exists(): os.remove(cls.TEMP_TEST_FILE)
            return f"Error in CodeEditor: {str(e)}"

    @classmethod
    def safe_patch_core(cls, file_path: str, new_content: str, test_code: str) -> str:
        """
        Safely modify a core file (e.g., core/agent.py) with rollback protection.
        
        Args:
            file_path: Relative path to the core file (e.g., 'core/agent.py').
            new_content: The full content of the file.
            test_code: Python code to verify the new file. Should use 'assert'.
        """
        target_path = Path(file_path).resolve()
        backup_path = target_path.with_suffix(target_path.suffix + ".bak")
        test_file = Path("tests/temp_core_test.py").resolve()
        
        if not target_path.exists():
            return f"Error: Target file '{file_path}' does not exist."
            
        # 1. Create Backup
        try:
            shutil.copy2(target_path, backup_path)
        except Exception as e:
            return f"Error creating backup: {e}"
            
        try:
            # 2. Write New Content
            target_path.write_text(new_content, encoding='utf-8')
            
            # 3. Create Test File
            test_script = f"""
import sys
import os
import traceback
import importlib

# Add project root to path
sys.path.insert(0, os.getcwd())

def run_tests():
    try:
        # 1. Attempt to import the modified module
        # We need to deduce module name from path, e.g., core/agent.py -> core.agent
        # This is a bit tricky, let's assume standard structure
        rel_path = "{file_path}".replace("\\\\", "/")
        module_name = rel_path.replace(".py", "").replace("/", ".")
        
        print(f"Testing module import: {{module_name}}")
        if module_name in sys.modules:
            del sys.modules[module_name] # Force reload
        
        mod = importlib.import_module(module_name)
        
        # 2. Run user provided test code
        # Inject module into test scope as 'module'
        local_scope = {{'module': mod, 'sys': sys, 'os': os}}
        exec({repr(test_code)}, local_scope)
        
        print("TEST_PASSED")
        
    except Exception:
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
"""
            test_file.write_text(test_script, encoding='utf-8')
            
            # 4. Run Verification Process
            result = cls._run_script_sandboxed(test_file, timeout=15)
            
            # 5. Check Result
            if result.returncode == 0 and "TEST_PASSED" in result.stdout:
                # Success: Keep the change
                if backup_path.exists(): os.remove(backup_path)
                if test_file.exists(): os.remove(test_file)
                return f"Successfully patched '{file_path}'. Verification passed."
            else:
                # Failure: Rollback
                shutil.copy2(backup_path, target_path)
                if backup_path.exists(): os.remove(backup_path)
                if test_file.exists(): os.remove(test_file)
                
                error_log = result.stderr + "\n" + result.stdout
                return f"Patch verification failed. Rolled back changes.\nOutput:\n{error_log}"
                
        except Exception as e:
            # Emergency Rollback
            if backup_path.exists():
                shutil.copy2(backup_path, target_path)
                os.remove(backup_path)
            if test_file.exists():
                os.remove(test_file)
            return f"Critical Error during patching: {e}"
