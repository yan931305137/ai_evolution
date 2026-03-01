import importlib
import inspect
from src import skills

from .file_tools import list_files, read_file, write_file, move_file, scan_project, register_document, check_documents_status
from .code_tools import modify_skill, patch_core_code, create_skill, patch_code
from .system_tools import restart_system, run_command
from .web_tools import get_weather, web_search, open_browser
from .peripheral_tools import (
    mouse_move, mouse_click, mouse_double_click, mouse_drag, 
    key_press, key_release, key_tap, type_text, 
    key_enter, key_backspace, key_tab, key_esc
)
from .repository_tools import list_github_repos, list_gitee_repos, list_all_repos, clone_repo, get_repo_info
from .video_tools import generate_video_from_text, generate_video_from_image, generate_video_between_images
from .ai_assistant_tools import analyze_code, search_code, get_project_overview, analyze_change_impact, get_code_summary
# New tools
from .directory_tools import mkdir, rmdir, get_dir_info, list_dir_tree, copy_dir
from .file_utils_tools import delete_file, get_file_info, copy_file, rename_file, compare_files
from .git_tools import git_status, git_diff, git_add, git_commit, git_log, git_branch
from .json_yaml_tools import read_json, write_json, update_json, read_yaml, write_yaml, validate_json
from .text_processing_tools import find_in_files, replace_in_files, count_lines, extract_strings
from .agent_tools import spawn_agent, delegate_task, list_spawned_agents, get_agent_info, terminate_agent, spawn_agents_for_project
from .cicd_tools import trigger_ci_pipeline, check_ci_status, get_ci_logs, create_pr_from_branch, merge_pull_request, run_evolution_ci_pipeline
from .security_tools import scan_code_for_secrets, check_text_security, sanitize_sensitive_data, validate_pr_content, check_commit_message_safety, run_pre_commit_check, get_security_rules_info
from .docs_tools import update_project_docs, check_readme_compliance, check_gitignore_complete, update_readme_badges

