import importlib
import inspect
from src import skills

from .file_tools import list_files, read_file, write_file, move_file, scan_project, register_document, check_documents_status
from .code_tools import modify_skill, patch_core_code, create_skill, patch_code
from .system_tools import restart_system, run_command
from .web_tools import get_weather, web_search
from .repository_tools import list_github_repos, list_gitee_repos, list_all_repos, clone_repo, get_repo_info
from .video_tools import generate_video_from_text, generate_video_from_image, generate_video_between_images
from .ai_assistant_tools import analyze_code, search_code, get_project_overview, analyze_change_impact, get_code_summary
# New tools
from .directory_tools import mkdir, rmdir, get_dir_info, list_dir_tree, copy_dir
from .file_utils_tools import delete_file, get_file_info, copy_file, rename_file, compare_files
from .git_tools import git_status, git_diff, git_add, git_commit, git_log, git_branch
from .json_yaml_tools import read_json, write_json, update_json, read_yaml, write_yaml, validate_json
from .text_processing_tools import find_in_files, replace_in_files, count_lines, extract_strings

class Tools:
    """Collection of tools for the AI agent to interact with the local system."""
    
    # Static methods are now imported from submodules
    modify_skill = staticmethod(modify_skill)
    patch_core_code = staticmethod(patch_core_code)
    restart_system = staticmethod(restart_system)
    create_skill = staticmethod(create_skill)
    get_weather = staticmethod(get_weather)
    web_search = staticmethod(web_search)
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
            "8. patch_code(file_path, old_str, new_str): Modify source code by replacing a block of text.",
            "9. get_weather(location): Get current weather report for a location.",
            "10. create_skill(name, code, description): Create a new reusable Python function (skill).",
            "11. modify_skill(skill_name, new_code, test_code): Update a skill ONLY if it passes tests. Use for self-improvement.",
            "12. patch_core_code(file_path, new_content, test_code): Safely modify a core system file (like core/agent.py) with automatic rollback on error.",
            "13. restart_system(): Restart the entire agent process to apply core changes.",
            # Repository management tools
            "14. list_github_repos(username=None): Get GitHub repository list (authenticated user or specified username).",
            "15. list_gitee_repos(username=None): Get Gitee repository list (authenticated user or specified username).",
            "16. list_all_repos(username=None): Get all repositories from both GitHub and Gitee platforms.",
            "17. clone_repo(repo_url, target_dir, branch=None): Clone a repository to local directory.",
            "18. get_repo_info(platform, owner, repo_name): Get detailed information about a specific repository.",
            # Video generation tools
            "19. generate_video_from_text(prompt, resolution='720p', ratio='16:9', duration=5): Generate video from text description.",
            "20. generate_video_from_image(image_url, prompt=None, resolution='720p', ratio='16:9', duration=5): Generate video from image (first frame animation).",
            "21. generate_video_between_images(first_image_url, last_image_url, prompt=None, resolution='720p', ratio='16:9', duration=5): Generate video with smooth transition between first and last frames.",
            # Document lifecycle tools
            "22. register_document(doc_path, title, doc_type, task_goal, related_files=None): Register a document for lifecycle management. Types: analysis(7d,auto-del), design(14d,auto-del), learning(3d,auto-del), decision(perm), config(perm), standard(30d).",
            "23. check_documents_status(): Check document status and show which documents need updates.",
            # AI Assistant Tools
            "24. analyze_code(file_path=None, function_name=None, class_name=None): Analyze code structure. Finds function/class definitions, shows args, docstrings, complexity.",
            "25. search_code(query, file_pattern='*.py'): Search for code patterns, function calls, variable usage across the project.",
            "26. get_project_overview(): Get project statistics: file count, lines of code, function/class counts, directory structure.",
            "27. analyze_change_impact(file_path, change_description): Analyze the impact of a code change - shows which files depend on the modified file.",
            "28. get_code_summary(file_path, max_lines=50): Get a summary of a code file: imports, definitions, and first 50 lines of actual code.",
            # Directory tools
            "29. mkdir(directory_path, exist_ok=True, parents=True): Create a directory. IMPORTANT: This is a Python function, NOT a shell command. Does NOT support brace expansion like {a,b,c}. Create multiple directories by calling mkdir separately for each.",
            "30. rmdir(directory_path, recursive=False): Remove a directory.",
            "31. get_dir_info(directory_path='.'): Get detailed directory information: file count, size, file type distribution.",
            "32. list_dir_tree(directory_path='.', max_depth=3): Display directory structure as a tree.",
            "33. copy_dir(src, dst, overwrite=False): Copy an entire directory.",
            # File utils tools
            "34. delete_file(file_path, safe_mode=True): Delete a file (safe mode protects core files).",
            "35. get_file_info(file_path): Get detailed file information: size, timestamps, MD5 hash.",
            "36. copy_file(src, dst, overwrite=False): Copy a file.",
            "37. rename_file(src, dst, overwrite=False): Rename a file.",
            "38. compare_files(file1, file2): Compare two files and show differences.",
            # Git tools
            "39. git_status(repo_path='.'): Get Git repository status.",
            "40. git_diff(file_path=None, repo_path='.', cached=False): Show Git diff.",
            "41. git_add(files, repo_path='.'): Add files to Git staging area.",
            "42. git_commit(message, repo_path='.', allow_empty=False): Commit staged changes.",
            "43. git_log(max_count=10, repo_path='.', oneline=True): Show commit history.",
            "44. git_branch(repo_path='.'): List Git branches.",
            # JSON/YAML tools
            "45. read_json(file_path): Read and display JSON file content.",
            "46. write_json(file_path, data, overwrite=False): Write data to JSON file.",
            "47. update_json(file_path, key_path, value, create_if_missing=False): Update a specific value in JSON file.",
            "48. read_yaml(file_path): Read and display YAML file content.",
            "49. write_yaml(file_path, data, overwrite=False): Write data to YAML file.",
            "50. validate_json(file_path): Validate JSON file format.",
            # Text processing tools
            "51. find_in_files(pattern, directory='.', file_pattern='*.py', use_regex=False): Search for text in multiple files.",
            "52. replace_in_files(old_text, new_text, directory='.', file_pattern='*.py', preview=True): Replace text in multiple files.",
            "53. count_lines(directory='.', file_pattern='*.py'): Count code lines in files.",
            "54. extract_strings(file_path, min_length=5): Extract string literals from code files.",
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
