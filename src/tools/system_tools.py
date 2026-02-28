import sys
import platform
import subprocess

def restart_system() -> str:
    """
    Triggers a system restart to apply changes.
    Stops the current process and signals the Kernel to reboot.
    """
    print("Restarting system...")
    sys.exit(42) # Magic number for restart in main.py kernel

def run_command(command: str) -> str:
    """Run a shell command (Use with caution!)."""
    # Security: Block dangerous commands
    forbidden = ['rm -rf', 'format', 'del /s /q', 'mkfs'] 
    if any(f in command for f in forbidden):
            return f"Error: Command '{command}' is blocked for safety reasons."
            
    # Platform adaptation
    system = platform.system().lower()
    if system == 'windows':
        # Translate common Unix commands to Windows CMD
        # Note: This is a basic translation and might not handle complex flags
        cmd_map = {
            'ls': 'dir /b',
            'cp': 'copy',
            'mv': 'move',
            'rm': 'del',
            'clear': 'cls',
            'cat': 'type'
        }
        parts = command.split()
        if parts and parts[0] in cmd_map:
            # Simple replacement for the command verb
            command = cmd_map[parts[0]] + command[len(parts[0]):]
        
        # Handle specific cases
        if command.startswith('touch '):
                # Approximate 'touch' on Windows
                filename = command[6:].strip()
                command = f"if not exist {filename} type nul > {filename}"
                
        # Handle 'mkdir -p' which is invalid in CMD
        if 'mkdir -p' in command:
            command = command.replace('mkdir -p', 'mkdir')
            
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        output = result.stdout
        if result.stderr:
            output += f"\nSTDERR: {result.stderr}"
        return output.strip() or "(Command executed with no output)"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out."
    except Exception as e:
        return f"Error running command: {str(e)}"
