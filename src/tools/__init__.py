import importlib
import inspect
from src.tools import skills

from .file_tools import list_files, read_file, write_file, move_file, scan_project
from .code_tools import modify_skill, patch_core_code, create_skill, patch_code
from .system_tools import restart_system, run_command
from .web_tools import get_weather, web_search
from .repository_tools import list_github_repos, list_gitee_repos, list_all_repos, clone_repo, get_repo_info
from .video_tools import generate_video_from_text, generate_video_from_image, generate_video_between_images

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
        ]
        
        # 2. Dynamic Skills from src.tools.skills
        importlib.reload(skills) # Ensure fresh load
        skill_functions = [f for f in dir(skills) if inspect.isfunction(getattr(skills, f))]
        
        if skill_functions:
            descriptions.append("\nCustom Skills:")
            for i, func_name in enumerate(skill_functions, 12):
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