class Tools:
    """Collection of tools for the AI agent to interact with the local system."""
    
    # Static methods are now imported from submodules
    modify_skill = staticmethod(modify_skill)
    patch_core_code = staticmethod(patch_core_code)
    restart_system = staticmethod(restart_system)
    create_skill = staticmethod(create_skill)
    get_weather = staticmethod(get_weather)
    web_search = staticmethod(web_search)
    open_browser = staticmethod(open_browser)
    # Peripheral tools
    mouse_move = staticmethod(mouse_move)
    mouse_click = staticmethod(mouse_click)
    mouse_double_click = staticmethod(mouse_double_click)
    mouse_drag = staticmethod(mouse_drag)
    key_press = staticmethod(key_press)
    key_release = staticmethod(key_release)
    key_tap = staticmethod(key_tap)
    type_text = staticmethod(type_text)
    key_enter = staticmethod(key_enter)
    key_backspace = staticmethod(key_backspace)
    key_tab = staticmethod(key_tab)
    key_esc = staticmethod(key_esc)
    
    patch_code = staticmethod(patch_code)
    list_files = staticmethod(list_files)
    read_file = staticmethod(read_file)
    write_file = staticmethod(write_file)
    move_file = staticmethod(move_file)
    run_command = staticmethod(run_command)
    scan_project = staticmethod(scan_project)
    register_document = staticmethod(register_document)
    check_documents_status = staticmethod(check_documents_status)
    # AI Assistant Tools
    analyze_code = staticmethod(analyze_code)
    search_code = staticmethod(search_code)
    get_project_overview = staticmethod(get_project_overview)
    analyze_change_impact = staticmethod(analyze_change_impact)
    get_code_summary = staticmethod(get_code_summary)
    # Repository management tools
    list_github_repos = staticmethod(list_github_repos)
    list_gitee_repos = staticmethod(list_gitee_repos)
    list_all_repos = staticmethod(list_all_repos)
    clone_repo = staticmethod(clone_repo)
    get_repo_info = staticmethod(get_repo_info)
    # Video generation tools
    generate_video_from_text = staticmethod(generate_video_from_text)
    generate_video_from_image = staticmethod(generate_video_from_image)
    generate_video_between_images = staticmethod(generate_video_between_images)
    # Directory tools
    mkdir = staticmethod(mkdir)
    rmdir = staticmethod(rmdir)
    get_dir_info = staticmethod(get_dir_info)
    list_dir_tree = staticmethod(list_dir_tree)
    copy_dir = staticmethod(copy_dir)
    # File utils tools
    delete_file = staticmethod(delete_file)
    get_file_info = staticmethod(get_file_info)
    copy_file = staticmethod(copy_file)
    rename_file = staticmethod(rename_file)
    compare_files = staticmethod(compare_files)
    # Git tools
    git_status = staticmethod(git_status)
    git_diff = staticmethod(git_diff)
    git_add = staticmethod(git_add)
    git_commit = staticmethod(git_commit)
    git_log = staticmethod(git_log)
    git_branch = staticmethod(git_branch)
    # JSON/YAML tools
    read_json = staticmethod(read_json)
    write_json = staticmethod(write_json)
    update_json = staticmethod(update_json)
    read_yaml = staticmethod(read_yaml)
    write_yaml = staticmethod(write_yaml)
    validate_json = staticmethod(validate_json)
    # Text processing tools
    find_in_files = staticmethod(find_in_files)
    replace_in_files = staticmethod(replace_in_files)
    count_lines = staticmethod(count_lines)
    extract_strings = staticmethod(extract_strings)
    # Dynamic Agent tools
    spawn_agent = staticmethod(spawn_agent)
    delegate_task = staticmethod(delegate_task)
    list_spawned_agents = staticmethod(list_spawned_agents)
    get_agent_info = staticmethod(get_agent_info)
    terminate_agent = staticmethod(terminate_agent)
    spawn_agents_for_project = staticmethod(spawn_agents_for_project)
    # CI/CD tools
    trigger_ci_pipeline = staticmethod(trigger_ci_pipeline)
    check_ci_status = staticmethod(check_ci_status)
    get_ci_logs = staticmethod(get_ci_logs)
    create_pr_from_branch = staticmethod(create_pr_from_branch)
    merge_pull_request = staticmethod(merge_pull_request)
    run_evolution_ci_pipeline = staticmethod(run_evolution_ci_pipeline)
    # Security tools
    scan_code_for_secrets = staticmethod(scan_code_for_secrets)
    check_text_security = staticmethod(check_text_security)
    sanitize_sensitive_data = staticmethod(sanitize_sensitive_data)
    validate_pr_content = staticmethod(validate_pr_content)
    check_commit_message_safety = staticmethod(check_commit_message_safety)
    run_pre_commit_check = staticmethod(run_pre_commit_check)
    get_security_rules_info = staticmethod(get_security_rules_info)
    # Documentation tools
    update_project_docs = staticmethod(update_project_docs)
    check_readme_compliance = staticmethod(check_readme_compliance)
    check_gitignore_complete = staticmethod(check_gitignore_complete)
    update_readme_badges = staticmethod(update_readme_badges)

    @classmethod
    def get_tool_descriptions(cls) -> str:
        """Return a formatted string describing available tools."""
        
        # 1. System Tools (Static)
        descriptions = [
            "Available Tools:",
            "1. list_files(directory='.'): List files in a directory.",
            "2. read_file(file_path): Read text content of a file.",
            "3. write_file(file_path, content): Write text to a file.",
            "4. move_file(src, dst): Move a file or directory.",
            "5. run_command(command): Execute a shell command (e.g., 'mkdir new_folder', 'python script.py').",
            "6. scan_project(directory='.'): Recursively scan the project structure and summarize code files.",
            "7. web_search(query): Search the internet for information using Bing.",
            "8. open_browser(url): Open a URL in the system's default web browser.",
            "9. patch_code(file_path, old_str, new_str): Modify source code by replacing a block of text.",
            "10. get_weather(location): Get current weather report for a location.",
            "11. create_skill(name, code, description): Create a new reusable Python function (skill).",
            "12. modify_skill(skill_name, new_code, test_code): Update a skill ONLY if it passes tests. Use for self-improvement.",
            "13. patch_core_code(file_path, new_content, test_code): Safely modify a core system file (like core/agent.py) with automatic rollback on error.",
            "14. restart_system(): Restart the entire agent process to apply core changes.",
            # Peripheral tools
            "15. mouse_move(x, y, duration=0.0): Move mouse to coordinates (x, y).",
            "16. mouse_click(button='left', count=1): Click mouse button.",
            "17. mouse_double_click(button='left'): Double click mouse button.",
            "18. mouse_drag(start_x, start_y, end_x, end_y, duration=0.2): Drag mouse from start to end coordinates.",
            "19. type_text(text, interval=0.02): Type text using keyboard.",
            "20. key_tap(key, count=1): Tap a specific key (e.g., 'enter', 'tab', 'esc').",
            "21. key_enter(count=1): Press Enter key.",
            # Repository management tools
            "22. list_github_repos(username=None): Get GitHub repository list (authenticated user or specified username).",
            "23. list_gitee_repos(username=None): Get Gitee repository list (authenticated user or specified username).",
            "24. list_all_repos(username=None): Get all repositories from both GitHub and Gitee platforms.",
            "25. clone_repo(repo_url, target_dir, branch=None): Clone a repository to local directory.",
            "26. get_repo_info(platform, owner, repo_name): Get detailed information about a specific repository.",
            # Video generation tools
            "27. generate_video_from_text(prompt, resolution='720p', ratio='16:9', duration=5): Generate video from text description.",
            "28. generate_video_from_image(image_url, prompt=None, resolution='720p', ratio='16:9', duration=5): Generate video from image (first frame animation).",
            "29. generate_video_between_images(first_image_url, last_image_url, prompt=None, resolution='720p', ratio='16:9', duration=5): Generate video with smooth transition between first and last frames.",
            # Document lifecycle tools
            "30. register_document(doc_path, title, doc_type, task_goal, related_files=None): Register a document for lifecycle management. Types: analysis(7d,auto-del), design(14d,auto-del), learning(3d,auto-del), decision(perm), config(perm), standard(30d).",
            "31. check_documents_status(): Check document status and show which documents need updates.",
            # AI Assistant Tools
            "32. analyze_code(file_path=None, function_name=None, class_name=None): Analyze code structure. Finds function/class definitions, shows args, docstrings, complexity.",
            "33. search_code(query, file_pattern='*.py'): Search for code patterns, function calls, variable usage across the project.",
            "34. get_project_overview(): Get project statistics: file count, lines of code, function/class counts, directory structure.",
            "35. analyze_change_impact(file_path, change_description): Analyze the impact of a code change - shows which files depend on the modified file.",
            "36. get_code_summary(file_path, max_lines=50): Get a summary of a code file: imports, definitions, and first 50 lines of actual code.",
            # Directory tools
            "37. mkdir(directory_path, exist_ok=True, parents=True): Create a directory. IMPORTANT: This is a Python function, NOT a shell command. Does NOT support brace expansion like {a,b,c}. Create multiple directories by calling mkdir separately for each.",
            "38. rmdir(directory_path, recursive=False): Remove a directory.",
            "39. get_dir_info(directory_path='.'): Get detailed directory information: file count, size, file type distribution.",
            "40. list_dir_tree(directory_path='.', max_depth=3): Display directory structure as a tree.",
            "41. copy_dir(src, dst, overwrite=False): Copy an entire directory.",
            # File utils tools
            "42. delete_file(file_path, safe_mode=True): Delete a file (safe mode protects core files).",
            "43. get_file_info(file_path): Get detailed file information: size, timestamps, MD5 hash.",
            "44. copy_file(src, dst, overwrite=False): Copy a file.",
            "45. rename_file(src, dst, overwrite=False): Rename a file.",
            "46. compare_files(file1, file2): Compare two files and show differences.",
            # Git tools
            "47. git_status(repo_path='.'): Get Git repository status.",
            "48. git_diff(file_path=None, repo_path='.', cached=False): Show Git diff.",
            "49. git_add(files, repo_path='.'): Add files to Git staging area.",
            "50. git_commit(message, repo_path='.', allow_empty=False): Commit staged changes.",
            "51. git_log(max_count=10, repo_path='.', oneline=True): Show commit history.",
            "52. git_branch(repo_path='.'): List Git branches.",
            # JSON/YAML tools
            "53. read_json(file_path): Read and display JSON file content.",
            "54. write_json(file_path, data, overwrite=False): Write data to JSON file.",
            "55. update_json(file_path, key_path, value, create_if_missing=False): Update a specific value in JSON file.",
            "56. read_yaml(file_path): Read and display YAML file content.",
            "57. write_yaml(file_path, data, overwrite=False): Write data to YAML file.",
            "58. validate_json(file_path): Validate JSON file format.",
            # Text processing tools
            "59. find_in_files(pattern, directory='.', file_pattern='*.py', use_regex=False): Search for text in multiple files.",
            "60. replace_in_files(old_text, new_text, directory='.', file_pattern='*.py', preview=True): Replace text in multiple files.",
            "61. count_lines(directory='.', file_pattern='*.py'): Count code lines in files.",
            "62. extract_strings(file_path, min_length=5): Extract string literals from code files.",
            # Dynamic Agent tools
            "63. spawn_agent(task_description, agent_name=None): Create a new Specialist Agent for a specific task type. The agent will be tailored to the task requirements.",
            "64. delegate_task(agent_id, subtask, context=None): Delegate a task to a previously created agent. The agent will execute independently and return results.",
            "65. list_spawned_agents(): List all dynamically created agents with their status and statistics.",
            "66. get_agent_info(agent_id): Get detailed information about a specific agent.",
            "67. terminate_agent(agent_id): Delete a dynamic agent that is no longer needed.",
            "68. spawn_agents_for_project(project_description): Create a team of agents for a complete project.",
            # CI/CD tools
            "69. trigger_ci_pipeline(branch='main', workflow='ci.yml', wait_for_completion=True): Trigger GitHub Actions CI/CD pipeline and wait for results.",
            "70. check_ci_status(run_id): Check the status of a running or completed CI/CD pipeline.",
            "71. get_ci_logs(run_id, max_lines=100): Get logs from a CI/CD pipeline run.",
            "72. create_pr_from_branch(branch, title, body=None, base_branch='main'): Create a Pull Request from a branch.",
            "73. merge_pull_request(pr_number, commit_message=None): Merge a Pull Request.",
            "74. run_evolution_ci_pipeline(evolution_branch='evolution', create_pr=True, auto_merge=False): Complete CI/CD pipeline for evolution changes including test, PR creation, and optional auto-merge.",
            # Security tools
            "75. scan_code_for_secrets(file_paths=None, scan_all=False, max_critical=0, max_high=0): Scan code for secrets and sensitive data. Returns scan results with findings.",
            "76. check_text_security(text): Check if text contains sensitive information like API keys or passwords.",
            "77. sanitize_sensitive_data(text): Remove sensitive data from text for safe logging.",
            "78. validate_pr_content(title, body, branch=''): Validate PR title and body for security issues before creating PR.",
            "79. check_commit_message_safety(message): Check if commit message contains sensitive information.",
            "80. run_pre_commit_check(): Run pre-commit security check on staged files.",
            "81. get_security_rules_info(): Get information about security scanning rules.",
            # Documentation tools
            "82. update_project_docs(test_results=None, new_features=None): Update README badges and check .gitignore before CI/CD.",
            "83. check_readme_compliance(): Check if README.md meets GitHub standards and return compliance score.",
            "84. check_gitignore_complete(): Check if .gitignore has all required security rules.",
            "85. update_readme_badges(test_status='passing', coverage='85%', security='audit passed'): Update README badge status.",
        ]
        
        # 2. Dynamic Skills from src.tools.skills
        importlib.reload(skills) # Ensure fresh load
        skill_functions = [f for f in dir(skills) if inspect.isfunction(getattr(skills, f))]
        
        if skill_functions:
            descriptions.append("\nCustom Skills:")
            for i, func_name in enumerate(skill_functions, 55):
                func = getattr(skills, func_name)
                doc = inspect.getdoc(func) or "No description provided."
                # Get signature for accurate args
                sig = inspect.signature(func)
                descriptions.append(f"{i}. {func_name}{sig}: {doc}")
                
        return "\n".join(descriptions)

    @classmethod
    def execute_tool(cls, tool_name: str, **kwargs) -> str:
        """Dispatch execution to the appropriate static method or skill."""
        
        # 1. Check System Tools
        if hasattr(cls, tool_name):
            method = getattr(cls, tool_name)
            try:
                # Handle args mismatch for simple tools
                if tool_name == 'web_search' and 'max_results' not in kwargs:
                     kwargs['max_results'] = 5
                     
                return method(**kwargs)
            except TypeError as e:
                # Add more helpful error for missing arguments
                import inspect
                sig = inspect.signature(method)
                return f"Error executing {tool_name}: {str(e)}\nExpected arguments: {sig}"
            except Exception as e:
                return f"Error executing {tool_name}: {str(e)}"
                
        # 2. Check Custom Skills
        elif hasattr(skills, tool_name):
            func = getattr(skills, tool_name)
            try:
                return str(func(**kwargs))
            except Exception as e:
                return f"Error executing skill '{tool_name}': {str(e)}"
                
        else:
            return f"Error: Tool '{tool_name}' not found."
